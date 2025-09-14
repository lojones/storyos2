"""
StoryOS v2 - System Prompt Management Page
Provides admin interface for managing system prompts used by the AI dungeon master
"""

import streamlit as st
import time
from typing import Dict, Any, Optional

# Import our custom modules
from logging_config import StoryOSLogger, get_logger
from st_session_management import SessionManager, navigate_to_page, Pages
from auth import is_admin
from db_utils import get_db_manager


class SystemPromptInterface:
    """Interface for managing system prompts (admin only)"""
    
    def __init__(self):
        """Initialize the system prompt interface"""
        self.logger = get_logger("system_prompt_page")
        self.db = get_db_manager()
        self.logger.debug("SystemPromptInterface initialized")

    def check_admin_access(self, user_id: str) -> bool:
        """Check if user has admin access and log the access attempt"""
        try:
            if not is_admin():
                self.logger.warning(f"Non-admin user {user_id} attempted to access system prompt page")
                StoryOSLogger.log_user_action(user_id, "system_prompt_access_denied", {
                    "reason": "insufficient_privileges"
                })
                st.error("Access denied. Admin privileges required.")
                return False
            
            self.logger.info(f"Admin {user_id} accessing system prompt management")
            StoryOSLogger.log_user_action(user_id, "system_prompt_page_access", {})
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking admin access for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("system_prompt_page", e, {
                "operation": "check_admin_access",
                "user_id": user_id
            })
            st.error("Error verifying admin access")
            return False

    def display_current_prompt(self, active_prompt: Dict[str, Any], user_id: str) -> str:
        """Display current active system prompt and return its content"""
        try:
            self.logger.debug(f"Displaying current system prompt for admin {user_id}")
            
            st.subheader("Current Active System Prompt")
            
            # Display prompt metadata
            st.write(f"**Name:** {active_prompt.get('name', 'Unknown')}")
            st.write(f"**Version:** {active_prompt.get('version', 'Unknown')}")
            st.write(f"**Last Updated:** {active_prompt.get('updated_at', 'Unknown')}")
            
            # Show content in expandable section
            current_content = active_prompt.get('content', '')
            
            with st.expander("Current System Prompt Content", expanded=True):
                st.text_area(
                    "System Prompt", 
                    value=current_content, 
                    height=400, 
                    disabled=True,
                    key="current_prompt_display"
                )
            
            StoryOSLogger.log_user_action(user_id, "view_current_system_prompt", {
                "prompt_name": active_prompt.get('name'),
                "prompt_version": active_prompt.get('version'),
                "content_length": len(current_content)
            })
            
            return current_content
            
        except Exception as e:
            self.logger.error(f"Error displaying current system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("system_prompt_page", e, {
                "operation": "display_current_prompt",
                "user_id": user_id
            })
            st.error("Error displaying current system prompt")
            return ""

    def handle_prompt_update(self, active_prompt: Dict[str, Any], user_id: str) -> None:
        """Handle system prompt update form"""
        start_time = time.time()
        
        try:
            current_content = active_prompt.get('content', '')
            
            st.subheader("Edit System Prompt")
            
            with st.form("edit_system_prompt"):
                new_content = st.text_area(
                    "New System Prompt Content", 
                    value=current_content, 
                    height=400,
                    key="edit_prompt_content"
                )
                submitted = st.form_submit_button("💾 Update System Prompt")
                
                if submitted:
                    self.logger.info(f"Admin {user_id} submitted system prompt update")
                    
                    if new_content and new_content.strip():
                        if new_content.strip() == current_content.strip():
                            self.logger.debug(f"No changes detected in system prompt update by {user_id}")
                            st.info("No changes detected in the system prompt.")
                            return
                        
                        # Attempt to update the system prompt
                        if self.db.update_system_prompt(active_prompt['_id'], new_content.strip()):
                            duration = time.time() - start_time
                            self.logger.info(f"System prompt updated successfully by {user_id} (took {duration:.2f}s)")
                            
                            StoryOSLogger.log_user_action(user_id, "system_prompt_updated", {
                                "prompt_id": str(active_prompt['_id']),
                                "old_content_length": len(current_content),
                                "new_content_length": len(new_content.strip()),
                                "duration": duration
                            })
                            
                            st.success("System prompt updated successfully!")
                            st.rerun()
                        else:
                            duration = time.time() - start_time
                            self.logger.error(f"Failed to update system prompt for {user_id} (took {duration:.2f}s)")
                            
                            StoryOSLogger.log_user_action(user_id, "system_prompt_update_failed", {
                                "prompt_id": str(active_prompt['_id']),
                                "duration": duration
                            })
                            
                            st.error("Failed to update system prompt")
                    else:
                        self.logger.warning(f"Admin {user_id} attempted to save empty system prompt")
                        StoryOSLogger.log_user_action(user_id, "system_prompt_update_validation_failed", {
                            "reason": "empty_content"
                        })
                        st.error("System prompt cannot be empty")
                        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error handling system prompt update: {str(e)}")
            StoryOSLogger.log_error_with_context("system_prompt_page", e, {
                "operation": "handle_prompt_update",
                "user_id": user_id,
                "duration": duration
            })
            st.error("Error processing system prompt update")

    def handle_prompt_creation(self, user_id: str) -> None:
        """Handle initial system prompt creation form"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Displaying system prompt creation form for admin {user_id}")
            
            st.warning("No active system prompt found!")
            st.subheader("Create Initial System Prompt")
            
            with st.form("create_system_prompt"):
                name = st.text_input("Prompt Name", value="Default StoryOS System Prompt")
                version = st.text_input("Version", value="1.0.0")
                content = st.text_area("System Prompt Content", height=400, key="create_prompt_content")
                submitted = st.form_submit_button("💾 Create System Prompt")
                
                if submitted:
                    self.logger.info(f"Admin {user_id} submitted new system prompt creation")
                    
                    if name.strip() and version.strip() and content.strip():
                        prompt_data = {
                            'name': name.strip(),
                            'version': version.strip(),
                            'content': content.strip(),
                            'active': True
                        }
                        
                        if self.db.create_system_prompt(prompt_data):
                            duration = time.time() - start_time
                            self.logger.info(f"System prompt created successfully by {user_id} (took {duration:.2f}s)")
                            
                            StoryOSLogger.log_user_action(user_id, "system_prompt_created", {
                                "prompt_name": name.strip(),
                                "prompt_version": version.strip(),
                                "content_length": len(content.strip()),
                                "duration": duration
                            })
                            
                            st.success("System prompt created successfully!")
                            st.rerun()
                        else:
                            duration = time.time() - start_time
                            self.logger.error(f"Failed to create system prompt for {user_id} (took {duration:.2f}s)")
                            
                            StoryOSLogger.log_user_action(user_id, "system_prompt_creation_failed", {
                                "prompt_name": name.strip(),
                                "duration": duration
                            })
                            
                            st.error("Failed to create system prompt")
                    else:
                        self.logger.warning(f"Admin {user_id} attempted to create system prompt with missing fields")
                        StoryOSLogger.log_user_action(user_id, "system_prompt_creation_validation_failed", {
                            "reason": "missing_required_fields",
                            "name_provided": bool(name.strip()),
                            "version_provided": bool(version.strip()),
                            "content_provided": bool(content.strip())
                        })
                        st.error("All fields are required")
                        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error handling system prompt creation: {str(e)}")
            StoryOSLogger.log_error_with_context("system_prompt_page", e, {
                "operation": "handle_prompt_creation",
                "user_id": user_id,
                "duration": duration
            })
            st.error("Error processing system prompt creation")

    def show_page(self, user: Dict[str, Any]) -> None:
        """Main method to display the system prompt management page"""
        start_time = time.time()
        
        try:
            user_id = user.get('user_id', 'unknown')
            self.logger.info(f"Displaying system prompt page for user: {user_id}")
            
            # Check admin access first
            if not self.check_admin_access(user_id):
                return
            
            st.title("⚙️ System Prompt Management")
            
            # Back button
            if st.button("← Back to Menu"):
                self.logger.debug(f"Admin {user_id} clicked back to menu from system prompt page")
                StoryOSLogger.log_user_action(user_id, "navigate_back_to_menu", {
                    "from_page": "system_prompt"
                })
                navigate_to_page(Pages.MAIN_MENU)
                return
            
            # Get current active system prompt
            active_prompt = self.db.get_active_system_prompt()
            
            if active_prompt:
                self.logger.debug(f"Found active system prompt for admin {user_id}")
                
                # Display current prompt
                current_content = self.display_current_prompt(active_prompt, user_id)
                
                # Handle prompt update
                self.handle_prompt_update(active_prompt, user_id)
                
            else:
                self.logger.warning(f"No active system prompt found when admin {user_id} accessed page")
                
                # Handle prompt creation
                self.handle_prompt_creation(user_id)
            
            duration = time.time() - start_time
            StoryOSLogger.log_performance("system_prompt_page", "show_page", duration, {
                "user_id": user_id,
                "has_active_prompt": bool(active_prompt),
                "is_admin": True
            })
            
        except Exception as e:
            duration = time.time() - start_time
            user_id = user.get('user_id', 'unknown') if user else 'unknown'
            self.logger.error(f"Error displaying system prompt page for user {user_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("system_prompt_page", e, {
                "operation": "show_page",
                "user_id": user_id,
                "duration": duration
            })
            st.error("Error loading system prompt management page")


def show_system_prompt_page(user: Dict[str, Any]) -> None:
    """Main function to display system prompt page (maintains compatibility with app.py routing)"""
    interface = SystemPromptInterface()
    interface.show_page(user)