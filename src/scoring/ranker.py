"""
Rank leads based on scores and additional criteria
"""
from datetime import datetime
import pandas as pd

class LeadRanker:
    def __init__(self):
        pass
    
    def rank_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main ranking function with PROPER column order
        """
        if df.empty:
            return df
        
        # Create a copy
        ranked_df = df.copy()
        
        # Ensure 'score' column exists
        if 'score' not in ranked_df.columns:
            ranked_df['score'] = 0
        
        # Calculate priority score (combination of score and other factors)
        ranked_df['priority_score'] = ranked_df.apply(self._calculate_priority, axis=1)
        
        # Sort by priority score (descending)
        ranked_df = ranked_df.sort_values('priority_score', ascending=False)
        
        # Reset index to create final rank
        ranked_df = ranked_df.reset_index(drop=True)
        ranked_df['final_rank'] = ranked_df.index + 1
        
        # ===== FIXED: PROPER COLUMN ORDER =====
        # Define the EXACT column order we want
        column_order = [
            'final_rank',        # 1. Rank (most important - first column)
            'name',              # 2. Name
            'title',             # 3. Job Title
            'company',           # 4. Company/University
            'location',          # 5. Location
            'score',             # 6. Score (0-100)
            'email',             # 7. Email
            'paper_title',       # 8. Recent Paper
            'paper_date',        # 9. Paper Date
            'journal',           # 10. Journal
            'is_corresponding_author',  # 11. Corresponding Author?
            'affiliation',       # 12. Full Affiliation
            'data_source',       # 13. Data Source
            'priority_score',    # 14. Internal Priority Score
            'search_keywords'    # 15. Search Keywords
        ]
        
        # Keep only columns that actually exist in the DataFrame
        existing_columns = [col for col in column_order if col in ranked_df.columns]
        
        # Add any remaining columns (just in case)
        other_columns = [col for col in ranked_df.columns if col not in existing_columns]
        final_columns = existing_columns + other_columns
        
        # Reorder DataFrame with exact column order
        ranked_df = ranked_df[final_columns]
        
        # Ensure 'rank' column doesn't conflict (remove if exists)
        if 'rank' in ranked_df.columns and 'rank' != 'final_rank':
            ranked_df = ranked_df.drop(columns=['rank'])
        
        return ranked_df
    
    def _calculate_priority(self, row):
        """
        Calculate priority score (0-1) for sorting
        """
        # Get base score (normalize to 0-1)
        base_score = row.get('score', 0) / 100
        
        # Bonus for corresponding author
        author_bonus = 0.1 if row.get('is_corresponding_author', False) else 0
        
        # Bonus for recent papers
        recency_bonus = 0
        if 'paper_date' in row and row['paper_date']:
            try:
                # Try to parse date
                if isinstance(row['paper_date'], str):
                    # Extract year if possible
                    if len(row['paper_date']) >= 4:
                        year = int(row['paper_date'][:4])
                        current_year = datetime.now().year
                        if year >= current_year - 1:  # Last 2 years
                            recency_bonus = 0.05
            except:
                pass
        
        # Bonus for hub location
        location_bonus = 0
        if 'location' in row and row['location']:
            hub_locations = ['boston', 'cambridge', 'san francisco', 'london', 
                           'new york', 'basel', 'zurich', 'tokyo', 'singapore']
            location_str = str(row['location']).lower()
            if any(hub in location_str for hub in hub_locations):
                location_bonus = 0.05
        
        return base_score + author_bonus + recency_bonus + location_bonus
    
    def filter_top_leads(self, df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
        """
        Get top N leads
        """
        if df.empty:
            return df
        
        ranked_df = self.rank_leads(df)
        return ranked_df.head(top_n)
    
    def export_for_display(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for display in Streamlit table
        Returns a clean DataFrame with properly named columns
        """
        if df.empty:
            return df
        
        # Start with ranked data
        display_df = self.rank_leads(df).copy()
        
        # Rename columns for user-friendly display
        rename_map = {
            'final_rank': 'Rank',
            'name': 'Name',
            'title': 'Title',
            'company': 'Company',
            'location': 'Location',
            'score': 'Score',
            'email': 'Email',
            'paper_title': 'Recent Paper',
            'paper_date': 'Paper Date',
            'journal': 'Journal',
            'is_corresponding_author': 'Corresponding Author',
            'affiliation': 'Affiliation',
            'data_source': 'Data Source',
            'priority_score': 'Priority Score',
            'search_keywords': 'Search Keywords'
        }
        
        # Apply renaming for columns that exist
        display_df = display_df.rename(columns={
            old: new for old, new in rename_map.items() 
            if old in display_df.columns
        })
        
        return display_df