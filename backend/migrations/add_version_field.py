"""
Migration script to add version field to existing game sessions.
Run this once to add the version field to all existing documents.

Usage:
    python -m backend.migrations.add_version_field
"""

from backend.utils.db_utils import get_db_manager
from backend.logging_config import get_logger

logger = get_logger("migration.add_version_field")


def add_version_to_game_sessions():
    """Add version field to all game sessions that don't have it."""
    db_manager = get_db_manager()

    if not db_manager.is_connected():
        logger.error("Database not connected")
        return False

    try:
        # Find all documents without a version field
        result = db_manager.db.active_game_sessions.update_many(
            {"version": {"$exists": False}},
            {"$set": {"version": 1}}
        )

        logger.info(f"Migration complete: Updated {result.modified_count} documents with version field")
        print(f"✓ Migration complete: Updated {result.modified_count} documents")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"✗ Migration failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("Running migration: add_version_field")
    success = add_version_to_game_sessions()
    exit(0 if success else 1)
