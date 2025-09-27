"""
Database game session operations for StoryOS v2
Handles CRUD operations for game sessions in MongoDB
"""

import time
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.database import Database
from logging_config import get_logger, StoryOSLogger

# Model imports
from models.game_session_model import GameSession


class DbGameSessionActions:
    """Handles game session database operations"""

    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.logger = get_logger("database.game_session_actions")
        self.logger.debug("DbGameSessionActions initialized")

    def create_game_session(self, session_data: GameSession) -> Optional[str]:
        """Create a new game session"""
        start_time = time.time()
        user_id = session_data.user_id
        scenario_id = session_data.scenario_id
        self.logger.info(f"Creating game session for user: {user_id}, scenario: {scenario_id}")
        
        try:
            if self.db is None:
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
            if self.db is None:
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
            if self.db is None:
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
            if self.db is None:
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
