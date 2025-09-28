"""
Database Scenario Actions for StoryOS v2
Handles scenario-related MongoDB operations
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.utils.streamlit_shim import st
from pymongo.database import Database

from backend.logging_config import get_logger, StoryOSLogger


class DbScenarioActions:
    """Handles all scenario-related database operations."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
        self.logger = get_logger("db_scenario_actions")
    
    def create_scenario(self, scenario_data: Dict[str, Any]) -> bool:
        """Create a new scenario"""
        start_time = time.time()
        scenario_id = scenario_data.get('scenario_id', 'unknown')
        self.logger.info(f"Creating scenario: {scenario_id}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot create scenario")
                return False
                
            # Ensure created_at is set
            if 'created_at' not in scenario_data:
                scenario_data['created_at'] = datetime.utcnow().isoformat()
                
            result = self.db.scenarios.insert_one(scenario_data)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Scenario created successfully: {scenario_id}")
                StoryOSLogger.log_performance("database", "create_scenario", duration, {
                    "scenario_id": scenario_id,
                    "success": True
                })
            else:
                self.logger.error(f"Failed to create scenario: {scenario_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_scenario", "scenario_id": scenario_id})
            st.error(f"Error creating scenario: {str(e)}")
            return False
    
    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Get all scenarios"""
        start_time = time.time()
        self.logger.debug("Retrieving all scenarios")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get scenarios")
                return []
                
            scenarios = list(self.db.scenarios.find({}))
            duration = time.time() - start_time
            
            self.logger.debug(f"Retrieved {len(scenarios)} scenarios")
            StoryOSLogger.log_performance("database", "get_all_scenarios", duration, {"count": len(scenarios)})
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Error getting scenarios: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_all_scenarios"})
            st.error(f"Error getting scenarios: {str(e)}")
            return []
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by scenario_id"""
        start_time = time.time()
        self.logger.debug(f"Retrieving scenario: {scenario_id}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get scenario")
                return None
                
            scenario = self.db.scenarios.find_one({'scenario_id': scenario_id})
            duration = time.time() - start_time
            
            if scenario:
                self.logger.debug(f"Scenario found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": True
                })
            else:
                self.logger.debug(f"Scenario not found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": False
                })
                
            return scenario
            
        except Exception as e:
            self.logger.error(f"Error getting scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_scenario", "scenario_id": scenario_id})
            st.error(f"Error getting scenario: {str(e)}")
            return None
    
    def update_scenario(self, scenario_id: str, scenario_data: Dict[str, Any]) -> bool:
        """Update a scenario"""
        start_time = time.time()
        self.logger.info(f"Updating scenario: {scenario_id}")
        
        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot update scenario")
                return False
                
            result = self.db.scenarios.update_one(
                {'scenario_id': scenario_id},
                {'$set': scenario_data}
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Scenario updated successfully: {scenario_id}")
                StoryOSLogger.log_performance("database", "update_scenario", duration, {
                    "scenario_id": scenario_id,
                    "success": True
                })
            else:
                self.logger.warning(f"No changes made to scenario: {scenario_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "update_scenario", "scenario_id": scenario_id})
            st.error(f"Error updating scenario: {str(e)}")
            return False
