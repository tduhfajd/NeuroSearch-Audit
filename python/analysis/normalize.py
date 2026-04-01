from __future__ import annotations

from python.analysis.contracts import (
    EntitiesDocument,
    Entity,
    FactsDocument,
    NormalizedFact,
    SourceEvidence,
)


SCHEMA_VERSION = "1.0.0"


def entity_id_for(audit_id: str, url: str) -> str:
    slug = (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace(":", "_")
    )
    return f"{audit_id}:page:{slug}"


def normalize_page_blocks(document: dict) -> tuple[EntitiesDocument, FactsDocument]:
    audit_id = document["audit_id"]
    url = document["url"]
    page_type = document["page_type"]
    entity_id = entity_id_for(audit_id, url)

    entity = Entity(
        entity_id=entity_id,
        type="page",
        label=url,
        attributes={"page_type": page_type},
        source_urls=[url],
    )

    facts: list[NormalizedFact] = [
        NormalizedFact(
            fact_id=f"{entity_id}:page_type",
            entity_id=entity_id,
            fact_type="page_type",
            value=page_type,
            evidence=[SourceEvidence(source_url=url, field="page_type")],
        )
    ]

    for block in document.get("blocks", []):
        facts.append(
            NormalizedFact(
                fact_id=f"{entity_id}:block:{block['type']}",
                entity_id=entity_id,
                fact_type="block_presence",
                value=f"{block['type']}:{str(block['present']).lower()}",
                evidence=[
                    SourceEvidence(
                        source_url=item["source_url"],
                        field=item["field"],
                    )
                    for item in block.get("evidence", [])
                ],
            )
        )

    for index, item in enumerate(document.get("facts", []), start=1):
        facts.append(
            NormalizedFact(
                fact_id=f"{entity_id}:{item['fact_type']}:{index:02d}",
                entity_id=entity_id,
                fact_type=item["fact_type"],
                value=item["value"],
                evidence=[
                    SourceEvidence(
                        source_url=evidence["source_url"],
                        field=evidence["field"],
                    )
                    for evidence in item.get("evidence", [])
                ],
            )
        )

    return (
        EntitiesDocument(schema_version=SCHEMA_VERSION, audit_id=audit_id, entities=[entity]),
        FactsDocument(schema_version=SCHEMA_VERSION, audit_id=audit_id, facts=facts),
    )
