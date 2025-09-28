"""Game domain services bridging synchronous core logic with async FastAPI."""
from __future__ import annotations

import asyncio
from functools import partial
from typing import Any, AsyncGenerator, Dict, Generator, Optional, cast

from backend.core import game_logic
from backend.logging_config import get_logger
from backend.utils.db_utils import DatabaseManager, get_db_manager
from backend.utils.game_session_manager import get_user_game_sessions
from backend.utils.llm_utils import LLMUtility, get_llm_utility


class GameService:
    """Facade over the legacy game logic that exposes async-friendly helpers."""

    def __init__(
        self,
        *,
        db_manager: Optional[DatabaseManager] = None,
        llm_utility: Optional[LLMUtility] = None,
    ) -> None:
        self.logger = get_logger("game_service")
        self.db_manager = db_manager or get_db_manager()
        self.llm_utility = llm_utility or get_llm_utility()

    async def create_game_session(self, user_id: str, scenario_id: str) -> Optional[str]:
        """Create a new game session for the user."""
        self.logger.debug("Creating game session for user=%s scenario=%s", user_id, scenario_id)
        return await asyncio.to_thread(game_logic.create_new_game, user_id, scenario_id)

    async def list_user_sessions(self, user_id: str) -> list[Dict[str, Any]]:
        """Return all sessions owned by a user."""
        self.logger.debug("Listing sessions for user=%s", user_id)
        return await asyncio.to_thread(get_user_game_sessions, user_id)

    async def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata and message history."""
        self.logger.debug("Loading session=%s", session_id)
        return await asyncio.to_thread(game_logic.load_game_session, session_id)

    async def stream_initial_story(self, session_id: str) -> AsyncGenerator[str, None]:
        """Async wrapper around the synchronous generator that yields initial story chunks."""
        generator = game_logic.generate_initial_story_message(session_id)
        async for chunk in self._iterate_generator(generator):
            yield chunk

    async def stream_player_input(
        self, session_id: str, player_input: str
    ) -> AsyncGenerator[str, None]:
        """Async wrapper around the streaming response for player input."""
        generator = game_logic.process_player_input(
            session_id,
            player_input,
            db_manager=self.db_manager,
            llm_utility=self.llm_utility,
        )
        async for chunk in self._iterate_generator(generator):
            yield chunk

    async def _iterate_generator(
        self, generator: Generator[str, None, None]
    ) -> AsyncGenerator[str, None]:
        """Convert a blocking generator into an async generator using a thread pool."""
        loop = asyncio.get_running_loop()
        sentinel = object()
        while True:
            next_item = await loop.run_in_executor(
                None, partial(next, generator, sentinel)
            )
            if next_item is sentinel:
                break
            yield cast(str, next_item)

    async def append_story_chunk(
        self, session_id: str, chunk: str
    ) -> None:
        """Placeholder for potential post-processing hooks."""
        self.logger.debug(
            "Received chunk for session=%s length=%s", session_id, len(chunk)
        )


__all__ = ["GameService"]
