"""
Database System Prompt Actions for StoryOS v2
Handles system prompt-related MongoDB operations
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import streamlit as st
from pymongo.database import Database

from logging_config import get_logger, StoryOSLogger


class DbSystemPromptActions:
    """Handles all system prompt-related database operations."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
        self.logger = get_logger("db_system_prompt_actions")
    
    def create_system_prompt(self, prompt_data: Dict[str, Any]) -> bool:
        """Create a new system prompt"""
        start_time = time.time()
        prompt_name = prompt_data.get('name', 'unnamed')
        self.logger.info(f"Creating system prompt: {prompt_name}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot create system prompt")
                return False
                
            # Ensure timestamps are set
            now = datetime.utcnow().isoformat()
            if 'created_at' not in prompt_data:
                prompt_data['created_at'] = now
            if 'updated_at' not in prompt_data:
                prompt_data['updated_at'] = now
                
            result = self.db.system_prompts.insert_one(prompt_data)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"System prompt created successfully: {prompt_name}")
                StoryOSLogger.log_performance("database", "create_system_prompt", duration, {
                    "prompt_name": prompt_name,
                    "success": True
                })
            else:
                self.logger.error(f"Failed to create system prompt: {prompt_name}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating system prompt {prompt_name}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_system_prompt", "prompt_name": prompt_name})
            st.error(f"Error creating system prompt: {str(e)}")
            return False
    
    def get_active_system_prompt(self) -> Optional[Dict[str, Any]]:
        """Get the active system prompt"""
        start_time = time.time()
        self.logger.debug("Retrieving active system prompt")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get active system prompt")
                return None

            prompt = self.db.system_prompts.find_one({'active': True, 'name': 'Default StoryOS System Prompt'})
            duration = time.time() - start_time

            if prompt:
                self.logger.debug(f"Active system prompt found: {prompt.get('name', 'unnamed')}")
                StoryOSLogger.log_performance("database", "get_active_system_prompt", duration, {
                    "found": True,
                    "prompt_name": prompt.get('name', 'unnamed')
                })
            else:
                self.logger.debug("No active system prompt found")
                StoryOSLogger.log_performance("database", "get_active_system_prompt", duration, {
                    "found": False
                })

            return prompt

        except Exception as e:
            self.logger.error(f"Error getting active system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_active_system_prompt"})
            st.error(f"Error getting active system prompt: {str(e)}")
            return None

    def get_active_visualization_system_prompt(self) -> Optional[str]:
        """Get the active visualization system prompt content."""
        start_time = time.time()
        self.logger.debug("Retrieving active visualization system prompt")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get visualization system prompt")
                raise LookupError("Database not connected")

            prompt_doc = self.db.system_prompts.find_one({
                'active': True,
                'name': 'Default StoryOS Visualization System Prompt'
            })
            duration = time.time() - start_time

            if prompt_doc and 'content' in prompt_doc:
                self.logger.debug("Active visualization system prompt found")
                StoryOSLogger.log_performance("database", "get_active_visualization_system_prompt", duration, {
                    "found": True
                })
                return prompt_doc['content']

            self.logger.warning("No active visualization system prompt found")
            StoryOSLogger.log_performance("database", "get_active_visualization_system_prompt", duration, {
                "found": False
            })
            raise LookupError("Active visualization system prompt not found")

        except Exception as e:
            self.logger.error(f"Error getting visualization system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "get_active_visualization_system_prompt"
            })
            raise

    def update_visualization_system_prompt(self, content: str) -> bool:
        """Update the visualization system prompt content"""
        start_time = time.time()
        self.logger.debug("Updating visualization system prompt")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot update visualization system prompt")
                return False

            # Update the visualization system prompt by name
            result = self.db.system_prompts.update_one(
                {
                    'active': True,
                    'name': 'Default StoryOS Visualization System Prompt'
                },
                {
                    '$set': {
                        'content': content,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )

            duration = time.time() - start_time

            if result.modified_count > 0:
                self.logger.info("Visualization system prompt updated successfully")
                StoryOSLogger.log_performance("database", "update_visualization_system_prompt", duration, {
                    "modified_count": result.modified_count,
                    "content_length": len(content)
                })
                return True
            else:
                self.logger.warning("No visualization system prompt was updated (may not exist)")
                StoryOSLogger.log_performance("database", "update_visualization_system_prompt", duration, {
                    "modified_count": 0,
                    "content_length": len(content)
                })
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error updating visualization system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "update_visualization_system_prompt",
                "content_length": len(content) if content else 0,
                "duration": duration
            })
            return False

    def update_system_prompt(self, prompt_id: str, content: str) -> bool:
        """Update system prompt content"""
        start_time = time.time()
        self.logger.info(f"Updating system prompt: {prompt_id}")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot update system prompt")
                return False
                
            # First deactivate all prompts
            self.logger.debug("Deactivating all system prompts")
            deactivate_result = self.db.system_prompts.update_many({}, {'$set': {'active': False}})
            self.logger.debug(f"Deactivated {deactivate_result.modified_count} prompts")
            
            # Then update and activate the specified prompt
            result = self.db.system_prompts.update_one(
                {'_id': prompt_id},
                {
                    '$set': {
                        'content': content,
                        'active': True,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"System prompt updated successfully: {prompt_id}")
                StoryOSLogger.log_performance("database", "update_system_prompt", duration, {
                    "prompt_id": str(prompt_id),
                    "success": True
                })
            else:
                self.logger.warning(f"No changes made to system prompt: {prompt_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating system prompt {prompt_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "update_system_prompt", "prompt_id": str(prompt_id)})
            st.error(f"Error updating system prompt: {str(e)}")
            return False
