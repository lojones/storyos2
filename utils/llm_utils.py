"""
LLM utilities for StoryOS v2
Handles Grok API integration with streaming support
"""

import openai
import os
from typing import Generator, Optional, Dict, Any, List, Union
import streamlit as st
from dotenv import load_dotenv
from logging_config import get_logger, StoryOSLogger
import time

# Load environment variables
load_dotenv()

class LLMUtility:
    def __init__(self):
        self.logger = get_logger("llm")
        self.api_key = os.getenv("XAI_API_KEY")
        
        if not self.api_key:
            self.logger.error("XAI_API_KEY not found in environment variables")
            st.error("XAI_API_KEY not found in environment variables")
            return
        
        self.logger.info("Initializing LLM client with xAI Grok API")
        self.logger.debug("API base URL: https://api.x.ai/v1")
        
        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
            self.logger.info("LLM client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {str(e)}")
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "client_initialization"})
            st.error(f"Failed to initialize LLM client: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if LLM client is available"""
        available = self.api_key is not None and self.client is not None
        if not available:
            self.logger.warning("LLM client is not available - missing API key or client initialization failed")
        return available
    
    def call_creative_llm(self, messages: List[Dict[str, Any]], stream: bool = False) -> str:
        """
        Call Grok-4 model for creative tasks
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            
        Returns:
            Complete response text
        """
        start_time = time.time()
        message_count = len(messages)
        total_tokens = sum(len(str(msg.get('content', ''))) for msg in messages)
        
        self.logger.info(f"Calling Grok-4 for creative task (stream: {stream}, messages: {message_count}, est. tokens: {total_tokens})")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for Grok-4 call")
            return "LLM service unavailable"
        
        if not self.client:
            self.logger.error("LLM client is None - cannot proceed")
            return "LLM service unavailable"
        
        try:
            if stream:
                return self._stream_response(messages, "grok-4")
            else:
                response = self.client.chat.completions.create(
                    model="grok-4",
                    messages=messages,  # type: ignore
                    temperature=0.7,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content or ""
                duration = time.time() - start_time
                
                self.logger.info(f"Grok-4 call completed successfully")
                StoryOSLogger.log_api_call("xAI", "grok-4", "success", duration, {
                    "input_messages": message_count,
                    "estimated_input_tokens": total_tokens,
                    "response_length": len(content),
                    "stream": stream
                })
                
                return content
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error calling Grok-4: {str(e)}")
            StoryOSLogger.log_api_call("xAI", "grok-4", "error", duration, {
                "error": str(e),
                "input_messages": message_count,
                "stream": stream
            })
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "call_creative_llm", "model": "grok-4"})
            st.error(f"Error calling Grok-4: {str(e)}")
            return f"Error: {str(e)}"
    
    def call_fast_llm_nostream(self, messages: List[Dict[str, Any]], response_schema: Dict) -> str:
        """
        Call Grok-3-mini model for fast, non-streaming tasks with structured output
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_schema: JSON schema for structured response format
            
        Returns:
            Complete response text (structured JSON if schema provided)
        """
        start_time = time.time()
        message_count = len(messages)
        total_tokens = sum(len(str(msg.get('content', ''))) for msg in messages)
        
        self.logger.info(f"Calling Grok-3-mini for fast task (messages: {message_count}, est. tokens: {total_tokens}, structured: {bool(response_schema)})")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for Grok-3-mini call")
            return "LLM service unavailable"
        
        if not self.client:
            self.logger.error("LLM client is None - cannot proceed")
            return "LLM service unavailable"
        
        try:
            # Prepare API call parameters
            api_params = {
                "model": "grok-3-mini",
                "messages": messages,  # type: ignore
                "temperature": 0.5,
                "max_tokens": 10000
            }
            
            # Add structured output format if schema provided
            if response_schema:
                api_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_response",
                        "schema": response_schema
                    }
                }
                self.logger.debug("Added structured response format to API call")
            
            response = self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content or ""
            duration = time.time() - start_time
            
            self.logger.info(f"Grok-3-mini call completed successfully")
            StoryOSLogger.log_api_call("xAI", "grok-3-mini", "success", duration, {
                "input_messages": message_count,
                "estimated_input_tokens": total_tokens,
                "response_length": len(content),
                "stream": False
            })
            
            return content
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error calling Grok-3-mini: {str(e)}")
            StoryOSLogger.log_api_call("xAI", "grok-3-mini", "error", duration, {
                "error": str(e),
                "input_messages": message_count,
                "stream": False
            })
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "call_fast_llm_nostream", "model": "grok-3-mini"})
            st.error(f"Error calling Grok-3-mini: {str(e)}")
            return f"Error: {str(e)}"
    
    def _create_streaming_response(self, messages: List[Dict[str, Any]], model: str) -> Generator[str, None, None]:
        """
        Create a streaming response from the specified model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use for the API call
            
        Yields:
            Response chunks as they arrive
        """
        start_time = time.time()
        message_count = len(messages)
        chunk_count = 0
        total_content = ""
        
        self.logger.info(f"Starting streaming response from {model} (messages: {message_count})")
        
        if not self.client:
            self.logger.error(f"LLM client is None - cannot create streaming response for {model}")
            yield "LLM service unavailable"
            return
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    chunk_content = chunk.choices[0].delta.content
                    chunk_count += 1
                    total_content += chunk_content
                    yield chunk_content
                    
            duration = time.time() - start_time
            self.logger.info(f"Streaming completed from {model} (chunks: {chunk_count}, duration: {duration:.2f}s)")
            StoryOSLogger.log_api_call("xAI", model, "success", duration, {
                "input_messages": message_count,
                "chunks_received": chunk_count,
                "total_response_length": len(total_content),
                "streaming": True
            })
                    
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error streaming from {model}: {str(e)}"
            self.logger.error(error_msg)
            StoryOSLogger.log_api_call("xAI", model, "error", duration, {
                "error": str(e),
                "input_messages": message_count,
                "chunks_received": chunk_count,
                "streaming": True
            })
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "streaming_response", "model": model})
            st.error(error_msg)
            yield f"Error: {str(e)}"

    def call_creative_llm_stream(self, messages: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        Call Grok-4 model with streaming response
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Yields:
            Response chunks as they arrive
        """
        message_count = len(messages)
        self.logger.info(f"Starting Grok-4 streaming call (messages: {message_count})")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for Grok-4 streaming call")
            yield "LLM service unavailable"
            return
        
        yield from self._create_streaming_response(messages, "grok-4")
    
    def _stream_response(self, messages: List[Dict[str, Any]], model: str) -> str:
        """
        Helper method to get complete response from streaming
        Used internally when stream=True but we need the complete text
        """
        self.logger.debug(f"Getting complete response from streaming {model}")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for stream response")
            return "LLM service unavailable"
        
        complete_response = ""
        chunk_count = 0
        
        for chunk in self._create_streaming_response(messages, model):
            chunk_count += 1
            if not chunk.startswith("Error:"):
                complete_response += chunk
            else:
                self.logger.error(f"Error in streaming response after {chunk_count} chunks: {chunk}")
                return chunk  # Return error message immediately
        
        self.logger.debug(f"Complete streaming response assembled from {chunk_count} chunks (length: {len(complete_response)})")
        return complete_response
    
    def generate_story_response(self, system_prompt: str, game_summary: str, 
                              recent_messages: List[Dict[str, Any]], 
                              player_input: str) -> Generator[str, None, None]:
        """
        Generate StoryOS response to player input with streaming
        
        Args:
            system_prompt: The system prompt defining StoryOS behavior
            game_summary: Current game state summary
            recent_messages: Last few chat messages for context
            player_input: The player's latest input
            
        Yields:
            Response chunks as they arrive
        """
        self.logger.info(f"Generating story response for player input (length: {len(player_input)}, recent_messages: {len(recent_messages)})")
        self.logger.debug(f"Player input preview: {player_input[:100]}{'...' if len(player_input) > 100 else ''}")
        
        # Construct the prompt
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add game summary as context
        if game_summary:
            messages.append({
                "role": "system", 
                "content": f"Current Game State Summary:\n{game_summary}"
            })
            self.logger.debug(f"Game summary included (length: {len(game_summary)})")
        
        # Add recent conversation history
        for i, msg in enumerate(recent_messages):
            messages.append(msg)
            self.logger.debug(f"Added recent message {i+1}: {msg.get('role', 'unknown')} - {len(str(msg.get('content', '')))} chars")
        
        # Add the current player input
        messages.append({"role": "user", "content": player_input})
        
        self.logger.debug(f"Constructed prompt with {len(messages)} messages for story generation")
        
        # Generate streaming response
        yield from self.call_creative_llm_stream(messages)
    
    def update_game_summary(self, current_summary: str, player_input: str, ai_response: str) -> str:
        """
        Update the game summary with new player input and AI response
        
        Args:
            current_summary: The current game state summary
            player_input: The player's latest input
            ai_response: The AI's response to that input
            
        Returns:
            Updated game summary
        """
        start_time = time.time()
        self.logger.info(f"Updating game summary (current: {len(current_summary)} chars, input: {len(player_input)} chars, response: {len(ai_response)} chars)")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for game summary update")
            return current_summary
        
        if not self.client:
            self.logger.error("LLM client is None - cannot update game summary")
            return current_summary
        
        update_prompt = f"""
Update the following game summary by incorporating the recent player input and AI response. 
Keep the summary concise but include important story developments, character interactions, 
location changes, and any significant events.

Current Summary:
{current_summary}

Recent Player Input:
{player_input}

AI Response:
{ai_response}

Provide an updated summary that captures the current state of the game world, 
the player's situation, and any important developments:
"""
        
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant that maintains concise game state summaries for a text-based RPG."
            },
            {
                "role": "user", 
                "content": update_prompt
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="grok-3-mini",
                messages=messages,  # type: ignore
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=500
            )
            
            updated_summary = response.choices[0].message.content or current_summary
            duration = time.time() - start_time
            
            self.logger.info(f"Game summary updated successfully (new length: {len(updated_summary)} chars)")
            StoryOSLogger.log_api_call("xAI", "grok-3-mini", "success", duration, {
                "operation": "update_summary",
                "original_length": len(current_summary),
                "updated_length": len(updated_summary)
            })
            
            return updated_summary
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error updating game summary: {str(e)}")
            StoryOSLogger.log_api_call("xAI", "grok-3-mini", "error", duration, {
                "operation": "update_summary",
                "error": str(e)
            })
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "update_game_summary"})
            st.error(f"Error updating game summary: {str(e)}")
            return current_summary  # Return original summary on error
    
    def generate_initial_story_message(self, scenario: Dict[str, Any]) -> str:
        """
        Generate the initial story message when starting a new game
        
        Args:
            scenario: The scenario dictionary containing game setup
            
        Returns:
            Initial story message from StoryOS
        """
        start_time = time.time()
        scenario_name = scenario.get('name', 'Unknown')
        self.logger.info(f"Generating initial story message for scenario: {scenario_name}")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for initial story message generation")
            return "Welcome to StoryOS! (LLM service unavailable)"
        
        if not self.client:
            self.logger.error("LLM client is None - cannot generate initial story message")
            return "Welcome to StoryOS! (LLM service unavailable)"
        
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
        
        try:
            response = self.client.chat.completions.create(
                model="grok-4",
                messages=messages,  # type: ignore
                temperature=0.8,
                max_tokens=1000
            )
            
            story_message = response.choices[0].message.content or f"Welcome to {scenario.get('name', 'StoryOS')}! Your adventure begins now. What do you do?"
            duration = time.time() - start_time
            
            self.logger.info(f"Initial story message generated successfully for {scenario_name} (length: {len(story_message)} chars)")
            StoryOSLogger.log_api_call("xAI", "grok-4", "success", duration, {
                "operation": "generate_initial_story",
                "scenario_name": scenario_name,
                "message_length": len(story_message)
            })
            
            return story_message
            
        except Exception as e:
            duration = time.time() - start_time
            fallback_message = f"Welcome to {scenario.get('name', 'StoryOS')}! Your adventure begins now. What do you do?"
            
            self.logger.error(f"Error generating initial story message for {scenario_name}: {str(e)}")
            StoryOSLogger.log_api_call("xAI", "grok-4", "error", duration, {
                "operation": "generate_initial_story",
                "scenario_name": scenario_name,
                "error": str(e)
            })
            StoryOSLogger.log_error_with_context("llm", e, {"operation": "generate_initial_story_message", "scenario": scenario_name})
            st.error(f"Error generating initial story message: {str(e)}")
            
            return fallback_message

# Global LLM utility instance
_llm_utility = None

def get_llm_utility() -> LLMUtility:
    """Get the global LLM utility instance"""
    global _llm_utility
    if _llm_utility is None:
        logger = get_logger("llm")
        logger.debug("Creating new LLMUtility instance")
        _llm_utility = LLMUtility()
    return _llm_utility