from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SemanticHandoff:
    technical_artifact: str
    rendered_artifact: str | None = None


SEMANTIC_BLOCK_TYPES = (
    "definition",
    "process_steps",
    "pricing",
    "faq",
    "proof",
    "terms",
    "contacts",
    "messengers",
    "payment_options",
    "legal_trust",
    "secure_protocol",
    "strict_transport_security",
    "mixed_content_safe",
    "availability",
    "service_scope",
    "fulfillment",
    "comparison",
)
