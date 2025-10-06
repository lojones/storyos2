"""
Database Scenario Actions for StoryOS v2
Handles scenario-related MongoDB operations
"""

import time
from datetime import datetime
from typing import List, Optional

from pymongo.database import Database

from backend.logging_config import get_logger, StoryOSLogger
from backend.models.scenario import Scenario


class DbScenarioActions:
    """Handles all scenario-related database operations."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
        self.logger = get_logger("db_scenario_actions")
    
    def create_scenario(self, scenario: Scenario) -> bool:
        """Create a new scenario"""
        start_time = time.time()
        scenario_id = scenario.scenario_id
        self.logger.info(f"Creating scenario: {scenario_id}")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot create scenario")
                return False

            # Convert to dict for MongoDB insertion
            scenario_dict = scenario.model_dump()

            result = self.db.scenarios.insert_one(scenario_dict)
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
            return False
    
    def get_all_scenarios(self, user_id: Optional[str] = None) -> List[Scenario]:
        """Get all scenarios visible to the user (public scenarios or user's own scenarios)

        If user_id is None, returns all scenarios (for admin users)
        """
        start_time = time.time()
        self.logger.debug(f"Retrieving scenarios for user: {user_id}")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get scenarios")
                return []

            # Build query based on user_id
            if user_id is None:
                # Return all scenarios (for admin users)
                query = {}
            elif user_id:
                # Return public scenarios or user's own scenarios
                query = {
                    "$or": [
                        {"visibility": "public"},
                        {"author": user_id}
                    ]
                }
            else:
                # Fallback: return only public scenarios
                query = {"visibility": "public"}

            scenarios_data = list(self.db.scenarios.find(query))
            duration = time.time() - start_time

            # Convert to Scenario models
            scenarios = []
            for scenario_dict in scenarios_data:
                try:
                    # Remove MongoDB's _id field if present
                    scenario_dict.pop('_id', None)
                    scenarios.append(Scenario(**scenario_dict))
                except Exception as e:
                    scenario_id = scenario_dict.get('scenario_id', 'unknown')
                    self.logger.warning(f"Failed to instantiate scenario {scenario_id}: {str(e)} - skipping")
                    continue

            self.logger.debug(f"Retrieved {len(scenarios)} scenarios for user {user_id}")
            StoryOSLogger.log_performance("database", "get_all_scenarios", duration, {
                "count": len(scenarios),
                "user_id": user_id
            })

            return scenarios

        except Exception as e:
            self.logger.error(f"Error getting scenarios: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_all_scenarios", "user_id": user_id})
            return []
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario by scenario_id"""
        start_time = time.time()
        self.logger.debug(f"Retrieving scenario: {scenario_id}")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot get scenario")
                return None

            scenario_dict = self.db.scenarios.find_one({'scenario_id': scenario_id})
            duration = time.time() - start_time

            if scenario_dict:
                # Remove MongoDB's _id field if present
                scenario_dict.pop('_id', None)
                scenario = Scenario(**scenario_dict)

                self.logger.debug(f"Scenario found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": True
                })
                return scenario
            else:
                self.logger.debug(f"Scenario not found: {scenario_id}")
                StoryOSLogger.log_performance("database", "get_scenario", duration, {
                    "scenario_id": scenario_id,
                    "found": False
                })
                return None

        except Exception as e:
            self.logger.error(f"Error getting scenario {scenario_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_scenario", "scenario_id": scenario_id})
            return None
    
    def update_scenario(self, scenario: Scenario) -> bool:
        """Update a scenario"""
        start_time = time.time()
        scenario_id = scenario.scenario_id
        self.logger.info(f"Updating scenario: {scenario_id}")

        try:
            if self.db is None:
                self.logger.error("Database not connected - cannot update scenario")
                return False

            # Convert to dict for MongoDB update
            scenario_dict = scenario.model_dump()

            result = self.db.scenarios.update_one(
                {'scenario_id': scenario_id},
                {'$set': scenario_dict}
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
            return False
