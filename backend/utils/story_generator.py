"""Story generation helpers for StoryOS."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Generator, List, Optional

from backend.logging_config import get_logger
from backend.models.game_session_model import GameSession
from backend.models.message import Message
from backend.utils.db_utils import DatabaseManager
from backend.utils.llm_utils import LLMUtility
from backend.utils.prompts import PromptCreator


def prepare_game_context(
    session_id: str,
    session: GameSession,
    db: DatabaseManager,
    logger: logging.Logger,
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
    llm: LLMUtility,
    session_id: str,
    logger: logging.Logger,
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
    session: GameSession,
    player_input: str,
    complete_response: str,
    db: DatabaseManager,
    logger: logging.Logger,
    *,
    session_updater: Callable[[GameSession, str, str], GameSession],
) -> None:
    """Persist world-state changes and manage session flags."""

    logger.debug("Updating game summary with new interaction")
    session_updater(session, player_input, complete_response)

    if not db.update_game_session(session):
        logger.warning("Failed to save updated game summary")
