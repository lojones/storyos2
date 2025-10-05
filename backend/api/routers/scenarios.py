"""Scenario management API routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user, get_db_manager_dep, require_admin
from backend.api.schemas import ScenarioPayload, ScenarioUpdate
from backend.models.scenario import Scenario
from backend.utils.db_utils import DatabaseManager

router = APIRouter()


@router.get("/")
async def list_scenarios(
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> List[Scenario]:
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "user")

    # Admins see all scenarios, regular users see filtered scenarios
    if user_role == "admin":
        scenarios = db_manager.get_all_scenarios(user_id=None)
    else:
        scenarios = db_manager.get_all_scenarios(user_id=user_id)

    return scenarios


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    scenario = db_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return scenario


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ScenarioPayload,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    # Convert payload to Scenario model
    scenario = Scenario(**payload.model_dump())
    created = db_manager.create_scenario(scenario)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scenario",
        )

    # Retrieve the created scenario to return
    created_scenario = db_manager.get_scenario(scenario.scenario_id)
    if not created_scenario:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created scenario",
        )

    return created_scenario


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdate,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    # Get the existing scenario
    existing_scenario = db_manager.get_scenario(scenario_id)
    if not existing_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    # Apply updates to the existing scenario
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    # Create updated scenario by merging existing data with updates
    updated_scenario_dict = existing_scenario.model_dump()
    updated_scenario_dict.update(update_data)
    updated_scenario = Scenario(**updated_scenario_dict)

    # Update in database
    success = db_manager.update_scenario(updated_scenario)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scenario",
        )

    # Retrieve and return the updated scenario
    result = db_manager.get_scenario(scenario_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated scenario",
        )

    return result


__all__ = ["router"]
