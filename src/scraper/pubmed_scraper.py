"""
PubMed API scraper to fetch relevant research papers and authors
"""
import xml.etree.ElementTree as ET
from typing import List, Dict
import pandas as pd
import requests
import time
import json
import re
from ..utils.data_cleaner import extract_email, extract_location, clean_name, extract_company

class PubMedScraper:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = "your-email@example.com"  # Change this to your email
        
    def search_papers(self, query: str, max_results: int = 50) -> List[str]:
        """
        Search PubMed for papers matching query
        Returns list of PubMed IDs (PMIDs)
        """
        try:
            search_url = f"{self.base_url}esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'email': self.email,
                'sort': 'relevance'  # Get most relevant papers
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            paper_ids = data.get('esearchresult', {}).get('idlist', [])
            
            print(f"✅ Found {len(paper_ids)} papers for query: {query}")
            return paper_ids
            
        except Exception as e:
            print(f"❌ Error searching PubMed for '{query}': {e}")
            return []
    
    def get_paper_details(self, paper_ids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for each paper
        """
        all_details = []
        
        if not paper_ids:
            return all_details
        
        try:
            fetch_url = f"{self.base_url}efetch.fcgi"
            
            # Fetch all papers at once (PubMed allows up to 100)
            params = {
                'db': 'pubmed',
                'id': ','.join(paper_ids),
                'retmode': 'xml',
                'email': self.email
            }
            
            print(f"📄 Fetching details for {len(paper_ids)} papers...")
            response = requests.get(fetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the XML response
            root = ET.fromstring(response.content)
            
            # Find all articles
            for article in root.findall('.//PubmedArticle'):
                paper_data = self._parse_paper_element(article)
                if paper_data:
                    all_details.append(paper_data)
            
            print(f"✅ Successfully parsed {len(all_details)} papers")
            
        except Exception as e:
            print(f"❌ Error fetching paper details: {e}")
            import traceback
            traceback.print_exc()
        
        return all_details
    
    def _parse_paper_element(self, article) -> Dict:
        """
        Parse a single PubMed article element
        """
        try:
            # Extract PMID
            pmid_element = article.find('.//PMID')
            pmid = pmid_element.text if pmid_element is not None else ""
            
            # Extract title
            title_element = article.find('.//ArticleTitle')
            title = title_element.text if title_element is not None else ""
            
            # Extract abstract
            abstract_element = article.find('.//AbstractText')
            abstract = abstract_element.text if abstract_element is not None else ""
            
            # Extract publication date
            pub_date = ""
            pub_date_element = article.find('.//PubDate/Year')
            if pub_date_element is not None:
                pub_date = pub_date_element.text
            else:
                pub_date_element = article.find('.//PubMedPubDate[@PubStatus="pubmed"]/Year')
                if pub_date_element is not None:
                    pub_date = pub_date_element.text
            
            # Extract journal
            journal_element = article.find('.//Journal/Title')
            journal = journal_element.text if journal_element is not None else ""
            
            # Extract authors
            authors = []
            corresponding_author = ""
            
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author_elem in author_list.findall('Author'):
                    # Get author name
                    last_name_elem = author_elem.find('LastName')
                    fore_name_elem = author_elem.find('ForeName')
                    
                    if last_name_elem is not None and fore_name_elem is not None:
                        name = f"{fore_name_elem.text} {last_name_elem.text}"
                    elif last_name_elem is not None:
                        name = last_name_elem.text
                    else:
                        continue
                    
                    # Get affiliation
                    affiliation_elem = author_elem.find('AffiliationInfo/Affiliation')
                    affiliation = affiliation_elem.text if affiliation_elem is not None else ""
                    
                    # Get email from affiliation
                    email = extract_email(affiliation)
                    
                    # Check if corresponding author
                    is_corresponding = False
                    for identifier in author_elem.findall('Identifier'):
                        if identifier.get('Source', '').lower() == 'email':
                            email = identifier.text
                            is_corresponding = True
                    
                    author_data = {
                        'name': name,
                        'affiliation': affiliation,
                        'email': email,
                        'is_corresponding': is_corresponding
                    }
                    authors.append(author_data)
                    
                    if is_corresponding:
                        corresponding_author = name
            
            # If no corresponding author found, use first author
            if not corresponding_author and authors:
                corresponding_author = authors[0]['name']
            
            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'corresponding_author': corresponding_author,
                'publication_date': pub_date,
                'journal': journal
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing article: {e}")
            return None
    
    def find_authors_from_keywords(self, keywords_file: str = "../../config/keywords.json") -> pd.DataFrame:
        """
        Main function: Search for papers based on keywords and extract authors
        """
        # Load keywords
        try:
            with open(keywords_file, 'r') as f:
                config = json.load(f)
            search_terms = config.get('search_terms', ["Drug-Induced Liver Injury"])
        except:
            search_terms = ["Drug-Induced Liver Injury", "3D cell culture", "hepatic spheroids"]
        
        all_authors = []
        papers_processed = 0
        
        for term in search_terms[:3]:  # Limit to 3 terms to avoid too many requests
            print(f"\n🔍 Searching for: {term}")
            
            # Search for papers
            paper_ids = self.search_papers(term, max_results=50)
            
            
            if not paper_ids:
                print(f"   No papers found for: {term}")
                continue
            
            # Get paper details
            papers = self.get_paper_details(paper_ids)
            papers_processed += len(papers)
            
            # Extract authors from papers
            for paper in papers:
                if not paper or 'authors' not in paper:
                    continue
                    
                for author in paper.get('authors', []):
                    # Process author data
                    processed_author = self._process_author_data(author, paper)
                    if processed_author:
                        all_authors.append(processed_author)
            
            time.sleep(0.5)  # Be nice to PubMed API
        
        print(f"\n📊 Total: {papers_processed} papers processed, {len(all_authors)} authors found")
        
        # Convert to DataFrame
        if all_authors:
            df = pd.DataFrame(all_authors)
            
            # Remove duplicates based on email
            if not df.empty and 'email' in df.columns:
                df = df.drop_duplicates(subset=['email'], keep='first')
            
            print(f"📈 Final unique authors: {len(df)}")
            return df
        else:
            print("❌ No authors extracted. Returning empty DataFrame.")
            return pd.DataFrame()
    
    def _process_author_data(self, author: Dict, paper: Dict) -> Dict:
        """
        Process and clean individual author data
        """
        try:
            name = clean_name(author.get('name', ''))
            affiliation = author.get('affiliation', '')
            email = author.get('email', '') or extract_email(affiliation)
            
            if not name:
                return None
            
            # Extract location and company
            location = extract_location(affiliation)
            company = extract_company(affiliation)
            
            # Determine title based on patterns
            title = self._guess_title(name, affiliation, paper.get('title', ''))
            
            # Check if corresponding author
            is_corresponding = author.get('is_corresponding', False) or name == paper.get('corresponding_author', '')
            
            return {
                'name': name,
                'title': title,
                'company': company,
                'affiliation': affiliation,
                'location': location,
                'email': email,
                'paper_title': paper.get('title', ''),
                'paper_date': paper.get('publication_date', ''),
                'journal': paper.get('journal', ''),
                'is_corresponding_author': is_corresponding,
                'data_source': 'PubMed',
                'search_keywords': paper.get('title', '') + ' ' + (paper.get('abstract', '')[:200] if paper.get('abstract') else '')
            }
            
        except Exception as e:
            print(f"Error processing author {author.get('name')}: {e}")
            return None
    
    def _guess_title(self, name: str, affiliation: str, paper_title: str) -> str:
        """
        Guess job title based on name patterns, affiliation, and paper
        """
        # Check name for titles
        name_lower = name.lower()
        if 'prof' in name_lower or 'professor' in name_lower:
            return "Professor"
        if 'dr.' in name_lower or ' dr ' in name_lower:
            return "Doctor/Researcher"
        
        # Check affiliation
        aff_lower = affiliation.lower()
        if any(word in aff_lower for word in ['university', 'college', 'institute']):
            if any(word in aff_lower for word in ['department', 'division']):
                return "Faculty/Researcher"
            return "Academic Researcher"
        
        if any(word in aff_lower for word in ['hospital', 'medical center', 'clinic']):
            return "Clinical Researcher"
        
        if any(word in aff_lower for word in ['pharma', 'biotech', 'therapeutics', 'inc', 'ltd']):
            return "Industry Scientist"
        
        # Check paper title for clues
        paper_lower = paper_title.lower()
        if any(word in paper_lower for word in ['clinical', 'trial', 'patient']):
            return "Clinical Researcher"
        if any(word in paper_lower for word in ['professor', 'chair', 'director']):
            return "Professor/Director"
        
        return "Researcher/Scientist"