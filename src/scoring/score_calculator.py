"""
Scoring engine to calculate lead scores (0-100)
"""
from datetime import datetime
from typing import Dict
import pandas as pd
import json
import os

class LeadScorer:

    def __init__(self, config_path: str = None):
        # Get absolute path to config
        current_file = os.path.abspath(__file__) 
        src_dir = os.path.dirname(os.path.dirname(current_file))  # D:/.../src
        project_root = os.path.dirname(src_dir)  
        
        if config_path is None:
            config_path = os.path.join(project_root, "config", "keywords.json")
        
        print(f"Looking for config at: {config_path}")
        
        if not os.path.exists(config_path):
            # Try alternative path
            alt_path = os.path.join(os.getcwd(), "config", "keywords.json")
            print(f"Trying alternative: {alt_path}")
            if os.path.exists(alt_path):
                config_path = alt_path
            else:
                # Create default config
                print("Creating default config file...")
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                default_config = {
                    "search_terms": ["Drug-Induced Liver Injury"],
                    "scoring_weights": {"title_match": 30, "recent_publication": 40}
                }
                with open(config_path, 'w') as f:
                    json.dump(default_config, f)
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.weights = self.config['scoring_weights']
    
    def calculate_score(self, lead: Dict) -> int:
        """
        Calculate score for a single lead (0-100)
        """
        score = 0
        
        # 1. Title Match (+30)
        title = str(lead.get('title', '')).lower()
        print(f"  Title: {title}")
    
        for keyword in self.config['high_score_keywords']:
            if keyword.lower() in title:
                score += self.weights['title_match']
                print(f"  +{self.weights['title_match']} for title keyword: {keyword}")
                break
        
        # 2. Recent Publication (+40)
        paper_date = lead.get('paper_date', '')
        if self._is_recent_publication(paper_date):
            score += self.weights['recent_publication']
        
        # 3. Hub Location (+10)
        location = str(lead.get('location', '')).lower()
        for hub in self.config['hub_locations']:
            if hub.lower() in location:
                score += self.weights['hub_location']
                break
        
        # 4. Corresponding Author (+15)
        if lead.get('is_corresponding_author', False):
            score += self.weights['corresponding_author']
        
        # 5. Title contains high-value words
        for high_title in self.config['high_score_titles']:
            if high_title.lower() in title:
                score += 20  # Bonus for director/head titles
                break
        
        # 6. Paper contains specific keywords
        search_text = f"{lead.get('paper_title', '')} {lead.get('search_keywords', '')}".lower()
        if any(keyword.lower() in search_text for keyword in ['3d', 'in vitro', 'organ-on-chip']):
            score += self.weights['tech_usage']
        
        # 7. Company name suggests biotech/pharma
        company = str(lead.get('company', '')).lower()
        if any(word in company for word in ['bio', 'pharma', 'therapeutics', 'biotech']):
            score += 10  # Bonus for biotech companies
        
        # Cap at 100
        print(f"  Final score: {score}")
        return min(score, 100)
    
    def _is_recent_publication(self, date_str: str) -> bool:
        """
        Check if publication is within last 2 years
        """
        try:
            if not date_str:
                return False
            
            # Try to parse different date formats
            for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
                try:
                    pub_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False
            
            # Check if within last 2 years
            two_years_ago = datetime.now().replace(year=datetime.now().year - 2)
            return pub_date >= two_years_ago
            
        except:
            return False
    
    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add score column to DataFrame
        """
        if df.empty:
            return df
        
        # Calculate score for each row
        scores = []
        for _, row in df.iterrows():
            score = self.calculate_score(row.to_dict())
            scores.append(score)
        
        df['score'] = scores
        
        # Add rank based on score
        df['rank'] = df['score'].rank(method='dense', ascending=False).astype(int)
        
        # Sort by rank
        df = df.sort_values('rank')
        
        return df
    
    def categorize_score(self, score: int) -> str:
        """
        Categorize score into priority levels
        """
        if score >= 80:
            return "Hot Lead"
        elif score >= 60:
            return "Warm Lead"
        elif score >= 40:
            return "Cold Lead"
        else:
            return "Low Priority"