"""
Start New Game Page Module for StoryOS v2
Handles the new game creation interface and scenario selection
"""

import streamlit as st
from typing import Dict, Any
from logging_config import StoryOSLogger, get_logger
from utils.st_session_management import SessionManager, navigate_to_page, Pages
from utils.db_utils import get_db_manager
from game.game_logic import create_new_game


class StartNewGameInterface:
    """Handles the new game creation interface"""
    
    @classmethod
    def show_new_game_page(cls, user: Dict[str, Any]):
        """Show the new game creation page with scenario selection"""
        logger = get_logger("start_new_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.info(f"Displaying new game page for user: {user_id}")
            
            # Page header
            st.title("🎮 Start New Game")
            
            # Back to menu button
            if st.button("← Back to Menu", key="back_to_menu"):
                logger.debug(f"User {user_id} clicked back to menu from new game page")
                navigate_to_page(Pages.MAIN_MENU)
                return
            
            # Load and display scenarios
            cls._render_scenario_selection(user)
            
        except Exception as e:
            logger.error(f"Error displaying new game page for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("start_new_game", e, {
                "operation": "show_new_game_page",
                "user_id": user_id
            })
            st.error("Error loading new game page")
    
    @classmethod
    def _render_scenario_selection(cls, user: Dict[str, Any]):
        """Render the scenario selection interface"""
        logger = get_logger("start_new_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            # Check if we're in the process of starting a game
            if st.session_state.get("storyos_starting_game", False):
                logger.debug(f"Game starting state detected for user {user_id} - showing loading")
                cls._show_game_starting_state()
                return
            
            db = get_db_manager()
            
            if not db.is_connected():
                logger.error("Database connection failed when loading scenarios")
                st.error("Database connection failed. Please try again.")
                return
            
            # Get available scenarios
            scenarios = db.get_all_scenarios()
            logger.debug(f"Retrieved {len(scenarios)} scenarios for user {user_id}")
            
            if not scenarios:
                logger.warning(f"No scenarios available for user {user_id}")
                cls._show_no_scenarios_message()
                return
            
            # Display scenario selection
            st.subheader("Choose a Scenario")
            cls._render_scenarios_list(scenarios, user)
            
        except Exception as e:
            logger.error(f"Error rendering scenario selection for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("start_new_game", e, {
                "operation": "_render_scenario_selection",
                "user_id": user_id
            })
            st.error("Error loading scenarios")
    
    @classmethod
    def _show_no_scenarios_message(cls):
        """Display message when no scenarios are available"""
        logger = get_logger("start_new_game")
        logger.debug("Displaying no scenarios available message")
        
        st.warning("No scenarios available. Please contact an admin to add scenarios.")
        st.info("Scenarios need to be uploaded by an administrator before you can start playing.")
    
    @classmethod
    def _show_game_starting_state(cls):
        """Display loading state and handle game creation when game is starting"""
        logger = get_logger("start_new_game")
        logger.debug("Displaying game starting state and handling creation")
        
        # Show loading indicator
        st.info("🚀 Starting your adventure...")
        st.write("Please wait while we prepare your game...")
        
        # Get the stored game creation data from session state
        scenario_id = st.session_state.get("storyos_scenario_id")
        scenario_name = st.session_state.get("storyos_scenario_name")
        user_data = st.session_state.get("storyos_start_game_user")
        
        if scenario_id and user_data:
            logger.debug(f"Found game creation data - Scenario: {scenario_name}")
            
            # Create progress placeholders
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Show progress steps
            with progress_placeholder:
                progress_bar = st.progress(0)
            
            with status_placeholder:
                status_text = st.empty()
                
            # Step 1: Preparing
            progress_bar.progress(25)
            status_text.text("Preparing scenario...")
            
            # Actually create the game session
            try:
                user_id = user_data.get('user_id', 'unknown')
                
                # Step 2: Creating session
                progress_bar.progress(50)
                status_text.text("Creating game session...")
                
                session_id = create_new_game(user_id, scenario_id)
                
                if session_id:
                    # Step 3: Initializing
                    progress_bar.progress(75)
                    status_text.text("Initializing adventure...")
                    
                    # Set the game session in session manager
                    SessionManager.set_game_session_id(session_id, user_id)
                    
                    # Step 4: Complete
                    progress_bar.progress(100)
                    status_text.text("Adventure ready!")
                    
                    # Clear the visual elements immediately
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    
                    # Clear the starting state and temp data
                    st.session_state.pop("storyos_starting_game", None)
                    st.session_state.pop("storyos_scenario_id", None)
                    st.session_state.pop("storyos_scenario_name", None)
                    st.session_state.pop("storyos_start_game_user", None)
                    
                    # Log successful game creation
                    StoryOSLogger.log_user_action(user_id, "game_started_successfully", {
                        "scenario_id": scenario_id,
                        "scenario_name": scenario_name,
                        "session_id": session_id
                    })
                    
                    # Navigate to game page
                    navigate_to_page(Pages.GAME, user_id)
                    
                    # Force rerun to navigate
                    st.rerun()
                    
                else:
                    # Failed to create session
                    progress_bar.progress(100)
                    status_text.error("Failed to create game session")
                    
                    # Clear the visual elements after showing error
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    
                    # Clear state on failure
                    st.session_state.pop("storyos_starting_game", None)
                    st.session_state.pop("storyos_scenario_id", None)
                    st.session_state.pop("storyos_scenario_name", None)
                    st.session_state.pop("storyos_start_game_user", None)
                    
                    st.error("❌ Failed to start game. Please try again.")
                    
                    if st.button("← Back to Scenario Selection"):
                        st.rerun()
                        
            except Exception as e:
                logger.error(f"Error during game creation: {str(e)}")
                
                # Clear the visual elements after showing error
                progress_placeholder.empty()
                status_placeholder.empty()
                
                # Clear state on error
                st.session_state.pop("storyos_starting_game", None)
                st.session_state.pop("storyos_scenario_id", None)
                st.session_state.pop("storyos_scenario_name", None)
                st.session_state.pop("storyos_start_game_user", None)
                
                st.error("❌ An error occurred while starting the game.")
                
                if st.button("← Back to Scenario Selection"):
                    st.rerun()
        else:
            logger.warning("No game creation data found in session state")
            st.error("Game creation data not found. Please try again.")
            
            # Clear the starting state
            st.session_state.pop("storyos_starting_game", None)
            
            if st.button("← Back to Scenario Selection"):
                st.rerun()
    
    @classmethod
    def _render_scenarios_list(cls, scenarios: list, user: Dict[str, Any]):
        """Render the list of available scenarios"""
        logger = get_logger("start_new_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.debug(f"Rendering {len(scenarios)} scenarios for user {user_id}")
            
            # Display each scenario in an expander
            for i, scenario in enumerate(scenarios):
                scenario_name = scenario.get('name', 'Unnamed Scenario')
                scenario_id = scenario.get('scenario_id', str(scenario.get('_id', 'unknown')))
                
                logger.debug(f"Rendering scenario {i+1}: {scenario_name} (ID: {scenario_id})")
                
                with st.expander(f"📖 {scenario_name}"):
                    cls._render_scenario_details(scenario)
                    cls._render_start_game_button(scenario, user)
                    
        except Exception as e:
            logger.error(f"Error rendering scenarios list for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("start_new_game", e, {
                "operation": "_render_scenarios_list",
                "user_id": user_id,
                "scenarios_count": len(scenarios)
            })
    
    @classmethod
    def _render_scenario_details(cls, scenario: Dict[str, Any]):
        """Render the details of a single scenario"""
        logger = get_logger("start_new_game")
        
        try:
            scenario_name = scenario.get('name', 'Unnamed')
            
            # Display scenario information
            st.write(f"**Author:** {scenario.get('author', 'Unknown')}")
            st.write(f"**Setting:** {scenario.get('setting', 'Unknown')}")
            st.write(f"**Description:** {scenario.get('description', 'No description')}")
            st.write(f"**Player Role:** {scenario.get('role', 'Unknown')}")
            st.write(f"**Starting Location:** {scenario.get('initial_location', 'Unknown')}")
            
            # Additional details if available
            if 'version' in scenario:
                st.write(f"**Version:** {scenario.get('version', 'Unknown')}")
            
            logger.debug(f"Rendered details for scenario: {scenario_name}")
            
        except Exception as e:
            logger.error(f"Error rendering scenario details: {str(e)}")
            st.error("Error displaying scenario details")
    
    @classmethod
    def _render_start_game_button(cls, scenario: Dict[str, Any], user: Dict[str, Any]):
        """Render the start game button for a scenario"""
        logger = get_logger("start_new_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            scenario_name = scenario.get('name', 'Unnamed')
            scenario_key = scenario.get('scenario_id', str(scenario.get('_id', 'unknown')))
            
            button_key = f"start_{scenario_key}"
            button_label = f"🚀 Start Game: {scenario_name}"
            
            if st.button(button_label, key=button_key, width="stretch"):
                logger.info(f"User {user_id} clicked start game for scenario: {scenario_name} (ID: {scenario_key})")
                cls._handle_start_game_click(scenario_key, scenario_name, user)
                
        except Exception as e:
            logger.error(f"Error rendering start game button: {str(e)}")
            StoryOSLogger.log_error_with_context("start_new_game", e, {
                "operation": "_render_start_game_button",
                "user_id": user_id,
                "scenario_name": scenario.get('name', 'unknown')
            })
    
    @classmethod
    def _handle_start_game_click(cls, scenario_id: str, scenario_name: str, user: Dict[str, Any]):
        """Handle the start game button click"""
        logger = get_logger("start_new_game")
        user_id = user.get('user_id', 'unknown')
        
        try:
            logger.info(f"Starting new game for user {user_id}, scenario: {scenario_name}")
            
            # Store game creation data in session state
            st.session_state["storyos_starting_game"] = True
            st.session_state["storyos_scenario_id"] = scenario_id
            st.session_state["storyos_scenario_name"] = scenario_name
            st.session_state["storyos_start_game_user"] = user
            
            # Log user action
            StoryOSLogger.log_user_action(user_id, "start_new_game_attempt", {
                "scenario_id": scenario_id,
                "scenario_name": scenario_name
            })
            
            # Rerun to immediately show loading state and handle creation
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error initiating game start for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("start_new_game", e, {
                "operation": "_handle_start_game_click",
                "user_id": user_id,
                "scenario_id": scenario_id,
                "scenario_name": scenario_name
            })
            st.error("❌ An error occurred while starting the game.")
    
# Convenience function for easier import
def show_new_game_page(user: Dict[str, Any]):
    """Show the new game page (convenience function)"""
    StartNewGameInterface.show_new_game_page(user)


# Additional utilities for new game page
class StartNewGameUtils:
    """Utility functions for start new game operations"""
    
    @staticmethod
    def get_available_scenarios_count() -> int:
        """Get the count of available scenarios"""
        logger = get_logger("start_new_game")
        
        try:
            db = get_db_manager()
            if not db.is_connected():
                logger.warning("Database not connected when counting scenarios")
                return 0
            
            scenarios = db.get_all_scenarios()
            count = len(scenarios) if scenarios else 0
            logger.debug(f"Available scenarios count: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting available scenarios: {str(e)}")
            return 0
    
    @staticmethod
    def validate_scenario_selection(scenario_id: str) -> bool:
        """Validate that a scenario exists and is accessible"""
        logger = get_logger("start_new_game")
        
        try:
            if not scenario_id or scenario_id == 'unknown':
                logger.debug("Invalid scenario ID provided")
                return False
            
            db = get_db_manager()
            if not db.is_connected():
                logger.warning("Database not connected for scenario validation")
                return False
            
            scenario = db.get_scenario(scenario_id)
            is_valid = bool(scenario)
            logger.debug(f"Scenario validation - ID: {scenario_id}, Valid: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating scenario {scenario_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_popular_scenarios(limit: int = 5) -> list:
        """Get popular scenarios (placeholder for future implementation)"""
        logger = get_logger("start_new_game")
        
        try:
            # For now, just return all scenarios limited by count
            # In future, this could be based on play statistics
            db = get_db_manager()
            if not db.is_connected():
                return []
            
            scenarios = db.get_all_scenarios()
            if not scenarios:
                return []
            
            # Return up to 'limit' scenarios
            popular = scenarios[:limit]
            logger.debug(f"Retrieved {len(popular)} popular scenarios (limit: {limit})")
            return popular
            
        except Exception as e:
            logger.error(f"Error getting popular scenarios: {str(e)}")
            return []