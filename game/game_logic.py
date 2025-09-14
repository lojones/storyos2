"""
Game logic module for StoryOS v2
Handles game session management, prompt construction, and chat handling
"""

from typing import Dict, List, Any, Optional, Generator
import streamlit as st
from datetime import datetime
import json
import time
import random
from utils.db_utils import get_db_manager
from utils.llm_utils import get_llm_utility
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
        llm = get_llm_utility()
        
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
        session_data = {
            'user_id': user_id,
            'scenario_id': scenario_id,
            'game_session_id': session_game_id,
            'timeline': [],
            'character_summaries': {},
            'world_state': f"Game started in {scenario.get('setting', 'unknown setting')}",
            'current_scenario': f"Player ({scenario.get('player_name', 'Player')}) begins their adventure as {scenario.get('role', 'an adventurer')} in {scenario.get('initial_location', 'an unknown location')}."
        }
        
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
        scenario_id = session.get('scenario_id')
        if not scenario_id:
            logger.error("No scenario_id found in session")
            yield "Error: No scenario configured"
            return
            
        scenario = db.get_scenario(scenario_id)
        if not scenario:
            logger.error(f"Scenario not found: {scenario_id}")
            yield "Error: Scenario not found"
            return
        
        user_id = session.get('user_id', 'unknown')
        logger.debug(f"Generating initial message for user: {user_id}, scenario: {scenario.get('name', 'unknown')}")
        
        # Construct messages for initial story generation
        scenario_name = scenario.get('name', 'Unknown')
        prompt = f"""
Based on the following scenario, generate an engaging opening message that sets the scene 
and begins the interactive story. This should establish the setting, introduce the player's 
situation, and end with a clear prompt for the player to take action.

Scenario Details:
- Name: {scenario.get('name', 'Unknown')}
- Setting: {scenario.get('setting', 'Unknown')}
- Player Role: {scenario.get('role', 'Player')}
- Player Name: {scenario.get('player_name', 'Player')}
- Initial Location: {scenario.get('initial_location', 'Unknown')}
- Description: {scenario.get('description', 'No description available')}

Generate an immersive opening that brings the player into this world and ends with 
"What do you do?" to prompt their first action.
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are StoryOS, an expert storyteller and dungeon master. Create engaging, immersive openings for text-based RPGs."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Generate streaming initial message
        complete_response = ""
        chunk_count = 0
        try:
            logger.info(f"Starting initial story generation for session: {session_id}")
            for chunk in llm.call_creative_llm_stream(messages):
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
            if not db.add_chat_message(session_id, 'StoryOS', complete_response):
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
        
        user_id = session.get('user_id', 'unknown')
        scenario_id = session.get('scenario_id', 'unknown')
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

def construct_game_prompt(system_prompt: str, game_session: Dict[str, Any], 
                         recent_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Construct the prompt for StoryOS response
    
    Args:
        system_prompt: The system prompt defining StoryOS behavior
        game_session: Current game session data
        recent_messages: Recent chat messages for context
        
    Returns:
        List of messages formatted for LLM API
    """
    logger = get_logger("game_logic")
    session_id = game_session.get('_id', 'unknown')
    
    logger.debug(f"Constructing game prompt for session: {session_id} with {len(recent_messages)} recent messages")
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    logger.debug(f"System prompt added (length: {len(system_prompt)})")
    
    # Add game state summary as system context
    world_state = game_session.get('world_state', '')
    current_scenario = game_session.get('current_scenario', '')
    character_summaries = game_session.get('character_summaries', {})
    
    if world_state or current_scenario:
        context = "=== CURRENT GAME STATE ===\n"
        if world_state:
            context += f"World State: {world_state}\n"
            logger.debug(f"World state added (length: {len(world_state)})")
        if current_scenario:
            context += f"Current Scenario: {current_scenario}\n"
            logger.debug(f"Current scenario added (length: {len(current_scenario)})")
        
        # Add character summaries if any
        if character_summaries:
            context += "\n=== CHARACTER SUMMARIES ===\n"
            for char_name, char_data in character_summaries.items():
                char_story = char_data.get('character_story', 'No summary available')
                context += f"{char_name}: {char_story}\n"
                logger.debug(f"Character summary added - {char_name} (length: {len(char_story)})")
        
        messages.append({"role": "system", "content": context})
        logger.debug(f"Game state context added (total length: {len(context)})")
    
    # Add recent conversation history (last 10 messages)
    recent_slice = recent_messages[-10:]  # Get last 10 messages for context
    message_count = 0
    for message in recent_slice:
        role = "user" if message['sender'] == 'player' else "assistant"
        content = message['content']
        messages.append({
            "role": role,
            "content": content
        })
        message_count += 1
        logger.debug(f"Added recent message {message_count}: {role} (length: {len(content)})")
    
    total_prompt_length = sum(len(str(msg.get('content', ''))) for msg in messages)
    logger.info(f"Game prompt constructed - {len(messages)} messages, {total_prompt_length} total chars")
    
    return messages

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
        db = get_db_manager()
        llm = get_llm_utility()
        
        if not db.is_connected():
            logger.error("Database connection failed during player input processing")
            yield "Database service unavailable"
            return
            
        if not llm.is_available():
            logger.error("LLM service unavailable during player input processing")
            yield "AI service unavailable"
            return
        
        # Get game session
        session = db.get_game_session(session_id)
        if not session:
            logger.error(f"Game session not found: {session_id}")
            yield "Game session not found"
            return
        
        user_id = session.get('user_id', 'unknown')
        logger.debug(f"Processing input for user: {user_id}")
        
        # Get system prompt
        system_prompt_doc = db.get_active_system_prompt()
        if not system_prompt_doc:
            logger.error("No active system prompt found")
            yield "System configuration error"
            return
        
        system_prompt = system_prompt_doc['content']
        logger.debug(f"Using system prompt: {system_prompt_doc.get('name', 'unnamed')} (length: {len(system_prompt)})")
        
        # Get recent messages
        recent_messages = db.get_chat_messages(session_id, limit=10)
        logger.debug(f"Retrieved {len(recent_messages)} recent messages for context")
        
        # Add player message to chat
        logger.debug("Adding player message to chat history")
        if not db.add_chat_message(session_id, 'player', player_input):
            logger.warning("Failed to save player message to chat history")
        
        StoryOSLogger.log_user_action(user_id, "player_input", {
            "session_id": session_id,
            "input_length": input_length
        })
        
        # Construct prompt
        messages = construct_game_prompt(system_prompt, session, recent_messages)
        messages.append({"role": "user", "content": player_input})
        logger.debug(f"Prompt constructed with {len(messages)} total messages")
        
        # Generate streaming response
        complete_response = ""
        chunk_count = 0
        try:
            logger.info(f"Starting StoryOS response generation for session: {session_id}")
            for chunk in llm.call_creative_llm_stream(messages):
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
        
        # Add StoryOS response to chat
        if complete_response and not complete_response.startswith("Error:"):
            response_length = len(complete_response)
            logger.info(f"StoryOS response generated (length: {response_length}, chunks: {chunk_count})")
            
            # Save response to chat
            if not db.add_chat_message(session_id, 'StoryOS', complete_response):
                logger.error("Failed to save StoryOS response to chat history")
            
            # Update game summary
            logger.debug("Updating game summary with new interaction")
            current_summary = session.get('current_scenario', '')
            updated_summary = llm.update_game_summary(current_summary, player_input, complete_response)
            
            # Update session with new summary
            if updated_summary != current_summary:
                logger.debug(f"Game summary updated (old: {len(current_summary)}, new: {len(updated_summary)} chars)")
                if not db.update_game_session(session_id, {
                    'current_scenario': updated_summary
                }):
                    logger.warning("Failed to save updated game summary")
            else:
                logger.debug("Game summary unchanged")
        else:
            logger.warning(f"No valid response to save for session: {session_id}")
        
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

def display_game_session_info(session: Dict[str, Any]) -> None:
    """
    Display game session information in the sidebar
    
    Args:
        session: Game session dictionary
    """
    logger = get_logger("game_logic")
    
    try:
        session_id = session.get('_id', 'unknown')
        logger.debug(f"Displaying game session info for session: {session_id}")
        
        with st.sidebar:
            st.subheader("Current Game Session")
            
            # Session details
            if 'scenario_name' in session:
                st.write(f"**Scenario:** {session['scenario_name']}")
                logger.debug(f"Displayed scenario: {session['scenario_name']}")
            
            st.write(f"**Started:** {format_timestamp(session.get('created_at', ''))}")
            st.write(f"**Last Updated:** {format_timestamp(session.get('last_updated', ''))}")
            
            # World state
            world_state = session.get('world_state', '')
            if world_state:
                with st.expander("World State"):
                    st.write(world_state)
                logger.debug(f"Displayed world state (length: {len(world_state)})")
            
            # Current scenario summary
            current_scenario = session.get('current_scenario', '')
            if current_scenario:
                with st.expander("Current Situation"):
                    st.write(current_scenario)
                logger.debug(f"Displayed current scenario (length: {len(current_scenario)})")
            
            # Character summaries
            character_summaries = session.get('character_summaries', {})
            if character_summaries:
                with st.expander("Characters"):
                    for char_name, char_data in character_summaries.items():
                        st.write(f"**{char_name}:** {char_data.get('character_story', 'No summary')}")
                logger.debug(f"Displayed {len(character_summaries)} character summaries")
        
    except Exception as e:
        logger.error(f"Error displaying game session info: {str(e)}")
        StoryOSLogger.log_error_with_context("game_logic", e, {
            "operation": "display_game_session_info",
            "session_id": session.get('_id', 'unknown')
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