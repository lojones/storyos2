"""Scenario management API routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user, get_db_manager_dep, require_admin
from backend.api.schemas import ScenarioPayload, ScenarioUpdate
from backend.logging_config import get_logger
from backend.models.scenario import Scenario
from backend.utils.db_utils import DatabaseManager

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_scenarios(
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> List[Scenario]:
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "user")
    logger.info(f"GET /api/scenarios - List scenarios request by user_id={user_id}, role={user_role}")

    # Admins see all scenarios, regular users see filtered scenarios
    if user_role == "admin":
        scenarios = db_manager.get_all_scenarios(user_id=None)
    else:
        scenarios = db_manager.get_all_scenarios(user_id=user_id)

    logger.info(f"GET /api/scenarios - Returning {len(scenarios)} scenarios for user_id={user_id}")
    return scenarios


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    logger.info(f"GET /api/scenarios/{scenario_id} - Get scenario request")
    scenario = db_manager.get_scenario(scenario_id)
    if not scenario:
        logger.warning(f"GET /api/scenarios/{scenario_id} - Scenario not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    logger.info(f"GET /api/scenarios/{scenario_id} - Returning scenario")
    return scenario


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ScenarioPayload,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    logger.info(f"POST /api/scenarios - Create scenario request by user_id={current_user['user_id']}, scenario_id={payload.scenario_id}")
    # Convert payload to Scenario model
    scenario = Scenario(**payload.model_dump())
    created = db_manager.create_scenario(scenario)
    if not created:
        logger.error(f"POST /api/scenarios - Failed to create scenario scenario_id={payload.scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scenario",
        )

    # Retrieve the created scenario to return
    created_scenario = db_manager.get_scenario(scenario.scenario_id)
    if not created_scenario:
        logger.error(f"POST /api/scenarios - Failed to retrieve created scenario scenario_id={payload.scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created scenario",
        )

    logger.info(f"POST /api/scenarios - Successfully created scenario scenario_id={payload.scenario_id}")
    return created_scenario


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdate,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager_dep),
) -> Scenario:
    logger.info(f"PUT /api/scenarios/{scenario_id} - Update scenario request by user_id={current_user['user_id']}")
    # Get the existing scenario
    existing_scenario = db_manager.get_scenario(scenario_id)
    if not existing_scenario:
        logger.warning(f"PUT /api/scenarios/{scenario_id} - Scenario not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    # Apply updates to the existing scenario
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        logger.warning(f"PUT /api/scenarios/{scenario_id} - No update fields provided")
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
        logger.error(f"PUT /api/scenarios/{scenario_id} - Failed to update scenario")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scenario",
        )

    # Retrieve and return the updated scenario
    result = db_manager.get_scenario(scenario_id)
    if not result:
        logger.error(f"PUT /api/scenarios/{scenario_id} - Failed to retrieve updated scenario")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated scenario",
        )

    logger.info(f"PUT /api/scenarios/{scenario_id} - Successfully updated scenario")
    return result


__all__ = ["router"]
