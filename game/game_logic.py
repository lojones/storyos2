"""
Game logic module for StoryOS v2
Handles core game session lifecycle and player interaction flows.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Generator, Optional

import streamlit as st

from logging_config import StoryOSLogger, get_logger
from models.game_session_model import GameSession, GameSessionUtils
from models.summary_update import SummaryUpdate
from models.message import Message
from utils.db_utils import get_db_manager
from utils.game_session_manager import generate_session_id, validate_services_and_session
from utils.llm_utils import get_llm_utility
from utils.prompts import PromptCreator
from utils.story_generator import (
    generate_streaming_response,
    prepare_game_context,
    update_world_state,
)
from utils.visualization_utils import VisualizationManager


def create_new_game(user_id: str, scenario_id: str) -> Optional[str]:
    """Create a new game session backed by MongoDB."""
    logger = get_logger("game_logic")
    start_time = time.time()

    logger.info("Creating new game for user: %s, scenario: %s", user_id, scenario_id)

    try:
        db = get_db_manager()

        if not db.is_connected():
            logger.error("Database connection failed during game creation")
            st.error("Database connection failed")
            return None

        scenario = db.get_scenario(scenario_id)
        if not scenario:
            logger.error("Scenario not found: %s", scenario_id)
            st.error("Scenario not found")
            return None

        scenario_name = scenario.get("name", "Unknown")
        logger.info("Using scenario '%s' for new game", scenario_name)

        session_game_id = generate_session_id()
        session_data = GameSessionUtils.create_new_session(user_id, scenario_id, session_game_id)
        description = scenario.get("description", "No description available.")
        initial_location = scenario.get("initial_location", "an unknown location")
        session_data.update_world_state(
            f"Game initialized. {description} The adventure begins in {initial_location}."
        )
        session_data.update_last_scene(f"The adventure begins in {initial_location}.")

        logger.debug("Generated session data with game_session_id: %s", session_game_id)

        session_id = db.create_game_session(session_data)
        if not session_id:
            logger.error("Failed to create game session for user: %s", user_id)
            st.error("Failed to create game session")
            return None

        logger.info("Game session created in database: %s", session_id)

        if not db.create_chat_document(session_id):
            logger.error("Failed to create chat document for session: %s", session_id)
            st.error("Failed to create chat document")
            return None

        logger.debug("Chat document created for session: %s", session_id)

        duration = time.time() - start_time
        StoryOSLogger.log_user_action(
            user_id,
            "game_created",
            {
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "session_id": session_id,
            },
        )
        StoryOSLogger.log_performance(
            "game_logic",
            "create_new_game",
            duration,
            {
                "user_id": user_id,
                "scenario_id": scenario_id,
                "session_id": session_id,
            },
        )

        return session_id

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error creating new game for user %s: %s", user_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_logic",
            exc,
            {
                "operation": "create_new_game",
                "user_id": user_id,
                "scenario_id": scenario_id,
                "duration": duration,
            },
        )
        return None


def generate_initial_story_message(session_id: str) -> Generator[str, None, None]:
    """Stream the opening narrative for a newly created session."""
    logger = get_logger("game_logic")
    start_time = time.time()

    logger.info("Generating initial story message for session: %s", session_id)

    try:
        db = get_db_manager()
        llm = get_llm_utility()

        if not db.is_connected():
            logger.error("Database connection failed during initial story generation")
            yield "Error: Database service unavailable"
            return

        if not llm.is_available():
            logger.error("LLM service unavailable during initial story generation")
            yield "Error: AI service unavailable"
            return

        session = db.get_game_session(session_id)
        if not session:
            logger.error("Game session not found: %s", session_id)
            yield "Error: Game session not found"
            return

        scenario_id = session.scenario_id
        if not scenario_id:
            logger.error("No scenario_id found in session")
            yield "Error: No scenario configured"
            return

        user_id = session.user_id
        messages = PromptCreator.generate_initial_story_prompt(session_id)

        complete_response = ""
        chunk_count = 0
        try:
            logger.info("Starting initial story generation for session: %s", session_id)
            scenario = db.get_scenario(scenario_id)
            scenario_player_name = scenario.get("player_name") if isinstance(scenario, dict) else None
            character_candidates = list(session.character_summaries.keys()) if session.character_summaries else []
            if scenario_player_name:
                character_candidates.append(str(scenario_player_name))
            character_candidates.append("player")
            character_candidates = list(dict.fromkeys(character_candidates))
            stream_metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "scenario_id": scenario_id,
                "context": "initial_story",
            }
            for chunk in llm.call_creative_llm_stream(
                messages,
                prompt_type="initial-story",
                involved_characters=character_candidates,
                metadata=stream_metadata,
            ):
                if not chunk.startswith("Error:"):
                    complete_response += chunk
                    chunk_count += 1
                    yield chunk
                else:
                    logger.error("Error in initial story generation: %s", chunk)
                    yield chunk
                    complete_response = chunk
                    break
        except Exception as exc:  # noqa: BLE001
            error_msg = f"Error generating initial story: {exc}"
            logger.error("Exception during initial story generation: %s", exc)
            StoryOSLogger.log_error_with_context(
                "game_logic",
                exc,
                {
                    "operation": "generate_initial_story_message_llm",
                    "session_id": session_id,
                    "user_id": user_id,
                },
            )
            yield error_msg
            complete_response = error_msg

        if complete_response and not complete_response.startswith("Error:"):
            response_length = len(complete_response)
            logger.info(
                "Initial story message generated (length: %s, chunks: %s)",
                response_length,
                chunk_count,
            )

            prompt_payload = [message.to_llm_format() for message in messages]
            if not db.add_chat_message(
                session_id,
                "StoryOS",
                complete_response,
                prompt_payload,
                role="assistant",
            ):
                logger.error("Failed to save initial story message to chat history")
            else:
                logger.debug("Initial story message saved to chat history")

            StoryOSLogger.log_user_action(
                user_id,
                "initial_story_generated",
                {
                    "session_id": session_id,
                    "scenario_id": scenario_id,
                    "response_length": response_length,
                    "chunk_count": chunk_count,
                },
            )
        else:
            logger.warning("No valid initial story message to save for session: %s", session_id)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_logic",
            "generate_initial_story_message",
            duration,
            {
                "session_id": session_id,
                "user_id": user_id,
                "response_length": len(complete_response),
                "chunks_generated": chunk_count,
            },
        )

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Unexpected error generating initial story for session %s: %s", session_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_logic",
            exc,
            {
                "operation": "generate_initial_story_message",
                "session_id": session_id,
                "duration": duration,
            },
        )
        yield f"Unexpected error: {exc}"


def load_game_session(session_id: str) -> Dict[str, Any]:
    """Load a game session and its chat history."""
    logger = get_logger("game_logic")
    start_time = time.time()

    logger.info("Loading game session: %s", session_id)

    try:
        db = get_db_manager()

        if not db.is_connected():
            logger.error("Database connection failed during session load")
            raise RuntimeError("Database service unavailable")

        session = db.get_game_session(session_id)
        if not session:
            logger.warning("Game session not found: %s", session_id)
            raise RuntimeError("Game session not found")

        user_id = session.user_id
        scenario_id = session.scenario_id
        logger.debug("Session found - user: %s, scenario: %s", user_id, scenario_id)

        messages = db.get_chat_messages(session_id)
        logger.debug("Retrieved %s messages for session: %s", len(messages), session_id)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_logic",
            "load_game_session",
            duration,
            {
                "session_id": session_id,
                "user_id": user_id,
                "message_count": len(messages),
            },
        )

        return {"session": session, "messages": messages}

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error loading game session %s: %s", session_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_logic",
            exc,
            {
                "operation": "load_game_session",
                "session_id": session_id,
                "duration": duration,
            },
        )
        raise


def update_game_session(
    session: GameSession,
    player_input: str,
    complete_response: str,
) -> GameSession:
    """Update game session with new player input and AI response."""
    logger = get_logger("game_logic")
    start_time = time.time()

    session_id = session.game_session_id
    user_id = session.user_id
    input_length = len(player_input)
    response_length = len(complete_response)

    logger.info("Updating game session: %s for user: %s", session_id, user_id)
    logger.debug("Input length: %s, Response length: %s", input_length, response_length)
    logger.debug(
        "Player input preview: %s",
        f"{player_input[:100]}{'...' if input_length > 100 else ''}",
    )

    try:
        logger.debug("Constructing game session summary update prompt")
        updated_summary_prompt = PromptCreator.construct_game_session_prompt(
            session,
            player_input,
            complete_response,
        )
        prompt_length = sum(len(message.content or "") for message in updated_summary_prompt)
        logger.debug("Generated summary prompt with length: %s", prompt_length)

        llm = get_llm_utility()
        if not llm.is_available():
            logger.error("LLM service unavailable during session update")
            raise RuntimeError("LLM service unavailable")

        schema = SummaryUpdate.model_json_schema()
        schema_size = len(json.dumps(schema))
        logger.debug("Using SummaryUpdate JSON schema (size: %s bytes)", schema_size)

        logger.info("Calling LLM to generate summary update")
        summary_update_json_str = llm.call_fast_llm_nostream(
            updated_summary_prompt,
            schema,
            prompt_type="update-summary",
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "player_input_length": input_length,
                "response_length_estimate": response_length,
            },
        )

        if not summary_update_json_str:
            logger.error("Empty response from LLM during summary update")
            raise RuntimeError("Empty LLM response")

        json_response_length = len(summary_update_json_str)
        logger.debug(
            "Received JSON response from LLM (length: %s)",
            json_response_length,
        )
        logger.debug(
            "JSON response preview: %s",
            f"{summary_update_json_str[:200]}{'...' if json_response_length > 200 else ''}",
        )

        try:
            logger.debug("Parsing JSON response from LLM")
            summary_update_json = json.loads(summary_update_json_str)
            logger.debug(
                "Successfully parsed JSON with keys: %s",
                list(summary_update_json.keys())
                if isinstance(summary_update_json, dict)
                else "non-dict response",
            )
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON response from LLM: %s", exc)
            logger.error("Invalid JSON content: %s", summary_update_json_str[:500])
            raise RuntimeError(f"Invalid JSON response from LLM: {exc}")

        try:
            logger.debug("Creating SummaryUpdate object from parsed JSON")
            summary_update = SummaryUpdate.from_dict(summary_update_json)

            event_summary = summary_update.summarized_event.event_summary
            involved_characters = summary_update.summarized_event.involved_characters
            character_count = len(
                summary_update.summarized_event.updated_character_summaries
            )

            logger.debug(
                "Summary update created - Event: %s",
                f"{event_summary[:100]}{'...' if len(event_summary) > 100 else ''}",
            )
            logger.debug("Involved characters: %s", involved_characters)
            logger.debug(
                "Updated character summaries count: %s",
                character_count,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to create SummaryUpdate object: %s", exc)
            logger.error(
                "JSON data: %s",
                json.dumps(summary_update_json, indent=2)
                if isinstance(summary_update_json, dict)
                else str(summary_update_json),
            )
            raise RuntimeError(f"Failed to create SummaryUpdate object: {exc}")

        logger.debug("Applying summary update to game session")
        session.update(summary_update)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_logic",
            "update_game_session",
            duration,
            {
                "session_id": session_id,
                "user_id": user_id,
                "input_length": input_length,
                "response_length": response_length,
                "json_response_length": json_response_length,
                "character_updates": character_count,
            },
        )

        StoryOSLogger.log_user_action(
            user_id,
            "session_updated",
            {
                "session_id": session_id,
                "event_summary": event_summary[:100],
                "characters_involved": len(involved_characters),
                "duration": duration,
            },
        )

        return session

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error updating game session %s: %s", session_id, exc)
        StoryOSLogger.log_error_with_context(
            "game_logic",
            exc,
            {
                "operation": "update_game_session",
                "session_id": session_id,
                "user_id": user_id,
                "input_length": input_length,
                "response_length": response_length,
                "duration": duration,
            },
        )
        logger.warning(
            "Returning original session due to update failure: %s", session_id
        )
        return session


def process_player_input(
    session_id: str,
    player_input: str,
    *,
    db_manager: Optional[Any] = None,
    llm_utility: Optional[Any] = None,
) -> Generator[str, None, None]:
    """Process player input and stream the StoryOS response."""
    logger = get_logger("game_logic")
    start_time = time.time()

    input_length = len(player_input)
    logger.info(
        "Processing player input for session: %s (length: %s)",
        session_id,
        input_length,
    )
    logger.debug(
        "Player input preview: %s",
        f"{player_input[:100]}{'...' if input_length > 100 else ''}",
    )

    try:
        db, llm, session = validate_services_and_session(
            session_id,
            logger,
            db_manager=db_manager,
            llm_utility=llm_utility,
        )
    except (RuntimeError, ValueError) as exc:
        yield str(exc)
        return

    try:
        user_id = session.user_id

        messages, error_msg = prepare_game_context(session_id, session, db, logger)
        if error_msg:
            yield error_msg
            return

        user_message = Message.create_chat_message(
            sender="player",
            content=player_input,
            role="user",
        )
        messages.append(user_message)
        logger.debug("Adding player message to chat history")
        prompt_payload = [message.to_llm_format() for message in messages]
        if not db.add_chat_message(
            session_id,
            "player",
            player_input,
            prompt_payload,
            role="user",
        ):
            logger.warning("Failed to save player message to chat history")

        StoryOSLogger.log_user_action(
            user_id,
            "player_input",
            {
                "session_id": session_id,
                "input_length": input_length,
            },
        )

        complete_response = ""
        chunk_count = 0

        try:
            character_candidates = list(session.character_summaries.keys()) if session.character_summaries else []
            character_candidates.append("player")
            character_candidates = list(dict.fromkeys(character_candidates))
            stream_metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "scenario_id": session.scenario_id,
                "context": "story_turn",
            }
            for chunk in generate_streaming_response(
                messages,
                llm,
                session_id,
                logger,
                prompt_type="story-turn",
                involved_characters=character_candidates,
                metadata=stream_metadata,
            ):
                if not chunk.startswith("Error:"):
                    complete_response += chunk
                    chunk_count += 1
                    yield chunk
                else:
                    logger.error("Error in LLM response: %s", chunk)
                    yield chunk
                    complete_response = chunk
                    break
        except Exception as exc:  # noqa: BLE001
            error_msg = f"Error generating response: {exc}"
            logger.error("Exception during response generation: %s", exc)
            StoryOSLogger.log_error_with_context(
                "game_logic",
                exc,
                {
                    "operation": "process_player_input_llm",
                    "session_id": session_id,
                    "user_id": user_id,
                },
            )
            yield error_msg
            complete_response = error_msg

        if complete_response and not complete_response.startswith("Error:"):
            response_length = len(complete_response)
            logger.info(
                "StoryOS response generated (length: %s, chunks: %s)",
                response_length,
                chunk_count,
            )

            if not db.add_chat_message(
                session_id,
                "StoryOS",
                complete_response,
                prompt_payload,
                role="assistant",
            ):
                logger.error("Failed to save StoryOS response to chat history")

            update_world_state(
                session,
                player_input,
                complete_response,
                db,
                logger,
                session_updater=update_game_session,
            )
            VisualizationManager.generate_prompts_for_session(session_id)
        else:
            logger.warning("No valid response to save for session: %s", session_id)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "game_logic",
            "process_player_input",
            duration,
            {
                "session_id": session_id,
                "user_id": user_id,
                "input_length": input_length,
                "response_length": len(complete_response),
                "chunks_generated": chunk_count,
            },
        )

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error(
            "Unexpected error processing player input for session %s: %s",
            session_id,
            exc,
        )
        StoryOSLogger.log_error_with_context(
            "game_logic",
            exc,
            {
                "operation": "process_player_input",
                "session_id": session_id,
                "input_length": input_length,
                "duration": duration,
            },
        )
        yield f"Unexpected error: {exc}"
