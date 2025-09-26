"""Game session helper utilities for StoryOS."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from logging import Logger

import streamlit as st

from logging_config import StoryOSLogger, get_logger
from models.game_session_model import GameSession
from utils.chat_formatter import format_timestamp
from utils.db_utils import DatabaseManager, get_db_manager
from utils.llm_utils import LLMUtility, get_llm_utility


def generate_session_id() -> int:
    """Generate a unique session identifier."""
    logger = get_logger("game_session_manager")
    session_id = int(datetime.utcnow().timestamp() * 1000) + random.randint(0, 999)
    logger.debug("Generated session ID: %s", session_id)
    return session_id


def validate_services_and_session(
    session_id: str,
    logger: Logger,
    *,
    db_manager: Optional[DatabaseManager] = None,
    llm_utility: Optional[LLMUtility] = None,
) -> Tuple[DatabaseManager, LLMUtility, GameSession]:
    """Validate service availability and retrieve the active session."""
    db: DatabaseManager = db_manager if db_manager is not None else get_db_manager()
    llm: LLMUtility = llm_utility if llm_utility is not None else get_llm_utility()

    if not db.is_connected():
        logger.error("Database connection failed during player input processing")
        raise RuntimeError("Database service unavailable")

    if not llm.is_available():
        logger.error("LLM service unavailable during player input processing")
        raise RuntimeError("AI service unavailable")

    session = db.get_game_session(session_id)
    if session is None:
        logger.error("Game session not found: %s", session_id)
        raise ValueError("Game session not found")

    logger.debug("Processing input for user: %s", session.user_id)
    return db, llm, session


def get_user_game_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Fetch sessions for the supplied user."""
    logger = get_logger("game_session_manager")
    start_time = time.time()

    logger.debug("Retrieving game sessions for user: %s", user_id)

    try:
        db = get_db_manager()

        if not db.is_connected():
            logger.error("Cannot get user game sessions - database not connected")
            return []

        sessions = db.get_user_game_sessions(user_id)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_session_manager",
            "get_user_game_sessions",
            duration,
            {
                "user_id": user_id,
                "sessions": len(sessions),
            },
        )

        logger.debug(
            "Retrieved %s game sessions for user %s",
            len(sessions),
            user_id,
        )
        return sessions

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error getting user game sessions for %s: %s", user_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_session_manager",
            exc,
            {
                "operation": "get_user_game_sessions",
                "user_id": user_id,
                "duration": duration,
            },
        )
        st.error(f"Error loading saved games: {exc}")
        return []


def display_game_session_info(session: GameSession) -> None:
    """Render key session information in the Streamlit sidebar."""
    logger = get_logger("game_session_manager")

    try:
        session_id = session.id or "unknown"
        logger.debug("Displaying game session info for session: %s", session_id)

        with st.sidebar:
            st.subheader("Current Game Session")
            st.write(
                f"**Started:** {format_timestamp(session.created_at.isoformat())}"
            )
            st.write(
                f"**Last Updated:** {format_timestamp(session.last_updated.isoformat())}"
            )

            if session.world_state:
                with st.expander("World State"):
                    st.write(session.world_state)
                logger.debug(
                    "Displayed world state (length: %s)",
                    len(session.world_state),
                )

            if session.last_scene:
                with st.expander("Current Situation"):
                    st.write(session.last_scene)
                logger.debug(
                    "Displayed current scenario (length: %s)",
                    len(session.last_scene),
                )

            if session.character_summaries:
                with st.expander("Characters"):
                    for char_name, char_data in session.character_summaries.items():
                        st.write(f"**{char_name}:** {char_data.character_story}")
                logger.debug(
                    "Displayed %s character summaries",
                    len(session.character_summaries),
                )

    except Exception as exc:  # noqa: BLE001
        logger.error("Error displaying game session info: %s", exc)
        StoryOSLogger.log_error_with_context(
            "game_session_manager",
            exc,
            {
                "operation": "display_game_session_info",
                "session_id": getattr(session, "id", "unknown"),
            },
        )
        with st.sidebar:
            st.error("Error displaying session information")


def export_game_session(session_id: str) -> Optional[str]:
    """Export a session to a JSON string."""
    logger = get_logger("game_session_manager")
    start_time = time.time()

    logger.info("Exporting game session: %s", session_id)

    try:
        db = get_db_manager()

        if not db.is_connected():
            logger.error("Cannot export session - database not connected")
            st.error("Database connection required for export")
            return None

        session_data = db.get_game_session(session_id)
        if not session_data:
            logger.error("Game session not found: %s", session_id)
            st.error("Game session not found")
            return None

        chat_history = db.get_chat_messages(session_id)
        export_payload = {
            "session": session_data.model_dump() if hasattr(session_data, "model_dump") else session_data,
            "chat_history": chat_history,
        }

        json_export = json.dumps(export_payload, indent=2)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_session_manager",
            "export_game_session",
            duration,
            {
                "session_id": session_id,
                "export_size": len(json_export),
            },
        )

        logger.info("Export completed for session: %s", session_id)
        return json_export

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error exporting game session %s: %s", session_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_session_manager",
            exc,
            {
                "operation": "export_game_session",
                "session_id": session_id,
                "duration": duration,
            },
        )
        st.error(f"Error exporting game session: {exc}")
        return None
