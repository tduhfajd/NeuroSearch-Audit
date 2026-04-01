from __future__ import annotations

from python.analysis.findings import build_contradictions, build_coverage
from python.analysis.scoring import build_recommendations


def test_build_coverage_uses_runet_blocks_for_contacts_page() -> None:
    audit_id = "aud_20260311T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "type": "page",
                "label": "https://example.com/kontakty",
                "attributes": {"page_type": "contacts"},
                "source_urls": ["https://example.com/kontakty"],
            }
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:messengers",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "messengers:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "runet_signals.messenger_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:legal_trust",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "legal_trust:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "runet_signals.legal_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:secure_protocol",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "secure_protocol:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "canonical_url"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:strict_transport_security",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "strict_transport_security:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "transport_signals.strict_transport_security"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:block:mixed_content_safe",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "block_presence",
                "value": "mixed_content_safe:true",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "transport_signals.mixed_content_urls"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    item = report["items"][0]

    assert item["coverage_score"] == 1.0
    assert item["missing"] == []
    assert item["priority"] == "P2"


def test_build_coverage_marks_ru_trust_gaps_on_wholesale_page() -> None:
    audit_id = "aud_20260311T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_wholesale",
                "type": "page",
                "label": "https://example.com/optovym-klientam",
                "attributes": {"page_type": "wholesale"},
                "source_urls": ["https://example.com/optovym-klientam"],
            }
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_wholesale:block:pricing",
                "entity_id": f"{audit_id}:page:example.com_wholesale",
                "fact_type": "block_presence",
                "value": "pricing:true",
                "evidence": [{"source_url": "https://example.com/optovym-klientam", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_wholesale:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_wholesale",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "https://example.com/optovym-klientam", "field": "runet_signals.phones"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    item = report["items"][0]

    assert "legal_trust" in item["missing"]
    assert "messengers" in item["missing"]
    assert item["priority"] == "P0"


def test_build_coverage_uses_deeper_service_and_commerce_expectations() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_service",
                "type": "page",
                "label": "https://example.com/service",
                "attributes": {"page_type": "service"},
                "source_urls": ["https://example.com/service"],
            },
            {
                "entity_id": f"{audit_id}:page:example.com_product",
                "type": "page",
                "label": "https://example.com/product/1",
                "attributes": {"page_type": "product"},
                "source_urls": ["https://example.com/product/1"],
            },
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_service:block:definition",
                "entity_id": f"{audit_id}:page:example.com_service",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/service", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_service:block:pricing",
                "entity_id": f"{audit_id}:page:example.com_service",
                "fact_type": "block_presence",
                "value": "pricing:true",
                "evidence": [{"source_url": "https://example.com/service", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_service:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_service",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "https://example.com/service", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_product:block:definition",
                "entity_id": f"{audit_id}:page:example.com_product",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/product/1", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_product:block:specs",
                "entity_id": f"{audit_id}:page:example.com_product",
                "fact_type": "block_presence",
                "value": "specs:true",
                "evidence": [{"source_url": "https://example.com/product/1", "field": "headings.h1"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_product:block:pricing",
                "entity_id": f"{audit_id}:page:example.com_product",
                "fact_type": "block_presence",
                "value": "pricing:true",
                "evidence": [{"source_url": "https://example.com/product/1", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_product:block:terms",
                "entity_id": f"{audit_id}:page:example.com_product",
                "fact_type": "block_presence",
                "value": "terms:true",
                "evidence": [{"source_url": "https://example.com/product/1", "field": "runet_signals.legal_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_product:block:payment_options",
                "entity_id": f"{audit_id}:page:example.com_product",
                "fact_type": "block_presence",
                "value": "payment_options:true",
                "evidence": [{"source_url": "https://example.com/product/1", "field": "runet_signals.payment_hints"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    items = {item["target"]: item for item in report["items"]}

    service_item = items[f"{audit_id}:page:example.com_service"]
    product_item = items[f"{audit_id}:page:example.com_product"]

    assert "service_scope" in service_item["missing"]
    assert service_item["priority"] == "P0"
    assert "availability" in product_item["missing"]
    assert "fulfillment" in product_item["missing"]
    assert product_item["priority"] == "P0"


def test_build_coverage_supports_refined_service_company_page_types() -> None:
    audit_id = "aud_20260313T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_about",
                "type": "page",
                "label": "https://example.com/o-kompanii",
                "attributes": {"page_type": "about"},
                "source_urls": ["https://example.com/o-kompanii"],
            },
            {
                "entity_id": f"{audit_id}:page:example.com_pricing",
                "type": "page",
                "label": "https://example.com/czeny",
                "attributes": {"page_type": "pricing"},
                "source_urls": ["https://example.com/czeny"],
            },
            {
                "entity_id": f"{audit_id}:page:example.com_case",
                "type": "page",
                "label": "https://example.com/case/launch",
                "attributes": {"page_type": "case_study"},
                "source_urls": ["https://example.com/case/launch"],
            },
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_about:block:definition",
                "entity_id": f"{audit_id}:page:example.com_about",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/o-kompanii", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_about:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_about",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "https://example.com/o-kompanii", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_pricing:block:definition",
                "entity_id": f"{audit_id}:page:example.com_pricing",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/czeny", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_pricing:block:pricing",
                "entity_id": f"{audit_id}:page:example.com_pricing",
                "fact_type": "block_presence",
                "value": "pricing:true",
                "evidence": [{"source_url": "https://example.com/czeny", "field": "commercial_signals.price_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_case:block:definition",
                "entity_id": f"{audit_id}:page:example.com_case",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/case/launch", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_case:block:proof",
                "entity_id": f"{audit_id}:page:example.com_case",
                "fact_type": "block_presence",
                "value": "proof:true",
                "evidence": [{"source_url": "https://example.com/case/launch", "field": "title"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    items = {item["target"]: item for item in report["items"]}

    assert "legal_trust" in items[f"{audit_id}:page:example.com_about"]["missing"]
    assert "terms" in items[f"{audit_id}:page:example.com_pricing"]["missing"]
    assert "service_scope" in items[f"{audit_id}:page:example.com_case"]["missing"]
    assert items[f"{audit_id}:page:example.com_pricing"]["priority"] == "P0"
    assert items[f"{audit_id}:page:example.com_case"]["priority"] == "P0"


def test_build_coverage_treats_careers_as_supportive_not_core_service_page() -> None:
    audit_id = "aud_20260313T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_careers",
                "type": "page",
                "label": "https://example.com/karera-v-kompanii",
                "attributes": {"page_type": "careers"},
                "source_urls": ["https://example.com/karera-v-kompanii"],
            }
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_careers:block:definition",
                "entity_id": f"{audit_id}:page:example.com_careers",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "https://example.com/karera-v-kompanii", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_careers:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_careers",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "https://example.com/karera-v-kompanii", "field": "runet_signals.phones"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    item = report["items"][0]

    assert "legal_trust" in item["missing"]
    assert item["priority"] == "P1"


def test_build_contradictions_uses_domain_specific_trust_risk() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:contact:one",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "contact",
                "value": "+79990000001",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_delivery:contact:two",
                "entity_id": f"{audit_id}:page:example.com_delivery",
                "fact_type": "contact",
                "value": "+79990000002",
                "evidence": [{"source_url": "https://example.com/delivery", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_delivery:timeline:one",
                "entity_id": f"{audit_id}:page:example.com_delivery",
                "fact_type": "timeline",
                "value": "1 day",
                "evidence": [{"source_url": "https://example.com/delivery", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_delivery:timeline:two",
                "entity_id": f"{audit_id}:page:example.com_delivery",
                "fact_type": "timeline",
                "value": "5 days",
                "evidence": [{"source_url": "https://example.com/delivery/faq", "field": "schema_hints"}],
            },
        ],
    }

    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {"entity_id": f"{audit_id}:page:example.com_contacts", "type": "page", "label": "https://example.com/kontakty", "attributes": {"page_type": "contacts"}, "source_urls": ["https://example.com/kontakty"]},
            {"entity_id": f"{audit_id}:page:example.com_delivery", "type": "page", "label": "https://example.com/delivery", "attributes": {"page_type": "delivery"}, "source_urls": ["https://example.com/delivery"]},
        ],
    }
    report = build_contradictions(audit_id, entities_payload, facts_payload).to_json()
    contradictions = report["contradictions"]
    contact_conflict = next(item for item in contradictions if item["type"] == "contact_conflict")
    timeline_conflict = next(item for item in contradictions if item["type"] == "timeline_conflict")

    assert contact_conflict["entity_id"] == f"{audit_id}:site"
    assert contact_conflict["severity"] == "high"
    assert "lead_quality" in contact_conflict["risk"]
    assert timeline_conflict["severity"] == "high"
    assert "operations" in timeline_conflict["risk"]


def test_build_contradictions_detects_sitewide_phone_conflict() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_home:contact_phone:one",
                "entity_id": f"{audit_id}:page:example.com_home",
                "fact_type": "contact_phone",
                "value": "+79990000001",
                "evidence": [{"source_url": "https://example.com/", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:contact_phone:two",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "contact_phone",
                "value": "+79990000002",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "runet_signals.phones"}],
            },
        ],
    }

    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {"entity_id": f"{audit_id}:page:example.com_home", "type": "page", "label": "https://example.com/", "attributes": {"page_type": "homepage"}, "source_urls": ["https://example.com/"]},
            {"entity_id": f"{audit_id}:page:example.com_contacts", "type": "page", "label": "https://example.com/kontakty", "attributes": {"page_type": "contacts"}, "source_urls": ["https://example.com/kontakty"]},
        ],
    }
    report = build_contradictions(audit_id, entities_payload, facts_payload).to_json()

    assert report["contradictions"][0]["type"] == "contact_phone_conflict"
    assert report["contradictions"][0]["entity_id"] == f"{audit_id}:site"
    assert "lead_quality" in report["contradictions"][0]["risk"]


def test_build_contradictions_detects_sitewide_price_and_geo_conflicts() -> None:
    audit_id = "aud_20260313T120000Z_abc1234"
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_service:price:one",
                "entity_id": f"{audit_id}:page:example.com_service",
                "fact_type": "price",
                "value": "50 000 ₽",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.price_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_wholesale:price:two",
                "entity_id": f"{audit_id}:page:example.com_wholesale",
                "fact_type": "price",
                "value": "70 000 ₽",
                "evidence": [{"source_url": "https://example.com/opt", "field": "commercial_signals.price_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_service:geo:one",
                "entity_id": f"{audit_id}:page:example.com_service",
                "fact_type": "geo",
                "value": "Москва",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.geo_hints"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_contacts:geo:two",
                "entity_id": f"{audit_id}:page:example.com_contacts",
                "fact_type": "geo",
                "value": "По России",
                "evidence": [{"source_url": "https://example.com/kontakty", "field": "commercial_signals.geo_hints"}],
            },
        ],
    }
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {"entity_id": f"{audit_id}:page:example.com_service", "type": "page", "label": "https://example.com/service", "attributes": {"page_type": "service"}, "source_urls": ["https://example.com/service"]},
            {"entity_id": f"{audit_id}:page:example.com_wholesale", "type": "page", "label": "https://example.com/opt", "attributes": {"page_type": "wholesale"}, "source_urls": ["https://example.com/opt"]},
            {"entity_id": f"{audit_id}:page:example.com_contacts", "type": "page", "label": "https://example.com/kontakty", "attributes": {"page_type": "contacts"}, "source_urls": ["https://example.com/kontakty"]},
        ],
    }

    report = build_contradictions(audit_id, entities_payload, facts_payload).to_json()
    contradictions = {item["type"]: item for item in report["contradictions"]}

    assert contradictions["price_conflict"]["entity_id"] == f"{audit_id}:site"
    assert contradictions["price_conflict"]["severity"] == "high"
    assert "conversion" in contradictions["price_conflict"]["risk"]
    assert contradictions["geo_conflict"]["entity_id"] == f"{audit_id}:site"
    assert contradictions["geo_conflict"]["severity"] == "medium"
    assert "operations" in contradictions["geo_conflict"]["risk"]


def test_build_recommendations_specializes_contact_conflict_resolution() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    coverage_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "coverage_ruleset": "mvp-1",
        "items": [],
        "summary": {"targets": 0, "p0": 0, "p1": 0, "p2": 0},
    }
    contradictions_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "contradictions": [
            {
                "contradiction_id": f"{audit_id}:site:contact_phone_conflict",
                "entity_id": f"{audit_id}:site",
                "type": "contact_phone_conflict",
                "severity": "high",
                "sources": ["https://example.com/", "https://example.com/kontakty"],
                "risk": ["trust", "lead_quality"],
            }
        ],
    }

    report = build_recommendations(audit_id, coverage_payload, contradictions_payload).to_json()
    recommendation = report["recommendations"][0]

    assert recommendation["expected_impact"] == "Remove conflicting contact data that reduces trust and lead quality"
    assert "Choose one canonical contact value for the affected site section" in recommendation["acceptance_criteria"]


def test_build_recommendations_specializes_commercial_conflict_resolution() -> None:
    audit_id = "aud_20260313T120000Z_abc1234"
    coverage_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "coverage_ruleset": "mvp-1",
        "items": [],
        "summary": {"targets": 0, "p0": 0, "p1": 0, "p2": 0},
    }
    contradictions_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "contradictions": [
            {
                "contradiction_id": f"{audit_id}:site:price_conflict",
                "entity_id": f"{audit_id}:site",
                "type": "price_conflict",
                "severity": "high",
                "sources": ["https://example.com/service", "https://example.com/opt"],
                "risk": ["trust", "conversion"],
            },
            {
                "contradiction_id": f"{audit_id}:site:geo_conflict",
                "entity_id": f"{audit_id}:site",
                "type": "geo_conflict",
                "severity": "medium",
                "sources": ["https://example.com/service", "https://example.com/kontakty"],
                "risk": ["trust", "operations"],
            },
        ],
    }

    report = build_recommendations(audit_id, coverage_payload, contradictions_payload).to_json()
    recommendations = {item["related_findings"][0]: item for item in report["recommendations"]}

    price_rec = recommendations[f"{audit_id}:site:price_conflict"]
    geo_rec = recommendations[f"{audit_id}:site:geo_conflict"]

    assert price_rec["expected_impact"] == "Remove conflicting pricing signals that reduce trust and conversion clarity"
    assert "Choose one canonical price or price range for the affected offer" in price_rec["acceptance_criteria"]
    assert geo_rec["expected_impact"] == "Remove conflicting geography claims that reduce trust and operational predictability"
    assert "Choose one canonical geography or service area statement for the affected offer" in geo_rec["acceptance_criteria"]


def test_build_contradictions_ignores_contact_conflicts_on_low_priority_article_pages() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {"entity_id": f"{audit_id}:page:example.com_article_one", "type": "page", "label": "https://example.com/blog/1", "attributes": {"page_type": "article"}, "source_urls": ["https://example.com/blog/1"]},
            {"entity_id": f"{audit_id}:page:example.com_article_two", "type": "page", "label": "https://example.com/blog/2", "attributes": {"page_type": "article"}, "source_urls": ["https://example.com/blog/2"]},
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_article_one:contact_phone:one",
                "entity_id": f"{audit_id}:page:example.com_article_one",
                "fact_type": "contact_phone",
                "value": "+79990000001",
                "evidence": [{"source_url": "https://example.com/blog/1", "field": "runet_signals.phones"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_article_two:contact_phone:two",
                "entity_id": f"{audit_id}:page:example.com_article_two",
                "fact_type": "contact_phone",
                "value": "+79990000002",
                "evidence": [{"source_url": "https://example.com/blog/2", "field": "runet_signals.phones"}],
            },
        ],
    }

    report = build_contradictions(audit_id, entities_payload, facts_payload).to_json()

    assert report["contradictions"] == []


def test_build_coverage_marks_secure_protocol_as_critical_gap() -> None:
    audit_id = "aud_20260312T120000Z_abc1234"
    entities_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "entities": [
            {
                "entity_id": f"{audit_id}:page:example.com_home",
                "type": "page",
                "label": "http://example.com/",
                "attributes": {"page_type": "homepage"},
                "source_urls": ["http://example.com/"],
            }
        ],
    }
    facts_payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "facts": [
            {
                "fact_id": f"{audit_id}:page:example.com_home:block:definition",
                "entity_id": f"{audit_id}:page:example.com_home",
                "fact_type": "block_presence",
                "value": "definition:true",
                "evidence": [{"source_url": "http://example.com/", "field": "title"}],
            },
            {
                "fact_id": f"{audit_id}:page:example.com_home:block:contacts",
                "entity_id": f"{audit_id}:page:example.com_home",
                "fact_type": "block_presence",
                "value": "contacts:true",
                "evidence": [{"source_url": "http://example.com/", "field": "runet_signals.phones"}],
            },
        ],
    }

    report = build_coverage(audit_id, entities_payload, facts_payload).to_json()
    item = report["items"][0]

    assert "secure_protocol" in item["missing"]
    assert "strict_transport_security" in item["missing"]
    assert "mixed_content_safe" in item["missing"]
    assert item["priority"] == "P0"

    recommendations = build_recommendations(audit_id, report, {"schema_version": "1.0.0", "audit_id": audit_id, "contradictions": []}).to_json()
    rec = recommendations["recommendations"][0]
    assert rec["expected_impact"] == "Improve protocol trust, canonical consistency, and readiness signals"
    assert "Redirect all http URLs to https with a permanent 301/308 response" in rec["acceptance_criteria"]
    assert "Enable Strict-Transport-Security on HTTPS responses" in rec["acceptance_criteria"]
    assert "Remove http:// asset, script, stylesheet, and media references from HTTPS pages" in rec["acceptance_criteria"]
