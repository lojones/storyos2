"""
StoryOS v2 - Scenarios Management Page
Provides interface for viewing and managing RPG scenarios
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional

# Import our custom modules
from logging_config import StoryOSLogger, get_logger
from utils.st_session_management import SessionManager, navigate_to_page, Pages
from utils.auth import is_admin
from utils.db_utils import get_db_manager
from utils.scenario_parser import validate_scenario_data, parse_scenario_from_markdown


class ScenariosInterface:
    """Interface for managing and viewing RPG scenarios"""
    
    def __init__(self):
        """Initialize the scenarios interface"""
        self.logger = get_logger("show_scenarios_page")
        self.db = get_db_manager()
        self.logger.debug("ScenariosInterface initialized")

    def show_scenario_details(self, scenario: Dict[str, Any]) -> None:
        """Display detailed information about a scenario"""
        try:
            # Display scenario in a nice format
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {scenario.get('name', 'Unknown')}")
                st.write(f"**Author:** {scenario.get('author', 'Unknown')}")
                st.write(f"**Version:** {scenario.get('version', 'Unknown')}")
                st.write(f"**Setting:** {scenario.get('setting', 'Unknown')}")
            
            with col2:
                st.write(f"**Player Role:** {scenario.get('role', 'Unknown')}")
                st.write(f"**Player Name:** {scenario.get('player_name', 'Unknown')}")
                st.write(f"**Initial Location:** {scenario.get('initial_location', 'Unknown')}")
            
            st.write(f"**Description:**")
            st.write(scenario.get('description', 'No description available'))
            
            if 'dungeon_master_behaviour' in scenario:
                with st.expander("DM Behavior Guidelines"):
                    st.write(scenario['dungeon_master_behaviour'])
            
            scenario_name = scenario.get('name', 'Unknown')
            self.logger.debug(f"Displayed details for scenario: {scenario_name}")
            
        except Exception as e:
            self.logger.error(f"Error displaying scenario details: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "show_scenario_details",
                "scenario_id": scenario.get('scenario_id', 'unknown')
            })
            st.error("Error displaying scenario details")

    def show_admin_edit_button(self, scenario: Dict[str, Any], user_id: str) -> None:
        """Show edit button for admins"""
        try:
            if not is_admin():
                return
            
            # Use scenario_id if available, otherwise use MongoDB _id
            scenario_key = scenario.get('scenario_id', str(scenario.get('_id', 'unknown')))
            scenario_name = scenario.get('name', 'Unknown')
            
            if st.button(f"✏️ Edit Scenario", key=f"edit_{scenario_key}"):
                self.logger.info(f"Admin {user_id} initiated edit for scenario: {scenario_name}")
                StoryOSLogger.log_user_action(user_id, "edit_scenario_initiated", {
                    "scenario_id": scenario.get('scenario_id'),
                    "scenario_name": scenario_name
                })
                
                SessionManager.set_editing_scenario(scenario, user_id)
                navigate_to_page(Pages.EDIT_SCENARIO, user_id)
                
        except Exception as e:
            self.logger.error(f"Error handling admin edit button: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "show_admin_edit_button",
                "user_id": user_id,
                "scenario_id": scenario.get('scenario_id', 'unknown')
            })

    def show_scenarios_list(self, scenarios: List[Dict[str, Any]], user_id: str) -> None:
        """Display list of available scenarios"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"Displaying {len(scenarios)} scenarios for user: {user_id}")
            
            for scenario in scenarios:
                scenario_name = scenario.get('name', 'Unnamed Scenario')
                with st.expander(f"📖 {scenario_name}"):
                    self.show_scenario_details(scenario)
                    self.show_admin_edit_button(scenario, user_id)
            
            duration = time.time() - start_time
            StoryOSLogger.log_performance("show_scenarios_page", "show_scenarios_list", duration, {
                "scenarios_count": len(scenarios),
                "user_id": user_id
            })
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error displaying scenarios list: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "show_scenarios_list",
                "user_id": user_id,
                "scenarios_count": len(scenarios) if scenarios else 0,
                "duration": duration
            })
            st.error("Error displaying scenarios list")

    def handle_scenario_upload(self, user_id: str) -> None:
        """Handle scenario file upload and validation"""
        try:
            uploaded_file = st.file_uploader("Upload Scenario Markdown File", type=['md'])
            if uploaded_file is not None:
                self.logger.info(f"Admin {user_id} uploaded scenario file: {uploaded_file.name}")
                
                try:
                    content = uploaded_file.read().decode('utf-8')
                    scenario_data = parse_scenario_from_markdown(content)
                    
                    self.logger.debug(f"Parsed scenario data from uploaded file: {uploaded_file.name}")
                    
                    # Validate scenario data
                    errors = validate_scenario_data(scenario_data)
                    
                    if errors:
                        self.logger.warning(f"Scenario validation failed for {uploaded_file.name}: {len(errors)} errors")
                        st.error("Validation errors:")
                        for error in errors:
                            st.write(f"- {error}")
                        
                        StoryOSLogger.log_user_action(user_id, "scenario_upload_validation_failed", {
                            "filename": uploaded_file.name,
                            "error_count": len(errors),
                            "errors": errors
                        })
                    else:
                        self.logger.info(f"Scenario validation passed for {uploaded_file.name}")
                        st.success("Scenario validation passed!")
                        st.json(scenario_data)
                        
                        StoryOSLogger.log_user_action(user_id, "scenario_upload_validation_passed", {
                            "filename": uploaded_file.name,
                            "scenario_name": scenario_data.get('name', 'unknown')
                        })
                        
                        if st.button("💾 Save Scenario"):
                            self.save_scenario(scenario_data, user_id, uploaded_file.name)
                            
                except Exception as parse_error:
                    self.logger.error(f"Error parsing scenario file {uploaded_file.name}: {str(parse_error)}")
                    StoryOSLogger.log_error_with_context("show_scenarios_page", parse_error, {
                        "operation": "parse_scenario_file",
                        "filename": uploaded_file.name,
                        "user_id": user_id
                    })
                    st.error(f"Error parsing scenario file: {str(parse_error)}")
                    
        except Exception as e:
            self.logger.error(f"Error handling scenario upload: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "handle_scenario_upload",
                "user_id": user_id
            })
            st.error("Error handling file upload")

    def save_scenario(self, scenario_data: Dict[str, Any], user_id: str, filename: str) -> None:
        """Save a validated scenario to the database"""
        start_time = time.time()
        
        try:
            scenario_name = scenario_data.get('name', 'unknown')
            self.logger.info(f"Admin {user_id} attempting to save scenario: {scenario_name}")
            
            if self.db.create_scenario(scenario_data):
                duration = time.time() - start_time
                self.logger.info(f"Scenario saved successfully: {scenario_name} (took {duration:.2f}s)")
                
                StoryOSLogger.log_user_action(user_id, "scenario_saved", {
                    "scenario_name": scenario_name,
                    "scenario_id": scenario_data.get('scenario_id'),
                    "filename": filename,
                    "duration": duration
                })
                
                st.success("Scenario saved successfully!")
                st.rerun()
            else:
                duration = time.time() - start_time
                self.logger.error(f"Failed to save scenario: {scenario_name} (took {duration:.2f}s)")
                
                StoryOSLogger.log_user_action(user_id, "scenario_save_failed", {
                    "scenario_name": scenario_name,
                    "filename": filename,
                    "duration": duration
                })
                
                st.error("Failed to save scenario")
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error saving scenario: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "save_scenario",
                "user_id": user_id,
                "scenario_name": scenario_data.get('name', 'unknown'),
                "duration": duration
            })
            st.error("Error saving scenario")

    def show_admin_upload_section(self, user_id: str) -> None:
        """Display admin section for uploading new scenarios"""
        try:
            self.logger.debug(f"Displaying admin upload section for user: {user_id}")
            
            st.divider()
            st.subheader("🔧 Admin: Add New Scenario")
            
            StoryOSLogger.log_user_action(user_id, "view_admin_upload_section", {})
            
            self.handle_scenario_upload(user_id)
            
        except Exception as e:
            self.logger.error(f"Error showing admin upload section: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "show_admin_upload_section",
                "user_id": user_id
            })

    def show_page(self, user: Dict[str, Any]) -> None:
        """Main method to display the scenarios page"""
        start_time = time.time()
        
        try:
            user_id = user.get('user_id', 'unknown')
            self.logger.info(f"Displaying scenarios page for user: {user_id}")
            
            st.title("📖 Role Playing Game Scenarios")
            
            # Back button
            if st.button("← Back to Menu"):
                self.logger.debug(f"User {user_id} clicked back to menu from scenarios page")
                StoryOSLogger.log_user_action(user_id, "navigate_back_to_menu", {
                    "from_page": "scenarios"
                })
                navigate_to_page(Pages.MAIN_MENU)
                return
            
            # Load scenarios from database
            scenarios = self.db.get_all_scenarios()
            
            if not scenarios:
                self.logger.info(f"No scenarios available for user: {user_id}")
                st.info("No scenarios available.")
                if is_admin():
                    st.info("As an admin, you can add scenarios by uploading markdown files.")
                    
                StoryOSLogger.log_user_action(user_id, "view_empty_scenarios_list", {})
            else:
                self.logger.info(f"Displaying {len(scenarios)} scenarios for user: {user_id}")
                self.show_scenarios_list(scenarios, user_id)
                
                StoryOSLogger.log_user_action(user_id, "view_scenarios_list", {
                    "scenarios_count": len(scenarios)
                })
            
            # Admin features
            if is_admin():
                self.show_admin_upload_section(user_id)
            
            duration = time.time() - start_time
            StoryOSLogger.log_performance("show_scenarios_page", "show_page", duration, {
                "user_id": user_id,
                "scenarios_count": len(scenarios) if scenarios else 0,
                "is_admin": is_admin()
            })
            
        except Exception as e:
            duration = time.time() - start_time
            user_id = user.get('user_id', 'unknown') if user else 'unknown'
            self.logger.error(f"Error displaying scenarios page for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("show_scenarios_page", e, {
                "operation": "show_page",
                "user_id": user_id,
                "duration": duration
            })
            st.error("Error loading scenarios page")


def show_scenarios_page(user: Dict[str, Any]) -> None:
    """Main function to display scenarios page (maintains compatibility with app.py routing)"""
    interface = ScenariosInterface()
    interface.show_page(user)
