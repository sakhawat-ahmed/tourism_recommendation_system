from datetime import datetime
from .data_processor import DataProcessor
from .user_module import UserModule
from .recommendation_engine import RecommendationEngine
from .database import Database
import getpass

class TourismRecommendationSystem:
    def __init__(self, dataset_path):
        print("\n" + "="*60)
        print("🏨 CONTEXT-AWARE TOURISM RECOMMENDATION SYSTEM")
        print("="*60)
        
        print("\n📂 Initializing system...")
        
        # Initialize database
        self.db = Database()
        
        # Load data
        self.data_processor = DataProcessor(dataset_path)
        
        # Initialize user module with database
        self.user_module = UserModule(self.db)
        
        # Initialize recommendation engine
        self.recommendation_engine = RecommendationEngine(
            self.data_processor, 
            self.user_module
        )
        print("\n✓ System ready!\n")
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def clear_screen(self):
        """Clear terminal screen"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_user_location(self):
        """Get current user location"""
        print("\n📍 Enter your current location:")
        print("   (You can use coordinates from the dataset)")
        try:
            lat = float(input("  Latitude (e.g., 30.267): "))
            lon = float(input("  Longitude (e.g., -97.74): "))
            return lat, lon
        except ValueError:
            print("  Invalid input. Using default coordinates (Austin, TX).")
            return 30.267, -97.74
    
    def get_current_time(self):
        """Get current time category"""
        current_hour = datetime.now().hour
        return self.data_processor.get_time_category(current_hour)
    
    def show_user_profile(self):
        """Show user profile"""
        user_info = self.user_module.get_user_info()
        if user_info:
            self.print_header("👤 USER PROFILE")
            print(f"\n  Username: {user_info['username']}")
            print(f"  Full Name: {user_info['full_name']}")
            print(f"  Email: {user_info['email']}")
            print(f"  Member Since: {user_info['created_at']}")
            print(f"  Last Login: {user_info['last_login']}")
            
            self.user_module.display_preferences()
    
    def edit_preferences(self):
        """Edit user preferences"""
        self.print_header("✏️ EDIT PREFERENCES")
        current = self.user_module.get_current_user_preferences()
        
        print("\n  Current preferences:")
        print(f"    Food: {'✓' if current['food'] else '✗'}")
        print(f"    Museum: {'✓' if current['museum'] else '✗'}")
        print(f"    Park: {'✓' if current['park'] else '✗'}")
        print(f"    Shopping: {'✓' if current['shopping'] else '✗'}")
        
        print("\n  Update preferences (y/n):")
        new_prefs = {
            'food': input("    Like food places? (y/n): ").lower() == 'y',
            'museum': input("    Like museums? (y/n): ").lower() == 'y',
            'park': input("    Like parks? (y/n): ").lower() == 'y',
            'shopping': input("    Like shopping? (y/n): ").lower() == 'y'
        }
        
        if self.user_module.update_preferences(new_prefs):
            print("\n  ✓ Preferences updated successfully!")
        else:
            print("\n  ❌ Failed to update preferences")
    
    def get_recommendations(self):
        """Get recommendations for current user"""
        self.print_header("🔍 GET RECOMMENDATIONS")
        
        # Get sample user from dataset (user with most check-ins)
        sample_users = self.data_processor.get_sample_users(3)
        if not sample_users:
            print("\n  ❌ No users found in dataset!")
            return
        
        print("\n  📊 Dataset Statistics:")
        print(f"     Total Users: {self.data_processor.df['user_id'].nunique():,}")
        print(f"     Total Locations: {self.data_processor.df['location_id'].nunique():,}")
        print(f"     Total Check-ins: {len(self.data_processor.df):,}")
        
        print("\n  Select a user for recommendations:")
        for i, user in enumerate(sample_users, 1):
            history_count = len(self.data_processor.get_user_history(user))
            print(f"    {i}. User {user} ({history_count} check-ins)")
        print(f"    {len(sample_users)+1}. Enter custom user ID")
        
        choice = input(f"\n  Choose option (1-{len(sample_users)+1}): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(sample_users):
            dataset_user_id = sample_users[int(choice)-1]
        elif choice.isdigit() and int(choice) == len(sample_users)+1:
            dataset_user_id = input("  Enter user ID: ").strip()
        else:
            dataset_user_id = sample_users[0]
        
        user_history = self.data_processor.get_user_history(dataset_user_id)
        print(f"\n  ✓ Using user: {dataset_user_id}")
        print(f"  ✓ User has {len(user_history)} check-ins")
        
        # Get location
        user_lat, user_lon = self.get_user_location()
        
        # Get time
        time_category = self.get_current_time()
        print(f"  🕐 Current time: {time_category.upper()}")
        
        # Generate recommendations
        print("\n  Generating recommendations...")
        recommendations = self.recommendation_engine.recommend(
            dataset_user_id, user_lat, user_lon, time_category
        )
        
        # Display results
        self.display_recommendations(recommendations, time_category)
        
        # Save to history
        if recommendations:
            self.db.save_recommendation_history(self.user_module.current_user_id, recommendations)
            print("\n  ✓ Recommendations saved to your history!")
    
    def recommend(self, user_id, user_lat, user_lon, time_category):
        """Generate recommendations using all methods"""
        print("\n  📊 Method A: Collaborative Filtering")
        cf_recs = self.recommendation_engine.collaborative_filtering(user_id)
        print(f"     → Found {len(cf_recs)} recommendations")
        
        print("\n  📍 Method B: Location-Based Filtering")
        lb_recs = self.recommendation_engine.location_based_filtering(user_lat, user_lon)
        print(f"     → Found {len(lb_recs)} nearby locations")
        
        print("\n  🕒 Method C: Context-Aware Filtering")
        context_recs = self.recommendation_engine.context_aware_filtering(
            cf_recs[:30] if cf_recs else [], user_lat, user_lon, time_category
        )
        print(f"     → Found {len(context_recs)} context-aware recommendations")
        
        user_prefs = self.user_module.get_current_user_preferences()
        
        print("\n  🏆 Ranking Final Recommendations...")
        final_recs = self.recommendation_engine.rank_recommendations(context_recs, user_prefs)
        
        return final_recs
    
    def display_recommendations(self, recommendations, time_category):
        """Display top recommendations"""
        self.print_header(f"✨ TOP 5 RECOMMENDATIONS ({time_category.upper()} time)")
        
        if not recommendations:
            print("\n  😕 No recommendations found.")
            print("  Try adjusting your location or preferences.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. 🏢 Location ID: {rec['location_id']}")
            print(f"     📍 Distance: {rec['distance']:.2f} km")
            print(f"     ⭐ Score: {rec['final_score']:.3f}/1.0")
            print(f"     🔥 Popularity: {(rec['popularity']*100):.1f}%")
            
            # Add recommendation reason
            if rec['distance'] < 2:
                print(f"     💡 Very close to your location!")
            elif rec['popularity'] > 0.8:
                print(f"     💡 Very popular destination!")
    
    def show_menu(self):
        """Display main menu"""
        if self.user_module.is_logged_in():
            print(f"\n  👋 Hello, {self.user_module.current_username}!")
        
        print("\n  📱 MAIN MENU")
        print("  " + "="*40)
        
        if not self.user_module.is_logged_in():
            print("    1. Login")
            print("    2. Register")
            print("    3. Exit")
        else:
            print("    1. Get Recommendations")
            print("    2. My Profile")
            print("    3. Edit Preferences")
            print("    4. Logout")
            print("    5. Exit")
        
        print("  " + "="*40)
        
    def run_interactive(self):
        """Run interactive session"""
        while True:
            self.show_menu()
            choice = input("\n  Choose option: ").strip()
            
            if not self.user_module.is_logged_in():
                # Guest menu
                if choice == '1':
                    self.login_menu()
                elif choice == '2':
                    self.register_menu()
                elif choice == '3':
                    print("\n  👋 Thank you for using the Tourism Recommendation System!")
                    print("  Goodbye!\n")
                    break
                else:
                    print("\n  ❌ Invalid choice. Please select 1, 2, or 3.")
            else:
                # User menu
                if choice == '1':
                    self.get_recommendations()
                elif choice == '2':
                    self.show_user_profile()
                elif choice == '3':
                    self.edit_preferences()
                elif choice == '4':
                    self.user_module.logout()
                    print("\n  ✓ Logged out successfully!")
                elif choice == '5':
                    print("\n  👋 Thank you for using the Tourism Recommendation System!")
                    print("  Goodbye!\n")
                    break
                else:
                    print("\n  ❌ Invalid choice. Please select 1-5.")
    
    def login_menu(self):
        """Login menu"""
        self.print_header("🔐 LOGIN")
        
        username = input("\n  Username: ").strip()
        password = getpass.getpass("  Password: ")
        
        success, message = self.user_module.login(username, password)
        print(f"\n  {message}")
        
        if success:
            input("\n  Press Enter to continue...")
    
    def register_menu(self):
        """Registration menu"""
        self.print_header("📝 REGISTER NEW USER")
        
        print("\n  Please enter your information:")
        username = input("  Username: ").strip()
        password = getpass.getpass("  Password: ")
        confirm_password = getpass.getpass("  Confirm Password: ")
        
        if password != confirm_password:
            print("\n  ❌ Passwords do not match!")
            input("\n  Press Enter to continue...")
            return
        
        email = input("  Email: ").strip()
        full_name = input("  Full Name: ").strip()
        
        print("\n  📌 Select your preferences (y/n):")
        prefs = {
            'food': input("    Like food places? (y/n): ").lower() == 'y',
            'museum': input("    Like museums? (y/n): ").lower() == 'y',
            'park': input("    Like parks? (y/n): ").lower() == 'y',
            'shopping': input("    Like shopping? (y/n): ").lower() == 'y'
        }
        
        success, message = self.user_module.register(username, password, email, full_name, prefs)
        print(f"\n  {message}")
        
        if success:
            print("\n  ✓ You are now logged in!")
        
        input("\n  Press Enter to continue...")