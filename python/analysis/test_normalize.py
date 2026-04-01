from __future__ import annotations

from python.analysis.normalize import normalize_page_blocks


def test_normalize_page_blocks_emits_factual_signals() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/service",
        "page_type": "service",
        "blocks": [
            {
                "type": "contacts",
                "present": True,
                "confidence": 0.9,
                "evidence": [{"source_url": "https://example.com/service", "field": "runet_signals.phones"}],
            }
        ],
        "facts": [
            {
                "fact_type": "contact_phone",
                "value": "+7 999 000-00-00",
                "evidence": [{"source_url": "https://example.com/service", "field": "runet_signals.phones"}],
            },
            {
                "fact_type": "payment_option",
                "value": "visa",
                "evidence": [{"source_url": "https://example.com/service", "field": "runet_signals.payment_hints"}],
            },
            {
                "fact_type": "price",
                "value": "25 000 руб.",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.price_hints"}],
            },
            {
                "fact_type": "timeline",
                "value": "5 дней",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.timeline_hints"}],
            },
            {
                "fact_type": "geo",
                "value": "по россии",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.geo_hints"}],
            },
            {
                "fact_type": "terms",
                "value": "по договору",
                "evidence": [{"source_url": "https://example.com/service", "field": "commercial_signals.offer_terms"}],
            },
        ],
        "updated_at": "2026-03-13T12:00:00Z",
    }

    _, facts = normalize_page_blocks(payload)
    data = facts.to_json()
    facts_by_type = {(item["fact_type"], item["value"]) for item in data["facts"]}

    assert ("page_type", "service") in facts_by_type
    assert ("block_presence", "contacts:true") in facts_by_type
    assert ("contact_phone", "+7 999 000-00-00") in facts_by_type
    assert ("payment_option", "visa") in facts_by_type
    assert ("price", "25 000 руб.") in facts_by_type
    assert ("timeline", "5 дней") in facts_by_type
    assert ("geo", "по россии") in facts_by_type
    assert ("terms", "по договору") in facts_by_type
