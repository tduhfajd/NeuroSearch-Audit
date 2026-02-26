from __future__ import annotations

from backend.db.models import Page


def prompt_schema_description() -> str:
    return (
        "{\n"
        '  "answer_format": 0-10,\n'
        '  "structure_density": 0-10,\n'
        '  "definition_coverage": 0-10,\n'
        '  "authority_signals": 0-10,\n'
        '  "schema_need": 0-10,\n'
        '  "recommendations": "short actionable text"\n'
        "}"
    )


def build_page_prompt(page: Page) -> str:
    page_snapshot = {
        "url": page.url,
        "title": page.title,
        "h1": page.h1,
        "meta_description": page.meta_description,
        "word_count": page.word_count,
        "pagespeed_score": page.pagespeed_score,
    }
    return (
        "Evaluate this web page for AI-answer readiness. "
        "Return JSON only and do not include markdown.\n"
        "Use this exact schema:\n"
        f"{prompt_schema_description()}\n\n"
        f"Page data: {page_snapshot}"
    )


def build_json_repair_prompt(previous_response: str) -> str:
    return (
        "Your previous response was invalid. "
        "Return ONLY valid JSON with the required keys and numeric scores 0..10.\n"
        f"Previous response: {previous_response[:2000]}"
    )
