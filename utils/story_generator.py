"""Story generation helpers for StoryOS."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Generator, List, Optional

import streamlit as st

from logging_config import get_logger
from models.message import Message
from utils.prompts import PromptCreator


def prepare_game_context(
    session_id: str,
    session: Any,
    db: Any,
    logger,
) -> tuple[List[Message], str]:
    """Build the message stack required for the LLM call."""
    system_prompt_doc = db.get_active_system_prompt()
    if not system_prompt_doc:
        logger.error("No active system prompt found")
        return [], "System configuration error"

    system_prompt = system_prompt_doc["content"]
    logger.debug(
        "Using system prompt: %s (length: %s)",
        system_prompt_doc.get("name", "unnamed"),
        len(system_prompt),
    )

    recent_messages = db.get_chat_messages(session_id, limit=10)
    logger.debug("Retrieved %s recent messages for context", len(recent_messages))

    messages = PromptCreator.construct_game_prompt(system_prompt, session, recent_messages)
    logger.debug("Prompt constructed with %s total messages", len(messages))

    return messages, ""


def generate_streaming_response(
    messages: List[Message],
    llm: Any,
    session_id: str,
    logger,
    *,
    prompt_type: str = "creative",
    involved_characters: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Generator[str, None, None]:
    """Stream tokens from the LLM response."""
    try:
        logger.info("Starting StoryOS response generation for session: %s", session_id)
        for chunk in llm.call_creative_llm_stream(
            messages,
            prompt_type=prompt_type,
            involved_characters=involved_characters,
            metadata=metadata,
        ):
            yield chunk
    except Exception as exc:  # noqa: BLE001
        error_msg = f"Error generating response: {exc}"
        logger.error("Exception during response generation: %s", exc)
        yield error_msg


def update_world_state(
    session: Any,
    player_input: str,
    complete_response: str,
    db: Any,
    logger,
    *,
    session_updater: Callable[[Any, str, str], Any],
) -> None:
    """Persist world-state changes and manage session flags."""
    try:
        st.session_state["storyos_updating_world_state"] = True
        st.session_state["storyos_world_update_start_time"] = time.time()
        logger.debug("Set world state update flag")
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Could not set world state flag (likely not in Streamlit context): %s",
            exc,
        )

    logger.debug("Updating game summary with new interaction")
    session_updater(session, player_input, complete_response)

    try:
        st.session_state.pop("storyos_updating_world_state", None)
        st.session_state.pop("storyos_world_update_start_time", None)
        logger.debug("Cleared world state update flag")
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Could not clear world state flag (likely not in Streamlit context): %s",
            exc,
        )

    if not db.update_game_session(session):
        logger.warning("Failed to save updated game summary")
