import pytest

from utils.model_utils import ModelUtils
from models.image_prompts import VisualPrompts
from models.game_session_model import GameSession


def test_json_from_string_success():
    payload = '{"alpha": 1, "beta": "two"}'
    result = ModelUtils.json_from_string(payload)
    assert result == {"alpha": 1, "beta": "two"}


def test_json_from_string_invalid_json():
    with pytest.raises(ValueError):
        ModelUtils.json_from_string('{invalid}')


def test_json_from_string_not_object():
    with pytest.raises(ValueError):
        ModelUtils.json_from_string('[1, 2, 3]')


def test_model_from_json_success():
    payload = {
        "visual_prompt_1": "First prompt",
        "visual_prompt_2": "Second prompt",
        "visual_prompt_3": "Third prompt",
    }

    result = ModelUtils.model_from_json(payload, VisualPrompts)

    assert isinstance(result, VisualPrompts)
    assert result.visual_prompt_1 == "First prompt"
    assert result.visual_prompt_2 == "Second prompt"
    assert result.visual_prompt_3 == "Third prompt"


def test_model_from_json_validation_error():
    payload = {
        "visual_prompt_1": "Only prompt",
        "visual_prompt_2": "Still second",
        # Missing visual_prompt_3
    }

    with pytest.raises(Exception):
        ModelUtils.model_from_json(payload, VisualPrompts)


def test_model_from_json_gamesession(tmp_path):
    example_path = tmp_path / "game_session.json"
    example_path.write_text(
        '{"created_at": "2025-01-15T10:00:00Z", "last_updated": "2025-01-15T11:30:00Z", "user_id": "user123",'
        ' "scenario_id": "fantasy_dungeon_v1", "game_session_id": 1705320000123, "timeline": ['
        ' {"event_datetime": "2025-01-15T10:05:00Z", "event_title": "Adventure Begins",'
        ' "event_description": "The hero starts their journey in the village square"}], '
        '"character_summaries": {"Hero": {"character_story": "Brave hero"}}, '
        '"world_state": "Peaceful", "last_scene": "Arrived", "current_location": "Village"}'
    )

    payload = ModelUtils.json_from_string(example_path.read_text())
    session_model = ModelUtils.model_from_json(payload, GameSession)

    assert isinstance(session_model, GameSession)
    assert session_model.user_id == "user123"
    assert session_model.scenario_id == "fantasy_dungeon_v1"


def test_model_from_string_visual_prompts():
    payload = '{"visual_prompt_1": "One", "visual_prompt_2": "Two", "visual_prompt_3": "Three"}'
    prompts = ModelUtils.model_from_json(ModelUtils.json_from_string(payload), VisualPrompts)

    assert isinstance(prompts, VisualPrompts)
    assert prompts.visual_prompt_1 == "One"
