"""
Database User Actions for StoryOS v2
Handles user-related MongoDB operations
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.utils.streamlit_shim import st
from pymongo.errors import DuplicateKeyError
from pymongo.database import Database

from backend.logging_config import get_logger, StoryOSLogger


class DbUserActions:
    """Handles all user-related database operations."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
        self.logger = get_logger("db_user_actions")
    
    def create_user(self, user_id: str, password_hash: str, role: str = 'user') -> bool:
        """Create a new user"""
        start_time = time.time()
        self.logger.info(f"Creating user: {user_id} with role: {role}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot create user")
                return False
            
            user_doc = {
                'user_id': user_id,
                'password_hash': password_hash,
                'role': role,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.db.users.insert_one(user_doc)
            success = result.inserted_id is not None
            
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"User created successfully: {user_id} with role: {role}")
                StoryOSLogger.log_performance("database", "create_user", duration, {
                    "user_id": user_id,
                    "role": role,
                    "success": True
                })
            else:
                self.logger.error(f"Failed to create user: {user_id}")
            
            return success
            
        except DuplicateKeyError as e:
            self.logger.warning(f"User creation failed - duplicate key for: {user_id}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_user", "user_id": user_id})
            return False
        except Exception as e:
            self.logger.error(f"Error creating user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_user", "user_id": user_id})
            st.error(f"Error creating user: {str(e)}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        start_time = time.time()
        self.logger.debug(f"Retrieving user: {user_id}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get user")
                return None
                
            result = self.db.users.find_one({'user_id': user_id})
            duration = time.time() - start_time
            
            if result:
                self.logger.debug(f"User found: {user_id}")
                StoryOSLogger.log_performance("database", "get_user", duration, {
                    "user_id": user_id,
                    "found": True
                })
            else:
                self.logger.debug(f"User not found: {user_id}")
                StoryOSLogger.log_performance("database", "get_user", duration, {
                    "user_id": user_id,
                    "found": False
                })
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_user", "user_id": user_id})
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        self.logger.debug(f"Checking if user exists: {user_id}")
        exists = self.get_user(user_id) is not None
        self.logger.debug(f"User {user_id} exists: {exists}")
        return exists
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        start_time = time.time()
        self.logger.debug("Getting user count")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot count users")
                return 0
                
            count = self.db.users.count_documents({})
            duration = time.time() - start_time
            
            self.logger.debug(f"User count: {count}")
            StoryOSLogger.log_performance("database", "get_user_count", duration, {"count": count})
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting users: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_user_count"})
            st.error(f"Error counting users: {str(e)}")
            return 0
