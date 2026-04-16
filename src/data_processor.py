import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import os
import re

class DataProcessor:
    def __init__(self, dataset_path):
        """Load and process Gowalla dataset"""
        print(f"Loading dataset from: {dataset_path}")
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        
        # Read file line by line to handle mixed delimiters
        data_rows = []
        with open(dataset_path, 'r') as f:
            for line in f:
                # Split on whitespace (handles both spaces and tabs)
                parts = line.strip().split()
                if len(parts) >= 5:
                    data_rows.append(parts[:5])
        
        # Create DataFrame
        self.df = pd.DataFrame(data_rows, columns=['user_id', 'checkin_time', 'latitude', 'longitude', 'location_id'])
        
        # Convert types
        self.df['user_id'] = self.df['user_id'].astype(str)
        self.df['location_id'] = self.df['location_id'].astype(str)
        self.df['latitude'] = pd.to_numeric(self.df['latitude'], errors='coerce')
        self.df['longitude'] = pd.to_numeric(self.df['longitude'], errors='coerce')
        
        # Remove invalid coordinates
        self.df = self.df.dropna(subset=['latitude', 'longitude'])
        
        print(f"Loaded {len(self.df)} valid check-ins")
        self.process_data()
    
    def process_data(self):
        """Extract and prepare features"""
        # Convert check-in time to datetime
        self.df['checkin_time'] = pd.to_datetime(self.df['checkin_time'], errors='coerce')
        
        # Remove rows with invalid dates
        self.df = self.df.dropna(subset=['checkin_time'])
        
        # Extract time features
        self.df['hour'] = self.df['checkin_time'].dt.hour
        self.df['day_of_week'] = self.df['checkin_time'].dt.dayofweek
        
        # Categorize time of day
        self.df['time_category'] = self.df['hour'].apply(self.get_time_category)
        
        # Create location popularity score
        location_stats = self.df.groupby('location_id').size().reset_index(name='visit_count')
        
        # Normalize popularity scores
        if len(location_stats) > 1:
            scaler = MinMaxScaler()
            location_stats['popularity_score'] = scaler.fit_transform(
                location_stats[['visit_count']]
            )
        else:
            location_stats['popularity_score'] = 1.0
        
        # Merge back
        self.df = self.df.merge(
            location_stats[['location_id', 'popularity_score']], 
            on='location_id', 
            how='left'
        )
        
        print(f"✓ Data loaded successfully!")
        print(f"  - Total check-ins: {len(self.df):,}")
        print(f"  - Unique users: {self.df['user_id'].nunique():,}")
        print(f"  - Unique locations: {self.df['location_id'].nunique():,}")
        print(f"  - Date range: {self.df['checkin_time'].min()} to {self.df['checkin_time'].max()}")
    
    @staticmethod
    def get_time_category(hour):
        """Categorize time into morning/afternoon/evening/night"""
        if pd.isna(hour):
            return 'night'
        elif 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def get_user_history(self, user_id):
        """Get user's check-in history"""
        return self.df[self.df['user_id'] == str(user_id)]
    
    def get_location_info(self, location_id):
        """Get location details"""
        loc_data = self.df[self.df['location_id'] == str(location_id)].iloc[0]
        return {
            'latitude': loc_data['latitude'],
            'longitude': loc_data['longitude'],
            'popularity': loc_data['popularity_score']
        }
    
    def get_sample_users(self, n=10):
        """Get sample user IDs for testing"""
        users = self.df.groupby('user_id').size().sort_values(ascending=False)
        return users.head(n).index.tolist()