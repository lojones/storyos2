"""
Database game session operations for StoryOS v2
Handles CRUD operations for game sessions in MongoDB
"""

import time
from backend.utils.streamlit_shim import st
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.database import Database
from backend.logging_config import get_logger, StoryOSLogger

# Model imports
from backend.models.game_session_model import GameSession


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
                
            sessions = list(self.db.active_game_sessions.find({'user_id': user_id, 'deleted': {'$ne': True}}))
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
            session = self.db.active_game_sessions.find_one({'_id': ObjectId(session_id), 'deleted': {'$ne': True}})
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

    def update_game_session(self, session: GameSession, max_retries: int = 3) -> bool:
        """Update a game session with optimistic locking"""
        start_time = time.time()
        
        if not session.id:
            raise ValueError("Game session ID is required for update operation")
        
        session_id: str = session.id

        for attempt in range(1, max_retries + 1):
            self.logger.debug(f"Updating game session (attempt {attempt}/{max_retries}): {session_id}")

            try:
                if self.db is None:
                    self.logger.error("Cannot update game session - database not connected")
                    return False

                from bson import ObjectId

                # Get current version from the session object
                current_version = getattr(session, 'version', 1)

                # Prepare update data
                update_data = session.to_dict()

                # Remove _id and version from update data
                if '_id' in update_data:
                    del update_data['_id']
                if 'version' in update_data:
                    del update_data['version']

                # Update timestamps and increment version
                update_data['last_updated'] = datetime.utcnow().isoformat()
                new_version = current_version + 1

                # Atomic update with version check
                result = self.db.active_game_sessions.update_one(
                    {
                        '_id': ObjectId(session_id),
                        'version': current_version
                    },
                    {
                        '$set': update_data,
                        '$inc': {'version': 1}
                    }
                )

                if result.matched_count == 0:
                    # Document not found or version mismatch
                    if attempt < max_retries:
                        self.logger.warning(f"Version conflict updating session {session_id}, retrying (attempt {attempt}/{max_retries})")
                        # Reload the session to get the latest version
                        try:
                            fresh_session = self.get_game_session(session_id)
                            session.version = fresh_session.version
                        except Exception as reload_error:
                            self.logger.error(f"Failed to reload session for retry: {str(reload_error)}")
                            return False
                        time.sleep(0.05 * attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"Version conflict persisted after {max_retries} attempts for session {session_id}")
                        return False

                # Success
                duration = time.time() - start_time
                session.version = new_version  # Update in-memory version

                self.logger.debug(f"Game session updated successfully: {session_id} (version {current_version} -> {new_version})")
                StoryOSLogger.log_performance("database", "update_game_session", duration, {
                    "session_id": session_id,
                    "attempts": attempt,
                    "version": new_version
                })
                return True

            except Exception as e:
                self.logger.error(f"Error updating game session {session_id}: {str(e)}")
                StoryOSLogger.log_error_with_context("database", e, {
                    "operation": "update_game_session",
                    "session_id": session_id,
                    "attempt": attempt
                })
                if attempt == max_retries:
                    st.error(f"Error updating game session: {str(e)}")
                    return False
                time.sleep(0.05 * attempt)  # Exponential backoff

        return False

    def update_game_session_fields(self, session_id: str, updates: Dict[str, Any], max_retries: int = 3) -> bool:
        """Update specific fields of a game session with optimistic locking"""
        start_time = time.time()

        for attempt in range(1, max_retries + 1):
            self.logger.debug(f"Updating game session fields (attempt {attempt}/{max_retries}): {session_id}, fields: {list(updates.keys())}")

            try:
                if self.db is None:
                    self.logger.error("Cannot update game session - database not connected")
                    return False

                from bson import ObjectId

                # Get current document to read version
                current_doc = self.db.active_game_sessions.find_one(
                    {'_id': ObjectId(session_id), 'deleted': {'$ne': True}},
                    {'version': 1}
                )

                if not current_doc:
                    self.logger.error(f"Game session not found: {session_id}")
                    return False

                current_version = current_doc.get('version', 1)

                # Prepare update data
                update_data = {**updates, 'last_updated': datetime.utcnow().isoformat()}

                # Don't allow version to be updated directly
                if 'version' in update_data:
                    del update_data['version']

                # Atomic update with version check
                result = self.db.active_game_sessions.update_one(
                    {
                        '_id': ObjectId(session_id),
                        'version': current_version
                    },
                    {
                        '$set': update_data,
                        '$inc': {'version': 1}
                    }
                )

                if result.matched_count == 0:
                    # Version mismatch - retry
                    if attempt < max_retries:
                        self.logger.warning(f"Version conflict updating session fields for {session_id}, retrying (attempt {attempt}/{max_retries})")
                        time.sleep(0.05 * attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"Version conflict persisted after {max_retries} attempts for session {session_id}")
                        return False

                # Success
                duration = time.time() - start_time
                new_version = current_version + 1

                self.logger.debug(f"Game session fields updated successfully: {session_id} (version {current_version} -> {new_version})")
                StoryOSLogger.log_performance("database", "update_game_session_fields", duration, {
                    "session_id": session_id,
                    "attempts": attempt,
                    "version": new_version,
                    "fields": list(updates.keys())
                })
                return True

            except Exception as e:
                self.logger.error(f"Error updating game session fields {session_id}: {str(e)}")
                StoryOSLogger.log_error_with_context("database", e, {
                    "operation": "update_game_session_fields",
                    "session_id": session_id,
                    "attempt": attempt
                })
                if attempt == max_retries:
                    st.error(f"Error updating game session: {str(e)}")
                    return False
                time.sleep(0.05 * attempt)  # Exponential backoff

        return False
