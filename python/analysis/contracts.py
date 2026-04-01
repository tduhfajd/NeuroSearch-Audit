from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SourceEvidence:
    source_url: str
    field: str


@dataclass(slots=True)
class Entity:
    entity_id: str
    type: str
    label: str
    attributes: dict[str, str]
    source_urls: list[str]

    def to_json(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "type": self.type,
            "label": self.label,
            "attributes": self.attributes,
            "source_urls": self.source_urls,
        }


@dataclass(slots=True)
class NormalizedFact:
    fact_id: str
    entity_id: str
    fact_type: str
    value: str
    evidence: list[SourceEvidence] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "entity_id": self.entity_id,
            "fact_type": self.fact_type,
            "value": self.value,
            "evidence": [
                {
                    "source_url": item.source_url,
                    "field": item.field,
                }
                for item in self.evidence
            ],
        }


@dataclass(slots=True)
class EntitiesDocument:
    schema_version: str
    audit_id: str
    entities: list[Entity]

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "entities": [entity.to_json() for entity in self.entities],
        }


@dataclass(slots=True)
class FactsDocument:
    schema_version: str
    audit_id: str
    facts: list[NormalizedFact]

    def to_json(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "facts": [fact.to_json() for fact in self.facts],
        }
