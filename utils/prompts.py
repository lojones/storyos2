from typing import Dict, List, Any
from logging_config import get_logger, StoryOSLogger
from models.game_session_model import GameSession
from utils.db_utils import get_db_manager

class PromptCreator:
    """Utility class for creating and managing prompts"""
    
    @staticmethod
    def create_scenario_system_prompt() -> str:
        logger = get_logger("prompts")
        db=get_db_manager()
        active_sys_prompt_obj = db.get_active_system_prompt()        
        try:
            if not active_sys_prompt_obj or 'content' not in active_sys_prompt_obj: 
                raise ValueError("No active system prompt found in the database.")
            
            sys_prompt = active_sys_prompt_obj.get('content')
            if sys_prompt is None:
                sys_prompt = "You are the game master. No scenario details available."
            
            logger.debug(f"Using this system prompt template: {sys_prompt}")
            return sys_prompt
        except Exception as e:
            logger.error(f"Error creating system prompt: {str(e)}", exc_info=True)
            return "You are the game master. No scenario details available."
        
    @staticmethod
    def create_custom_system_prompt(user_input: str, scenario_summary: str, scenario_instructions: str) -> str:
        """Create a custom system prompt based on user input"""
        logger = get_logger("prompts")
        try:
            if not user_input or not isinstance(user_input, str):
                raise ValueError("User input must be a non-empty string.")
            if not scenario_summary or not isinstance(scenario_summary, str):
                raise ValueError("Scenario summary must be a non-empty string.")
            if not scenario_instructions or not isinstance(scenario_instructions, str):
                raise ValueError("Scenario instructions must be a non-empty string.")

            system_prompt = PromptCreator.create_scenario_system_prompt()

            custom_prompt = f"You are the game master. {scenario_summary} {scenario_instructions} {user_input}"
            
            logger.debug(f"Using custom system prompt: {custom_prompt}")
            return custom_prompt
        except Exception as e:
            logger.error(f"Error creating custom system prompt: {str(e)}", exc_info=True)
            return "You are the game master. No scenario details available."
    
    @staticmethod
    def construct_game_prompt(system_prompt: str, game_session: GameSession, 
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
        logger = get_logger("prompts")
        session_id = game_session.id
        
        logger.debug(f"Constructing game prompt for session: {session_id} with {len(recent_messages)} recent messages")
        
        messages = []

        context = "=== GENERAL GAME RULES ===\n"
        context += f"{system_prompt}\n\n"
        context += "=== SCENARIO RULES ===\n"

        scenario_id = game_session.scenario_id
        db = get_db_manager()
        scenario_obj = db.get_scenario(scenario_id) if scenario_id else None

        # TODO: add validation for these fields earlier on, and if these are not found then fail the whole app instead of using default values
        scenario_desc = scenario_obj.get('description', 'No scenario description available.') if scenario_obj else 'No scenario description available.'
        player_role = scenario_obj.get('role', 'an adventurer') if scenario_obj else 'an adventurer'
        player_name = scenario_obj.get('player_name', 'Player') if scenario_obj else 'Player'
        dungeon_master_behavior = scenario_obj.get('dungeon_master_behavior', 'You are a fair and engaging dungeon master.') if scenario_obj else 'You are a fair and engaging dungeon master.'

        context += f"- Scenario Description: {scenario_desc}\n"
        context += f"- Player Role: {player_role}\n"
        context += f"- Player Name: {player_name}\n"
        context += f"- Dungeon Master Behavior: {dungeon_master_behavior}\n"

        # Add game state summary as system context
        world_state = game_session.world_state
        last_scene = game_session.last_scene
        character_summaries = game_session.character_summaries
        timeline_entries = getattr(game_session, "timeline", []) or []

        story_path_summaries: List[str] = []
        if timeline_entries:
            for idx, event in enumerate(timeline_entries):
                title = getattr(event, "event_title", None)
                description = getattr(event, "event_description", None)

                if isinstance(event, dict):
                    title = event.get("event_title", title)
                    description = event.get("event_description", description)

                title = title.strip() if isinstance(title, str) else "Untitled"
                description = description.strip() if isinstance(description, str) else ""

                summary_parts = [title]
                if description:
                    summary_parts.append(description)

                story_summary = " - ".join(summary_parts)
                story_path_summaries.append(story_summary)
                logger.debug(
                    "Timeline summary added (%s): %s",
                    idx,
                    story_summary[:120] + ("..." if len(story_summary) > 120 else ""),
                )
        
        if world_state or last_scene or story_path_summaries:
            context += "=== CURRENT GAME STATE ===\n"
            if world_state:
                context += f"World State: {world_state}\n"
                logger.debug(f"World state added (length: {len(world_state)})")
            if last_scene:
                context += f"Last Scene: {last_scene}\n"
                logger.debug(f"Last Scene added (length: {len(last_scene)})")
            if story_path_summaries:
                context += "The Story So Far:\n"
                for summary in story_path_summaries:
                    context += f"- {summary}\n"
                logger.debug(f"Added {len(story_path_summaries)} timeline summaries to context")
        
            # Add character summaries if any
            if character_summaries:
                context += "\n=== CHARACTER SUMMARIES ===\n"
                for char_name, char_data in character_summaries.items():
                    char_story = char_data.character_story
                    context += f"{char_name}: {char_story}\n"
                    logger.debug(f"Character summary added - {char_name} (length: {len(char_story)})")
            
            messages.append({"role": "system", "content": context})
            logger.debug(f"Game state context added (total length: {len(context)})")

        # Add recent conversation history (last 4 messages)
        recent_slice = recent_messages[-4:]  # Get last 4 messages for context
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

    @staticmethod
    def generate_initial_story_prompt(session_id: str) -> list:

        logger = get_logger("prompts")
        
        logger.info(f"Generating initial story message for session: {session_id}")
        
        db = get_db_manager()
        
        # Get game session
        session = db.get_game_session(session_id)
        if session is None:
            logger.error(f"No game session found for session_id: {session_id}")
            raise ValueError(f"No game session found for session_id: {session_id}")
        
        scenario_id = session.scenario_id
        if scenario_id is None:
            logger.error(f"No scenario_id found in session for session_id: {session_id}")
            raise ValueError(f"No scenario_id found in session for session_id: {session_id}")
        
        scenario = db.get_scenario(scenario_id)
        if scenario is None:
            logger.error(f"No scenario found for scenario_id: {scenario_id}")
            raise ValueError(f"No scenario found for scenario_id: {scenario_id}")
        
        user_id = session.user_id
        logger.debug(f"Generating initial message for user: {user_id}, scenario: {scenario.get('name', 'unknown')}")
        
        # Construct messages for initial story generation
        prompt = f"""
Based on the following scenario, generate an engaging opening message that sets the scene 
and begins the interactive story. This should establish the setting, introduce the player's 
situation, and end with a clear prompt for the player to take action. It should be a brief paragraph, yet engaging and interesting.

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
        return messages
    
    @staticmethod
    def construct_game_session_prompt(current_game_session: GameSession, player_input: str, complete_response: str) -> list:
        """Construct a detailed prompt summarizing the game session"""
        logger = get_logger("prompts")
        session_id = current_game_session.id
        
        logger.debug(f"Constructing game session prompt for session: {session_id}")

        system_prompt = "You are StoryOS, an expert storyteller and dungeon master. You will summarize the parts of the story given the overall story context into the provided structured json output."
        system_prompt = f"# World State\n\n"
        system_prompt += f"{current_game_session.world_state}\n\n"
        system_prompt += f"# Last scene\n\n"
        system_prompt += f"{current_game_session.last_scene}\n\n"

        user_prompt = f"Summarize the following user input and dungeon master response.  Follow these rules when summarizing the interaction: \
            - list the characters involved in the scene, only list the characters that you know the names of \
            - create a brief title for the event, like a tv episode title \
            - update the summaries of all the characters that are involved in the scene. Don't lose old summaries, just update each summary to include the new information. \
            - update the world state based on the interaction. this should represent the current state of the world based on the latest interaction \
        Put it all into the provided json structured output.\n\n"
        user_prompt += f"## Player input\n\n{player_input}\n\n"
        user_prompt += f"## StoryOS response\n\n{complete_response}\n\n"

        messages = [ 
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return messages
