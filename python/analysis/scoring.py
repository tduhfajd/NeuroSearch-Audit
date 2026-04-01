from __future__ import annotations

from dataclasses import dataclass, field


SCHEMA_VERSION = "1.0.0"
RULESET_VERSION = "mvp-1"


@dataclass(slots=True)
class PageScores:
    url: str
    scores: dict[str, float]
    factors: dict[str, float]

    def to_json(self) -> dict:
        return {
            "url": self.url,
            "scores": self.scores,
            "factors": self.factors,
        }


@dataclass(slots=True)
class ScoreDocument:
    schema_version: str
    audit_id: str
    ruleset_version: str
    page_scores: list[PageScores]
    entity_scores: list[dict]
    top_gaps: list[str]
    lead_value_index: float

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "ruleset_version": self.ruleset_version,
            "page_scores": [item.to_json() for item in self.page_scores],
            "entity_scores": self.entity_scores,
            "top_gaps": self.top_gaps,
            "lead_value_index": self.lead_value_index,
        }


@dataclass(slots=True)
class Recommendation:
    recommendation_id: str
    related_findings: list[str]
    priority: str
    effort: str
    expected_impact: str
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "related_findings": self.related_findings,
            "priority": self.priority,
            "effort": self.effort,
            "expected_impact": self.expected_impact,
            "acceptance_criteria": self.acceptance_criteria,
        }


@dataclass(slots=True)
class RecommendationsDocument:
    schema_version: str
    audit_id: str
    recommendations: list[Recommendation]

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "recommendations": [item.to_json() for item in self.recommendations],
        }


def _round(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def build_scores(audit_id: str, entities_payload: dict, coverage_payload: dict, contradictions_payload: dict) -> ScoreDocument:
    contradiction_weight = 0.0
    for contradiction in contradictions_payload.get("contradictions", []):
        severity = contradiction["severity"]
        contradiction_weight += {"high": 0.3, "medium": 0.2, "low": 0.1}.get(severity, 0.0)

    page_scores: list[PageScores] = []
    top_gaps: list[str] = []

    entity_lookup = {entity["entity_id"]: entity for entity in entities_payload.get("entities", [])}
    p0_count = 0
    p1_count = 0
    high_contradictions = sum(1 for item in contradictions_payload.get("contradictions", []) if item["severity"] == "high")

    for item in coverage_payload.get("items", []):
        entity = entity_lookup.get(item["target"], {})
        url = entity.get("source_urls", ["unknown"])[0]
        score = item["coverage_score"]
        factors = {
            "entity_coverage_score": score,
            "contradiction_penalty": contradiction_weight,
        }
        scores = {
            "SEO": _round(score),
            "GEO": _round(score - contradiction_weight / 2),
            "AEO": _round(score),
            "AIO": _round(score - contradiction_weight),
            "LEO": _round(score - contradiction_weight / 3),
        }
        page_scores.append(PageScores(url=url, scores=scores, factors=factors))
        top_gaps.extend(item.get("missing", []))
        if item["priority"] == "P0":
            p0_count += 1
        elif item["priority"] == "P1":
            p1_count += 1

    lead_value_index = round((0.4 * p0_count) + (0.2 * p1_count) + (0.3 * high_contradictions) + (0.1 * len(page_scores)), 2)

    return ScoreDocument(
        schema_version=SCHEMA_VERSION,
        audit_id=audit_id,
        ruleset_version=RULESET_VERSION,
        page_scores=page_scores,
        entity_scores=[],
        top_gaps=sorted(set(top_gaps)),
        lead_value_index=lead_value_index,
    )


def build_recommendations(audit_id: str, coverage_payload: dict, contradictions_payload: dict) -> RecommendationsDocument:
    recommendations: list[Recommendation] = []
    transport_gaps = {"secure_protocol", "strict_transport_security", "mixed_content_safe"}

    for item in coverage_payload.get("items", []):
        if not item.get("missing"):
            continue
        acceptance_criteria = [f"Add or verify blocks: {', '.join(item['missing'])}"]
        if any(gap in item["missing"] for gap in transport_gaps):
            acceptance_criteria = [
                "Redirect all http URLs to https with a permanent 301/308 response",
                "Set canonical URLs to the https version only",
                "Ensure sitemap and internal links point to https URLs",
                "Enable Strict-Transport-Security on HTTPS responses",
                "Remove http:// asset, script, stylesheet, and media references from HTTPS pages",
            ] + acceptance_criteria
        recommendations.append(
            Recommendation(
                recommendation_id=f"{item['target']}:coverage",
                related_findings=[item["target"]],
                priority=item["priority"],
                effort="medium" if len(item["missing"]) > 2 else "small",
                expected_impact="Improve protocol trust, canonical consistency, and readiness signals"
                if any(gap in item["missing"] for gap in transport_gaps)
                else "Improve content completeness and readiness signals",
                acceptance_criteria=acceptance_criteria + ([] if any(gap in item["missing"] for gap in transport_gaps) else ["Each new block includes source-backed content and evidence links"]),
            )
        )

    for contradiction in contradictions_payload.get("contradictions", []):
        contradiction_type = contradiction["type"]
        acceptance_criteria = [
            "Unify the contradictory fact across all affected URLs",
            "Document the canonical source of truth for the resolved value",
        ]
        expected_impact = "Remove conflicting facts that reduce trust and AI readiness"
        if contradiction_type in {"contact_conflict", "contact_phone_conflict", "contact_email_conflict"}:
            acceptance_criteria = [
                "Choose one canonical contact value for the affected site section",
                "Update header, footer, contact pages, and conversion points to the same value",
                "Repeat the audit and confirm the contact contradiction no longer appears",
            ]
            expected_impact = "Remove conflicting contact data that reduces trust and lead quality"
        elif contradiction_type == "price_conflict":
            acceptance_criteria = [
                "Choose one canonical price or price range for the affected offer",
                "Align service pages, landing pages, category pages, and commercial blocks to the same price statement",
                "Clarify whether the published values refer to different packages, scopes, or starting prices",
                "Repeat the audit and confirm the price contradiction no longer appears",
            ]
            expected_impact = "Remove conflicting pricing signals that reduce trust and conversion clarity"
        elif contradiction_type == "timeline_conflict":
            acceptance_criteria = [
                "Choose one canonical timeline or explain the valid timeline variants for the offer",
                "Align service pages, FAQ blocks, and commercial pages to the same timeline statement",
                "Document which timeline applies to each package or scope if multiple timelines are valid",
                "Repeat the audit and confirm the timeline contradiction no longer appears",
            ]
            expected_impact = "Remove conflicting delivery or production timelines that reduce trust and operational clarity"
        elif contradiction_type == "terms_conflict":
            acceptance_criteria = [
                "Align the conflicting terms or policy statement across all affected URLs",
                "Document the approved canonical wording for delivery, return, or policy terms",
                "Repeat the audit and confirm the contradiction no longer appears",
            ]
            expected_impact = "Remove conflicting policy data that reduces trust and operational clarity"
        elif contradiction_type == "geo_conflict":
            acceptance_criteria = [
                "Choose one canonical geography or service area statement for the affected offer",
                "Align service pages, contact pages, and commercial pages to the same geography statement",
                "Clarify whether the differences describe separate branches, markets, or delivery zones",
                "Repeat the audit and confirm the geography contradiction no longer appears",
            ]
            expected_impact = "Remove conflicting geography claims that reduce trust and operational predictability"
        recommendations.append(
            Recommendation(
                recommendation_id=f"{contradiction['contradiction_id']}:resolve",
                related_findings=[contradiction["contradiction_id"]],
                priority="P0" if contradiction["severity"] == "high" else "P1",
                effort="medium",
                expected_impact=expected_impact,
                acceptance_criteria=acceptance_criteria,
            )
        )

    return RecommendationsDocument(
        schema_version=SCHEMA_VERSION,
        audit_id=audit_id,
        recommendations=recommendations,
    )
