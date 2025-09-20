"""
Database utilities for StoryOS v2
Handles MongoDB connection and CRUD operations for all collections
"""
# pyright: reportOptionalMemberAccess=false

import pymongo
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError, ConnectionFailure
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st
from dotenv import load_dotenv
from pymongo.database import Database
from logging_config import get_logger, StoryOSLogger
import time

# from models import game_session_model
from models.game_session_model import GameSession, GameSessionUtils

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.logger = get_logger("database")
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        start_time = time.time()
        self.logger.info("Attempting to connect to MongoDB")
        
        try:
            # Get connection details from environment
            mongodb_uri = os.getenv('MONGODB_URI')
            username = os.getenv('MONGODB_USERNAME')
            password = os.getenv('MONGODB_PASSWORD')
            db_name = os.getenv('MONGODB_DATABASE_NAME', 'storyos')
            
            self.logger.debug(f"Database name: {db_name}")
            self.logger.debug(f"MongoDB URI present: {bool(mongodb_uri)}")
            self.logger.debug(f"Username present: {bool(username)}")
            self.logger.debug(f"Password present: {bool(password)}")
            
            if not mongodb_uri:
                self.logger.error("MongoDB URI not found in environment variables")
                st.error("MongoDB URI not found in environment variables")
                return
                
            # Replace placeholders in URI
            if username and password:
                mongodb_uri = mongodb_uri.replace('<username>', username).replace('<password>', password)
                self.logger.debug("URI placeholders replaced with credentials")
            
            # Remove quotes if present
            mongodb_uri = mongodb_uri.strip("'\"")
            
            # Connect to MongoDB
            self.logger.info("Creating MongoDB client connection")
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            
            # Test the connection
            self.logger.debug("Testing database connection with ping")
            ping_result = self.client.admin.command('ping')
            
            duration = time.time() - start_time
            self.logger.info(f"MongoDB connection successful to database '{db_name}'")
            StoryOSLogger.log_performance("database", "mongodb_connect", duration, {
                "database": db_name,
                "ping_result": ping_result
            })
            
        except ServerSelectionTimeoutError as e:
            duration = time.time() - start_time
            self.logger.error(f"MongoDB server selection timeout after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error("Failed to connect to MongoDB: Connection timeout")
            self.client = None
            self.db = None
            
        except ConnectionFailure as e:
            duration = time.time() - start_time
            self.logger.error(f"MongoDB connection failure after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error("Failed to connect to MongoDB: Connection failed")
            self.client = None
            self.db = None
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Unexpected error during MongoDB connection after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
    
    def is_connected(self):
        """Check if database connection is active"""
        connected = self.client is not None and self.db is not None
        if not connected:
            self.logger.warning("Database connection check failed - client or db is None")
        return connected
    
    # USER OPERATIONS
    def create_user(self, user_id: str, password_hash: str, role: str = 'user') -> bool:
        """Create a new user"""
        start_time = time.time()
        self.logger.info(f"Creating user: {user_id} with role: {role}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot create user - database not connected")
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
                self.logger.info(f"User created successfully: {user_id} (ID: {result.inserted_id})")
                StoryOSLogger.log_performance("database", "create_user", duration, {
                    "user_id": user_id, 
                    "role": role, 
                    "document_id": str(result.inserted_id)
                })
            else:
                self.logger.error(f"User creation failed - no document ID returned for: {user_id}")
            
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
            if not self.is_connected():
                self.logger.error("Cannot get user - database not connected")
                return None
                
            result = self.db.users.find_one({'user_id': user_id})
            duration = time.time() - start_time
            
            if result:
                self.logger.debug(f"User found: {user_id} with role: {result.get('role', 'unknown')}")
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
            if not self.is_connected():
                self.logger.error("Cannot get user count - database not connected")
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
    
    # SCENARIO OPERATIONS
    def create_scenario(self, scenario_data: Dict[str, Any]) -> bool:
        """Create a new scenario"""
        start_time = time.time()
        scenario_id = scenario_data.get('scenario_id', 'unknown')
        self.logger.info(f"Creating scenario: {scenario_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot create scenario - database not connected")
                return False
                
            # Ensure created_at is set
            if 'created_at' not in scenario_data:
                scenario_data['created_at'] = datetime.utcnow().isoformat()
                
            result = self.db.scenarios.insert_one(scenario_data)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Scenario created successfully: {scenario_id} (ID: {result.inserted_id})")
                StoryOSLogger.log_performance("database", "create_scenario", duration, {
                    "scenario_id": scenario_id,
                    "document_id": str(result.inserted_id)
                })
            else:
                self.logger.error(f"Scenario creation failed - no document ID returned for: {scenario_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_scenario", "scenario_id": scenario_id})
            st.error(f"Error creating scenario: {str(e)}")
            return False
    
    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Get all scenarios"""
        start_time = time.time()
        self.logger.debug("Retrieving all scenarios")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get scenarios - database not connected")
                return []
                
            scenarios = list(self.db.scenarios.find({}))
            duration = time.time() - start_time
            
            self.logger.debug(f"Retrieved {len(scenarios)} scenarios")
            StoryOSLogger.log_performance("database", "get_all_scenarios", duration, {"count": len(scenarios)})
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Error getting scenarios: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_all_scenarios"})
            st.error(f"Error getting scenarios: {str(e)}")
            return []
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by scenario_id"""
        start_time = time.time()
        self.logger.debug(f"Retrieving scenario: {scenario_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get scenario - database not connected")
                return None
                
            scenario = self.db.scenarios.find_one({'scenario_id': scenario_id})
            duration = time.time() - start_time
            
            if scenario:
                self.logger.debug(f"Scenario found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": True
                })
            else:
                self.logger.debug(f"Scenario not found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": False
                })
                
            return scenario
            
        except Exception as e:
            self.logger.error(f"Error getting scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_scenario", "scenario_id": scenario_id})
            st.error(f"Error getting scenario: {str(e)}")
            return None
    
    def update_scenario(self, scenario_id: str, scenario_data: Dict[str, Any]) -> bool:
        """Update a scenario"""
        start_time = time.time()
        self.logger.info(f"Updating scenario: {scenario_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot update scenario - database not connected")
                return False
                
            result = self.db.scenarios.update_one(
                {'scenario_id': scenario_id},
                {'$set': scenario_data}
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Scenario updated successfully: {scenario_id} ({result.modified_count} documents modified)")
                StoryOSLogger.log_performance("database", "update_scenario", duration, {
                    "scenario_id": scenario_id,
                    "modified_count": result.modified_count
                })
            else:
                self.logger.warning(f"Scenario update resulted in 0 modifications: {scenario_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "update_scenario", "scenario_id": scenario_id})
            st.error(f"Error updating scenario: {str(e)}")
            return False
    
    # SYSTEM PROMPT OPERATIONS
    def create_system_prompt(self, prompt_data: Dict[str, Any]) -> bool:
        """Create a new system prompt"""
        start_time = time.time()
        prompt_name = prompt_data.get('name', 'unnamed')
        self.logger.info(f"Creating system prompt: {prompt_name}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot create system prompt - database not connected")
                return False
                
            # Ensure timestamps are set
            now = datetime.utcnow().isoformat()
            if 'created_at' not in prompt_data:
                prompt_data['created_at'] = now
            if 'updated_at' not in prompt_data:
                prompt_data['updated_at'] = now
                
            result = self.db.system_prompts.insert_one(prompt_data)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"System prompt created successfully: {prompt_name} (ID: {result.inserted_id})")
                StoryOSLogger.log_performance("database", "create_system_prompt", duration, {
                    "prompt_name": prompt_name,
                    "document_id": str(result.inserted_id)
                })
            else:
                self.logger.error(f"System prompt creation failed - no document ID returned for: {prompt_name}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating system prompt {prompt_name}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_system_prompt", "prompt_name": prompt_name})
            st.error(f"Error creating system prompt: {str(e)}")
            return False
    
    def get_active_system_prompt(self) -> Optional[Dict[str, Any]]:
        """Get the active system prompt"""
        start_time = time.time()
        self.logger.debug("Retrieving active system prompt")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get active system prompt - database not connected")
                return None
                
            prompt = self.db.system_prompts.find_one({'active': True})
            duration = time.time() - start_time
            
            if prompt:
                prompt_name = prompt.get('name', 'unnamed')
                self.logger.debug(f"Active system prompt found: {prompt_name}")
                StoryOSLogger.log_performance("database", "get_active_system_prompt", duration, {
                    "prompt_name": prompt_name,
                    "found": True
                })
            else:
                self.logger.warning("No active system prompt found")
                StoryOSLogger.log_performance("database", "get_active_system_prompt", duration, {"found": False})
                
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error getting active system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_active_system_prompt"})
            st.error(f"Error getting active system prompt: {str(e)}")
            return None
    
    def update_system_prompt(self, prompt_id: str, content: str) -> bool:
        """Update system prompt content"""
        start_time = time.time()
        self.logger.info(f"Updating system prompt: {prompt_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot update system prompt - database not connected")
                return False
                
            # First deactivate all prompts
            self.logger.debug("Deactivating all system prompts")
            deactivate_result = self.db.system_prompts.update_many({}, {'$set': {'active': False}})
            self.logger.debug(f"Deactivated {deactivate_result.modified_count} prompts")
            
            # Then update and activate the specified prompt
            result = self.db.system_prompts.update_one(
                {'_id': prompt_id},
                {
                    '$set': {
                        'content': content,
                        'active': True,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"System prompt updated successfully: {prompt_id}")
                StoryOSLogger.log_performance("database", "update_system_prompt", duration, {
                    "prompt_id": str(prompt_id),
                    "modified_count": result.modified_count
                })
            else:
                self.logger.warning(f"System prompt update resulted in 0 modifications: {prompt_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating system prompt {prompt_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "update_system_prompt", "prompt_id": str(prompt_id)})
            st.error(f"Error updating system prompt: {str(e)}")
            return False
    
    # GAME SESSION OPERATIONS
    def create_game_session(self, session_data: GameSession) -> Optional[str]:
        """Create a new game session"""
        start_time = time.time()
        user_id = session_data.user_id
        scenario_id = session_data.scenario_id
        self.logger.info(f"Creating game session for user: {user_id}, scenario: {scenario_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot create game session - database not connected")
                return None
                
            # Ensure timestamps are set
            now = datetime.utcnow()
            session_data.last_updated = now
            
            # Convert GameSession to dictionary for MongoDB insertion
            session_dict = session_data.to_dict()
                
            result = self.db.active_game_sessions.insert_one(session_dict)
            session_id = str(result.inserted_id)
            duration = time.time() - start_time
            
            self.logger.info(f"Game session created successfully: {session_id} for user: {user_id}")
            StoryOSLogger.log_performance("database", "create_game_session", duration, {
                "user_id": user_id,
                "scenario_id": scenario_id,
                "session_id": session_id
            })
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creating game session for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_game_session", "user_id": user_id, "scenario_id": scenario_id})
            st.error(f"Error creating game session: {str(e)}")
            return None
    
    def get_user_game_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all game sessions for a user"""
        start_time = time.time()
        self.logger.debug(f"Retrieving game sessions for user: {user_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get user game sessions - database not connected")
                return []
                
            sessions = list(self.db.active_game_sessions.find({'user_id': user_id}))
            duration = time.time() - start_time
            
            self.logger.debug(f"Retrieved {len(sessions)} game sessions for user: {user_id}")
            StoryOSLogger.log_performance("database", "get_user_game_sessions", duration, {
                "user_id": user_id,
                "session_count": len(sessions)
            })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting user game sessions for {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_user_game_sessions", "user_id": user_id})
            st.error(f"Error getting user game sessions: {str(e)}")
            return []
    
    def get_game_session(self, session_id: str) -> GameSession:
        """Get game session by ID"""
        start_time = time.time()
        self.logger.debug(f"Retrieving game session: {session_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get game session - database not connected")
                raise ValueError("Database not connected")
                
            from bson import ObjectId
            session = self.db.active_game_sessions.find_one({'_id': ObjectId(session_id)})
            duration = time.time() - start_time
            
            if session:
                user_id = session.get('user_id', 'unknown')
                self.logger.debug(f"Game session found: {session_id} for user: {user_id}")
                StoryOSLogger.log_performance("database", "get_game_session", duration, {
                    "session_id": session_id,
                    "user_id": user_id,
                    "found": True
                })
                game_session = GameSession.from_dict(session)  # Validate and convert to GameSession
                return game_session
            else:
                self.logger.debug(f"Game session not found: {session_id}")
                StoryOSLogger.log_performance("database", "get_game_session", duration, {
                    "session_id": session_id,
                    "found": False
                })
                raise ValueError("Game session not found in database")            
            
        except Exception as e:
            self.logger.error(f"Error getting game session {session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_game_session", "session_id": session_id})
            st.error(f"Error getting game session: {str(e)}")
            raise e
    
    def update_game_session(self, session: GameSession) -> bool:
        """Update a game session"""
        start_time = time.time()
        self.logger.debug(f"Updating game session: {session.id}")
        session_id = session.id
        update_data = session.to_dict() 
        
        # Remove _id field from update data since it's immutable in MongoDB
        if '_id' in update_data:
            del update_data['_id']
            self.logger.debug("Removed _id field from update data to prevent MongoDB error")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot update game session - database not connected")
                return False
                
            from bson import ObjectId
            update_data['last_updated'] = datetime.utcnow().isoformat()
            
            result = self.db.active_game_sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': update_data}
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.debug(f"Game session updated successfully: {session_id} ({result.modified_count} documents modified)")
                StoryOSLogger.log_performance("database", "update_game_session", duration, {
                    "session_id": session_id,
                    "modified_count": result.modified_count
                })
            else:
                self.logger.warning(f"Game session update resulted in 0 modifications: {session_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating game session {session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "update_game_session", "session_id": session_id})
            st.error(f"Error updating game session: {str(e)}")
            return False
    
    # CHAT OPERATIONS
    def create_chat_document(self, game_session_id: str) -> bool:
        """Create a new chat document for a game session"""
        start_time = time.time()
        self.logger.info(f"Creating chat document for game session: {game_session_id}")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot create chat document - database not connected")
                return False
                
            from bson import ObjectId
            chat_doc = {
                'game_session_id': ObjectId(game_session_id),
                'messages': [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.db.chats.insert_one(chat_doc)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Chat document created successfully: {result.inserted_id} for session: {game_session_id}")
                StoryOSLogger.log_performance("database", "create_chat_document", duration, {
                    "game_session_id": game_session_id,
                    "chat_document_id": str(result.inserted_id)
                })
            else:
                self.logger.error(f"Chat document creation failed - no document ID returned for session: {game_session_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating chat document for session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_chat_document", "game_session_id": game_session_id})
            st.error(f"Error creating chat document: {str(e)}")
            return False

    def add_chat_message(self, game_session_id: str, sender: str, content: str, full_prompt: list) -> bool:
        """Add a message to the chat"""
        start_time = time.time()
        content_length = len(content)
        self.logger.debug(f"Adding chat message from {sender} to session {game_session_id} (length: {content_length})")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot add chat message - database not connected")
                return False
                
            from bson import ObjectId
            message = {
                'sender': sender,
                'content': content,
                'full_prompt': full_prompt,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = self.db.chats.update_one(
                {'game_session_id': ObjectId(game_session_id)},
                {'$push': {'messages': message}}
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.debug(f"Chat message added successfully from {sender} to session {game_session_id}")
                StoryOSLogger.log_performance("database", "add_chat_message", duration, {
                    "game_session_id": game_session_id,
                    "sender": sender,
                    "content_length": content_length,
                    "modified_count": result.modified_count
                })
            else:
                self.logger.warning(f"Chat message add resulted in 0 modifications for session {game_session_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding chat message from {sender} to session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "add_chat_message", 
                "game_session_id": game_session_id, 
                "sender": sender,
                "content_length": content_length
            })
            st.error(f"Error adding chat message: {str(e)}")
            return False
    
    def get_chat_messages(self, game_session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get chat messages for a game session"""
        start_time = time.time()
        self.logger.debug(f"Retrieving chat messages for session: {game_session_id} (limit: {limit})")
        
        try:
            if not self.is_connected():
                self.logger.error("Cannot get chat messages - database not connected")
                return []
                
            from bson import ObjectId
            chat_doc = self.db.chats.find_one({'game_session_id': ObjectId(game_session_id)})
            
            if not chat_doc or 'messages' not in chat_doc:
                self.logger.debug(f"No chat document or messages found for session: {game_session_id}")
                return []
                
            messages = chat_doc['messages']
            original_count = len(messages)
            
            if limit and len(messages) > limit:
                messages = messages[-limit:]  # Get last N messages
                
            duration = time.time() - start_time
            self.logger.debug(f"Retrieved {len(messages)}/{original_count} chat messages for session: {game_session_id}")
            StoryOSLogger.log_performance("database", "get_chat_messages", duration, {
                "game_session_id": game_session_id,
                "total_messages": original_count,
                "returned_messages": len(messages),
                "limit": limit
            })
                
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting chat messages for session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_chat_messages", "game_session_id": game_session_id})
            st.error(f"Error getting chat messages: {str(e)}")
            return []
    
    def close_connection(self):
        """Close database connection"""
        self.logger.info("Closing database connection")
        if self.client:
            self.client.close()
            self.logger.info("Database connection closed successfully")
            self.client = None
            self.db = None
        else:
            self.logger.debug("No database connection to close")

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        logger = get_logger("database")
        logger.debug("Creating new DatabaseManager instance")
        _db_manager = DatabaseManager()
    return _db_manager