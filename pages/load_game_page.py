"""
Load Game Page Module for StoryOS v2
Handles loading saved games and game session management
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from logging_config import StoryOSLogger, get_logger
from utils.st_session_management import SessionManager, navigate_to_page, Pages
from game.game_logic import get_user_game_sessions, export_game_session


class LoadGameInterface:
    """Handles the load game interface and saved game management"""
    
    @classmethod
    def show_load_game_page(cls, user: Dict[str, Any]):
        """Show the load game page with user's saved games"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.info(f"Displaying load game page for user: {user_id}")
            
            # Page header
            st.title("📚 Load Saved Game")
            
            # Back to menu button
            if st.button("← Back to Menu", key="back_to_menu"):
                logger.debug(f"User {user_id} clicked back to menu from load game page")
                navigate_to_page(Pages.MAIN_MENU)
                return
            
            # Load and display user's game sessions
            cls._render_saved_games(user)
            
        except Exception as e:
            logger.error(f"Error displaying load game page for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "show_load_game_page",
                "user_id": user_id
            })
            st.error("Error loading saved games page")
    
    @classmethod
    def _render_saved_games(cls, user: Dict[str, Any]):
        """Render the list of user's saved games"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.debug(f"Loading saved games for user: {user_id}")
            
            # Get user's game sessions
            sessions = get_user_game_sessions(user_id)
            logger.info(f"Retrieved {len(sessions)} saved games for user: {user_id}")
            
            if not sessions:
                logger.debug(f"No saved games found for user: {user_id}")
                cls._show_no_games_message()
                return
            
            # Display saved games
            st.subheader("Your Game Sessions")
            cls._render_games_list(sessions, user)
            
            # Log user action
            StoryOSLogger.log_user_action(user_id, "view_saved_games", {
                "games_count": len(sessions)
            })
            
        except Exception as e:
            logger.error(f"Error rendering saved games for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_render_saved_games",
                "user_id": user_id
            })
            st.error("Error loading your saved games")
    
    @classmethod
    def _show_no_games_message(cls):
        """Display message when user has no saved games"""
        logger = get_logger("load_game")
        logger.debug("Displaying no saved games message")
        
        st.info("You don't have any saved games yet. Start a new game to begin!")
        st.markdown("""
        **Getting Started:**
        1. Go back to the main menu
        2. Click "🎮 Start New Game"
        3. Choose a scenario and begin your adventure
        4. Your progress will be automatically saved
        """)
    
    @classmethod
    def _render_games_list(cls, sessions: List[Dict[str, Any]], user: Dict[str, Any]):
        """Render the list of saved games"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.debug(f"Rendering {len(sessions)} game sessions for user: {user_id}")
            
            # Sort sessions by last updated (most recent first)
            sorted_sessions = sorted(sessions, 
                                   key=lambda x: x.get('last_updated', ''), 
                                   reverse=True)
            
            # Display each game session
            for i, session in enumerate(sorted_sessions):
                session_id = str(session.get('_id', 'unknown'))
                scenario_name = session.get('scenario_name', 'Unknown Scenario')
                created_at = session.get('created_at', 'Unknown')
                
                logger.debug(f"Rendering session {i+1}: {scenario_name} (ID: {session_id})")
                
                with st.expander(f"🎲 {scenario_name} - Started {created_at}"):
                    cls._render_game_session_details(session, user)
                    
        except Exception as e:
            logger.error(f"Error rendering games list for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_render_games_list",
                "user_id": user_id,
                "sessions_count": len(sessions)
            })
    
    @classmethod
    def _render_game_session_details(cls, session: Dict[str, Any], user: Dict[str, Any]):
        """Render the details of a single game session"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            session_id = str(session.get('_id', 'unknown'))
            scenario_name = session.get('scenario_name', 'Unknown')
            
            # Display session information
            st.write(f"**Scenario:** {scenario_name}")
            st.write(f"**Last Updated:** {session.get('last_updated', 'Unknown')}")
            
            # Show current situation if available
            if 'current_scenario' in session and session['current_scenario']:
                current_situation = session['current_scenario']
                if len(current_situation) > 200:
                    st.write(f"**Current Situation:** {current_situation[:200]}...")
                else:
                    st.write(f"**Current Situation:** {current_situation}")
            
            # Show additional game stats if available
            if 'timeline' in session:
                timeline = session.get('timeline', [])
                if timeline:
                    st.write(f"**Story Events:** {len(timeline)}")
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                cls._render_continue_button(session, user)
            
            with col2:
                cls._render_export_button(session, user)
            
            logger.debug(f"Rendered details for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error rendering game session details: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_render_game_session_details",
                "user_id": user_id,
                "session_id": session.get('_id', 'unknown')
            })
    
    @classmethod
    def _render_continue_button(cls, session: Dict[str, Any], user: Dict[str, Any]):
        """Render the continue game button"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            session_id = str(session.get('_id', 'unknown'))
            button_key = f"load_{session_id}"
            
            if st.button("▶️ Continue Game", key=button_key, use_container_width=True):
                logger.info(f"User {user_id} clicked continue game for session: {session_id}")
                cls._handle_continue_game_click(session, user)
                
        except Exception as e:
            logger.error(f"Error rendering continue button: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_render_continue_button",
                "user_id": user_id,
                "session_id": session.get('_id', 'unknown')
            })
    
    @classmethod
    def _render_export_button(cls, session: Dict[str, Any], user: Dict[str, Any]):
        """Render the export game button"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            session_id = str(session.get('_id', 'unknown'))
            button_key = f"export_{session_id}"
            
            if st.button("📥 Export Game", key=button_key, use_container_width=True):
                logger.info(f"User {user_id} clicked export game for session: {session_id}")
                cls._handle_export_game_click(session, user)
                
        except Exception as e:
            logger.error(f"Error rendering export button: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_render_export_button",
                "user_id": user_id,
                "session_id": session.get('_id', 'unknown')
            })
    
    @classmethod
    def _handle_continue_game_click(cls, session: Dict[str, Any], user: Dict[str, Any]):
        """Handle the continue game button click"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        session_id = str(session.get('_id', 'unknown'))
        
        try:
            scenario_name = session.get('scenario_name', 'Unknown')
            logger.info(f"Continuing game for user {user_id}, session: {session_id}, scenario: {scenario_name}")
            
            # Log user action
            StoryOSLogger.log_user_action(user_id, "continue_game", {
                "session_id": session_id,
                "scenario_name": scenario_name
            })
            
            # Set the game session in session manager
            SessionManager.set_game_session(session_id, user_id)
            
            # Navigate to game page
            navigate_to_page(Pages.GAME, user_id)
            
            logger.info(f"Successfully loaded game session: {session_id} for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error continuing game for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_handle_continue_game_click",
                "user_id": user_id,
                "session_id": session_id
            })
            st.error("❌ Failed to continue game. Please try again.")
    
    @classmethod
    def _handle_export_game_click(cls, session: Dict[str, Any], user: Dict[str, Any]):
        """Handle the export game button click"""
        logger = get_logger("load_game")
        user_id = user.get('user_id', 'unknown')
        session_id = str(session.get('_id', 'unknown'))
        
        try:
            scenario_name = session.get('scenario_name', 'Unknown')
            logger.info(f"Exporting game for user {user_id}, session: {session_id}, scenario: {scenario_name}")
            
            # Log user action
            StoryOSLogger.log_user_action(user_id, "export_game_attempt", {
                "session_id": session_id,
                "scenario_name": scenario_name
            })
            
            # Export game session
            exported_data = export_game_session(session_id)
            
            if exported_data:
                # Create download button
                file_name = f"storyos_session_{session_id}.json"
                download_key = f"download_{session_id}"
                
                st.download_button(
                    label="📋 Download JSON",
                    data=exported_data,
                    file_name=file_name,
                    mime="application/json",
                    key=download_key,
                    use_container_width=True
                )
                
                logger.info(f"Game export successful for session: {session_id}")
                StoryOSLogger.log_user_action(user_id, "game_exported_successfully", {
                    "session_id": session_id,
                    "scenario_name": scenario_name,
                    "file_size": len(exported_data)
                })
                
                st.success("✅ Game exported successfully! Click the download button above.")
                
            else:
                logger.error(f"Failed to export game session: {session_id}")
                StoryOSLogger.log_user_action(user_id, "game_export_failed", {
                    "session_id": session_id,
                    "scenario_name": scenario_name
                })
                st.error("❌ Failed to export game. Please try again.")
                
        except Exception as e:
            logger.error(f"Error exporting game for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("load_game", e, {
                "operation": "_handle_export_game_click",
                "user_id": user_id,
                "session_id": session_id
            })
            st.error("❌ An unexpected error occurred during export.")


# Convenience function for easier import
def show_load_game_page(user: Dict[str, Any]):
    """Show the load game page (convenience function)"""
    LoadGameInterface.show_load_game_page(user)


# Additional utilities for load game page
class LoadGameUtils:
    """Utility functions for load game operations"""
    
    @staticmethod
    def get_user_games_count(user_id: str) -> int:
        """Get the count of saved games for a user"""
        logger = get_logger("load_game")
        
        try:
            sessions = get_user_game_sessions(user_id)
            count = len(sessions) if sessions else 0
            logger.debug(f"User {user_id} has {count} saved games")
            return count
            
        except Exception as e:
            logger.error(f"Error counting user games for {user_id}: {str(e)}")
            return 0
    
    @staticmethod
    def get_most_recent_game(user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recently updated game for a user"""
        logger = get_logger("load_game")
        
        try:
            sessions = get_user_game_sessions(user_id)
            if not sessions:
                return None
            
            # Sort by last_updated and return the most recent
            sorted_sessions = sorted(sessions, 
                                   key=lambda x: x.get('last_updated', ''), 
                                   reverse=True)
            
            most_recent = sorted_sessions[0]
            logger.debug(f"Most recent game for user {user_id}: {most_recent.get('scenario_name', 'Unknown')}")
            return most_recent
            
        except Exception as e:
            logger.error(f"Error getting most recent game for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def validate_game_session(session_id: str, user_id: str) -> bool:
        """Validate that a game session exists and belongs to the user"""
        logger = get_logger("load_game")
        
        try:
            sessions = get_user_game_sessions(user_id)
            if not sessions:
                return False
            
            # Check if session exists and belongs to user
            for session in sessions:
                if str(session.get('_id', '')) == session_id:
                    logger.debug(f"Valid session {session_id} for user {user_id}")
                    return True
            
            logger.warning(f"Invalid session {session_id} for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error validating session {session_id} for user {user_id}: {str(e)}")
            return False