import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from math import radians, sin, cos, sqrt, atan2
from scipy.sparse import csr_matrix

class RecommendationEngine:
    def __init__(self, data_processor, user_module):
        self.data = data_processor
        self.user_module = user_module
        
    def collaborative_filtering(self, user_id, top_n=20):
        """Find similar users using sparse matrix to avoid memory issues"""
        try:
            # Get top users with most check-ins
            user_activity = self.data.df.groupby('user_id').size().sort_values(ascending=False)
            top_users = user_activity.head(1000).index.tolist()  # Limit to top 1000 users
            
            if user_id not in top_users:
                return []
            
            # Filter data for top users
            filtered_df = self.data.df[self.data.df['user_id'].isin(top_users)]
            
            # Create sparse matrix
            user_item = filtered_df.groupby(['user_id', 'location_id'])['popularity_score'].first().unstack(fill_value=0)
            
            if user_id not in user_item.index:
                return []
            
            # Find similar users
            from sklearn.metrics.pairwise import cosine_similarity
            user_vector = user_item.loc[user_id].values.reshape(1, -1)
            similarities = cosine_similarity(user_vector, user_item)
            similarities = similarities.flatten()
            
            # Get top 10 similar users
            similar_users_idx = similarities.argsort()[::-1][1:11]
            similar_users = user_item.index[similar_users_idx]
            
            # Get recommendations
            recommendations = []
            user_visited = set(filtered_df[filtered_df['user_id'] == user_id]['location_id'].tolist())
            
            for sim_user in similar_users:
                sim_user_locations = set(filtered_df[filtered_df['user_id'] == sim_user]['location_id'].tolist())
                new_locations = sim_user_locations - user_visited
                recommendations.extend(new_locations)
            
            return list(set(recommendations))[:top_n]
            
        except Exception as e:
            print(f"     Warning: Collaborative filtering limited due to memory: {e}")
            return []
    
    def location_based_filtering(self, user_lat, user_lon, radius_km=10):
        """Recommend nearby places based on distance"""
        nearby_locations = []
        
        # Sample locations to avoid processing all
        unique_locations = self.data.df[['location_id', 'latitude', 'longitude', 'popularity_score']].drop_duplicates('location_id')
        
        # Limit to 50000 locations for performance
        if len(unique_locations) > 50000:
            unique_locations = unique_locations.sample(50000)
        
        for _, row in unique_locations.iterrows():
            distance = self.calculate_distance(
                user_lat, user_lon, 
                row['latitude'], row['longitude']
            )
            
            if distance <= radius_km:
                nearby_locations.append({
                    'location_id': row['location_id'],
                    'distance': distance,
                    'popularity': row['popularity_score']
                })
        
        nearby_locations.sort(key=lambda x: (x['distance'], -x['popularity']))
        return nearby_locations[:20]
    
    def context_aware_filtering(self, recommendations, user_lat, user_lon, time_of_day):
        """Filter recommendations based on context"""
        if not recommendations:
            return []
        
        filtered_recs = []
        unique_locations = self.data.df[['location_id', 'latitude', 'longitude', 'popularity_score']].drop_duplicates('location_id')
        loc_info_dict = {row['location_id']: row for _, row in unique_locations.iterrows()}
        
        for loc_id in recommendations[:100]:  # Limit to first 100
            if loc_id not in loc_info_dict:
                continue
            
            loc_data = loc_info_dict[loc_id]
            distance = self.calculate_distance(user_lat, user_lon, loc_data['latitude'], loc_data['longitude'])
            time_suitable = self.is_location_active_at_time(loc_id, time_of_day)
            
            if distance <= 15 and time_suitable:
                filtered_recs.append({
                    'location_id': loc_id,
                    'distance': distance,
                    'popularity': loc_data['popularity_score'],
                    'time_suitable': time_suitable
                })
        
        return filtered_recs
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance using Haversine formula"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def is_location_active_at_time(self, location_id, time_category):
        """Check if location is active during specified time"""
        location_data = self.data.df[self.data.df['location_id'] == str(location_id)]
        if len(location_data) == 0:
            return True
        time_checkins = location_data[location_data['time_category'] == time_category]
        return len(time_checkins) > 0
    
    def rank_recommendations(self, recommendations, user_preferences):
        """Rank places based on multiple factors"""
        for rec in recommendations:
            popularity_score = rec['popularity'] * 0.5
            distance_score = max(0, (1 - rec['distance'] / 15)) * 0.3
            preference_boost = popularity_score * 0.2
            rec['final_score'] = popularity_score + distance_score + preference_boost
        
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        return recommendations[:5]
    
    def recommend(self, user_id, user_lat, user_lon, time_category):
        """Main recommendation method"""
        cf_recs = self.collaborative_filtering(user_id)
        context_recs = self.context_aware_filtering(cf_recs, user_lat, user_lon, time_category)
        user_prefs = self.user_module.get_current_user_preferences()
        return self.rank_recommendations(context_recs, user_prefs)