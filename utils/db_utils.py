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
from models.image_prompts import VisualPrompts
from models.message import Message
from models.visualization_task import VisualizationTask
from utils.db_user_actions import DbUserActions
from utils.db_scenario_actions import DbScenarioActions
from utils.db_system_prompt_actions import DbSystemPromptActions
from utils.db_game_session_actions import DbGameSessionActions
from utils.db_chat_actions import DbChatActions
from utils.db_visualization_task_actions import DbVisualizationTaskActions

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.logger = get_logger("database")
        self._connect()
        
        # Initialize action handlers
        self.user_actions = DbUserActions(self.db) if self.db is not None else None
        self.scenario_actions = DbScenarioActions(self.db) if self.db is not None else None
        self.system_prompt_actions = DbSystemPromptActions(self.db) if self.db is not None else None
        self.game_session_actions = DbGameSessionActions(self.db) if self.db is not None else None
        self.chat_actions = DbChatActions(self.db) if self.db is not None else None
        self.visualization_task_actions = DbVisualizationTaskActions(self.db) if self.db is not None else None
    
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
            
            # Initialize action handlers now that database is connected
            self.user_actions = DbUserActions(self.db)
            self.scenario_actions = DbScenarioActions(self.db)
            self.system_prompt_actions = DbSystemPromptActions(self.db)
            self.game_session_actions = DbGameSessionActions(self.db)
            self.chat_actions = DbChatActions(self.db)
            self.visualization_task_actions = DbVisualizationTaskActions(self.db)
            
        except ServerSelectionTimeoutError as e:
            duration = time.time() - start_time
            self.logger.error(f"MongoDB server selection timeout after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error("Failed to connect to MongoDB: Connection timeout")
            self.client = None
            self.db = None
            self.user_actions = None
            self.scenario_actions = None
            self.system_prompt_actions = None
            self.game_session_actions = None
            self.chat_actions = None
            self.visualization_task_actions = None
            
        except ConnectionFailure as e:
            duration = time.time() - start_time
            self.logger.error(f"MongoDB connection failure after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error("Failed to connect to MongoDB: Connection failed")
            self.client = None
            self.db = None
            self.user_actions = None
            self.scenario_actions = None
            self.system_prompt_actions = None
            self.game_session_actions = None
            self.chat_actions = None
            self.visualization_task_actions = None
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Unexpected error during MongoDB connection after {duration:.2f}s: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "connect", "duration": duration})
            st.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.user_actions = None
            self.scenario_actions = None
            self.system_prompt_actions = None
            self.game_session_actions = None
            self.chat_actions = None
            self.visualization_task_actions = None
    
    def is_connected(self):
        """Check if database connection is active"""
        connected = self.client is not None and self.db is not None
        if not connected:
            self.logger.warning("Database connection check failed - client or db is None")
        return connected
    
    # USER OPERATIONS (delegated to DbUserActions)
    def create_user(self, user_id: str, password_hash: str, role: str = 'user') -> bool:
        """Create a new user"""
        if not self.user_actions:
            self.logger.error("User actions not available - database not connected")
            return False
        return self.user_actions.create_user(user_id, password_hash, role)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        if not self.user_actions:
            self.logger.error("User actions not available - database not connected")
            return None
        return self.user_actions.get_user(user_id)
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        if not self.user_actions:
            self.logger.error("User actions not available - database not connected")
            return False
        return self.user_actions.user_exists(user_id)
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        if not self.user_actions:
            self.logger.error("User actions not available - database not connected")
            return 0
        return self.user_actions.get_user_count()
    
    # SCENARIO OPERATIONS (delegated to DbScenarioActions)
    def create_scenario(self, scenario_data: Dict[str, Any]) -> bool:
        """Create a new scenario"""
        if not self.scenario_actions:
            self.logger.error("Scenario actions not available - database not connected")
            return False
        return self.scenario_actions.create_scenario(scenario_data)
    
    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Get all scenarios"""
        if not self.scenario_actions:
            self.logger.error("Scenario actions not available - database not connected")
            return []
        return self.scenario_actions.get_all_scenarios()
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by scenario_id"""
        if not self.scenario_actions:
            self.logger.error("Scenario actions not available - database not connected")
            return None
        return self.scenario_actions.get_scenario(scenario_id)
    
    def update_scenario(self, scenario_id: str, scenario_data: Dict[str, Any]) -> bool:
        """Update a scenario"""
        if not self.scenario_actions:
            self.logger.error("Scenario actions not available - database not connected")
            return False
        return self.scenario_actions.update_scenario(scenario_id, scenario_data)
    
    # SYSTEM PROMPT OPERATIONS (delegated to DbSystemPromptActions)
    def create_system_prompt(self, prompt_data: Dict[str, Any]) -> bool:
        """Create a new system prompt"""
        if not self.system_prompt_actions:
            self.logger.error("System prompt actions not available - database not connected")
            return False
        return self.system_prompt_actions.create_system_prompt(prompt_data)

    def get_active_system_prompt(self) -> Dict[str, Any]:
        """Get the active system prompt"""
        if not self.system_prompt_actions:
            self.logger.error("System prompt actions not available - database not connected")
            raise LookupError("Database not connected")
        return self.system_prompt_actions.get_active_system_prompt()

    def get_active_visualization_system_prompt(self) -> str:
        """Get the active visualization system prompt content."""
        if not self.system_prompt_actions:
            self.logger.error("System prompt actions not available - database not connected")
            raise LookupError("Database not connected")
        return self.system_prompt_actions.get_active_visualization_system_prompt()

    def update_system_prompt(self, prompt_id: str, content: str) -> bool:
        """Update system prompt content"""
        if not self.system_prompt_actions:
            self.logger.error("System prompt actions not available - database not connected")
            return False
        return self.system_prompt_actions.update_system_prompt(prompt_id, content)

    def update_visualization_system_prompt(self, content: str) -> bool:
        """Update visualization system prompt content"""
        if not self.system_prompt_actions:
            self.logger.error("System prompt actions not available - database not connected")
            return False
        return self.system_prompt_actions.update_visualization_system_prompt(content)
    
    # GAME SESSION OPERATIONS (delegated to DbGameSessionActions)
    def create_game_session(self, session_data: GameSession) -> Optional[str]:
        """Create a new game session"""
        if not self.game_session_actions:
            self.logger.error("Game session actions not available - database not connected")
            return None
        return self.game_session_actions.create_game_session(session_data)
    
    def get_user_game_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all game sessions for a user"""
        if not self.game_session_actions:
            self.logger.error("Game session actions not available - database not connected")
            return []
        return self.game_session_actions.get_user_game_sessions(user_id)
    
    def get_game_session(self, session_id: str) -> GameSession:
        """Get game session by ID"""
        if not self.game_session_actions:
            self.logger.error("Game session actions not available - database not connected")
            raise ValueError("Database not connected")
        return self.game_session_actions.get_game_session(session_id)
    
    def update_game_session(self, session: GameSession) -> bool:
        """Update a game session"""
        if not self.game_session_actions:
            self.logger.error("Game session actions not available - database not connected")
            return False
        return self.game_session_actions.update_game_session(session)
    
    # CHAT OPERATIONS (delegated to DbChatActions)
    def create_chat_document(self, game_session_id: str) -> bool:
        """Create a new chat document for a game session"""
        if not self.chat_actions:
            self.logger.error("Chat actions not available - database not connected")
            return False
        return self.chat_actions.create_chat_document(game_session_id)

    def add_chat_message(
        self,
        game_session_id: str,
        sender: str,
        content: str,
        full_prompt: Optional[List[Dict[str, Any]]] = None,
        *,
        role: Optional[str] = None,
    ) -> bool:
        """Add a message to the chat"""
        if not self.chat_actions:
            self.logger.error("Chat actions not available - database not connected")
            return False
        return self.chat_actions.add_chat_message(game_session_id, sender, content, full_prompt, role=role)
    
    def get_chat_messages(self, game_session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get chat messages for a game session"""
        if not self.chat_actions:
            self.logger.error("Chat actions not available - database not connected")
            return []
        return self.chat_actions.get_chat_messages(game_session_id, limit)

    def add_visual_prompts_to_latest_message(self, session_id: str, prompts: VisualPrompts) -> bool:
        """Attach visualization prompts to the latest chat message for a session."""
        if not self.chat_actions:
            self.logger.error("Chat actions not available - database not connected")
            return False
        return self.chat_actions.add_visual_prompts_to_latest_message(session_id, prompts)

    def get_visual_prompts(self, session_id: str, message_id: int) -> Dict[str, str]:
        """Return the visual prompts for a specific message in a chat session."""
        if not self.chat_actions:
            self.logger.error("Chat actions not available - database not connected")
            return {}
        return self.chat_actions.get_visual_prompts(session_id, message_id)

    # VISUALIZATION TASK OPERATIONS (delegated to DbVisualizationTaskActions)
    def create_visualization_task(self, task_data: Dict[str, Any]) -> bool:
        """Create or upsert a Kling visualization task record."""
        if not self.visualization_task_actions:
            self.logger.error("Visualization task actions not available - database not connected")
            return False
        return self.visualization_task_actions.create_visualization_task(task_data)

    def update_visualization_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing visualization task with new data."""
        if not self.visualization_task_actions:
            self.logger.error("Visualization task actions not available - database not connected")
            return False
        return self.visualization_task_actions.update_visualization_task(task_id, updates)

    def get_visualization_task(self, task_id: str) -> Optional[VisualizationTask]:
        """Retrieve a visualization task by its task_id."""
        if not self.visualization_task_actions:
            self.logger.error("Visualization task actions not available - database not connected")
            return None
        return self.visualization_task_actions.get_visualization_task(task_id)

    def get_visualization_tasks_by_message(self, session_id: str, message_id: str) -> List[VisualizationTask]:
        """Retrieve visualization tasks by session_id and message_id."""
        if not self.visualization_task_actions:
            self.logger.error("Visualization task actions not available - database not connected")
            return []
        return self.visualization_task_actions.get_visualization_tasks_by_message(session_id, message_id)

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
