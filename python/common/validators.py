from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import jsonschema


@dataclass(slots=True)
class ValidationIssue:
    path: str
    message: str


REQUIRED_FILES = (
    "manifest.json",
    "crawl/visited_urls.json",
    "crawl/fetch_log.json",
    "crawl/link_graph.json",
    "analysis/entities.json",
    "analysis/normalized_facts.json",
    "analysis/coverage_report.json",
    "analysis/contradictions.json",
    "analysis/ai_readiness_scores.json",
    "analysis/recommendations.json",
)

PROMPT_FILES = (
    "prompts/client_report_prompt.md",
    "prompts/tech_audit_prompt.md",
    "prompts/optimization_plan_prompt.md",
    "prompts/work_backlog_prompt.md",
    "prompts/commercial_offer_prompt.md",
)

PROMPT_SECTIONS = (
    "Role:",
    "Audience:",
    "Allowed Inputs:",
    "Document Structure:",
    "Evidence Rules:",
    "No Fabrication Policy:",
    "Output Constraints:",
)

REQUIRED_FIELDS = {
    "manifest.json": ("schema_version", "audit_id", "created_at", "ruleset_versions", "schema_versions", "stage_status", "files"),
    "crawl/visited_urls.json": ("schema_version", "audit_id", "visited_urls", "skipped_urls", "filtered_urls", "failure_count", "throttle_policy"),
    "crawl/fetch_log.json": ("schema_version", "audit_id", "entries"),
    "crawl/link_graph.json": ("schema_version", "audit_id", "edges"),
    "analysis/entities.json": ("schema_version", "audit_id", "entities"),
    "analysis/normalized_facts.json": ("schema_version", "audit_id", "facts"),
    "analysis/coverage_report.json": ("schema_version", "audit_id", "coverage_ruleset", "items", "summary"),
    "analysis/contradictions.json": ("schema_version", "audit_id", "contradictions"),
    "analysis/ai_readiness_scores.json": ("schema_version", "audit_id", "ruleset_version", "page_scores", "entity_scores", "top_gaps", "lead_value_index"),
    "analysis/recommendations.json": ("schema_version", "audit_id", "recommendations"),
    "exports/review_brief.json": ("schema_version", "audit_id", "package_status", "lead_value_index", "summary", "executive_summary", "crawl_quality", "top_gaps", "action_plan", "current_strengths", "focus_areas", "priority_pages", "high_contradictions", "priority_recommendations", "evidence_sources"),
}

SCHEMA_BY_PATH = {
    "manifest.json": "schemas/manifest.schema.json",
    "crawl/visited_urls.json": "schemas/crawl/visited_urls.schema.json",
    "crawl/fetch_log.json": "schemas/crawl/fetch_log.schema.json",
    "crawl/link_graph.json": "schemas/crawl/link_graph.schema.json",
    "analysis/entities.json": "schemas/entities.schema.json",
    "analysis/normalized_facts.json": "schemas/normalized_facts.schema.json",
    "analysis/coverage_report.json": "schemas/coverage_report.schema.json",
    "analysis/contradictions.json": "schemas/contradictions.schema.json",
    "analysis/ai_readiness_scores.json": "schemas/ai_readiness_scores.schema.json",
    "analysis/recommendations.json": "schemas/recommendations.schema.json",
    "analysis/legacy_factor_assessments.json": "schemas/legacy_factor_assessments.schema.json",
    "analysis/legacy_index_scores.json": "schemas/legacy_index_scores.schema.json",
    "exports/review_brief.json": "schemas/review_brief.schema.json",
}

OPTIONAL_SCHEMA_BY_GLOB = {
    "analysis/page_blocks.json": "schemas/page_blocks.schema.json",
    "render/render_plan.json": "schemas/render_plan.schema.json",
    "render/render_fallback_report.json": "schemas/render_fallback_report.schema.json",
    "pages/rendered/*.json": "schemas/rendered_page.schema.json",
    "exports/client_report_input.json": "schemas/client_report_input.schema.json",
    "exports/client_report.json": "schemas/client_report.schema.json",
    "exports/scoring_parity_snapshot.json": "schemas/scoring_parity_snapshot.schema.json",
    "exports/expert_report.json": "schemas/expert_report.schema.json",
    "exports/technical_client_report.json": "schemas/technical_client_report.schema.json",
    "exports/commercial_offer.json": "schemas/commercial_offer.schema.json",
    "exports/technical_action_plan.json": "schemas/technical_action_plan.schema.json",
    "exports/summary.json": "schemas/export_summary.schema.json",
    "exports/backlog.json": "schemas/export_backlog.schema.json",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(relative: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    return load_json(root / relative)


def validate_schema_payload(relative: str, payload: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    schema_path = SCHEMA_BY_PATH.get(relative)
    if not schema_path:
        return issues
    schema = load_schema(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
        path = ".".join(str(part) for part in error.absolute_path)
        message = error.message if not path else f"{path}: {error.message}"
        issues.append(ValidationIssue(relative, f"schema violation: {message}"))
    return issues


def validate_contracts(package_dir: Path, ignored_paths: tuple[str, ...] = ()) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    ignored = set(ignored_paths)

    for relative in REQUIRED_FILES:
        if relative in ignored:
            continue
        path = package_dir / relative
        if not path.exists():
            issues.append(ValidationIssue(relative, "required file is missing"))

    for relative, fields in REQUIRED_FIELDS.items():
        if relative in ignored:
            continue
        path = package_dir / relative
        if not path.exists():
            continue
        try:
            payload = load_json(path)
        except Exception as exc:  # noqa: BLE001
            issues.append(ValidationIssue(relative, f"invalid JSON: {exc}"))
            continue
        for field in fields:
            if field not in payload:
                issues.append(ValidationIssue(relative, f"missing required field {field!r}"))
        issues.extend(validate_schema_payload(relative, payload))
        if relative == "exports/review_brief.json":
            crawl_quality = payload.get("crawl_quality", {})
            for field in (
                "visited_url_count",
                "skipped_url_count",
                "filtered_url_count",
                "fetch_failure_count",
                "fetched_count",
                "html_count",
                "non_html_count",
                "raw_page_count",
                "submitted_count",
                "sitemap_count",
                "discovered_count",
                "discovery_mode",
                "protocol_duplication",
                "warnings",
            ):
                if field not in crawl_quality:
                    issues.append(ValidationIssue(relative, f"crawl_quality missing required field {field!r}"))

    for path in sorted((package_dir / "pages" / "technical").glob("*.json")):
        relative = path.relative_to(package_dir).as_posix()
        if relative in ignored:
            continue
        try:
            payload = load_json(path)
        except Exception as exc:  # noqa: BLE001
            issues.append(ValidationIssue(relative, f"invalid JSON: {exc}"))
            continue
        for field in ("schema_version", "audit_id", "url", "source", "extracted_at", "meta", "headings", "schema_hints", "runet_signals", "commercial_signals", "transport_signals"):
            if field not in payload:
                issues.append(ValidationIssue(relative, f"missing required field {field!r}"))
        commercial_signals = payload.get("commercial_signals", {})
        for field in ("price_hints", "timeline_hints", "geo_hints", "offer_terms"):
            if field not in commercial_signals:
                issues.append(ValidationIssue(relative, f"commercial_signals missing required field {field!r}"))
        transport_signals = payload.get("transport_signals", {})
        if "strict_transport_security" not in transport_signals:
            issues.append(ValidationIssue(relative, "transport_signals missing required field 'strict_transport_security'"))
        if "mixed_content_urls" not in transport_signals:
            issues.append(ValidationIssue(relative, "transport_signals missing required field 'mixed_content_urls'"))
        technical_schema = load_schema("schemas/technical_page.schema.json")
        validator = jsonschema.Draft202012Validator(technical_schema)
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
            path_str = ".".join(str(part) for part in error.absolute_path)
            message = error.message if not path_str else f"{path_str}: {error.message}"
            issues.append(ValidationIssue(relative, f"schema violation: {message}"))

    manifest_path = package_dir / "manifest.json"
    if manifest_path.exists():
        payload = load_json(manifest_path)
        manifest_files = {entry["path"] for entry in payload.get("files", []) if "path" in entry}
        for relative in REQUIRED_FILES:
            if relative in ignored:
                continue
            if relative not in manifest_files:
                issues.append(ValidationIssue("manifest.json", f"required file {relative!r} missing from manifest inventory"))

    for pattern, schema_path in OPTIONAL_SCHEMA_BY_GLOB.items():
        for path in sorted(package_dir.glob(pattern)):
            relative = path.relative_to(package_dir).as_posix()
            if relative in ignored:
                continue
            try:
                payload = load_json(path)
            except Exception as exc:  # noqa: BLE001
                issues.append(ValidationIssue(relative, f"invalid JSON: {exc}"))
                continue
            schema = load_schema(schema_path)
            validator = jsonschema.Draft202012Validator(schema)
            for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
                path_str = ".".join(str(part) for part in error.absolute_path)
                message = error.message if not path_str else f"{path_str}: {error.message}"
                issues.append(ValidationIssue(relative, f"schema violation: {message}"))

    return issues


def validate_evidence(package_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    coverage_path = package_dir / "analysis/coverage_report.json"
    if coverage_path.exists():
        coverage = load_json(coverage_path)
        for index, item in enumerate(coverage.get("items", [])):
            if item.get("priority") in {"P0", "P1"} and not item.get("evidence"):
                issues.append(ValidationIssue(f"analysis/coverage_report.json#{index}", "high-priority coverage item is missing evidence"))

    contradictions_path = package_dir / "analysis/contradictions.json"
    if contradictions_path.exists():
        contradictions = load_json(contradictions_path)
        for index, item in enumerate(contradictions.get("contradictions", [])):
            severity = item.get("severity")
            if severity in {"high", "medium"} and len(item.get("sources", [])) < 2:
                issues.append(ValidationIssue(f"analysis/contradictions.json#{index}", "contradiction must cite at least two sources"))

    recommendations_path = package_dir / "analysis/recommendations.json"
    if recommendations_path.exists():
        recommendations = load_json(recommendations_path)
        for index, item in enumerate(recommendations.get("recommendations", [])):
            if not item.get("related_findings"):
                issues.append(ValidationIssue(f"analysis/recommendations.json#{index}", "recommendation is missing related findings"))
            if not item.get("acceptance_criteria"):
                issues.append(ValidationIssue(f"analysis/recommendations.json#{index}", "recommendation is missing acceptance criteria"))

    return issues


def validate_prompts(package_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for relative in PROMPT_FILES:
        path = package_dir / relative
        if not path.exists():
            issues.append(ValidationIssue(relative, "required prompt file is missing"))
            continue
        content = path.read_text(encoding="utf-8")
        for section in PROMPT_SECTIONS:
            if section not in content:
                issues.append(ValidationIssue(relative, f"missing required prompt section {section!r}"))
        if "No fabrication" not in content and "не выдум" not in content.lower():
            issues.append(ValidationIssue(relative, "prompt must explicitly forbid fabrication"))
    return issues
