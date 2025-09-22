"""
Game Page Module for StoryOS v2
Handles the interactive RPG game interface and player interactions
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
from logging_config import StoryOSLogger, get_logger
from utils.st_session_management import SessionManager, navigate_to_page, Pages
from utils.prompts import PromptCreator
from utils.kling_client import KlingClient
from utils.db_utils import get_db_manager
from models.game_session_model import GameSession
from game.game_logic import (
    load_game_session, format_chat_message, display_game_session_info, 
    process_player_input, generate_initial_story_message
)


class GameInterface:
    """Handles the game interface and player interactions"""
    
    @classmethod
    def _show_animated_loading(cls, placeholder, message: str, emoji_sequence: Optional[list] = None):
        """Show an animated loading indicator with rotating emojis"""
        if emoji_sequence is None:
            emoji_sequence = ["🤔", "💭", "⚡", "✨"]

        import time
        import itertools
        emoji_cycle = itertools.cycle(emoji_sequence)

        # We'll animate for up to 30 seconds or until the placeholder is replaced
        max_cycles = 60  # 0.5s per emoji, 30s total
        for _ in range(max_cycles):
            current_emoji = next(emoji_cycle)
            loading_text = f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.2em;">{current_emoji}</span>
                <em style="color: #888;">{message}</em>
                <div style="display: inline-block; animation: pulse 1.5s ease-in-out infinite;">⏳</div>
            </div>
            <style>
                @keyframes pulse {{
                    0% {{ opacity: 0.5; }}
                    50% {{ opacity: 1; }}
                    100% {{ opacity: 0.5; }}
                }}
            </style>
            """
            placeholder.markdown(loading_text, unsafe_allow_html=True)
            time.sleep(0.5)
    
    @classmethod
    def _clear_new_game_loading_state(cls):
        """Clear any lingering loading state from the new game page"""
        logger = get_logger("game_page")
        
        try:
            # Clear all new game loading state variables
            loading_keys_to_clear = [
                "storyos_starting_game",
                "storyos_scenario_id", 
                "storyos_scenario_name",
                "storyos_start_game_user"
            ]
            
            cleared_count = 0
            for key in loading_keys_to_clear:
                if key in st.session_state:
                    st.session_state.pop(key, None)
                    cleared_count += 1
            
            if cleared_count > 0:
                logger.debug(f"Cleared {cleared_count} new game loading state keys")
            
        except Exception as e:
            logger.error(f"Error clearing new game loading state: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_clear_new_game_loading_state"
            })
    
    @classmethod
    def show_game_page(cls):
        """Show the main game interface"""
        logger = get_logger("game_page")
        
        try:
            # Clear any lingering new game loading state immediately
            cls._clear_new_game_loading_state()
            
            session_id = SessionManager.get_game_session_id()
            if not session_id:
                logger.warning("No game session found when accessing game page")
                cls._show_no_session_error()
                return
            
            logger.debug(f"Displaying game page for session: {session_id}")
            
            # Load game session data
            game_data = load_game_session(session_id)
            if not game_data:
                logger.error(f"Game session data not found: {session_id}")
                cls._show_session_not_found_error()
                return
            
            session = game_data['session']
            messages = game_data['messages']
            
            logger.info(f"Game page loaded - Session: {session_id}, Messages: {len(messages)}")
            
            # Render the game interface
            # cls._render_sidebar_info(session)
            cls._render_main_game_area(messages, session_id)
            
        except Exception as e:
            logger.error(f"Error displaying game page: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "show_game_page",
                "session_id": SessionManager.get_game_session_id()
            })
            st.error("An error occurred while loading the game page")
    
    @classmethod
    def _show_no_session_error(cls):
        """Display error when no game session is selected"""
        logger = get_logger("game_page")
        
        st.error("No game session selected")
        st.info("Please start a new game or load a saved game from the main menu.")
        
        if st.button("← Back to Menu", key="no_session_back"):
            logger.debug("User clicked back to menu from no session error")
            navigate_to_page(Pages.MAIN_MENU)
    
    @classmethod
    def _show_session_not_found_error(cls):
        """Display error when game session data is not found"""
        logger = get_logger("game_page")
        
        st.error("Game session not found")
        st.info("The game session may have been deleted or corrupted.")
        
        if st.button("← Back to Menu", key="session_not_found_back"):
            logger.debug("User clicked back to menu from session not found error")
            SessionManager.clear_game_session()
            navigate_to_page(Pages.MAIN_MENU)
    
    @classmethod
    def _render_sidebar_info(cls, session: GameSession):
        """Render the game session information in the sidebar"""
        logger = get_logger("game_page")
        
        try:
            # Show game info in sidebar
            display_game_session_info(session)
            
            # Back to menu button in sidebar
            if st.sidebar.button("← Back to Menu", key="sidebar_back"):
                session_id = SessionManager.get_game_session_id()
                logger.info(f"User returning to menu from game session: {session_id}")
                
                StoryOSLogger.log_user_action(session.user_id, "exit_game", {
                    "session_id": session_id
                })
                
                SessionManager.clear_game_session()
                navigate_to_page(Pages.MAIN_MENU)
                
        except Exception as e:
            logger.error(f"Error rendering sidebar info: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_render_sidebar_info"
            })
    
    @classmethod
    def _render_main_game_area(cls, messages: list, session_id: str):
        """Render the main game area with chat history and input"""
        logger = get_logger("game_page")
        
        try:
            # Main game area
            st.title("🎲 StoryOS - Interactive Adventure")
            
            # Display chat history and handle streaming in the same context
            st.subheader("Adventure Log")
            
            # Check if this is a new game (no messages) and generate initial story
            if not messages:
                logger.info(f"New game detected for session {session_id} - generating initial story")
                cls._render_initial_story_generation(session_id)
            else:
                cls._render_chat_history(messages, session_id)
            
            # Player input section
            st.divider()
            cls._render_player_input_form(session_id)
            
        except Exception as e:
            logger.error(f"Error rendering main game area: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_render_main_game_area",
                "session_id": session_id
            })
    
    @classmethod
    def _render_initial_story_generation(cls, session_id: str):
        """Render the initial story message generation for a new game"""
        logger = get_logger("game_page")

        try:
            logger.info(f"Rendering initial story generation for session: {session_id}")
            
            # Display an assistant message with streaming initial story
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                chunk_count = 0
                
                logger.debug(f"Starting initial story generation stream for session: {session_id}")
                
                # Show loading indicator while waiting for first chunk
                cls._show_animated_loading(response_placeholder, "Setting up your adventure...", ["🎲", "⚡", "🌟", "🗡️", "🏰"])
                
                # Add a small delay to ensure the loading indicator is visible
                time.sleep(0.2)
                
                try:
                    # Stream the initial story message
                    for chunk in generate_initial_story_message(session_id):
                        if chunk and not chunk.startswith("Error:"):
                            full_response += chunk
                            chunk_count += 1
                            response_placeholder.markdown(full_response + "▌")
                        else:
                            logger.error(f"Error in initial story generation: {chunk}")
                            response_placeholder.error(f"Initial Story Error: {chunk}")
                            break
                    
                    # Final response without cursor
                    if full_response:
                        response_placeholder.markdown(full_response)
                        
                        response_length = len(full_response)
                        logger.info(f"Initial story completed - Length: {response_length}, Chunks: {chunk_count}")
                        
                        StoryOSLogger.log_user_action("unknown", "initial_story_displayed", {
                            "session_id": session_id,
                            "response_length": response_length,
                            "chunk_count": chunk_count
                        })
                        
                        # Rerun to refresh and show the saved message in chat history
                        logger.debug("Rerunning to refresh chat history with initial message")
                        st.rerun()
                    else:
                        logger.warning("Empty initial story generated")
                        response_placeholder.warning("Failed to generate initial story. Please refresh the page.")
                
                except Exception as e:
                    logger.error(f"Error during initial story generation: {str(e)}")
                    response_placeholder.error(f"Error generating initial story: {str(e)}")
                    StoryOSLogger.log_error_with_context("game_page", e, {
                        "operation": "initial_story_generation",
                        "session_id": session_id
                    })
                    
        except Exception as e:
            logger.error(f"Error rendering initial story generation: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_render_initial_story_generation",
                "session_id": session_id
            })
            st.error("Error loading initial story")

    @classmethod
    def _render_chat_history(cls, messages: list, session_id: str):
        """Render the chat message history"""
        logger = get_logger("game_page")

        try:
            session = get_db_manager().get_game_session(session_id)
        except Exception as exc:
            logger.error(f"Unable to load session {session_id} for chat history: {exc}")
            st.error("Unable to load chat history for this session.")
            return

        try:
            # Render existing chat messages
            logger.debug(f"Rendering {len(messages)} chat messages")
            for i, message in enumerate(messages):
                try:
                    message_id = message.get('timestamp') or f"{session.game_session_id}_{i}"
                    format_chat_message(message, message_id=message_id)
                except Exception as e:
                    logger.error(f"Error formatting message {i}: {str(e)}")
                    st.error(f"Error displaying message {i + 1}")

            # Handle temporary player input and streaming if active
            if st.session_state.get("storyos_temp_streaming", False):
                player_input = st.session_state.get("storyos_temp_player_input", "")
                if player_input:
                    cls._render_streaming_response(player_input, session_id)

        except Exception as e:
            logger.error(f"Error rendering chat history: {str(e)}")
            st.error("Error loading chat history")
    
    @classmethod
    def _render_streaming_response(cls, player_input: str, session_id: str):
        """Render the player input and stream the AI response within the chat context"""
        logger = get_logger("game_page")
        
        try:
            # Show the player message
            with st.chat_message("user"):
                st.write(player_input)
            
            # Generate and stream StoryOS response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                chunk_count = 0
                
                logger.debug(f"Starting AI response generation for session: {session_id}")

                import random
                loading_messages = [
                    "The universe is aligning the threads of fate… please wait.",
                    "Your choices ripple across unseen realms… hold steady.",
                    "The dungeon master consults the ancient tomes… patience, traveler.",
                    "Destiny is being rewritten in real time… wait a moment.",
                    "Hidden dice are rolling in the shadows… please stand by.",
                    "The world stirs, waiting for your next move… hold fast.",
                    "Echoes of possibility converge into reality… wait here.",
                    "A storysmith hammers out the next moment of legend… please wait.",
                    "The cosmos weighs the balance of your decisions… just a moment.",
                    "Your path is being woven into the grand tapestry… patience, adventurer.",
                    "The fates whisper among themselves… please wait.",
                    "The tapestry of destiny is being woven… hold steady.",
                    "Shadows gather before the tale continues… wait a moment.",
                    "The dice tumble in the void of chance… patience, adventurer.",
                    "The realm holds its breath, awaiting your path… stand by.",
                    "Ancient tomes turn their pages to your story… please wait.",
                    "The stars align to shape your next choice… hold fast.",
                    "Unseen hands set the stage for what’s to come… wait here.",
                    "The echoes of possibility are resolving into truth… just a moment.",
                    "The wheel of fate creaks forward slowly… wait, traveler."
                ]
                random_loading_message = random.choice(loading_messages)
                # Show loading indicator while waiting for first chunk
                cls._show_animated_loading(response_placeholder, random_loading_message, ["🤔", "💭", "⚡", "✨", "🔮"])
                
                # Add a small delay to ensure the loading indicator is visible
                time.sleep(0.2)
                
                try:
                    # Stream the response
                    for chunk in process_player_input(session_id, player_input):
                        if chunk and not chunk.startswith("Error:"):
                            full_response += chunk
                            chunk_count += 1
                            response_placeholder.markdown(full_response + "▌")
                        else:
                            logger.error(f"Error in AI response: {chunk}")
                            response_placeholder.error(f"AI Response Error: {chunk}")
                            break
                    
                    # Final response without cursor
                    if full_response:
                        response_placeholder.markdown(full_response)
                        
                        response_length = len(full_response)
                        logger.info(f"AI response completed - Length: {response_length}, Chunks: {chunk_count}")
                        
                        StoryOSLogger.log_user_action("unknown", "ai_response_generated", {
                            "session_id": session_id,
                            "response_length": response_length,
                            "chunk_count": chunk_count
                        })
                        
                        # Clear the temporary streaming state
                        st.session_state.pop("storyos_temp_streaming", None)
                        st.session_state.pop("storyos_temp_player_input", None)
                        
                        # Rerun to refresh the chat history with saved messages
                        logger.debug("Rerunning to refresh chat history with saved messages")
                        st.rerun()
                    else:
                        logger.warning("Empty AI response generated")
                        response_placeholder.warning("No response generated. Please try again.")
                        
                        # Clear the temporary state even on empty response
                        st.session_state.pop("storyos_temp_streaming", None)
                        st.session_state.pop("storyos_temp_player_input", None)
                        
                        # Also clear world state update flags if they exist
                        st.session_state.pop("storyos_updating_world_state", None)
                        st.session_state.pop("storyos_world_update_start_time", None)
                
                except Exception as e:
                    logger.error(f"Error during AI response generation: {str(e)}")
                    response_placeholder.error(f"Error generating response: {str(e)}")
                    StoryOSLogger.log_error_with_context("game_page", e, {
                        "operation": "ai_response_generation",
                        "session_id": session_id,
                        "input_length": len(player_input)
                    })
                    
                    # Clear the temporary state on error
                    st.session_state.pop("storyos_temp_streaming", None)
                    st.session_state.pop("storyos_temp_player_input", None)
                    
                    # Also clear world state update flags if they exist
                    st.session_state.pop("storyos_updating_world_state", None)
                    st.session_state.pop("storyos_world_update_start_time", None)
                    
        except Exception as e:
            logger.error(f"Error rendering streaming response: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_render_streaming_response",
                "session_id": session_id
            })
            
            # Clear the temporary state on error
            st.session_state.pop("storyos_temp_streaming", None)
            st.session_state.pop("storyos_temp_player_input", None)
            
            # Also clear world state update flags if they exist
            st.session_state.pop("storyos_updating_world_state", None)
            st.session_state.pop("storyos_world_update_start_time", None)
    
    @classmethod
    def _render_player_input_form(cls, session_id: str):
        """Render the player input form and handle submissions"""
        logger = get_logger("game_page")
        
        try:
            # Check if we're updating the world state
            if st.session_state.get("storyos_updating_world_state", False):
                # Show loading indicator instead of input form
                with st.container():
                    st.markdown("---")
                    loading_placeholder = st.empty()
                    cls._show_animated_loading(
                        loading_placeholder, 
                        "Updating world state and character memories...", 
                        ["🌍", "📚", "⚡", "🔄", "💫"]
                    )
                return
            
            # Use a form to handle player input
            with st.form("player_input_form", clear_on_submit=True):
                current_key = SessionManager.get_chat_key()
                player_input = st.text_area(
                    "What do you do?", 
                    height=100, 
                    key=f"input_{current_key}",
                    placeholder="Describe your action, ask a question, or interact with the environment..."
                )
                submitted = st.form_submit_button("🎯 Submit Action", use_container_width=True)
                
                if submitted and player_input.strip():
                    cls._handle_player_input_submission(session_id, player_input.strip())
                    
        except Exception as e:
            logger.error(f"Error rendering player input form: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_render_player_input_form",
                "session_id": session_id
            })
    
    @classmethod
    def _handle_player_input_submission(cls, session_id: str, player_input: str):
        """Handle player input submission and generate AI response"""
        logger = get_logger("game_page")
        
        try:
            input_length = len(player_input)
            logger.info(f"Processing player input - Session: {session_id}, Length: {input_length}")
            logger.debug(f"Player input preview: {player_input[:100]}{'...' if input_length > 100 else ''}")
            
            # Increment the chat key to clear the input form
            SessionManager.increment_chat_key()
            
            # Log user action
            StoryOSLogger.log_user_action("unknown", "player_input", {
                "session_id": session_id,
                "input_length": input_length
            })
            
            # Store the player input and mark streaming state
            st.session_state["storyos_temp_player_input"] = player_input
            st.session_state["storyos_temp_streaming"] = True
            
            # Rerun to show the input in the chat history and start streaming
            logger.debug("Rerunning to show player input in chat history")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error handling player input submission: {str(e)}")
            StoryOSLogger.log_error_with_context("game_page", e, {
                "operation": "_handle_player_input_submission",
                "session_id": session_id,
                "input_length": len(player_input) if player_input else 0
            })
            st.error("Error processing your input. Please try again.")


# Convenience function for easier import
def show_game_page():
    """Show the game page (convenience function)"""
    GameInterface.show_game_page()


# Additional game page utilities
class GamePageUtils:
    """Utility functions for game page operations"""
    
    @staticmethod
    def get_current_game_info() -> Optional[Dict[str, Any]]:
        """Get information about the current game session"""
        logger = get_logger("game_page")
        
        try:
            current_session = SessionManager.get_game_session_id()
            if not current_session:
                return None
            
            game_data = load_game_session(current_session)
            if not game_data:
                logger.warning(f"No game data found for session: {current_session}")
                return None
            
            return {
                "session_id": current_session,
                "session": game_data['session'],
                "message_count": len(game_data.get('messages', [])),
                "scenario_name": game_data['session'].get('scenario_name', 'Unknown'),
                "created_at": game_data['session'].get('created_at'),
                "last_updated": game_data['session'].get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"Error getting current game info: {str(e)}")
            return None
    
    @staticmethod
    def validate_game_session() -> bool:
        """Validate that the current game session is valid and accessible"""
        logger = get_logger("game_page")
        
        try:
            current_session = SessionManager.get_game_session_id()
            if not current_session:
                logger.debug("No current game session")
                return False
            
            game_data = load_game_session(current_session)
            if not game_data:
                logger.warning(f"Invalid game session: {current_session}")
                return False
            
            logger.debug(f"Valid game session: {current_session}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating game session: {str(e)}")
            return False
