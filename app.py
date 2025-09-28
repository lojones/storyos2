"""
StoryOS v2 - Main Application
A Streamlit-based text-based RPG with AI-powered dungeon master
"""

import streamlit as st
from datetime import datetime
import json
import time
from typing import Dict, Any, List, Optional

# Import our custom modules
from logging_config import StoryOSLogger, get_logger
from utils.st_session_management import SessionManager, initialize_session_state, navigate_to_page, Pages
from utils.auth import require_auth, require_admin, show_login_form, logout_user, is_admin
from utils.db_utils import get_db_manager
from utils.llm_utils import get_llm_utility
from game.game_logic import load_game_session
from utils.scenario_parser import validate_scenario_data, parse_scenario_from_markdown
from pages.game_page import show_game_page
from utils.initialize_db import initialize_database
from utils.validation import validate_initial_data
from pages.new_game_page import show_new_game_page
from pages.load_game_page import show_load_game_page
from pages.scenarios_page import show_scenarios_page
from pages.system_prompt_page import show_system_prompt_page

# Configure Streamlit page
st.set_page_config(
    page_title="StoryOS v2",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'About': "https://lojones.github.io/"}
)



def show_main_menu(user: Dict[str, Any]):
    """Show the main menu with navigation options"""
    logger = get_logger("app")
    
    user_id = user.get('user_id', 'unknown')
    logger.info(f"Displaying main menu for user: {user_id}")
    
    try:
        st.title("🎲 StoryOS v2 - Interactive RPG")
        st.write(f"Welcome back, **{user_id}**!")
        
        StoryOSLogger.log_user_action(user_id, "view_main_menu", {})
        
        # Menu options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Game Sessions")
            
            if st.button("🎮 Start New Game", width="stretch"):
                logger.debug(f"User {user_id} clicked Start New Game")
                navigate_to_page(Pages.NEW_GAME, user_id)
            
            if st.button("📚 Load Saved Game", width="stretch"):
                logger.debug(f"User {user_id} clicked Load Saved Game")
                navigate_to_page(Pages.LOAD_GAME, user_id)
            
            if st.button("📖 View Scenarios", width="stretch"):
                logger.debug(f"User {user_id} clicked View Scenarios")
                navigate_to_page(Pages.SCENARIOS, user_id)
        
        with col2:
            st.subheader("Account & Settings")
            
            if is_admin():
                if st.button("⚙️ Admin: System Prompt", width="stretch"):
                    logger.debug(f"Admin {user_id} clicked System Prompt")
                    navigate_to_page(Pages.SYSTEM_PROMPT, user_id)
            
            if st.button("🚪 Logout", width="stretch"):
                logger.info(f"User {user_id} logging out")
                StoryOSLogger.log_user_action(user_id, "logout", {})
                logout_user()
                st.rerun()
                
    except Exception as e:
        logger.error(f"Error displaying main menu for user {user_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("app", e, {
            "operation": "show_main_menu",
            "user_id": user_id
        })
        st.error("Error loading main menu")


def main():
    """Main application entry point"""
    logger = get_logger("app")
    
    try:
        # Initialize logging for the application
        logger.info("Entered main")
        
        initialize_session_state()
        
        # Check if app initialization has already happened this session
        if 'app_initialized' not in st.session_state:
            st.session_state.app_initialized = False
        
        # Check authentication
        user = require_auth()
        if not user:
            logger.debug("User not authenticated, showing login form")
            show_login_form()
            return
        
        user_id = user.get('user_id', 'unknown')
        logger.info(f"Looping through for user: {user_id}")
        
        # Initialize database collections and indexes if needed (only once per session)
        if not st.session_state.app_initialized:
            logger.debug("Running database initialization check (first time this session)")
            initialize_database()
            st.session_state.app_initialized = True
            logger.info("App initialization completed successfully")
            # Validate that required initial data exists after initialization
            validation_result = validate_initial_data()
            if not validation_result.get('success', False):
                logger.error(f"Initial data validation issues detected: {validation_result.get('errors', [])}")
                st.error("Initial data validation failed. Cannot proceed.")
        else:
            logger.debug("Skipping database initialization - already completed this session")
                
        # Route to appropriate page
        page = SessionManager.get_current_page()
        logger.debug(f"Routing to page: {page} for user: {user_id}")      
        
        if page == Pages.MAIN_MENU:
            show_main_menu(user)
        elif page == Pages.NEW_GAME:
            show_new_game_page(user)
        elif page == Pages.LOAD_GAME:
            show_load_game_page(user)
        elif page == Pages.SCENARIOS:
            show_scenarios_page(user)
        elif page == Pages.SYSTEM_PROMPT:
            show_system_prompt_page(user)
        elif page == Pages.GAME:
            show_game_page()
        else:
            logger.warning(f"Unknown page requested: {page}, routing to main menu")
            show_main_menu(user)
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        StoryOSLogger.log_error_with_context("app", e, {
            "operation": "main",
            "current_page": SessionManager.get_current_page()
        })
        st.error("A critical error occurred. Please refresh the page.")

if __name__ == "__main__":
    # Set up logging when the application starts
    StoryOSLogger.setup_logging()
    logger = get_logger("app")
    logger.info("Starting new loop")
    
    main()
