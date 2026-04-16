import sqlite3
import bcrypt
from datetime import datetime
import json

class Database:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create user preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER,
                food BOOLEAN DEFAULT 0,
                museum BOOLEAN DEFAULT 0,
                park BOOLEAN DEFAULT 0,
                shopping BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                PRIMARY KEY (user_id)
            )
        ''')
        
        # Create user history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                location_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized successfully")
    
    def register_user(self, username, password, email, full_name):
        """Register a new user"""
        try:
            # Hash the password
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, password, email, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed, email, full_name))
            
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id, food, museum, park, shopping)
                VALUES (?, 0, 0, 0, 0)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, "User registered successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists!"
        except Exception as e:
            return False, f"Error: {e}"
    
    def login_user(self, username, password):
        """Authenticate user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                         (datetime.now(), user[0]))
            conn.commit()
            conn.close()
            return True, user[0], user[1]
        
        conn.close()
        return False, None, None
    
    def get_user_preferences(self, user_id):
        """Get user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT food, museum, park, shopping 
            FROM user_preferences WHERE user_id = ?
        ''', (user_id,))
        
        prefs = cursor.fetchone()
        conn.close()
        
        if prefs:
            return {
                'food': bool(prefs[0]),
                'museum': bool(prefs[1]),
                'park': bool(prefs[2]),
                'shopping': bool(prefs[3])
            }
        return {'food': False, 'museum': False, 'park': False, 'shopping': False}
    
    def update_user_preferences(self, user_id, preferences):
        """Update user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_preferences 
            SET food = ?, museum = ?, park = ?, shopping = ?
            WHERE user_id = ?
        ''', (preferences['food'], preferences['museum'], 
              preferences['park'], preferences['shopping'], user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def save_recommendation_history(self, user_id, recommendations):
        """Save recommendation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rec in recommendations:
            cursor.execute('''
                INSERT INTO user_history (user_id, action, location_id)
                VALUES (?, ?, ?)
            ''', (user_id, 'recommendation', rec['location_id']))
        
        conn.commit()
        conn.close()
    
    def get_user_info(self, user_id):
        """Get user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, full_name, created_at, last_login 
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'username': user[0],
                'email': user[1],
                'full_name': user[2],
                'created_at': user[3],
                'last_login': user[4]
            }
        return None