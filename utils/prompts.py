from typing import Dict, List, Any
from logging_config import get_logger, StoryOSLogger
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
        logger = get_logger("prompts")
        session_id = game_session.get('_id', 'unknown')
        
        logger.debug(f"Constructing game prompt for session: {session_id} with {len(recent_messages)} recent messages")
        
        messages = []

        context = "=== GENERAL GAME RULES ===\n"
        context += f"{system_prompt}\n\n"
        context += "=== SCENARIO RULES ===\n"

        scenario_id = game_session.get('scenario_id')
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
        world_state = game_session.get('world_state', '')
        current_scenario = game_session.get('current_scenario', '')
        character_summaries = game_session.get('character_summaries', {})
        
        if world_state or current_scenario:
            context += "=== CURRENT GAME STATE ===\n"
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
        
        scenario_id = session.get('scenario_id')
        if scenario_id is None:
            logger.error(f"No scenario_id found in session for session_id: {session_id}")
            raise ValueError(f"No scenario_id found in session for session_id: {session_id}")
        
        scenario = db.get_scenario(scenario_id)
        if scenario is None:
            logger.error(f"No scenario found for scenario_id: {scenario_id}")
            raise ValueError(f"No scenario found for scenario_id: {scenario_id}")
        
        user_id = session.get('user_id', 'unknown')
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