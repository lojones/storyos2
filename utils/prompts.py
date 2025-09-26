from typing import Dict, List, Any

from logging_config import get_logger, StoryOSLogger
from models.game_session_model import GameSession
from models.message import Message
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
    def construct_game_prompt(
        system_prompt: str,
        game_session: GameSession,
        recent_messages: List[Message],
    ) -> List[Message]:
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
        
        messages: List[Message] = []

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
            
            messages.append(
                Message(
                    sender="system",
                    content=context,
                    role="system",
                )
            )
            logger.debug(f"Game state context added (total length: {len(context)})")

        # Add recent conversation history (last 4 messages)
        recent_slice = recent_messages[-4:]
        message_count = 0
        for message in recent_slice:
            role = message.role or ("user" if message.sender == "player" else "assistant")
            content = message.content or ""
            messages.append(
                Message(
                    sender=message.sender,
                    content=content,
                    role=role,
                    timestamp=message.timestamp,
                    message_id=message.message_id,
                    full_prompt=message.full_prompt,
                    visual_prompts=message.visual_prompts,
                )
            )
            message_count += 1
            logger.debug(f"Added recent message {message_count}: {role} (length: {len(content)})")
        
        total_prompt_length = sum(len(msg.content or "") for msg in messages)
        logger.info(f"Game prompt constructed - {len(messages)} messages, {total_prompt_length} total chars")
        
        return messages

    @staticmethod
    def build_visualization_prompt(session: GameSession) -> List[Message]:
        """Load the visualization system prompt and pair it with session context."""
        logger = get_logger("prompts")

        try:
            db = get_db_manager()
            system_prompt = db.get_active_visualization_system_prompt()
        except Exception as exc:
            logger.error("Unable to retrieve visualization system prompt: %s", str(exc))
            raise

        world_state = session.world_state or "World state unavailable."
        last_scene = session.last_scene or "Last scene details unavailable."
        current_location = getattr(session, "current_location", None) or "Location not specified."

        user_prompt = (
            "The following game session details should inform the three visualization prompts. "
            "Incorporate them while preserving the consistent aesthetic described by the system instructions.\n\n"
            f"World State:\n{world_state}\n\n"
            f"Last Scene:\n{last_scene}\n\n"
            f"Current Location:\n{current_location}\n"
        )

        messages = [
            Message(sender="system", content=system_prompt, role="system"),
            Message(sender="StoryOS", content=user_prompt, role="user"),
        ]

        logger.debug("Visualization prompt messages prepared with session context")
        return messages

    @staticmethod
    def generate_initial_story_prompt(session_id: str) -> List[Message]:

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
            Message(
                sender="system",
                content="You are StoryOS, an expert storyteller and dungeon master. Create engaging, immersive openings for text-based RPGs.",
                role="system",
            ),
            Message(
                sender="StoryOS",
                content=prompt,
                role="user",
            ),
        ]
        return messages
    
    @staticmethod
    def _char_summaries_markdown(game_session: GameSession) -> str:
        """Helper to format character summaries as markdown"""
        summaries = "## Characters\n"
        for char_name, char_data in game_session.character_summaries.items():
            summaries += f"### {char_name}\n"
            summaries += f"{char_data.character_story}\n\n"
        return summaries
    
    @staticmethod
    def construct_game_session_prompt(
        current_game_session: GameSession,
        player_input: str,
        complete_response: str,
    ) -> List[Message]:
        """Construct a detailed prompt summarizing the game session"""
        logger = get_logger("prompts")
        session_id = current_game_session.id
        
        logger.debug(f"Constructing game session prompt for session: {session_id}")

        char_summaries_md = PromptCreator._char_summaries_markdown(current_game_session)

        system_prompt = (
            "You are StoryOS, an expert storyteller and dungeon master. "
            "You convert the provided world + scene context into strictly validated JSON that summarizes the event "
            "and updates character details with concise, factual, non-redundant information.\n\n"
            "# World State\n"
            f"{current_game_session.world_state}\n\n"
            "# Last Scene\n"
            f"{current_game_session.last_scene}\n\n"
            "# Character Summaries So Far\n"
            f"{char_summaries_md}\n"
            "## Output Contract (IMPORTANT)\n"
            "- Respond with **JSON only**. No markdown, no commentary.\n"
            "- Follow the exact schema provided in the user prompt.\n"
            "- Do **not** copy large spans of the scene. Extract concise facts.\n"
            "- Ground every asserted fact in the given scene; if uncertain, omit or mark confidence.\n"
            "- Prefer small, atomic updates over long prose. Avoid repetition of previously known facts unless they changed.\n"
        )

        user_prompt = (
            "Summarize the following player input and DM response, then return JSON matching the schema below.\n\n"
            "### Instructions\n"
            "1) List the characters explicitly named in the scene (no placeholders).\n"
            "2) Create a short, TV-episode style title.\n"
            "3) Write a 1 to 2 sentence event summary focused on actions and outcomes.\n"
            "4) For **each involved character**, generate a **holistic character summary**:\n"
            "   - Treat the provided character summaries in the system prompt as the baseline.\n"
            "   - Fully replace the old summary with a new markdown dossier that merges all previously known details with the new changes.\n"
            "   - The result should reflect both the historical background and the updated, current point-in-time state of the character.\n"
            "   - Do not lose prior important details; carry them forward unless contradicted.\n"
            "   - If something has changed (traits, goals, relationships, inventory, conditions, reputation, etc.), update it accordingly.\n\n"
            "### Character Summary Format (value must be a single markdown string)\n"
            "```\n"
            "### <CharacterName>\n"
            "**Summary:** 2 to 4 sentences blending prior essence + new developments (holistic, up-to-date view).\n\n"
            "**Facts:**\n"
            "- <atomic fact> (confidence: high|medium|low)\n"
            "- <atomic fact> (confidence: ...)\n\n"
            "**Stable Traits:** brave negotiator, lockpicking novice\n\n"
            "**Goals:**\n"
            "- Short-term: <goal1>, <goal2>\n"
            "- Long-term: <goal1>, <goal2>\n\n"
            "**Relationships:**\n"
            "- <OtherCharacter>: <relationship update or null>\n\n"
            "**Status:**\n"
            "- Location: <where>\n"
            "- Conditions: [wounded, fatigued]\n"
            "- Reputation changes: [owed favor by X]\n\n"
            "```\n\n"
            "### JSON Schema (do not alter key names)\n"
            "{\n"
            "  \"summarized_event\": {\n"
            "    \"involved_characters\": [\"<CharacterName>\", \"<CharacterName>\"],\n"
            "    \"event_summary\": \"<1 to 2 sentences>\",\n"
            "    \"event_title\": \"<short title>\",\n"
            "    \"updated_character_summaries\": {\n"
            "      \"<CharacterName>\": \"<markdown dossier as described above>\",\n"
            "      \"<CharacterName>\": \"<markdown dossier as described above>\"\n"
            "    },\n"
            "    \"updated_world_state\": \"<describe net new world changes; if none, repeat prior world state>\"\n"
            ""    "    \"location\": \"<The location where the event took place, if applicable>\"\n"
            "  }\n"
            "}\n\n"
            "### Input\n"
            f"## Player input\n{player_input}\n\n"
            f"## StoryOS response\n{complete_response}\n\n"
            "### Additional Requirements\n"
            "- Output **valid JSON only**.\n"
            "- Do not invent character names.\n"
            "- Each `updated_character_summaries` value must be holistic, markdown-formatted, and reflect both historical info and the new changes.\n"
            "- Do not copy large spans of narrative text. Extract only relevant facts.\n"
        )


        return [
            Message(sender="system", content=system_prompt, role="system"),
            Message(sender="StoryOS", content=user_prompt, role="user"),
        ]
