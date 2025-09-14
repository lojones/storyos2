"""
StoryOS v2 - Data Validation Utilities
Provides functions for validating initial application data and database state
"""

import time
from typing import Optional, Dict, Any, Tuple

# Import our custom modules
from logging_config import StoryOSLogger, get_logger
from utils.db_utils import get_db_manager


class DataValidator:
    """Class for validating application data and database state"""
    
    def __init__(self):
        """Initialize the data validator"""
        self.logger = get_logger("validation")
        self.logger.debug("DataValidator initialized")

    def check_database_connection(self) -> bool:
        """Check if database is connected and accessible"""
        try:
            db = get_db_manager()
            if not db.is_connected():
                self.logger.warning("Database connection check failed")
                return False
            
            self.logger.debug("Database connection verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking database connection: {str(e)}")
            StoryOSLogger.log_error_with_context("validation", e, {
                "operation": "check_database_connection"
            })
            return False

    def validate_system_prompt(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate that an active system prompt exists"""
        try:
            db = get_db_manager()
            active_prompt = db.get_active_system_prompt()
            
            if active_prompt:
                self.logger.debug(f"Active system prompt found: {active_prompt.get('name', 'unknown')}")
                return True, active_prompt
            else:
                self.logger.warning("No active system prompt found")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Error validating system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("validation", e, {
                "operation": "validate_system_prompt"
            })
            return False, None

    def validate_scenarios(self) -> Tuple[bool, int]:
        """Validate that scenarios exist in the database"""
        try:
            db = get_db_manager()
            scenarios = db.get_all_scenarios()
            
            scenario_count = len(scenarios) if scenarios else 0
            
            if scenario_count > 0:
                self.logger.debug(f"Found {scenario_count} scenarios in database")
                return True, scenario_count
            else:
                self.logger.warning("No scenarios found in database")
                return False, 0
                
        except Exception as e:
            self.logger.error(f"Error validating scenarios: {str(e)}")
            StoryOSLogger.log_error_with_context("validation", e, {
                "operation": "validate_scenarios"
            })
            return False, 0

    def validate_initial_data(self) -> Dict[str, Any]:
        """
        Validate that required initial data exists after database initialization
        
        Returns:
            Dict containing validation results and metrics
        """
        start_time = time.time()
        
        self.logger.debug("Running initial data validation check (post-initialization)")
        
        try:
            # Check database connection first
            if not self.check_database_connection():
                duration = time.time() - start_time
                result = {
                    "success": False,
                    "database_connected": False,
                    "system_prompt_exists": False,
                    "scenarios_count": 0,
                    "duration": duration,
                    "errors": ["Database not connected"]
                }
                
                StoryOSLogger.log_performance("validation", "validate_initial_data", duration, result)
                return result
            
            # Validate system prompt
            system_prompt_valid, active_prompt = self.validate_system_prompt()
            
            # Validate scenarios
            scenarios_valid, scenario_count = self.validate_scenarios()
            
            duration = time.time() - start_time
            
            # Prepare result summary
            result = {
                "success": system_prompt_valid and scenarios_valid,
                "database_connected": True,
                "system_prompt_exists": system_prompt_valid,
                "scenarios_count": scenario_count,
                "duration": duration,
                "errors": []
            }
            
            if not system_prompt_valid:
                result["errors"].append("No active system prompt found")
            
            if not scenarios_valid:
                result["errors"].append("No scenarios found in database")
            
            # Log results
            if result["success"]:
                self.logger.info(f"Initial data verification complete - System prompt: ✅, Scenarios: {scenario_count}")
            else:
                self.logger.warning(f"Initial data verification - System prompt: {'✅' if system_prompt_valid else '❌'}, Scenarios: {scenario_count}")
            
            StoryOSLogger.log_performance("validation", "validate_initial_data", duration, {
                "scenarios_exist": scenario_count,
                "system_prompt_exists": system_prompt_valid,
                "database_connected": True,
                "validation_success": result["success"]
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error during initial data validation: {str(e)}")
            
            result = {
                "success": False,
                "database_connected": False,
                "system_prompt_exists": False,
                "scenarios_count": 0,
                "duration": duration,
                "errors": [f"Validation error: {str(e)}"]
            }
            
            StoryOSLogger.log_error_with_context("validation", e, {
                "operation": "validate_initial_data",
                "duration": duration
            })
            
            return result

    def validate_user_permissions(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user permissions and access rights"""
        start_time = time.time()
        
        try:
            user_id = user.get('user_id', 'unknown')
            role = user.get('role', 'user')
            
            self.logger.debug(f"Validating permissions for user: {user_id} (role: {role})")
            
            result = {
                "user_id": user_id,
                "role": role,
                "is_admin": role == 'admin',
                "can_edit_scenarios": role == 'admin',
                "can_edit_system_prompt": role == 'admin',
                "can_create_games": True,
                "duration": time.time() - start_time
            }
            
            StoryOSLogger.log_user_action(user_id, "permissions_validated", {
                "role": role,
                "admin_access": result["is_admin"]
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error validating user permissions: {str(e)}")
            StoryOSLogger.log_error_with_context("validation", e, {
                "operation": "validate_user_permissions",
                "user_id": user.get('user_id', 'unknown') if user else 'unknown',
                "duration": duration
            })
            
            return {
                "user_id": user.get('user_id', 'unknown') if user else 'unknown',
                "role": 'unknown',
                "is_admin": False,
                "can_edit_scenarios": False,
                "can_edit_system_prompt": False,
                "can_create_games": False,
                "duration": duration,
                "error": str(e)
            }


# Global instance for easy access
_validator = DataValidator()


def validate_initial_data() -> Dict[str, Any]:
    """
    Validate that required initial data exists after database initialization
    
    This function maintains compatibility with the original app.py function signature
    while providing enhanced functionality through the DataValidator class.
    
    Returns:
        Dict containing validation results and metrics
    """
    return _validator.validate_initial_data()


def validate_user_permissions(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user permissions and access rights
    
    Args:
        user: User dictionary containing user_id and role information
        
    Returns:
        Dict containing user permission information
    """
    return _validator.validate_user_permissions(user)


def check_database_health() -> bool:
    """
    Quick health check for database connectivity
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    return _validator.check_database_connection()