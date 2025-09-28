"""Scenario management API routes."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_db_manager_dep, require_admin
from backend.api.schemas import ScenarioPayload, ScenarioUpdate
from backend.utils.db_utils import DatabaseManager

router = APIRouter()


@router.get("/")
async def list_scenarios(
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> List[Dict[str, Any]]:
    scenarios = db_manager.get_all_scenarios()
    for scenario in scenarios:
        if "_id" in scenario:
            scenario["_id"] = str(scenario["_id"])
    return scenarios


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    scenario = db_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    if "_id" in scenario:
        scenario["_id"] = str(scenario["_id"])
    return scenario


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ScenarioPayload,
    _: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    scenario_data: Dict[str, Any] = payload.model_dump()
    created = db_manager.create_scenario(scenario_data)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scenario",
        )
    return scenario_data


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdate,
    _: dict = Depends(require_admin),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Dict[str, Any]:
    scenario_data: Dict[str, Any] = {
        key: value for key, value in payload.model_dump().items() if value is not None
    }
    if not scenario_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )
    updated = db_manager.update_scenario(scenario_id, scenario_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scenario",
        )
    scenario = db_manager.get_scenario(scenario_id)
    if scenario and "_id" in scenario:
        scenario["_id"] = str(scenario["_id"])
    return scenario or scenario_data


__all__ = ["router"]
