"""Message model for chat messages in StoryOS."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a chat message used across StoryOS services."""

    sender: str = Field(..., description="Who sent the message (player, StoryOS, system)")
    content: str = Field(..., description="The message content")
    role: Optional[str] = Field(default=None, description="LLM role (user, assistant, system)")
    timestamp: Optional[str] = Field(default=None, description="When the message was created")
    message_id: Optional[str] = Field(default=None, description="Unique message identifier")
    full_prompt: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Full prompt context used to generate this message"
    )
    visual_prompts: Optional[List[str]] = Field(
        default=None,
        description="Visual/image prompts associated with this message"
    )

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create_chat_message(
        cls,
        sender: str,
        content: str,
        message_id: Optional[str] = None,
        *,
        role: Optional[str] = None,
        full_prompt: Optional[List[Dict[str, Any]]] = None,
        visual_prompts: Optional[List[str]] = None,
    ) -> Message:
        """Convenience factory for chat messages with automatic timestamping."""

        return cls(
            sender=sender,
            content=content,
            role=role,
            timestamp=datetime.utcnow().isoformat(),
            message_id=message_id,
            full_prompt=full_prompt or [],
            visual_prompts=visual_prompts,
        )

    def to_llm_format(self) -> Dict[str, str]:
        """Convert to the message format expected by LLM APIs."""

        return {
            "role": self.role or "user",
            "content": self.content,
        }

    def to_chat_format(self) -> Dict[str, Any]:
        """Convert to a lightweight chat display dictionary."""

        return {
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for storage or compatibility."""

        return {
            "sender": self.sender,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "full_prompt": self.full_prompt,
            "visual_prompts": self.visual_prompts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """Create a Message instance from a dictionary, applying safe defaults."""

        return cls(
            sender=data.get("sender", "unknown"),
            content=data.get("content", ""),
            role=data.get("role"),
            timestamp=data.get("timestamp"),
            message_id=data.get("message_id"),
            full_prompt=data.get("full_prompt") or None,
            visual_prompts=data.get("visual_prompts"),
        )
