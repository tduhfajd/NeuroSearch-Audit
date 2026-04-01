from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(slots=True)
class TechnicalPageInput:
    audit_id: str
    url: str
    source: str
    title: str = ""
    description: str = ""
    canonical_url: str = ""
    robots: str = ""
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    schema_hints: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    messenger_hints: list[str] = field(default_factory=list)
    payment_hints: list[str] = field(default_factory=list)
    legal_hints: list[str] = field(default_factory=list)
    price_hints: list[str] = field(default_factory=list)
    timeline_hints: list[str] = field(default_factory=list)
    geo_hints: list[str] = field(default_factory=list)
    offer_terms: list[str] = field(default_factory=list)
    strict_transport_security: str = ""
    mixed_content_urls: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, payload: dict) -> "TechnicalPageInput":
        return cls(
            audit_id=payload["audit_id"],
            url=payload["url"],
            source=payload["source"],
            title=payload.get("title", ""),
            description=payload.get("meta", {}).get("description", ""),
            canonical_url=payload.get("canonical_url", ""),
            robots=payload.get("robots", ""),
            h1=payload.get("headings", {}).get("h1", []),
            h2=payload.get("headings", {}).get("h2", []),
            schema_hints=payload.get("schema_hints", []),
            phones=payload.get("runet_signals", {}).get("phones", []),
            emails=payload.get("runet_signals", {}).get("emails", []),
            messenger_hints=payload.get("runet_signals", {}).get("messenger_hints", []),
            payment_hints=payload.get("runet_signals", {}).get("payment_hints", []),
            legal_hints=payload.get("runet_signals", {}).get("legal_hints", []),
            price_hints=payload.get("commercial_signals", {}).get("price_hints", []),
            timeline_hints=payload.get("commercial_signals", {}).get("timeline_hints", []),
            geo_hints=payload.get("commercial_signals", {}).get("geo_hints", []),
            offer_terms=payload.get("commercial_signals", {}).get("offer_terms", []),
            strict_transport_security=payload.get("transport_signals", {}).get("strict_transport_security", ""),
            mixed_content_urls=payload.get("transport_signals", {}).get("mixed_content_urls", []),
        )


@dataclass(slots=True)
class BlockEvidence:
    source_url: str
    field: str


@dataclass(slots=True)
class PageFact:
    fact_type: str
    value: str
    evidence: list[BlockEvidence] = field(default_factory=list)


@dataclass(slots=True)
class PageBlock:
    type: str
    present: bool
    confidence: float
    evidence: list[BlockEvidence] = field(default_factory=list)


@dataclass(slots=True)
class PageBlocksDocument:
    schema_version: str
    audit_id: str
    url: str
    page_type: str
    blocks: list[PageBlock]
    facts: list[PageFact]
    updated_at: str

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "url": self.url,
            "page_type": self.page_type,
            "blocks": [
                {
                    "type": block.type,
                    "present": block.present,
                    "confidence": block.confidence,
                    "evidence": [
                        {
                            "source_url": evidence.source_url,
                            "field": evidence.field,
                        }
                        for evidence in block.evidence
                    ],
                }
                for block in self.blocks
            ],
            "facts": [
                {
                    "fact_type": fact.fact_type,
                    "value": fact.value,
                    "evidence": [
                        {
                            "source_url": evidence.source_url,
                            "field": evidence.field,
                        }
                        for evidence in fact.evidence
                    ],
                }
                for fact in self.facts
            ],
            "updated_at": self.updated_at,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
