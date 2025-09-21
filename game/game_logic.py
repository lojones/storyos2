"""
Game logic module for StoryOS v2
Handles game session management, prompt construction, and chat handling
"""

from typing import Dict, List, Any, Optional, Generator, Tuple
import streamlit as st
from datetime import datetime
import json
import time
import random
from models.game_session_model import GameSessionUtils, GameSession
from models.summary_update import SummaryUpdate
from utils.db_utils import get_db_manager
from utils.llm_utils import get_llm_utility
from utils.prompts import PromptCreator
from logging_config import get_logger, StoryOSLogger

def create_new_game(user_id: str, scenario_id: str) -> Optional[str]:
    """
    Create a new game session
    
    Args:
        user_id: The user starting the game
        scenario_id: The scenario to use for the game
        
    Returns:
        Game session ID if successful, None otherwise
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    logger.info(f"Creating new game for user: {user_id}, scenario: {scenario_id}")
    
    try:
        db = get_db_manager()
        
        if not db.is_connected():
            logger.error("Database connection failed during game creation")
            st.error("Database connection failed")
            return None
        
        # Get scenario details
        scenario = db.get_scenario(scenario_id)
        if not scenario:
            logger.error(f"Scenario not found: {scenario_id}")
            st.error("Scenario not found")
            return None
        
        scenario_name = scenario.get('name', 'Unknown')
        logger.info(f"Using scenario '{scenario_name}' for new game")
        
        # Generate initial game session data
        session_game_id = generate_session_id()
        session_data = GameSessionUtils.create_new_session(user_id, scenario_id, session_game_id)
        description = scenario.get('description', 'No description available.')
        initial_location = scenario.get('initial_location', 'an unknown location')
        session_data.update_world_state(f"Game initialized. {description} The adventure begins in {initial_location}.")
        session_data.update_last_scene(f"The adventure begins in {initial_location}.")
        
        
        logger.debug(f"Generated session data with game_session_id: {session_game_id}")
        
        # Create game session in database
        session_id = db.create_game_session(session_data)
        if not session_id:
            logger.error(f"Failed to create game session for user: {user_id}")
            st.error("Failed to create game session")
            return None
        
        logger.info(f"Game session created in database: {session_id}")
        
        # Create chat document for this session
        if not db.create_chat_document(session_id):
            logger.error(f"Failed to create chat document for session: {session_id}")
            st.error("Failed to create chat document")
            return None
        
        logger.debug(f"Chat document created for session: {session_id}")
        
        # Note: Initial story message will be generated when the game page loads
        logger.debug("Game session created - initial message will be generated on first page load")
        
        duration = time.time() - start_time
        logger.info(f"New game created successfully for user: {user_id}, session: {session_id}")
        StoryOSLogger.log_user_action(user_id, "game_created", {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "session_id": session_id
        })
        StoryOSLogger.log_performance("game_logic", "create_new_game", duration, {
            "user_id": user_id,
            "scenario_id": scenario_id,
            "session_id": session_id
        })
        
        return session_id
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error creating new game for user {user_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "create_new_game",
            "user_id": user_id,
            "scenario_id": scenario_id,
            "duration": duration
        })
        return None

def generate_session_id() -> int:
    """Generate a unique session ID based on timestamp"""
    logger = get_logger("game_logic")
    session_id = int(datetime.utcnow().timestamp() * 1000) + random.randint(0, 999)
    logger.debug(f"Generated session ID: {session_id}")
    return session_id

def generate_initial_story_message(session_id: str) -> Generator[str, None, None]:
    """
    Generate the initial story message for a new game session
    
    Args:
        session_id: The game session ID
        
    Yields:
        Response chunks for the initial story message
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    logger.info(f"Generating initial story message for session: {session_id}")
    
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
        
        # Get game session
        session = db.get_game_session(session_id)
        if not session:
            logger.error(f"Game session not found: {session_id}")
            yield "Error: Game session not found"
            return
        
        # Get scenario details
        scenario_id = session.scenario_id
        if not scenario_id:
            logger.error("No scenario_id found in session")
            yield "Error: No scenario configured"
            return
                    
        user_id = session.user_id
        
        messages = PromptCreator.generate_initial_story_prompt(session_id)

        # Generate streaming initial message
        complete_response = ""
        chunk_count = 0
        try:
            logger.info(f"Starting initial story generation for session: {session_id}")
            scenario = db.get_scenario(scenario_id)
            scenario_player_name = scenario.get('player_name') if isinstance(scenario, dict) else None
            character_candidates = list(session.character_summaries.keys()) if session.character_summaries else []
            if scenario_player_name:
                character_candidates.append(str(scenario_player_name))
            character_candidates.append('player')
            character_candidates = list(dict.fromkeys(character_candidates))
            stream_metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "scenario_id": scenario_id,
                "context": "initial_story"
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
                    logger.error(f"Error in initial story generation: {chunk}")
                    yield chunk
                    complete_response = chunk
                    break
                    
        except Exception as e:
            error_msg = f"Error generating initial story: {str(e)}"
            logger.error(f"Exception during initial story generation: {str(e)}")
            StoryOSLogger.log_error_with_context("game_logic", e, {
                "operation": "generate_initial_story_message_llm",
                "session_id": session_id,
                "user_id": user_id
            })
            yield error_msg
            complete_response = error_msg
        
        # Save initial message to chat
        if complete_response and not complete_response.startswith("Error:"):
            response_length = len(complete_response)
            logger.info(f"Initial story message generated (length: {response_length}, chunks: {chunk_count})")
            
            # Save response to chat
            if not db.add_chat_message(session_id, 'StoryOS', complete_response, messages):
                logger.error("Failed to save initial story message to chat history")
            else:
                logger.debug("Initial story message saved to chat history")
            
            StoryOSLogger.log_user_action(user_id, "initial_story_generated", {
                "session_id": session_id,
                "scenario_id": scenario_id,
                "response_length": response_length,
                "chunk_count": chunk_count
            })
        else:
            logger.warning(f"No valid initial story message to save for session: {session_id}")
        
        duration = time.time() - start_time
        logger.info(f"Initial story message generation completed for session: {session_id}")
        StoryOSLogger.log_performance("game_logic", "generate_initial_story_message", duration, {
            "session_id": session_id,
            "user_id": user_id,
            "response_length": len(complete_response),
            "chunks_generated": chunk_count
        })
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Unexpected error generating initial story for session {session_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "generate_initial_story_message",
            "session_id": session_id,
            "duration": duration
        })
        yield f"Unexpected error: {str(e)}"

def load_game_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a game session with all its data
    
    Args:
        session_id: The game session ID
        
    Returns:
        Dictionary containing session data and chat history, or None if not found
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    logger.info(f"Loading game session: {session_id}")
    
    try:
        db = get_db_manager()
        
        if not db.is_connected():
            logger.error("Database connection failed during session load")
            return None
        
        # Get session data
        session = db.get_game_session(session_id)
        if not session:
            logger.warning(f"Game session not found: {session_id}")
            return None
        
        user_id = session.user_id
        scenario_id = session.scenario_id
        logger.debug(f"Session found - user: {user_id}, scenario: {scenario_id}")
        
        # Get chat history
        messages = db.get_chat_messages(session_id)
        logger.debug(f"Retrieved {len(messages)} messages for session: {session_id}")
        
        duration = time.time() - start_time
        logger.info(f"Game session loaded successfully: {session_id}")
        StoryOSLogger.log_performance("game_logic", "load_game_session", duration, {
            "session_id": session_id,
            "user_id": user_id,
            "message_count": len(messages)
        })
        
        return {
            'session': session,
            'messages': messages
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error loading game session {session_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "load_game_session",
            "session_id": session_id,
            "duration": duration
        })
        return None

def update_game_session(session: GameSession, player_input: str, complete_response: str) -> GameSession:
    """
    Update game session with new player input and AI response
    
    Args:
        session: The current game session
        player_input: The player's input text
        complete_response: The complete AI response
        
    Returns:
        Updated GameSession object
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    session_id = session.game_session_id
    user_id = session.user_id
    input_length = len(player_input)
    response_length = len(complete_response)
    
    logger.info(f"Updating game session: {session_id} for user: {user_id}")
    logger.debug(f"Input length: {input_length}, Response length: {response_length}")
    logger.debug(f"Player input preview: {player_input[:100]}{'...' if input_length > 100 else ''}")
    
    try:
        # Construct summary update prompt
        logger.debug("Constructing game session summary update prompt")
        updated_summary_prompt = PromptCreator.construct_game_session_prompt(session, player_input, complete_response)
        prompt_length = len(str(updated_summary_prompt))
        logger.debug(f"Generated summary prompt with length: {prompt_length}")
        
        # Get LLM utility
        llm = get_llm_utility()
        if not llm.is_available():
            logger.error("LLM service unavailable during session update")
            raise Exception("LLM service unavailable")
        
        # Get JSON schema for validation
        schema = SummaryUpdate.model_json_schema()
        schema_size = len(json.dumps(schema))
        logger.debug(f"Using SummaryUpdate JSON schema (size: {schema_size} bytes)")
        
        # Call LLM to generate summary update
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
            raise Exception("Empty LLM response")
        
        json_response_length = len(summary_update_json_str)
        logger.debug(f"Received JSON response from LLM (length: {json_response_length})")
        logger.debug(f"JSON response preview: {summary_update_json_str[:200]}{'...' if json_response_length > 200 else ''}")
        
        # Parse JSON response
        try:
            logger.debug("Parsing JSON response from LLM")
            summary_update_json = json.loads(summary_update_json_str)
            logger.debug(f"Successfully parsed JSON with keys: {list(summary_update_json.keys()) if isinstance(summary_update_json, dict) else 'non-dict response'}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from LLM: {str(e)}")
            logger.error(f"Invalid JSON content: {summary_update_json_str[:500]}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        
        # Create SummaryUpdate object
        try:
            logger.debug("Creating SummaryUpdate object from parsed JSON")
            summary_update = SummaryUpdate.from_dict(summary_update_json)
            
            # Log summary update details
            event_summary = summary_update.summarized_event.event_summary
            involved_characters = summary_update.summarized_event.involved_characters
            character_count = len(summary_update.summarized_event.updated_character_summaries)
            
            logger.debug(f"Summary update created - Event: {event_summary[:100]}{'...' if len(event_summary) > 100 else ''}")
            logger.debug(f"Involved characters: {involved_characters}")
            logger.debug(f"Updated character summaries count: {character_count}")
            
        except Exception as e:
            logger.error(f"Failed to create SummaryUpdate object: {str(e)}")
            logger.error(f"JSON data: {json.dumps(summary_update_json, indent=2) if isinstance(summary_update_json, dict) else str(summary_update_json)}")
            raise Exception(f"Failed to create SummaryUpdate object: {str(e)}")
        
        # Update session with summary
        logger.debug("Applying summary update to game session")
        session.update(summary_update)
        
        duration = time.time() - start_time
        logger.info(f"Successfully updated game session: {session_id}")
        
        # Log performance and user action
        StoryOSLogger.log_performance("game_logic", "update_game_session", duration, {
            "session_id": session_id,
            "user_id": user_id,
            "input_length": input_length,
            "response_length": response_length,
            "json_response_length": json_response_length,
            "character_updates": character_count
        })
        
        StoryOSLogger.log_user_action(user_id, "session_updated", {
            "session_id": session_id,
            "event_summary": event_summary[:100],
            "characters_involved": len(involved_characters),
            "duration": duration
        })
        
        return session
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error updating game session {session_id}: {str(e)}")
        
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "update_game_session",
            "session_id": session_id,
            "user_id": user_id,
            "input_length": input_length,
            "response_length": response_length,
            "duration": duration
        })
        
        # Return the original session on error
        logger.warning(f"Returning original session due to update failure: {session_id}")
        return session
    

def _validate_services_and_session(session_id: str, logger) -> Tuple[Any, Any, Any, str]:
    """
    Validate database/LLM services and retrieve game session
    
    Args:
        session_id: The game session ID
        logger: Logger instance
        
    Returns:
        Tuple of (db_manager, llm_utility, game_session, error_message)
        If error_message is not empty, other values may be None
    """
    db = get_db_manager()
    llm = get_llm_utility()
    
    if not db.is_connected():
        logger.error("Database connection failed during player input processing")
        return None, None, None, "Database service unavailable"
        
    if not llm.is_available():
        logger.error("LLM service unavailable during player input processing")
        return None, None, None, "AI service unavailable"
    
    # Get game session
    session = db.get_game_session(session_id)
    if not session:
        logger.error(f"Game session not found: {session_id}")
        return db, llm, None, "Game session not found"
    
    logger.debug(f"Processing input for user: {session.user_id}")
    return db, llm, session, ""


def _prepare_game_context(session_id: str, session: Any, db: Any, logger) -> Tuple[List[Dict], str]:
    """
    Prepare game context by retrieving system prompt and constructing messages
    
    Args:
        session_id: The game session ID
        session: Game session object
        db: Database manager
        logger: Logger instance
        
    Returns:
        Tuple of (messages_list, error_message)
        If error_message is not empty, messages_list will be empty
    """
    # Get system prompt
    system_prompt_doc = db.get_active_system_prompt()
    if not system_prompt_doc:
        logger.error("No active system prompt found")
        return [], "System configuration error"
    
    system_prompt = system_prompt_doc['content']
    logger.debug(f"Using system prompt: {system_prompt_doc.get('name', 'unnamed')} (length: {len(system_prompt)})")
    
    # Get recent messages
    recent_messages = db.get_chat_messages(session_id, limit=10)
    logger.debug(f"Retrieved {len(recent_messages)} recent messages for context")

    # Construct prompt
    messages = PromptCreator.construct_game_prompt(system_prompt, session, recent_messages)
    logger.debug(f"Prompt constructed with {len(messages)} total messages")
    
    return messages, ""


def _generate_streaming_response(
    messages: list,
    llm: Any,
    session_id: str,
    logger,
    *,
    prompt_type: str = "creative",
    involved_characters: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Generator[str, None, None]:
    """
    Generate streaming LLM response
    
    Args:
        messages: Prepared message list for LLM
        llm: LLM utility instance  
        session_id: Game session ID
        logger: Logger instance
        
    Yields:
        Response chunks from LLM
    """
    try:
        logger.info(f"Starting StoryOS response generation for session: {session_id}")
        for chunk in llm.call_creative_llm_stream(
            messages,
            prompt_type=prompt_type,
            involved_characters=involved_characters,
            metadata=metadata,
        ):
            yield chunk
                
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        logger.error(f"Exception during response generation: {str(e)}")
        yield error_msg


def _update_world_state(session: Any, player_input: str, complete_response: str, db: Any, logger) -> None:
    """
    Update world state with Streamlit flag management
    
    Args:
        session: Game session object
        player_input: Player's input text
        complete_response: Complete AI response
        db: Database manager
        logger: Logger instance
    """
    # Set flag to indicate we're updating world state
    try:
        import streamlit as st
        st.session_state["storyos_updating_world_state"] = True
        st.session_state["storyos_world_update_start_time"] = time.time()
        logger.debug("Set world state update flag")
    except Exception as e:
        logger.debug(f"Could not set world state flag (likely not in Streamlit context): {str(e)}")
    
    # Update game summary
    logger.debug("Updating game summary with new interaction")            
    update_game_session(session, player_input, complete_response)
    
    # Clear flag after world state update is complete
    try:
        import streamlit as st
        st.session_state.pop("storyos_updating_world_state", None)
        st.session_state.pop("storyos_world_update_start_time", None)
        logger.debug("Cleared world state update flag")
    except Exception as e:
        logger.debug(f"Could not clear world state flag (likely not in Streamlit context): {str(e)}")
    
    if not db.update_game_session(session):
        logger.warning("Failed to save updated game summary")


def process_player_input(session_id: str, player_input: str) -> Generator[str, None, None]:
    """
    Process player input and generate StoryOS response
    
    Args:
        session_id: The game session ID
        player_input: The player's input text
        
    Yields:
        Response chunks from StoryOS
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    input_length = len(player_input)
    logger.info(f"Processing player input for session: {session_id} (length: {input_length})")
    logger.debug(f"Player input preview: {player_input[:100]}{'...' if input_length > 100 else ''}")
    
    try:
        # Validate services and get session
        db, llm, session, error_msg = _validate_services_and_session(session_id, logger)
        if error_msg:
            yield error_msg
            return
        
        user_id = session.user_id
        
        # Prepare game context
        messages, error_msg = _prepare_game_context(session_id, session, db, logger)
        if error_msg:
            yield error_msg
            return
        
        # Add player input to messages and save to chat
        messages.append({"role": "user", "content": player_input})
        logger.debug("Adding player message to chat history")
        if not db.add_chat_message(session_id, 'player', player_input, messages):
            logger.warning("Failed to save player message to chat history")
        
        # Log user action
        StoryOSLogger.log_user_action(user_id, "player_input", {
            "session_id": session_id,
            "input_length": input_length
        })        
        
        # Generate streaming response
        complete_response = ""
        chunk_count = 0
        
        try:
            character_candidates = list(session.character_summaries.keys()) if session.character_summaries else []
            character_candidates.append('player')
            character_candidates = list(dict.fromkeys(character_candidates))
            stream_metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "scenario_id": session.scenario_id,
                "context": "story_turn"
            }
            # Stream response chunks and build complete response
            for chunk in _generate_streaming_response(
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
                    logger.error(f"Error in LLM response: {chunk}")
                    yield chunk
                    complete_response = chunk
                    break
                    
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(f"Exception during response generation: {str(e)}")
            StoryOSLogger.log_error_with_context("game_logic", e, {
                "operation": "process_player_input_llm", 
                "session_id": session_id,
                "user_id": user_id
            })
            yield error_msg
            complete_response = error_msg
        
        # Process successful response
        if complete_response and not complete_response.startswith("Error:"):
            response_length = len(complete_response)
            logger.info(f"StoryOS response generated (length: {response_length}, chunks: {chunk_count})")
            
            # Save response to chat
            if not db.add_chat_message(session_id, 'StoryOS', complete_response, messages):
                logger.error("Failed to save StoryOS response to chat history")
            
            # Update world state with flag management
            _update_world_state(session, player_input, complete_response, db, logger)
        else:
            logger.warning(f"No valid response to save for session: {session_id}")
        
        # Log completion
        duration = time.time() - start_time
        logger.info(f"Player input processing completed for session: {session_id}")
        StoryOSLogger.log_performance("game_logic", "process_player_input", duration, {
            "session_id": session_id,
            "user_id": user_id,
            "input_length": input_length,
            "response_length": len(complete_response),
            "chunks_generated": chunk_count
        })
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Unexpected error processing player input for session {session_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "process_player_input",
            "session_id": session_id,
            "input_length": input_length,
            "duration": duration
        })
        yield f"Unexpected error: {str(e)}"

# def update_game_session(session_id: str, player_input: str, full_response: str) -> Dict:


def get_user_game_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all game sessions for a user with scenario information
    
    Args:
        user_id: The user ID
        
    Returns:
        List of game sessions with scenario details
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    logger.debug(f"Retrieving game sessions for user: {user_id}")
    
    try:
        db = get_db_manager()
        
        if not db.is_connected():
            logger.error("Database connection failed when retrieving user game sessions")
            return []
        
        sessions = db.get_user_game_sessions(user_id)
        logger.info(f"Retrieved {len(sessions)} game sessions for user: {user_id}")
        
        # Enrich sessions with scenario information
        enriched_count = 0
        for session in sessions:
            scenario_id = session.get('scenario_id')
            if scenario_id:
                scenario = db.get_scenario(scenario_id)
                if scenario:
                    session['scenario_name'] = scenario.get('name', 'Unknown Scenario')
                    session['scenario_description'] = scenario.get('description', 'No description')
                    enriched_count += 1
                    logger.debug(f"Enriched session {session.get('_id')} with scenario: {scenario.get('name')}")
                else:
                    logger.warning(f"Scenario not found for ID: {scenario_id} in session {session.get('_id')}")
        
        logger.debug(f"Enriched {enriched_count} sessions with scenario information")
        
        duration = time.time() - start_time
        StoryOSLogger.log_performance("game_logic", "get_user_game_sessions", duration, {
            "user_id": user_id,
            "sessions_count": len(sessions),
            "enriched_count": enriched_count
        })
        
        return sessions
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error retrieving game sessions for user {user_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "get_user_game_sessions",
            "user_id": user_id,
            "duration": duration
        })
        return []

def format_chat_message(message: Dict[str, str]) -> None:
    """
    Display a chat message in Streamlit with appropriate styling
    
    Args:
        message: Message dictionary with 'sender' and 'content'
    """
    logger = get_logger("game_logic")
    
    try:
        sender = message.get('sender', 'unknown')
        content = message.get('content', '')
        
        if not content:
            logger.warning(f"Empty content in message from {sender}")
            return
        
        logger.debug(f"Formatting message from {sender} (length: {len(content)})")
        
        if sender == 'player':
            with st.chat_message("user"):
                st.write(content)
        else:  # StoryOS
            with st.chat_message("assistant"):
                st.write(content)
                
    except Exception as e:
        logger.error(f"Error formatting chat message: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "format_chat_message",
            "message_sender": message.get('sender', 'unknown')
        })
        # Fallback display
        st.error("Error displaying message")

def display_game_session_info(session: GameSession) -> None:
    """
    Display game session information in the sidebar
    
    Args:
        session: Game session model object
    """
    logger = get_logger("game_logic")
    
    try:
        session_id = session.id or 'unknown'
        logger.debug(f"Displaying game session info for session: {session_id}")
        
        with st.sidebar:
            st.subheader("Current Game Session")
            
            # Session details - Note: scenario_name is not in the GameSession model
            # We would need to fetch scenario name separately if needed
            # if hasattr(session, 'scenario_name') and session.scenario_name:
            #     st.write(f"**Scenario:** {session.scenario_name}")
            #     logger.debug(f"Displayed scenario: {session.scenario_name}")
            
            st.write(f"**Started:** {format_timestamp(session.created_at.isoformat())}")
            st.write(f"**Last Updated:** {format_timestamp(session.last_updated.isoformat())}")
            
            # World state
            if session.world_state:
                with st.expander("World State"):
                    st.write(session.world_state)
                logger.debug(f"Displayed world state (length: {len(session.world_state)})")
            
            # Current scenario summary - using last_scene from the model
            if session.last_scene:
                with st.expander("Current Situation"):
                    st.write(session.last_scene)
                logger.debug(f"Displayed current scenario (length: {len(session.last_scene)})")
            
            # Character summaries
            if session.character_summaries:
                with st.expander("Characters"):
                    for char_name, char_data in session.character_summaries.items():
                        st.write(f"**{char_name}:** {char_data.character_story}")
                logger.debug(f"Displayed {len(session.character_summaries)} character summaries")
        
    except Exception as e:
        logger.error(f"Error displaying game session info: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "display_game_session_info",
            "session_id": getattr(session, 'id', 'unknown')
        })
        with st.sidebar:
            st.error("Error displaying session information")

def format_timestamp(timestamp_str: str) -> str:
    """
    Format ISO timestamp string for display
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    logger = get_logger("game_logic")
    
    if not timestamp_str:
        logger.debug("Empty timestamp provided")
        return "Unknown"
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        logger.debug(f"Formatted timestamp: {timestamp_str} -> {formatted}")
        return formatted
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp: {timestamp_str}, error: {str(e)}")
        return timestamp_str

def export_game_session(session_id: str) -> Optional[str]:
    """
    Export a game session to JSON format
    
    Args:
        session_id: The game session ID
        
    Returns:
        JSON string of the game session, or None if error
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    logger.info(f"Exporting game session: {session_id}")
    
    try:
        game_data = load_game_session(session_id)
        if not game_data:
            logger.warning(f"No game data found for session: {session_id}")
            return None
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in game_data['session']:
            game_data['session']['_id'] = str(game_data['session']['_id'])
        
        json_output = json.dumps(game_data, indent=2, default=str)
        export_size = len(json_output)
        
        duration = time.time() - start_time
        logger.info(f"Game session exported successfully: {session_id} (size: {export_size} bytes)")
        
        StoryOSLogger.log_performance("game_logic", "export_game_session", duration, {
            "session_id": session_id,
            "export_size": export_size
        })
        
        return json_output
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error exporting game session {session_id}: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "export_game_session",
            "session_id": session_id,
            "duration": duration
        })
        st.error(f"Error exporting game session: {str(e)}")
        return None

def validate_scenario_data(scenario_data: Dict[str, Any]) -> List[str]:
    """
    Validate scenario data against the required schema
    
    Args:
        scenario_data: Scenario dictionary to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    scenario_id = scenario_data.get('scenario_id', 'unknown')
    logger.debug(f"Validating scenario data: {scenario_id}")
    
    try:
        errors = []
        
        required_fields = [
            'scenario_id', 'author', 'description', 'dungeon_master_behaviour',
            'initial_location', 'name', 'player_name', 'role', 'setting', 'version'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in scenario_data:
                errors.append(f"Missing required field: {field}")
                logger.debug(f"Missing field: {field}")
            elif not scenario_data[field]:
                errors.append(f"Empty required field: {field}")
                logger.debug(f"Empty field: {field}")
        
        # Validate version format
        version = scenario_data.get('version', '')
        if version and not is_valid_semver(version):
            errors.append(f"Invalid version format: {version} (expected semantic version like 1.0.0)")
            logger.debug(f"Invalid version format: {version}")
        
        duration = time.time() - start_time
        if errors:
            logger.warning(f"Scenario validation failed for {scenario_id}: {len(errors)} errors")
        else:
            logger.info(f"Scenario validation passed for {scenario_id}")
        
        StoryOSLogger.log_performance("game_logic", "validate_scenario_data", duration, {
            "scenario_id": scenario_id,
            "validation_errors": len(errors)
        })
        
        return errors
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error validating scenario data: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "validate_scenario_data",
            "scenario_id": scenario_id,
            "duration": duration
        })
        return [f"Validation error: {str(e)}"]

def is_valid_semver(version: str) -> bool:
    """
    Check if version string is valid semantic version
    
    Args:
        version: Version string to validate
        
    Returns:
        True if valid semantic version, False otherwise
    """
    logger = get_logger("game_logic")
    
    try:
        import re
        pattern = r'^[0-9]+\.[0-9]+\.[0-9]+$'
        is_valid = bool(re.match(pattern, version))
        
        if not is_valid:
            logger.debug(f"Invalid semantic version: {version}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error validating semantic version {version}: {str(e)}")
        return False

def parse_scenario_from_markdown(markdown_content: str) -> Dict[str, Any]:
    """
    Parse scenario data from markdown file format
    
    Args:
        markdown_content: Markdown content of scenario file
        
    Returns:
        Dictionary containing scenario data
    """
    logger = get_logger("game_logic")
    start_time = time.time()
    
    content_length = len(markdown_content)
    logger.debug(f"Parsing scenario from markdown (length: {content_length} chars)")
    
    try:
        lines = markdown_content.split('\n')
        scenario_data = {}
        current_section = None
        current_content = []
        sections_processed = 0
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('<!--'):
                continue
            
            # Check for headers
            if line.startswith('# ') and 'overview' in line.lower():
                current_section = 'overview'
                current_content = []
                logger.debug("Processing overview section")
            elif line.startswith('## '):
                section_name = line[3:].lower().strip()
                if current_section and current_content:
                    # Process previous section
                    process_section(scenario_data, current_section, current_content)
                    sections_processed += 1
                
                current_section = section_name
                current_content = []
                logger.debug(f"Processing section: {section_name}")
            else:
                if current_section:
                    current_content.append(line)
        
        # Process final section
        if current_section and current_content:
            process_section(scenario_data, current_section, current_content)
            sections_processed += 1
        
        # Set default values if not found
        if 'created_at' not in scenario_data:
            scenario_data['created_at'] = datetime.utcnow().isoformat()
            logger.debug("Added default created_at timestamp")
        
        # Generate scenario_id if not present
        if 'name' in scenario_data and 'scenario_id' not in scenario_data:
            scenario_data['scenario_id'] = scenario_data['name'].lower().replace(' ', '_')
            logger.debug(f"Generated scenario_id: {scenario_data['scenario_id']}")
        
        duration = time.time() - start_time
        scenario_name = scenario_data.get('name', 'unnamed')
        logger.info(f"Successfully parsed scenario: {scenario_name} ({sections_processed} sections)")
        
        StoryOSLogger.log_performance("game_logic", "parse_scenario_from_markdown", duration, {
            "content_length": content_length,
            "sections_processed": sections_processed,
            "scenario_name": scenario_name
        })
        
        return scenario_data
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error parsing scenario markdown: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "parse_scenario_from_markdown",
            "content_length": content_length,
            "duration": duration
        })
        return {}

def process_section(scenario_data: Dict[str, Any], section: str, content: List[str]) -> None:
    """
    Process a section of the scenario markdown
    
    Args:
        scenario_data: Dictionary to update with parsed data
        section: Section name
        content: List of content lines
    """
    logger = get_logger("game_logic")
    
    try:
        content_text = '\n'.join(content).strip()
        content_length = len(content_text)
        
        logger.debug(f"Processing section '{section}' with {len(content)} lines ({content_length} chars)")
        
        if section == 'overview':
            # Parse overview bullet points
            fields_found = 0
            for line in content:
                if line.startswith('- **Name**:'):
                    scenario_data['name'] = line.split(':', 1)[1].strip()
                    fields_found += 1
                elif line.startswith('- **Author**:'):
                    scenario_data['author'] = line.split(':', 1)[1].strip()
                    fields_found += 1
                elif line.startswith('- **Version**:'):
                    scenario_data['version'] = line.split(':', 1)[1].strip()
                    fields_found += 1
            logger.debug(f"Parsed {fields_found} fields from overview section")
        
        elif section == 'description':
            scenario_data['description'] = content_text
            logger.debug(f"Set description ({content_length} chars)")
        
        elif section == 'player details':
            fields_found = 0
            for line in content:
                if line.startswith('- **Player Name**:'):
                    scenario_data['player_name'] = line.split(':', 1)[1].strip()
                    fields_found += 1
                elif line.startswith('- **Role**:'):
                    scenario_data['role'] = line.split(':', 1)[1].strip()
                    fields_found += 1
                elif line.startswith('- **Initial Location**:'):
                    scenario_data['initial_location'] = line.split(':', 1)[1].strip()
                    fields_found += 1
            logger.debug(f"Parsed {fields_found} fields from player details section")
        
        elif section == 'setting':
            scenario_data['setting'] = content_text
            logger.debug(f"Set setting ({content_length} chars)")
        
        elif section == 'dungeon master behaviour':
            scenario_data['dungeon_master_behaviour'] = content_text
            logger.debug(f"Set dungeon master behaviour ({content_length} chars)")
        
        else:
            logger.warning(f"Unknown section encountered: {section}")
            
    except Exception as e:
        logger.error(f"Error processing section '{section}': {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "process_section",
            "section": section,
            "content_lines": len(content)
        })