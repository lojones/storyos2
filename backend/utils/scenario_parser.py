"""Scenario parsing and validation utilities for StoryOS."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.logging_config import get_logger, StoryOSLogger
from backend.models.scenario import Scenario


def validate_scenario_data(scenario_data: Dict[str, Any]) -> List[str]:
    """Validate scenario metadata and return a list of issues."""
    logger = get_logger("scenario_parser")
    start_time = time.time()

    scenario_id = scenario_data.get("scenario_id", "unknown")
    logger.debug("Validating scenario data: %s", scenario_id)

    try:
        errors: List[str] = []
        required_fields = [
            "scenario_id",
            "author",
            "description",
            "dungeon_master_behaviour",
            "initial_location",
            "name",
            "player_name",
            "role",
            "setting",
            "version",
        ]

        for field in required_fields:
            if field not in scenario_data:
                errors.append(f"Missing required field: {field}")
                logger.debug("Missing field: %s", field)
            elif not scenario_data[field]:
                errors.append(f"Empty required field: {field}")
                logger.debug("Empty field: %s", field)

        version = scenario_data.get("version", "")
        if version and not is_valid_semver(version):
            errors.append(
                f"Invalid version format: {version} (expected semantic version like 1.0.0)"
            )
            logger.debug("Invalid version format: %s", version)

        duration = time.time() - start_time
        StoryOSLogger.log_performance(
            "scenario_parser",
            "validate_scenario_data",
            duration,
            {
                "scenario_id": scenario_id,
                "validation_errors": len(errors),
            },
        )

        if errors:
            logger.warning(
                "Scenario validation failed for %s: %s errors",
                scenario_id,
                len(errors),
            )
        else:
            logger.info("Scenario validation passed for %s", scenario_id)

        return errors

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error validating scenario data: %s", exc)
        StoryOSLogger.log_error_with_context(
            "scenario_parser",
            exc,
            {
                "operation": "validate_scenario_data",
                "scenario_id": scenario_id,
                "duration": duration,
            },
        )
        return [f"Validation error: {exc}"]


def is_valid_semver(version: str) -> bool:
    """Return True if the version string matches semantic versioning (MAJOR.MINOR.PATCH)."""
    logger = get_logger("scenario_parser")

    try:
        pattern = r"^[0-9]+\.[0-9]+\.[0-9]+$"
        is_valid = bool(re.match(pattern, version))
        if not is_valid:
            logger.debug("Invalid semantic version: %s", version)
        return is_valid
    except Exception as exc:  # noqa: BLE001
        logger.error("Error validating semantic version %s: %s", version, exc)
        return False


def parse_scenario_from_markdown(markdown_content: str) -> Optional[Scenario]:
    """Parse a scenario definition from markdown content."""
    logger = get_logger("scenario_parser")
    start_time = time.time()

    content_length = len(markdown_content)
    logger.debug(
        "Parsing scenario from markdown (length: %s chars)",
        content_length,
    )

    try:
        lines = markdown_content.splitlines()
        scenario_data: Dict[str, Any] = {}
        current_section: str | None = None
        current_content: List[str] = []
        sections_processed = 0

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("<!--"):
                continue

            if line.startswith("# ") and "overview" in line.lower():
                current_section = "overview"
                current_content = []
                logger.debug("Processing overview section")
                continue

            if line.startswith("## "):
                section_name = line[3:].lower().strip()
                if current_section and current_content:
                    process_section(scenario_data, current_section, current_content)
                    sections_processed += 1

                current_section = section_name
                current_content = []
                logger.debug("Processing section: %s", section_name)
                continue

            if current_section:
                current_content.append(line)

        if current_section and current_content:
            process_section(scenario_data, current_section, current_content)
            sections_processed += 1

        if "created_at" not in scenario_data:
            scenario_data["created_at"] = datetime.utcnow().isoformat()
            logger.debug("Added default created_at timestamp")

        if "name" in scenario_data and "scenario_id" not in scenario_data:
            scenario_data["scenario_id"] = scenario_data["name"].lower().replace(" ", "_")
            logger.debug("Generated scenario_id: %s", scenario_data["scenario_id"])

        # Convert dict to Scenario model
        try:
            scenario = Scenario(**scenario_data)
        except Exception as model_exc:
            logger.error("Error creating Scenario model from parsed data: %s", model_exc)
            logger.debug("Parsed data: %s", scenario_data)
            raise

        duration = time.time() - start_time
        scenario_name = scenario.name
        StoryOSLogger.log_performance(
            "scenario_parser",
            "parse_scenario_from_markdown",
            duration,
            {
                "content_length": content_length,
                "sections_processed": sections_processed,
                "scenario_name": scenario_name,
            },
        )
        logger.info(
            "Successfully parsed scenario: %s (%s sections)",
            scenario_name,
            sections_processed,
        )
        return scenario

    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start_time
        logger.error("Error parsing scenario markdown: %s", exc)
        StoryOSLogger.log_error_with_context(
            "scenario_parser",
            exc,
            {
                "operation": "parse_scenario_from_markdown",
                "content_length": content_length,
                "duration": duration,
            },
        )
        return None


def process_section(scenario_data: Dict[str, Any], section: str, content: List[str]) -> None:
    """Update ``scenario_data`` with the contents of a parsed section."""
    logger = get_logger("scenario_parser")

    try:
        content_text = "\n".join(content).strip()
        logger.debug(
            "Processing section '%s' with %s lines (%s chars)",
            section,
            len(content),
            len(content_text),
        )

        if section == "overview":
            fields_found = 0
            for line in content:
                if line.startswith("- "):
                    parts = line[2:].split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        scenario_data[key] = value
                        fields_found += 1
            logger.debug("Overview section processed with %s fields", fields_found)
            return

        scenario_data[section] = content_text
        logger.debug("Stored section '%s' (%s chars)", section, len(content_text))

    except Exception as exc:  # noqa: BLE001
        logger.error("Error processing scenario section %s: %s", section, exc)
        StoryOSLogger.log_error_with_context(
            "scenario_parser",
            exc,
            {
                "operation": "process_section",
                "section": section,
            },
        )
