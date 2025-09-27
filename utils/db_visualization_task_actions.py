"""
Database visualization task operations for StoryOS v2
Handles CRUD operations for Kling visualization tasks in MongoDB
"""

import time
import streamlit as st
from datetime import datetime
from typing import Dict, Optional, Any
from pymongo.database import Database
from logging_config import get_logger, StoryOSLogger


class DbVisualizationTaskActions:
    """Handles visualization task database operations"""

    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.logger = get_logger("database.visualization_task_actions")
        self.logger.debug("DbVisualizationTaskActions initialized")

    def create_visualization_task(self, task_data: Dict[str, Any]) -> bool:
        """Create or upsert a Kling visualization task record."""
        start_time = time.time()
        task_id = task_data.get("task_id")
        if not task_id:
            self.logger.error("Visualization task creation failed - task_id missing")
            return False

        try:
            if self.db is None:
                self.logger.error("Cannot create visualization task - database not connected")
                return False

            now_iso = datetime.utcnow().isoformat()
            task_record = {
                key: value
                for key, value in task_data.items()
                if key != "created_at"
            }
            task_record.setdefault("updated_at", now_iso)

            update_doc = {
                "$set": task_record,
                "$setOnInsert": {"created_at": task_data.get("created_at", now_iso)},
            }

            result = self.db.visualizations.update_one(
                {"task_id": task_id},
                update_doc,
                upsert=True,
            )

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "create_visualization_task", duration, {
                "task_id": task_id,
                "matched": result.matched_count,
                "modified": result.modified_count,
            })

            return True

        except Exception as e:
            self.logger.error(f"Error creating visualization task {task_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "create_visualization_task",
                "task_id": task_id,
            })
            return False

    def update_visualization_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing visualization task with new data."""
        start_time = time.time()
        if not task_id:
            self.logger.error("Visualization task update failed - task_id missing")
            return False

        try:
            if self.db is None:
                self.logger.error("Cannot update visualization task - database not connected")
                return False

            now_iso = datetime.utcnow().isoformat()
            update_doc = {
                "$set": {
                    **updates,
                    "updated_at": now_iso,
                }
            }

            result = self.db.visualizations.update_one(
                {"task_id": task_id},
                update_doc,
                upsert=False,
            )

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "update_visualization_task", duration, {
                "task_id": task_id,
                "matched": result.matched_count,
                "modified": result.modified_count,
            })

            if result.matched_count == 0:
                self.logger.warning(f"Visualization task update found no matching task for task_id {task_id}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error updating visualization task {task_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "update_visualization_task",
                "task_id": task_id,
            })
            return False

    def get_visualization_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a visualization task by its task_id."""
        start_time = time.time()
        if not task_id:
            self.logger.error("Visualization task retrieval failed - task_id missing")
            return None

        try:
            if self.db is None:
                self.logger.error("Cannot retrieve visualization task - database not connected")
                return None

            task_doc = self.db.visualizations.find_one({"task_id": task_id})

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "get_visualization_task", duration, {
                "task_id": task_id,
                "found": bool(task_doc),
            })

            return task_doc

        except Exception as e:
            self.logger.error(f"Error retrieving visualization task {task_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "get_visualization_task",
                "task_id": task_id,
            })
            return None
