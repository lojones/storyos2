"""
LLM utilities for StoryOS v2
Handles Grok API integration with streaming support and prompt logging
"""

import json
import openai
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Dict, Any, List

import streamlit as st
from dotenv import load_dotenv

from logging_config import get_logger, StoryOSLogger

# Load environment variables
load_dotenv()

LOG_OUTPUT_DIR = Path("logs")


def _slugify(value: str) -> str:
    """Create a filesystem-safe slug from the provided value."""
    normalized = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "unknown"


def _ensure_logs_dir() -> None:
    """Ensure the log directory exists."""
    try:
        LOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Directory creation issues will surface again when writing the file; avoid noisy logs here.
        pass


def _format_message_content(content: Any) -> str:
    """Render message content as text for logging."""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, indent=2)
    except (TypeError, ValueError):
        return str(content)


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
    
    
    def call_fast_llm_nostream(
        self,
        messages: List[Dict[str, Any]],
        response_schema: Dict,
        *,
        prompt_type: str = "generic",
        involved_characters: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call grok-4-fast-non-reasoning model for fast, non-streaming tasks with structured output
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_schema: JSON schema for structured response format
            
        Returns:
            Complete response text (structured JSON if schema provided)
        """
        start_time = time.time()
        message_count = len(messages)
        total_tokens = sum(len(str(msg.get('content', ''))) for msg in messages)
        
        self.logger.info(f"Calling grok-4-fast-non-reasoning for fast task (messages: {message_count}, est. tokens: {total_tokens}, structured: {bool(response_schema)})")
        
        if not self.is_available():
            self.logger.error("LLM service unavailable for grok-4-fast-non-reasoning call")
            return "LLM service unavailable"
        
        if not self.client:
            self.logger.error("LLM client is None - cannot proceed")
            return "LLM service unavailable"
        
        try:
            # Prepare API call parameters
            api_params = {
                "model": "grok-4-fast-non-reasoning",
                "messages": messages,  # type: ignore
                "temperature": 0.5,
                "max_tokens": 20000
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
            
            self.logger.info(f"grok-4-fast-non-reasoning call completed successfully")
            StoryOSLogger.log_api_call("xAI", "grok-4-fast-non-reasoning", "success", duration, {
                "input_messages": message_count,
                "estimated_input_tokens": total_tokens,
                "response_length": len(content),
                "stream": False
            })
            
            self.log_prompt_interaction(
                messages,
                content,
                prompt_type=prompt_type,
                involved_characters=involved_characters,
                metadata=metadata,
            )
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
    
    def _create_streaming_response(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        *,
        prompt_type: str = "creative",
        involved_characters: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
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

            # Record prompt/response transcript once the stream completes successfully
            if total_content:
                self.log_prompt_interaction(
                    messages,
                    total_content,
                    prompt_type=prompt_type,
                    involved_characters=involved_characters,
                    metadata={
                        **(metadata or {}),
                        "chunk_count": chunk_count,
                        "model": model,
                    },
                )
                    
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

    def call_creative_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        *,
        prompt_type: str = "creative",
        involved_characters: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
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
        
        yield from self._create_streaming_response(
            messages,
            "grok-4-fast-reasoning",
            prompt_type=prompt_type,
            involved_characters=involved_characters,
            metadata=metadata,
        )

    def log_prompt_interaction(
        self,
        messages: List[Dict[str, Any]],
        response_text: str,
        *,
        prompt_type: str,
        involved_characters: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist the prompt and response to a markdown file for audit/debugging."""
        try:
            _ensure_logs_dir()

            timestamp = datetime.utcnow()
            timestamp_str = timestamp.strftime("%Y-%m-%d-%H%M%S")

            prompt_slug = _slugify(prompt_type)

            characters_display: List[str] = []
            if involved_characters:
                characters_display = [name.strip() for name in involved_characters if name and name.strip()]

            # Attempt to infer characters from JSON response when none provided
            inferred_characters: List[str] = []
            parsed_response: Optional[Any] = None
            if not characters_display:
                try:
                    parsed_response = json.loads(response_text)
                    if isinstance(parsed_response, dict):
                        summarized_event = parsed_response.get("summarized_event")
                        if isinstance(summarized_event, dict):
                            involved = summarized_event.get("involved_characters")
                            if isinstance(involved, list):
                                inferred_characters = [str(item) for item in involved if item]
                except (ValueError, TypeError):
                    parsed_response = None

            if inferred_characters:
                characters_display = inferred_characters

            # Fall back to unknown if still empty
            if not characters_display:
                characters_display = ["unknown"]

            character_slug = _slugify("-".join(characters_display))
            filename = f"{prompt_slug}-{character_slug}-{timestamp_str}.md"
            filepath = LOG_OUTPUT_DIR / filename

            # Prepare markdown content
            lines: List[str] = []
            lines.append(f"# Prompt Type: {prompt_type}")
            lines.append("")
            lines.append(f"- Timestamp (UTC): {timestamp.isoformat()}Z")
            lines.append(f"- Involved Characters: {', '.join(characters_display)}")
            if metadata:
                for key, value in metadata.items():
                    lines.append(f"- {key}: {value}")

            lines.append("")
            lines.append("## Request Messages")
            for idx, message in enumerate(messages, start=1):
                role = message.get('role', 'unknown')
                content = _format_message_content(message.get('content', ''))
                lines.append("")
                lines.append(f"### Message {idx} ({role})")
                lines.append("")
                lines.append("```")
                lines.append(content)
                lines.append("```")

            lines.append("")
            lines.append("## Response")
            lines.append("")

            response_block = response_text
            if parsed_response is None:
                try:
                    parsed_response = json.loads(response_text)
                except (ValueError, TypeError):
                    parsed_response = None

            if parsed_response is not None:
                response_block = json.dumps(parsed_response, indent=2)
                lines.append("```json")
            else:
                lines.append("```")

            lines.append(response_block)
            lines.append("```")

            filepath.write_text("\n".join(lines), encoding="utf-8")
            self.logger.debug(f"Prompt interaction logged to {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to log prompt interaction: {str(e)}")
    

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
