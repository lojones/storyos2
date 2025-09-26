"""Chat formatting utilities for StoryOS."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from logging_config import StoryOSLogger, get_logger
from utils.db_utils import get_db_manager
from utils.st_session_management import SessionManager
from utils.visualization_utils import VisualizationManager


def format_chat_message(
    message: Dict[str, str],
    message_id: Optional[str] = None,
    *,
    chat_idx: Optional[int] = None,
    session_id: Optional[str] = None,
) -> None:
    """Render a chat message within Streamlit."""
    logger = get_logger("chat_formatter")

    try:
        sender = message.get("sender", "unknown")
        content = message.get("content", "")

        if message_id:
            stable_message_id = message_id
        else:
            timestamp = message.get("timestamp")
            if timestamp:
                stable_message_id = str(timestamp)
            else:
                hash_input = f"{sender}:{content}".encode("utf-8", "ignore")
                stable_message_id = hashlib.sha1(hash_input).hexdigest()
        message_id = stable_message_id

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

            visualize_button_key = f"visualize_btn_{message_id}"
            images_state_key = f"storyos_visualizations_{message_id}"
            status_state_key = f"storyos_visualizations_status_{message_id}"
            prompts_cache_key = f"storyos_visual_prompts_cache_{message_id}"
            prompts_toggle_key = f"storyos_visual_prompts_visible_{message_id}"

            target_session_id = session_id or SessionManager.get_game_session_id()

            def _fetch_visual_prompts() -> List[str]:
                if not (target_session_id and chat_idx is not None):
                    return []
                try:
                    prompts_list = get_db_manager().get_visual_prompts(
                        target_session_id,
                        chat_idx,
                    )
                    return prompts_list
                except Exception as fetch_error:  # noqa: BLE001
                    logger.error(
                        "Error retrieving visual prompts for session %s message %s: %s",
                        target_session_id,
                        chat_idx,
                        fetch_error,
                    )
                    StoryOSLogger.log_error_with_context(
                        "chat_formatter",
                        fetch_error,
                        {
                            "operation": "fetch_visual_prompts",
                            "session_id": target_session_id,
                            "chat_index": chat_idx,
                        },
                    )
                    return []

            prompts_visible = bool(st.session_state.get(prompts_toggle_key, False))
            cached_prompts: Optional[List[str]] = st.session_state.get(prompts_cache_key)

            see_button_label = "Hide Prompts" if prompts_visible else "See Prompts"
            see_button_disabled = not (target_session_id and chat_idx is not None)

            if st.button(
                see_button_label,
                key=f"see_prompts_btn_{message_id}",
                use_container_width=False,
                disabled=see_button_disabled,
            ):
                if prompts_visible:
                    st.session_state[prompts_toggle_key] = False
                else:
                    prompts_list = cached_prompts
                    if prompts_list is None:
                        prompts_list = _fetch_visual_prompts()
                        st.session_state[prompts_cache_key] = prompts_list
                    st.session_state[prompts_toggle_key] = True
                prompts_visible = bool(st.session_state.get(prompts_toggle_key, False))
                cached_prompts = st.session_state.get(prompts_cache_key)

            if prompts_visible:
                prompts_to_show = st.session_state.get(prompts_cache_key)
                if prompts_to_show is None:
                    prompts_to_show = _fetch_visual_prompts()
                    st.session_state[prompts_cache_key] = prompts_to_show
                if prompts_to_show:
                    for idx, prompt_text in enumerate(prompts_to_show, start=1):
                        st.markdown(f"**Prompt {idx}:** {prompt_text}")
                else:
                    st.info("No visualization prompts available for this message yet.")

            if st.button("Visualize", key=visualize_button_key, use_container_width=False):
                st.session_state.pop(status_state_key, None)
                st.session_state.pop(images_state_key, None)

                if not target_session_id:
                    st.session_state[status_state_key] = (
                        "No active game session available for visualization."
                    )
                elif chat_idx is None:
                    st.session_state[status_state_key] = (
                        "Unable to locate this message for visualization."
                    )
                else:
                    prompts = _fetch_visual_prompts()
                    st.session_state[prompts_cache_key] = prompts

                    if not prompts:
                        st.session_state[status_state_key] = (
                            "No visualization prompts available for this message yet."
                        )
                    else:
                        generated_images: List[Dict[str, Any]] = []
                        with st.spinner("Generating visualizations..."):
                            for prompt_idx, prompt in enumerate(prompts, start=1):
                                try:
                                    viz_response = VisualizationManager.submit_prompt(prompt)
                                    image_url = viz_response.image_url
                                    if not image_url:
                                        raise ValueError("Visualization response missing image URL")

                                    generated_images.append(
                                        {
                                            "prompt": prompt,
                                            "task_id": viz_response.task_id,
                                        }
                                    )

                                except Exception as viz_error:  # noqa: BLE001
                                    logger.error(
                                        "Error generating visualization for session %s message %s prompt %s: %s",
                                        target_session_id,
                                        chat_idx,
                                        prompt_idx,
                                        viz_error,
                                    )
                                    StoryOSLogger.log_error_with_context(
                                        "chat_formatter",
                                        viz_error,
                                        {
                                            "operation": "visualize_message",
                                            "session_id": target_session_id,
                                            "chat_index": chat_idx,
                                            "prompt_index": prompt_idx,
                                        },
                                    )
                                    generated_images = []
                                    st.session_state[status_state_key] = (
                                        "Failed to generate one or more visualizations. Please try again."
                                    )
                                    break

                        if generated_images:
                            st.session_state[images_state_key] = generated_images
                            st.session_state.pop(status_state_key, None)

            status_message = st.session_state.get(status_state_key)
            if status_message:
                st.warning(status_message)

            stored_images = st.session_state.get(images_state_key, [])
            if stored_images:
                for idx, item in enumerate(stored_images, start=1):
                    caption = f"Visualization {idx}"
                    prompt_text = item.get("prompt")
                    if prompt_text:
                        caption = f"Visualization {idx}: {prompt_text}"
                    st.image(
                        item.get("content"),
                        caption=caption,
                        use_column_width=True,
                    )

    except Exception as exc:  # noqa: BLE001
        logger.error("Error formatting chat message: %s", exc)
        StoryOSLogger.log_error_with_context(
            "chat_formatter",
            exc,
            {
                "operation": "format_chat_message",
                "message_sender": message.get("sender", "unknown"),
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
