from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from backend.analyzer.ai_bridge_prompt import build_json_repair_prompt

METRIC_KEYS = (
    "answer_format",
    "structure_density",
    "definition_coverage",
    "authority_signals",
    "schema_need",
)


class AIParseError(RuntimeError):
    pass


@dataclass(slots=True)
class ParsedAIResult:
    parsed: dict
    raw_response: str
    diagnostics: dict


def _extract_json_fragment(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIParseError("no JSON object found in model response")
    return stripped[start : end + 1]


def parse_json_response(text: str) -> dict:
    fragment = _extract_json_fragment(text)
    try:
        payload = json.loads(fragment)
    except json.JSONDecodeError as exc:
        raise AIParseError("invalid JSON payload") from exc

    if not isinstance(payload, dict):
        raise AIParseError("JSON payload must be an object")

    for key in METRIC_KEYS:
        if key not in payload:
            raise AIParseError(f"missing metric key: {key}")
        value = payload[key]
        if not isinstance(value, (int, float)):
            raise AIParseError(f"metric {key} must be numeric")
        if value < 0 or value > 10:
            raise AIParseError(f"metric {key} must be within 0..10")

    recommendations = payload.get("recommendations")
    if not isinstance(recommendations, str) or not recommendations.strip():
        raise AIParseError("recommendations must be non-empty string")

    return {key: float(payload[key]) for key in METRIC_KEYS} | {
        "recommendations": recommendations.strip(),
    }


def parse_with_retries(
    send_prompt: Callable[[str], str],
    prompt: str,
    *,
    max_attempts: int = 3,
) -> ParsedAIResult:
    last_error = "unknown"
    last_response = ""

    for attempt in range(1, max_attempts + 1):
        current_prompt = prompt if attempt == 1 else build_json_repair_prompt(last_response)
        response_text = send_prompt(current_prompt)
        last_response = response_text
        try:
            parsed = parse_json_response(response_text)
            return ParsedAIResult(
                parsed=parsed,
                raw_response=response_text,
                diagnostics={
                    "attempts": attempt,
                    "valid_json": True,
                    "error": None,
                },
            )
        except AIParseError as exc:
            last_error = str(exc)

    return ParsedAIResult(
        parsed={},
        raw_response=last_response,
        diagnostics={
            "attempts": max_attempts,
            "valid_json": False,
            "error": last_error,
        },
    )
