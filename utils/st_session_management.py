"""
Streamlit Session State Management for StoryOS v2
Centralized session state management and navigation utilities
"""

import streamlit as st
from typing import Dict, Any, Optional, Union
from logging_config import StoryOSLogger, get_logger


class SessionManager:
    """Centralized session state management for StoryOS v2"""
    
    # Session state keys
    CURRENT_PAGE = 'current_page'
    CURRENT_GAME_SESSION = 'current_game_session'
    CHAT_INPUT_KEY = 'chat_input_key'
    EDITING_SCENARIO = 'editing_scenario'
    USER_DATA = 'user_data'
    
    # Page names
    class Pages:
        MAIN_MENU = 'main_menu'
        NEW_GAME = 'new_game'
        LOAD_GAME = 'load_game'
        SCENARIOS = 'scenarios'
        SYSTEM_PROMPT = 'system_prompt'
        GAME = 'game'
        EDIT_SCENARIO = 'edit_scenario'
    
    @classmethod
    def initialize_session_state(cls):
        """Initialize all session state variables with default values"""
        logger = get_logger("st_session_management")
        
        try:
            initialized_keys = []
            
            # Core navigation state
            if cls.CURRENT_PAGE not in st.session_state:
                st.session_state[cls.CURRENT_PAGE] = cls.Pages.MAIN_MENU
                initialized_keys.append(cls.CURRENT_PAGE)
            
            # Game session state
            if cls.CURRENT_GAME_SESSION not in st.session_state:
                st.session_state[cls.CURRENT_GAME_SESSION] = None
                initialized_keys.append(cls.CURRENT_GAME_SESSION)
            
            # UI state
            if cls.CHAT_INPUT_KEY not in st.session_state:
                st.session_state[cls.CHAT_INPUT_KEY] = 0
                initialized_keys.append(cls.CHAT_INPUT_KEY)
            
            # Editor state
            if cls.EDITING_SCENARIO not in st.session_state:
                st.session_state[cls.EDITING_SCENARIO] = None
                initialized_keys.append(cls.EDITING_SCENARIO)
            
            # User data cache
            if cls.USER_DATA not in st.session_state:
                st.session_state[cls.USER_DATA] = {}
                initialized_keys.append(cls.USER_DATA)
            
            if initialized_keys:
                logger.debug(f"Initialized session state keys: {initialized_keys}")
                
        except Exception as e:
            logger.error(f"Error initializing session state: {str(e)}")
            StoryOSLogger.log_error_with_context("st_session_management", e, {
                "operation": "initialize_session_state"
            })
    
    @classmethod
    def navigate_to_page(cls, page: str, user_id: Optional[str] = None):
        """Navigate to a specific page with logging"""
        logger = get_logger("st_session_management")
        
        try:
            current_page = cls.get_current_page()
            if current_page != page:
                st.session_state[cls.CURRENT_PAGE] = page
                logger.debug(f"Page navigation: {current_page} → {page}")
                
                if user_id:
                    StoryOSLogger.log_user_action(user_id, f"navigate_to_{page}", {
                        "from_page": current_page,
                        "to_page": page
                    })
                
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error navigating to page {page}: {str(e)}")
            StoryOSLogger.log_error_with_context("st_session_management", e, {
                "operation": "navigate_to_page",
                "target_page": page
            })
    
    @classmethod
    def get_current_page(cls) -> str:
        """Get the current page name"""
        return st.session_state.get(cls.CURRENT_PAGE, cls.Pages.MAIN_MENU)
    
    @classmethod
    def set_game_session(cls, session_id: Optional[str], user_id: Optional[str] = None):
        """Set the current game session ID"""
        logger = get_logger("st_session_management")
        
        try:
            current_session = cls.get_game_session()
            st.session_state[cls.CURRENT_GAME_SESSION] = session_id
            
            logger.debug(f"Game session updated: {current_session} → {session_id}")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "set_game_session", {
                    "previous_session": current_session,
                    "new_session": session_id
                })
                
        except Exception as e:
            logger.error(f"Error setting game session {session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("st_session_management", e, {
                "operation": "set_game_session",
                "session_id": session_id
            })
    
    @classmethod
    def get_game_session(cls) -> Optional[str]:
        """Get the current game session ID"""
        return st.session_state.get(cls.CURRENT_GAME_SESSION)
    
    @classmethod
    def clear_game_session(cls, user_id: Optional[str] = None):
        """Clear the current game session"""
        logger = get_logger("st_session_management")
        
        try:
            current_session = cls.get_game_session()
            st.session_state[cls.CURRENT_GAME_SESSION] = None
            
            logger.debug(f"Game session cleared: {current_session}")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "clear_game_session", {
                    "cleared_session": current_session
                })
                
        except Exception as e:
            logger.error(f"Error clearing game session: {str(e)}")
    
    @classmethod
    def increment_chat_key(cls) -> int:
        """Increment and return the chat input key for form clearing"""
        logger = get_logger("st_session_management")
        
        try:
            current_key = st.session_state.get(cls.CHAT_INPUT_KEY, 0)
            new_key = current_key + 1
            st.session_state[cls.CHAT_INPUT_KEY] = new_key
            
            logger.debug(f"Chat input key incremented: {current_key} → {new_key}")
            return new_key
            
        except Exception as e:
            logger.error(f"Error incrementing chat key: {str(e)}")
            return 0
    
    @classmethod
    def get_chat_key(cls) -> int:
        """Get the current chat input key"""
        return st.session_state.get(cls.CHAT_INPUT_KEY, 0)
    
    @classmethod
    def set_editing_scenario(cls, scenario: Optional[Dict[str, Any]], user_id: Optional[str] = None):
        """Set the scenario being edited"""
        logger = get_logger("st_session_management")
        
        try:
            st.session_state[cls.EDITING_SCENARIO] = scenario
            scenario_name = scenario.get('name', 'unnamed') if scenario else None
            
            logger.debug(f"Editing scenario set: {scenario_name}")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "set_editing_scenario", {
                    "scenario_name": scenario_name,
                    "scenario_id": scenario.get('scenario_id') if scenario else None
                })
                
        except Exception as e:
            logger.error(f"Error setting editing scenario: {str(e)}")
            StoryOSLogger.log_error_with_context("st_session_management", e, {
                "operation": "set_editing_scenario"
            })
    
    @classmethod
    def get_editing_scenario(cls) -> Optional[Dict[str, Any]]:
        """Get the scenario being edited"""
        return st.session_state.get(cls.EDITING_SCENARIO)
    
    @classmethod
    def clear_editing_scenario(cls, user_id: Optional[str] = None):
        """Clear the editing scenario"""
        logger = get_logger("st_session_management")
        
        try:
            current_scenario = cls.get_editing_scenario()
            st.session_state[cls.EDITING_SCENARIO] = None
            
            logger.debug("Editing scenario cleared")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "clear_editing_scenario", {
                    "was_editing": current_scenario.get('name') if current_scenario else None
                })
                
        except Exception as e:
            logger.error(f"Error clearing editing scenario: {str(e)}")
    
    @classmethod
    def cache_user_data(cls, key: str, data: Any, user_id: Optional[str] = None):
        """Cache user-specific data in session state"""
        logger = get_logger("st_session_management")
        
        try:
            if cls.USER_DATA not in st.session_state:
                st.session_state[cls.USER_DATA] = {}
            
            st.session_state[cls.USER_DATA][key] = data
            logger.debug(f"Cached user data: {key}")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "cache_user_data", {
                    "data_key": key,
                    "data_type": type(data).__name__
                })
                
        except Exception as e:
            logger.error(f"Error caching user data {key}: {str(e)}")
    
    @classmethod
    def get_cached_user_data(cls, key: str, default: Any = None) -> Any:
        """Get cached user data from session state"""
        user_data = st.session_state.get(cls.USER_DATA, {})
        return user_data.get(key, default)
    
    @classmethod
    def clear_user_cache(cls, user_id: Optional[str] = None):
        """Clear all cached user data"""
        logger = get_logger("st_session_management")
        
        try:
            st.session_state[cls.USER_DATA] = {}
            logger.debug("User data cache cleared")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "clear_user_cache", {})
                
        except Exception as e:
            logger.error(f"Error clearing user cache: {str(e)}")
    
    @classmethod
    def get_session_info(cls) -> Dict[str, Any]:
        """Get comprehensive session state information for debugging"""
        return {
            "current_page": cls.get_current_page(),
            "game_session": cls.get_game_session(),
            "chat_key": cls.get_chat_key(),
            "editing_scenario": bool(cls.get_editing_scenario()),
            "cached_data_keys": list(st.session_state.get(cls.USER_DATA, {}).keys()),
            "total_session_keys": len(st.session_state)
        }
    
    @classmethod
    def reset_session(cls, user_id: Optional[str] = None):
        """Reset session state to initial values"""
        logger = get_logger("st_session_management")
        
        try:
            # Store info before reset for logging
            session_info = cls.get_session_info()
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith('_'):  # Skip internal Streamlit keys
                    continue
                del st.session_state[key]
            
            # Reinitialize
            cls.initialize_session_state()
            
            logger.info("Session state reset completed")
            
            if user_id:
                StoryOSLogger.log_user_action(user_id, "reset_session", {
                    "previous_state": session_info
                })
                
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            StoryOSLogger.log_error_with_context("st_session_management", e, {
                "operation": "reset_session"
            })


# Convenience functions for easier usage
def initialize_session_state():
    """Initialize session state (convenience function)"""
    SessionManager.initialize_session_state()

def navigate_to_page(page: str, user_id: Optional[str] = None):
    """Navigate to a page (convenience function)"""
    SessionManager.navigate_to_page(page, user_id)

def get_current_page() -> str:
    """Get current page (convenience function)"""
    return SessionManager.get_current_page()

def set_game_session(session_id: Optional[str], user_id: Optional[str] = None):
    """Set game session (convenience function)"""
    SessionManager.set_game_session(session_id, user_id)

def get_game_session() -> Optional[str]:
    """Get game session (convenience function)"""
    return SessionManager.get_game_session()

def clear_game_session(user_id: Optional[str] = None):
    """Clear game session (convenience function)"""
    SessionManager.clear_game_session(user_id)

# Page constants for import
Pages = SessionManager.Pages