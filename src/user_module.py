class UserModule:
    def __init__(self, database):
        self.db = database
        self.current_user_id = None
        self.current_username = None
        
    def register(self, username, password, email, full_name, preferences=None):
        """Register new user"""
        if preferences is None:
            preferences = {
                'food': False,
                'museum': False,
                'park': False,
                'shopping': False
            }
        
        success, message = self.db.register_user(username, password, email, full_name)
        if success:
            # Login after registration
            success, user_id, username = self.db.login_user(username, password)
            if success:
                self.current_user_id = user_id
                self.current_username = username
                # Update preferences
                self.db.update_user_preferences(user_id, preferences)
            return True, message
        return False, message
    
    def login(self, username, password):
        """Login user"""
        success, user_id, username = self.db.login_user(username, password)
        if success:
            self.current_user_id = user_id
            self.current_username = username
            return True, f"✓ Welcome back, {username}!"
        return False, "❌ Invalid username or password!"
    
    def logout(self):
        """Logout user"""
        self.current_user_id = None
        self.current_username = None
        return True, "Logged out successfully!"
    
    def update_preferences(self, preferences):
        """Update user preferences"""
        if self.current_user_id:
            return self.db.update_user_preferences(self.current_user_id, preferences)
        return False
    
    def get_current_user_preferences(self):
        """Get current user's preferences"""
        if self.current_user_id:
            return self.db.get_user_preferences(self.current_user_id)
        return None
    
    def display_preferences(self):
        """Display current user preferences"""
        if self.current_user_id:
            prefs = self.db.get_user_preferences(self.current_user_id)
            print("\n📌 Your Preferences:")
            print(f"  {'✓' if prefs['food'] else '✗'} Food")
            print(f"  {'✓' if prefs['museum'] else '✗'} Museum")
            print(f"  {'✓' if prefs['park'] else '✗'} Park")
            print(f"  {'✓' if prefs['shopping'] else '✗'} Shopping")
    
    def get_user_info(self):
        """Get current user info"""
        if self.current_user_id:
            return self.db.get_user_info(self.current_user_id)
        return None
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.current_user_id is not None