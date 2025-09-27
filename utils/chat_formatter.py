"""Chat formatting utilities for StoryOS."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from logging_config import StoryOSLogger, get_logger
from models.message import Message
from utils.st_session_management import SessionManager
from utils.visualization_utils import VisualizationManager


def format_chat_message(
    message: Message,
    message_id: Optional[str] = None,
    *,
    chat_idx: Optional[int] = None,
    session_id: Optional[str] = None,
) -> None:
    """Render a chat message within Streamlit."""
    logger = get_logger("chat_formatter")

    try:
        if not isinstance(message, Message):  # Safeguard for legacy calls
            if isinstance(message, dict):
                message = Message.from_dict(message)
            else:
                serialized = getattr(message, "to_dict", lambda: message)()
                message = Message.from_dict(serialized)

        sender = message.sender or "unknown"
        content = message.content or ""

        stable_message_id = (
            message_id
            or message.message_id
            or message.timestamp
            or hashlib.sha1(f"{sender}:{content}".encode("utf-8", "ignore")).hexdigest()
        )
        message_id = str(stable_message_id)

        if not content:
            logger.warning("Empty content in message from %s", sender)
            return
        logger.debug("Formatting message from %s (length: %s)", sender, len(content))

        if sender == "player":
            with st.chat_message("user"):
                st.write(content)
            return

        assistant_container = st.chat_message("assistant")
        with assistant_container:
            st.write(content)


    except Exception as exc:  # noqa: BLE001
        logger.error("Error formatting chat message: %s", exc)
        StoryOSLogger.log_error_with_context(
            "chat_formatter",
            exc,
            {
                "operation": "format_chat_message",
                "message_sender": message.sender,
            },
        )
        st.error("Error displaying message")


def format_timestamp(timestamp_str: str) -> str:
    """Format an ISO timestamp string for display."""
    logger = get_logger("chat_formatter")

    if not timestamp_str:
        logger.debug("Empty timestamp provided")
        return "Unknown"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        logger.debug("Formatted timestamp: %s -> %s", timestamp_str, formatted)
        return formatted
    except (ValueError, AttributeError) as exc:
        logger.warning("Failed to parse timestamp %s: %s", timestamp_str, exc)
        return timestamp_str
