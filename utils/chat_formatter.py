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
    session_id: str,
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
        message_id = str(message.message_id)

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
            
            # Handle visualization for assistant messages
            if session_id and message_id:
                try:
                    # Check if this message already has visualized images
                    existing_images = VisualizationManager.get_visualized_images(session_id, message_id)
                    
                    if existing_images:
                        # Display existing images
                        logger.debug("Found %d existing visualized images for message %s", len(existing_images), message_id)
                        for prompt, image_url in existing_images.items():
                            st.image(image_url, width="stretch", caption=prompt)
                    else:
                        # Show visualize button if no existing images and message has visual prompts
                        if message.visual_prompts and len(message.visual_prompts) > 0:
                            first_prompt = message.visual_prompts[0]
                            
                            # Use session state to manage visualization state
                            visualize_key = f"visualize_{message_id}"
                            if visualize_key not in st.session_state:
                                st.session_state[visualize_key] = False
                            
                            if not st.session_state[visualize_key]:
                                if st.button("🎨 Visualize", key=f"btn_{message_id}"):
                                    st.session_state[visualize_key] = True
                                    st.rerun()
                            else:
                                # Show loading and process visualization
                                with st.spinner("Creating visualization..."):
                                    try:
                                        logger.info("Submitting visualization prompt for message %s: %s", message_id, first_prompt[:50])
                                        response = VisualizationManager.submit_prompt(first_prompt, session_id, message_id)
                                        
                                        if response and response.image_url:
                                            logger.info("Got image back: %s", response.image_url)
                                            st.image(response.image_url, width="stretch", caption=first_prompt)
                                            # Reset the state to allow re-checking for images
                                            st.session_state[visualize_key] = False
                                        else:
                                            logger.error("Invalid response from visualization submission")
                                            st.error("Failed to create visualization request")
                                            st.session_state[visualize_key] = False
                                    except Exception as viz_exc:
                                        logger.error("Error during visualization: %s", viz_exc)
                                        st.error(f"Visualization error: {str(viz_exc)}")
                                        st.session_state[visualize_key] = False
                                        
                except Exception as viz_check_exc:
                    logger.error("Error checking visualization status: %s", viz_check_exc)
                    # Don't show error to user for visualization checks, just log it


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
