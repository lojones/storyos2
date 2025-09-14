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
from st_session_management import SessionManager, initialize_session_state, navigate_to_page, Pages
from auth import require_auth, require_admin, show_login_form, logout_user, is_admin
from db_utils import get_db_manager
from llm_utils import get_llm_utility
from game_logic import (
    load_game_session, validate_scenario_data, parse_scenario_from_markdown
)
from game_page import show_game_page
from initialize_db import initialize_database
from start_new_game_page import show_new_game_page
from show_load_game_page import show_load_game_page
from show_scenarios_page import show_scenarios_page
from system_prompt_page import show_system_prompt_page

# Configure Streamlit page
st.set_page_config(
    page_title="StoryOS v2",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
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
            
            if st.button("🎮 Start New Game", use_container_width=True):
                logger.debug(f"User {user_id} clicked Start New Game")
                navigate_to_page(Pages.NEW_GAME, user_id)
            
            if st.button("📚 Load Saved Game", use_container_width=True):
                logger.debug(f"User {user_id} clicked Load Saved Game")
                navigate_to_page(Pages.LOAD_GAME, user_id)
            
            if st.button("📖 View Scenarios", use_container_width=True):
                logger.debug(f"User {user_id} clicked View Scenarios")
                navigate_to_page(Pages.SCENARIOS, user_id)
        
        with col2:
            st.subheader("Account & Settings")
            
            if is_admin():
                if st.button("⚙️ Admin: System Prompt", use_container_width=True):
                    logger.debug(f"Admin {user_id} clicked System Prompt")
                    navigate_to_page(Pages.SYSTEM_PROMPT, user_id)
            
            if st.button("🚪 Logout", use_container_width=True):
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


def validate_initial_data():
    """Validate that required initial data exists after database initialization"""
    logger = get_logger("app")
    start_time = time.time()
    
    logger.debug("Running initial data validation check (post-initialization)")
    
    try:
        db = get_db_manager()
        
        if not db.is_connected():
            logger.warning("Database not connected during initial data load")
            return
        
        # Just verify that data exists - initialization should have handled creation
        active_prompt = db.get_active_system_prompt()
        scenarios = db.get_all_scenarios()
        
        duration = time.time() - start_time
        
        if active_prompt and scenarios:
            logger.info(f"Initial data verification complete - System prompt: ✅, Scenarios: {len(scenarios)}")
        else:
            logger.warning(f"Initial data verification - System prompt: {'✅' if active_prompt else '❌'}, Scenarios: {len(scenarios) if scenarios else 0}")
        
        StoryOSLogger.log_performance("app", "validate_initial_data", duration, {
            "scenarios_exist": len(scenarios) if scenarios else 0,
            "system_prompt_exists": bool(active_prompt)
        })
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error during initial data validation: {str(e)}")
        StoryOSLogger.log_error_with_context("app", e, {
            "operation": "validate_initial_data",
            "duration": duration
        })

def main():
    """Main application entry point"""
    logger = get_logger("app")
    
    try:
        # Initialize logging for the application
        logger.info("Starting StoryOS v2 application")
        
        initialize_session_state()
        
        # Check authentication
        user = require_auth()
        if not user:
            logger.debug("User not authenticated, showing login form")
            show_login_form()
            return
        
        user_id = user.get('user_id', 'unknown')
        logger.info(f"Application started for user: {user_id}")
        
        # Initialize database collections and indexes if needed
        try:
            logger.debug("Running database initialization check")
            initialize_database()
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            StoryOSLogger.log_error_with_context("app", e, {
                "operation": "database_initialization"
            })
            # Continue even if initialization fails - app may still work with existing data
        
        # Validate that required initial data exists after initialization
        validate_initial_data()
        
        # Route to appropriate page
        page = SessionManager.get_current_page()
        logger.debug(f"Routing to page: {page} for user: {user_id}")
        
        StoryOSLogger.log_user_action(user_id, "page_view", {
            "page": page
        })
        
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
    logger.info("StoryOS v2 application starting up")
    
    main()
