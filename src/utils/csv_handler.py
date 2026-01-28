"""
CSV file operations
"""
from datetime import datetime
import pandas as pd
import os

class CSVHandler:
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        self.raw_dir = os.path.join(data_dir, "raw")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)
    
    def save_raw_data(self, df: pd.DataFrame, filename: str = None):
        """
        Save raw scraped data
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_leads_{timestamp}.csv"
        
        filepath = os.path.join(self.raw_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Raw data saved to: {filepath}")
        return filepath
    
    def save_processed_data(self, df: pd.DataFrame, filename: str = "leads.csv"):
        """
        Save processed/scored data
        """
        filepath = os.path.join(self.processed_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Processed data saved to: {filepath}")
        return filepath
    
    def load_latest_data(self) -> pd.DataFrame:
        """
        Load the latest processed data
        """
        filepath = os.path.join(self.processed_dir, "leads.csv")
        
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                print(f"Loaded data from: {filepath}")
                return df
            except Exception as e:
                print(f"Error loading data: {e}")
                return pd.DataFrame()
        else:
            print(f"No data file found at: {filepath}")
            return pd.DataFrame()
    
    def export_for_dashboard(self, df: pd.DataFrame) -> str:
        """
        Export data for dashboard (main CSV in data directory)
        """
        filepath = os.path.join(self.data_dir, "leads.csv")
        df.to_csv(filepath, index=False)
        print(f"Dashboard data exported to: {filepath}")
        return filepath
    
    def backup_data(self, df: pd.DataFrame):
        """
        Create backup of current data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.processed_dir, f"backup_leads_{timestamp}.csv")
        df.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")