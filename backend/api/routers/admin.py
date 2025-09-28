"""Administrative API routes."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_db_manager_dep, require_admin
from backend.utils.db_utils import DatabaseManager

router = APIRouter()


@router.get("/stats")
async def get_stats(
    _: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    user_count = db_manager.get_user_count()
    scenario_count = len(db_manager.get_all_scenarios())
    session_count = 0
    if db_manager.db is not None:
        session_count = db_manager.db.active_game_sessions.count_documents({})
    return {
        "users": user_count,
        "scenarios": scenario_count,
        "active_sessions": session_count,
    }


__all__ = ["router"]
