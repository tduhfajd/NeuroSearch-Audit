from __future__ import annotations

from dataclasses import dataclass, field

from python.analysis.contracts import NormalizedFact, SourceEvidence


SCHEMA_VERSION = "1.0.0"
RULESET_VERSION = "mvp-1"

PAGE_RULES = {
    "service": {
        "required": ("definition", "service_scope", "process_steps", "terms", "proof", "pricing", "faq", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("definition", "service_scope", "pricing", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("SEO", "AIO", "conversion"),
    },
    "about": {
        "required": ("definition", "proof", "contacts", "legal_trust", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("definition", "contacts", "legal_trust", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "lead_quality", "SEO"),
    },
    "careers": {
        "required": ("definition", "contacts", "legal_trust", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("definition", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "SEO"),
    },
    "pricing": {
        "required": ("definition", "pricing", "terms", "contacts", "service_scope", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("pricing", "terms", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("conversion", "trust", "lead_quality"),
    },
    "case_study": {
        "required": ("definition", "proof", "service_scope", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("proof", "service_scope", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion", "lead_quality"),
    },
    "portfolio": {
        "required": ("definition", "proof", "service_scope", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("proof", "service_scope", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion", "lead_quality"),
    },
    "product": {
        "required": ("definition", "specs", "pricing", "terms", "proof", "payment_options", "availability", "fulfillment"),
        "critical": ("specs", "pricing", "terms", "availability", "fulfillment"),
        "impact": ("conversion", "trust", "SEO"),
    },
    "category": {
        "required": ("definition", "specs", "pricing", "proof", "payment_options", "availability"),
        "critical": ("definition", "pricing", "availability"),
        "impact": ("conversion", "SEO", "merchandising"),
    },
    "homepage": {
        "required": ("definition", "contacts", "proof", "messengers", "legal_trust", "service_scope", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("definition", "contacts", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion", "SEO"),
    },
    "contacts": {
        "required": ("contacts", "messengers", "legal_trust", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("contacts", "messengers", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion"),
    },
    "delivery": {
        "required": ("process_steps", "pricing", "terms", "contacts", "payment_options", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("terms", "contacts", "payment_options", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion", "operations"),
    },
    "return_policy": {
        "required": ("terms", "contacts", "legal_trust", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("terms", "legal_trust", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("trust", "conversion"),
    },
    "wholesale": {
        "required": ("pricing", "contacts", "process_steps", "proof", "legal_trust", "messengers", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "critical": ("pricing", "contacts", "legal_trust", "fulfillment", "secure_protocol", "strict_transport_security", "mixed_content_safe"),
        "impact": ("conversion", "lead_quality", "trust"),
    },
    "article": {
        "required": ("definition", "proof"),
        "critical": ("definition",),
        "impact": ("SEO", "AIO"),
    },
    "generic": {
        "required": ("definition",),
        "critical": ("definition",),
        "impact": ("SEO",),
    },
}


def infer_site_profile(entities_payload: dict) -> str:
    counts: dict[str, int] = {}
    for entity in entities_payload.get("entities", []):
        if entity.get("type") != "page":
            continue
        page_type = entity.get("attributes", {}).get("page_type", "generic")
        counts[page_type] = counts.get(page_type, 0) + 1

    commerce_count = sum(counts.get(key, 0) for key in ("product", "category", "delivery", "return_policy", "wholesale"))
    service_count = sum(counts.get(key, 0) for key in ("service", "homepage", "contacts", "about", "pricing", "case_study", "portfolio", "careers"))
    if commerce_count >= 4 and commerce_count >= service_count:
        return "ecommerce"
    if service_count > 0 and counts.get("product", 0) == 0 and counts.get("category", 0) == 0:
        return "service"
    return "mixed"


def page_rule(page_type: str) -> dict[str, tuple[str, ...]]:
    return PAGE_RULES.get(page_type, PAGE_RULES["generic"])


def impact_for(site_profile: str, page_type: str) -> list[str]:
    impact = list(page_rule(page_type)["impact"])
    if site_profile == "ecommerce" and page_type in {"product", "category", "delivery", "return_policy", "wholesale"}:
        if "trust" not in impact:
            impact.append("trust")
        if page_type in {"delivery", "return_policy", "wholesale"} and "operations" not in impact:
            impact.append("operations")
        if page_type in {"product", "category"} and "merchandising" not in impact:
            impact.append("merchandising")
    if site_profile == "service" and page_type in {"service", "homepage", "contacts", "about", "pricing", "case_study", "portfolio", "careers"}:
        if "lead_quality" not in impact:
            impact.append("lead_quality")
        if page_type in {"service", "homepage", "pricing"} and "operations" not in impact:
            impact.append("operations")
    return impact


def priority_for(page_type: str, missing: list[str], required: tuple[str, ...], site_profile: str) -> str:
    if not missing:
        return "P2"

    if page_type == "careers":
        return "P1"

    critical = set(page_rule(page_type)["critical"])
    missing_critical = critical.intersection(missing)
    commerce_critical_pages = {"product", "category", "delivery", "return_policy", "wholesale"}
    always_business_critical_pages = {"service", "homepage", "contacts", "pricing", "case_study", "portfolio", "product", "delivery", "return_policy", "wholesale"}
    if missing_critical:
        if page_type in always_business_critical_pages:
            return "P0"
        if site_profile == "ecommerce" and page_type in commerce_critical_pages:
            return "P0"

    if len(missing) >= max(1, len(required) // 2):
        return "P0"
    return "P1"


@dataclass(slots=True)
class CoverageItem:
    target: str
    coverage_score: float
    missing: list[str]
    priority: str
    impact: list[str]
    evidence: list[SourceEvidence] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "target": self.target,
            "coverage_score": self.coverage_score,
            "missing": self.missing,
            "priority": self.priority,
            "impact": self.impact,
            "evidence": [
                {
                    "source_url": item.source_url,
                    "field": item.field,
                }
                for item in self.evidence
            ],
        }


@dataclass(slots=True)
class CoverageReport:
    schema_version: str
    audit_id: str
    coverage_ruleset: str
    items: list[CoverageItem]
    summary: dict[str, int]

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "coverage_ruleset": self.coverage_ruleset,
            "items": [item.to_json() for item in self.items],
            "summary": self.summary,
        }


@dataclass(slots=True)
class Contradiction:
    contradiction_id: str
    entity_id: str
    type: str
    severity: str
    sources: list[str]
    risk: list[str]

    def to_json(self) -> dict:
        return {
            "contradiction_id": self.contradiction_id,
            "entity_id": self.entity_id,
            "type": self.type,
            "severity": self.severity,
            "sources": self.sources,
            "risk": self.risk,
        }


@dataclass(slots=True)
class ContradictionsReport:
    schema_version: str
    audit_id: str
    contradictions: list[Contradiction]

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "contradictions": [item.to_json() for item in self.contradictions],
        }


def build_coverage(audit_id: str, entities_payload: dict, facts_payload: dict) -> CoverageReport:
    items: list[CoverageItem] = []
    site_profile = infer_site_profile(entities_payload)

    facts_by_entity: dict[str, list[NormalizedFact]] = {}
    for fact_payload in facts_payload.get("facts", []):
        fact = NormalizedFact(
            fact_id=fact_payload["fact_id"],
            entity_id=fact_payload["entity_id"],
            fact_type=fact_payload["fact_type"],
            value=fact_payload["value"],
            evidence=[
                SourceEvidence(source_url=item["source_url"], field=item["field"])
                for item in fact_payload.get("evidence", [])
            ],
        )
        facts_by_entity.setdefault(fact.entity_id, []).append(fact)

    for entity in entities_payload.get("entities", []):
        page_type = entity.get("attributes", {}).get("page_type", "generic")
        required = page_rule(page_type)["required"]
        facts = facts_by_entity.get(entity["entity_id"], [])
        present_blocks = {
            fact.value.split(":")[0]
            for fact in facts
            if fact.fact_type == "block_presence" and fact.value.endswith(":true")
        }
        missing = [block for block in required if block not in present_blocks]
        total = len(required)
        score = 1.0 if total == 0 else round((total - len(missing)) / total, 2)
        priority = priority_for(page_type, missing, required, site_profile)
        impact = impact_for(site_profile, page_type) if missing else ["SEO"]
        evidence = []
        if entity.get("source_urls"):
            evidence = [SourceEvidence(source_url=entity["source_urls"][0], field="page_type")]

        items.append(
            CoverageItem(
                target=entity["entity_id"],
                coverage_score=score,
                missing=missing,
                priority=priority,
                impact=impact,
                evidence=evidence,
            )
        )

    summary = {
        "targets": len(items),
        "p0": sum(1 for item in items if item.priority == "P0"),
        "p1": sum(1 for item in items if item.priority == "P1"),
        "p2": sum(1 for item in items if item.priority == "P2"),
    }
    return CoverageReport(
        schema_version=SCHEMA_VERSION,
        audit_id=audit_id,
        coverage_ruleset=RULESET_VERSION,
        items=items,
        summary=summary,
    )


CONTRADICTION_HEURISTICS = {
    "price": {"severity": "high", "risk": ["trust", "conversion", "ai-readiness"]},
    "terms": {"severity": "high", "risk": ["trust", "operations", "ai-readiness"]},
    "timeline": {"severity": "high", "risk": ["trust", "operations", "ai-readiness"]},
    "contact": {"severity": "high", "risk": ["trust", "lead_quality", "ai-readiness"]},
    "contact_phone": {"severity": "high", "risk": ["trust", "lead_quality", "ai-readiness"]},
    "contact_email": {"severity": "high", "risk": ["trust", "lead_quality", "ai-readiness"]},
    "geo": {"severity": "medium", "risk": ["trust", "operations", "ai-readiness"]},
}


def contradiction_heuristic(fact_type: str) -> dict[str, list[str] | str]:
    return CONTRADICTION_HEURISTICS.get(
        fact_type,
        {"severity": "medium", "risk": ["trust", "ai-readiness"]},
    )


def build_contradictions(audit_id: str, entities_payload: dict, facts_payload: dict) -> ContradictionsReport:
    grouped: dict[tuple[str, str], list[dict]] = {}
    sitewide_grouped: dict[str, list[dict]] = {}
    entity_page_types = {
        entity["entity_id"]: entity.get("attributes", {}).get("page_type", "generic")
        for entity in entities_payload.get("entities", [])
    }
    contact_priority_page_types = {"homepage", "service", "about", "pricing", "case_study", "portfolio", "contacts", "delivery", "return_policy", "wholesale"}
    commercial_priority_page_types = {"homepage", "service", "about", "pricing", "case_study", "portfolio", "product", "category", "delivery", "return_policy", "wholesale", "contacts"}
    for fact in facts_payload.get("facts", []):
        fact_type = fact["fact_type"]
        if fact_type in {"price", "terms", "timeline", "geo"}:
            grouped.setdefault((fact["entity_id"], fact_type), []).append(fact)
            if entity_page_types.get(fact["entity_id"], "generic") in commercial_priority_page_types:
                sitewide_grouped.setdefault(fact_type, []).append(fact)
            continue
        if fact_type in {"contact", "contact_phone", "contact_email"}:
            if entity_page_types.get(fact["entity_id"], "generic") not in contact_priority_page_types:
                continue
            sitewide_grouped.setdefault(fact_type, []).append(fact)
            continue

    contradictions: list[Contradiction] = []
    for (entity_id, fact_type), facts in grouped.items():
        values = {fact["value"] for fact in facts}
        if len(values) < 2:
            continue

        source_urls = sorted(
            {
                item["source_url"]
                for fact in facts
                for item in fact.get("evidence", [])
            }
        )
        if len(source_urls) < 2:
            continue

        contradiction_type = f"{fact_type}_conflict"
        heuristic = contradiction_heuristic(fact_type)
        contradictions.append(
            Contradiction(
                contradiction_id=f"{entity_id}:{contradiction_type}",
                entity_id=entity_id,
                type=contradiction_type,
                severity=str(heuristic["severity"]),
                sources=source_urls,
                risk=list(heuristic["risk"]),
            )
        )

    site_entity_id = f"{audit_id}:site"
    for fact_type, facts in sitewide_grouped.items():
        values = {fact["value"] for fact in facts}
        if len(values) < 2:
            continue

        entity_ids = {fact["entity_id"] for fact in facts}
        if len(entity_ids) < 2:
            continue

        source_urls = sorted(
            {
                item["source_url"]
                for fact in facts
                for item in fact.get("evidence", [])
            }
        )
        if len(source_urls) < 2:
            continue

        contradiction_type = f"{fact_type}_conflict"
        heuristic = contradiction_heuristic(fact_type)
        contradictions.append(
            Contradiction(
                contradiction_id=f"{site_entity_id}:{contradiction_type}",
                entity_id=site_entity_id,
                type=contradiction_type,
                severity=str(heuristic["severity"]),
                sources=source_urls,
                risk=list(heuristic["risk"]),
            )
        )

    return ContradictionsReport(
        schema_version=SCHEMA_VERSION,
        audit_id=audit_id,
        contradictions=contradictions,
    )
