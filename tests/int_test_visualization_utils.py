"""Live integration test for VisualizationManager.

This test is intentionally skipped unless Kling.ai credentials are available
via environment variables. When enabled it performs a real API call to verify
the end-to-end integration.
"""

from __future__ import annotations

import os

import pytest

from models.visualization_response import VisualizationResponse
from utils.visualization_utils import VisualizationManager


@pytest.mark.integration
@pytest.mark.external
def test_visualization_manager_submit_prompt_live():
    """Verify VisualizationManager submits prompts using real Kling.ai credentials."""

    required_env_vars = [
        "KLING_ACCESS_KEY",
        "KLING_SECRET_KEY",
    ]

    missing = [env for env in required_env_vars if not os.getenv(env)]
    if missing:
        pytest.skip(
            "Missing Kling.ai credentials in environment: " + ", ".join(missing)
        )

    prompt = "A college-age Indian-Canadian woman, south Indian Dravidian origin, Lush midnight-dark skin, very pretty with a radiant face, high cheekbones, almond-shaped eyes, and a warm, glowing complexion. Her classic long black Indian hair flows down her back, glossy and thick, framing her face elegantly. Her legs are powerfully built and muscular, sculpted by intense squats and heavy leg workouts, with thick, chiseled thighs showcasing pronounced quadriceps and hamstrings that flex with strength, yet retain a sleek, feminine form. Her calves are strikingly defined, bulging with each step, displaying robust development without being overly vascular. She’s dressed as a typical university student walking around campus, wearing a casual fitted crop top that shows her toned midriff, ultra-short blue cotton yoga microshorts that highlight her muscular legs, and simple flip-flops. She has a very thin, cinched waist that accentuates her athletic build, creating a striking hourglass silhouette. She’s dressed as a typical university student walking around campus, wearing a casual fitted crop top that highlights her narrow midriff, ultra-short cotton yoga microshorts that showcase her muscular legs, and simple flip-flops. She carries a relaxed, confident vibe, blending athletic strength with youthful, everyday university style."

    response = VisualizationManager.submit_prompt(prompt)

    assert isinstance(response, VisualizationResponse)
    assert response.task_id.strip(), "Expected non-empty task_id from Kling.ai"
    assert response.image_url, "Expected image URL in visualization response"
