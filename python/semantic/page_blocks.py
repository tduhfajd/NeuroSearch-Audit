from __future__ import annotations

from python.common.contracts import (
    BlockEvidence,
    PageFact,
    PageBlock,
    PageBlocksDocument,
    TechnicalPageInput,
    utc_now_iso,
)
from urllib.parse import urlparse


SCHEMA_VERSION = "1.0.0"


def _path(page: TechnicalPageInput) -> str:
    return urlparse(page.url).path.lower().rstrip("/")


def _title_text(page: TechnicalPageInput) -> str:
    return " ".join([page.title, *page.h1, *page.h2]).lower()


def _combined_text(page: TechnicalPageInput) -> str:
    return " ".join([page.url, page.title, *page.h1, *page.h2]).lower()


def _is_secure_protocol(page: TechnicalPageInput) -> bool:
    page_scheme = urlparse(page.url).scheme.lower()
    canonical = page.canonical_url.strip()
    canonical_scheme = urlparse(canonical).scheme.lower() if canonical else ""
    if page_scheme != "https":
        return False
    if canonical and canonical_scheme and canonical_scheme != "https":
        return False
    return True


def _has_strict_transport_security(page: TechnicalPageInput) -> bool:
    return bool(page.strict_transport_security.strip())


def _is_mixed_content_safe(page: TechnicalPageInput) -> bool:
    return len(page.mixed_content_urls) == 0


def _append_block(
    blocks: list[PageBlock],
    page: TechnicalPageInput,
    block_type: str,
    present: bool,
    confidence: float,
    field: str | None = None,
) -> None:
    evidence = [BlockEvidence(source_url=page.url, field=field)] if present and field else []
    blocks.append(
        PageBlock(
            type=block_type,
            present=present,
            confidence=confidence if present else 0.0,
            evidence=evidence,
        )
    )


def _normalize_text_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(value)
    return normalized


def _append_fact(facts: list[PageFact], page: TechnicalPageInput, fact_type: str, value: str, field: str) -> None:
    normalized = value.strip()
    if not normalized:
        return
    facts.append(
        PageFact(
            fact_type=fact_type,
            value=normalized,
            evidence=[BlockEvidence(source_url=page.url, field=field)],
        )
    )


def _build_page_facts(page: TechnicalPageInput) -> list[PageFact]:
    facts: list[PageFact] = []
    for phone in _normalize_text_values(page.phones):
        _append_fact(facts, page, "contact_phone", phone, "runet_signals.phones")
    for email in _normalize_text_values(page.emails):
        _append_fact(facts, page, "contact_email", email, "runet_signals.emails")
    for messenger in _normalize_text_values(page.messenger_hints):
        _append_fact(facts, page, "messenger", messenger, "runet_signals.messenger_hints")
    for payment in _normalize_text_values(page.payment_hints):
        _append_fact(facts, page, "payment_option", payment, "runet_signals.payment_hints")
    for legal in _normalize_text_values(page.legal_hints):
        _append_fact(facts, page, "legal_hint", legal, "runet_signals.legal_hints")
    for price in _normalize_text_values(page.price_hints):
        _append_fact(facts, page, "price", price, "commercial_signals.price_hints")
    for timeline in _normalize_text_values(page.timeline_hints):
        _append_fact(facts, page, "timeline", timeline, "commercial_signals.timeline_hints")
    for geo in _normalize_text_values(page.geo_hints):
        _append_fact(facts, page, "geo", geo, "commercial_signals.geo_hints")
    for term in _normalize_text_values(page.offer_terms):
        _append_fact(facts, page, "terms", term, "commercial_signals.offer_terms")
    if page.strict_transport_security.strip():
        _append_fact(facts, page, "transport_policy", page.strict_transport_security.strip(), "transport_signals.strict_transport_security")
    return facts


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def infer_page_type(page: TechnicalPageInput) -> str:
    title = _title_text(page)
    path = _path(page)
    combined = _combined_text(page)
    title_and_headings = " ".join([page.title, *page.h1, *page.h2]).lower()
    service_path_tokens = (
        "uslugi",
        "marketing",
        "razrabotka",
        "dizajn",
        "design",
        "prodvizhen",
        "support",
        "podderzh",
        "moderaczi",
        "translyac",
        "digital",
        "servisy",
    )
    service_text_tokens = (
        "услуги",
        "услуга",
        "маркетинг",
        "разработка",
        "дизайн",
        "продвижение",
        "поддержка",
        "модерация",
        "трансляц",
        "digital",
        "service",
        "consulting",
    )
    if path in ("", "/"):
        return "homepage"
    if "/tpost/" in path or "/blog/" in path or _contains_any(title_and_headings, ("новост", "статья", "blog", "article")):
        return "article"
    if _contains_any(path, ("privacy", "policy", "politika-konfidenc", "konfidenc", "privacy-policy")):
        return "return_policy"
    if _contains_any(path, ("karta-sajta", "sitemap")) or _contains_any(title_and_headings, ("карта сайта", "sitemap")):
        return "generic"
    if _contains_any(path, ("akczii", "sale", "promo", "promotions")) or _contains_any(title_and_headings, ("акции", "скидки", "special offer", "promo")):
        return "category"
    if "/kontakty" in path or _contains_any(combined, ("контакты", "contact", "contacts")):
        return "contacts"
    if _contains_any(path, ("karera", "career", "vacancy", "vakans")) or _contains_any(title_and_headings, ("карьера", "ваканс", "career", "jobs")):
        return "careers"
    if _contains_any(path, ("o-kompanii", "about", "company", "kompani", "about-us")) or _contains_any(title_and_headings, ("о компании", "о нас", "about us", "about company", "company profile")):
        return "about"
    if _contains_any(path, ("czeny", "price", "pricing", "tarif")) or _contains_any(title_and_headings, ("цены", "стоимость", "price", "pricing", "тариф")):
        return "pricing"
    if _contains_any(path, ("portfolio", "portfol", "proekty", "projects")) or _contains_any(title_and_headings, ("портфолио", "проекты", "projects", "portfolio")):
        return "portfolio"
    if _contains_any(path, ("case", "kejs", "кейсы")) or _contains_any(title_and_headings, ("кейс", "кейсы", "case study", "success story")):
        return "case_study"
    if "/dostavka" in path or _contains_any(combined, ("доставка", "delivery", "оплата", "shipping")):
        return "delivery"
    if _contains_any(path, ("vozvrat", "garant")) or _contains_any(combined, ("возврат", "обмен", "refund", "return", "гарант", "warranty")):
        return "return_policy"
    if _contains_any(path, ("optov",)) or _contains_any(combined, ("оптов", "wholesale")):
        return "wholesale"
    if "/category/" in path:
        return "category"
    if "/video-obzory" in path or _contains_any(combined, ("обзор", "video review", "review")):
        return "article"
    if _contains_any(path, service_path_tokens):
        return "service"
    if _contains_any(path, ("faq", "czeny", "price", "pricing", "tarif", "o-kompanii", "about", "company")):
        return "service"
    if _contains_any(title_and_headings, ("faq", "вопрос", "цены", "price", "pricing", "тариф", "о компании", "about company", "about us")):
        return "service"
    if _contains_any(title_and_headings, service_text_tokens):
        return "service"
    if path.split("/")[-1].isdigit() or _contains_any(combined, ("купить", "товар", "product")):
        return "product"
    return "generic"


def build_page_blocks(page: TechnicalPageInput) -> PageBlocksDocument:
    blocks: list[PageBlock] = []
    facts = _build_page_facts(page)
    combined = _combined_text(page)
    page_type = infer_page_type(page)
    contact_page_types = {"homepage", "service", "contacts", "about", "pricing", "case_study", "portfolio", "delivery", "return_policy", "wholesale"}
    payment_page_types = {"homepage", "service", "pricing", "product", "category", "delivery", "wholesale"}
    legal_page_types = {"homepage", "service", "about", "pricing", "contacts", "delivery", "return_policy", "wholesale", "careers"}
    commerce_page_types = {"product", "category", "delivery", "return_policy", "wholesale"}
    service_page_types = {"homepage", "service", "about", "pricing", "contacts", "case_study", "portfolio"}
    has_contact_text = _contains_any(combined, ("контакты", "contact", "contacts", "телефон", "whatsapp", "email"))
    has_payment_text = _contains_any(combined, ("купить", "цена", "price", "оплата", "стоимость"))
    has_legal_text = _contains_any(combined, ("доставка", "возврат", "обмен", "услов", "terms", "shipping", "refund"))
    has_availability_text = _contains_any(combined, ("в наличии", "наличие", "stock", "available", "заказ"))
    has_service_scope_text = _contains_any(combined, ("услуга", "service", "подбор", "монтаж", "консультац", "what we do"))
    has_fulfillment_text = _contains_any(combined, ("доставка", "shipping", "получение", "срок", "pickup", "выдач", "возврат"))
    has_faq_text = _contains_any(combined, ("faq", "частые вопросы", "вопросы и ответы", "вопрос-ответ", "questions", "q&a"))
    has_process_text = _contains_any(combined, ("этап", "этапы", "как работаем", "workflow", "процесс", "шаг"))
    has_proof_text = _contains_any(combined, ("отзывы", "review", "обзор", "rating", "кейс", "кейсы", "клиент", "клиенты", "портфолио", "проект", "проекты", "лет на рынке", "нам доверяют"))
    has_price_fact = bool(page.price_hints)
    has_timeline_fact = bool(page.timeline_hints)
    has_geo_fact = bool(page.geo_hints)
    has_terms_fact = bool(page.offer_terms)
    has_contacts = has_contact_text or (page_type in contact_page_types and bool(page.phones or page.emails))
    has_messengers = page_type in contact_page_types and bool(page.messenger_hints)
    has_payment = has_payment_text or (page_type in payment_page_types and bool(page.payment_hints))
    has_legal = has_legal_text or (page_type in legal_page_types and bool(page.legal_hints))

    if page.title or page.description or page.h1:
        _append_block(
            blocks,
            page,
            "definition",
            True,
            0.8,
            "title" if page.title else "headings.h1",
        )
    else:
        _append_block(blocks, page, "definition", False, 0.0)

    _append_block(
        blocks,
        page,
        "faq",
        "faqpage" in page.schema_hints or has_faq_text,
        0.9 if "faqpage" in page.schema_hints else 0.7 if has_faq_text else 0.0,
        "schema_hints" if "faqpage" in page.schema_hints else "title" if has_faq_text else None,
    )

    _append_block(
        blocks,
        page,
        "process_steps",
        len(page.h2) >= 2 or page_type == "delivery" or has_process_text or has_timeline_fact,
        0.8 if page_type == "delivery" or has_process_text else 0.7 if len(page.h2) >= 2 else 0.6 if has_timeline_fact else 0.2,
        "title" if has_process_text else "commercial_signals.timeline_hints" if has_timeline_fact else "headings.h2" if page.h2 else "url",
    )

    _append_block(
        blocks,
        page,
        "contacts",
        has_contacts,
        0.9 if page_type in contact_page_types and (page.phones or page.emails) else 0.7 if _contains_any(combined, ("контакты", "contact", "contacts")) else 0.4,
        "runet_signals.phones" if page.phones else "runet_signals.emails" if page.emails else "url",
    )

    _append_block(
        blocks,
        page,
        "pricing",
        has_payment or has_price_fact,
        0.9 if has_price_fact else 0.8 if _contains_any(combined, ("купить", "цена", "price")) else 0.6 if page_type in payment_page_types and page.payment_hints else 0.5,
        "commercial_signals.price_hints" if has_price_fact else "runet_signals.payment_hints" if page.payment_hints else "title",
    )

    _append_block(
        blocks,
        page,
        "terms",
        has_legal or has_terms_fact,
        0.9 if has_terms_fact else 0.8 if page_type in legal_page_types and page.legal_hints else 0.7 if _contains_any(combined, ("доставка", "возврат", "обмен", "terms", "refund")) else 0.5,
        "commercial_signals.offer_terms" if has_terms_fact else "runet_signals.legal_hints" if page.legal_hints else "title",
    )

    _append_block(
        blocks,
        page,
        "proof",
        has_proof_text or page_type in {"case_study", "portfolio"},
        0.9 if page_type in {"case_study", "portfolio"} else 0.8 if _contains_any(combined, ("кейс", "кейсы", "клиент", "клиенты", "портфолио", "проект", "проекты")) else 0.7 if has_proof_text else 0.0,
        "title" if has_proof_text or page_type in {"case_study", "portfolio"} else None,
    )

    _append_block(
        blocks,
        page,
        "specs",
        page_type in {"product", "category"} and bool(page.h1 or page.title),
        0.7 if page_type == "product" and (page.h1 or page.title) else 0.4,
        "headings.h1" if page.h1 else "title",
    )
    _append_block(
        blocks,
        page,
        "availability",
        page_type in commerce_page_types and (has_availability_text or bool(page.payment_hints) or page_type == "product"),
        0.8 if has_availability_text else 0.6 if page_type == "product" else 0.5,
        "runet_signals.payment_hints" if page.payment_hints else "title",
    )
    _append_block(
        blocks,
        page,
        "service_scope",
        page_type in service_page_types and (has_service_scope_text or bool(page.h2) or page_type in {"service", "pricing", "case_study", "portfolio"} or has_geo_fact or has_timeline_fact),
        0.85 if page_type in {"service", "pricing"} and (has_service_scope_text or page.h2 or has_geo_fact or has_timeline_fact) else 0.8 if page_type in {"case_study", "portfolio"} else 0.6 if page_type == "homepage" and page.h2 else 0.5,
        "commercial_signals.geo_hints" if has_geo_fact else "commercial_signals.timeline_hints" if has_timeline_fact else "headings.h2" if page.h2 else "title",
    )
    _append_block(
        blocks,
        page,
        "fulfillment",
        page_type in commerce_page_types and (has_fulfillment_text or bool(page.legal_hints) or bool(page.payment_hints) or page_type == "delivery"),
        0.8 if page_type == "delivery" else 0.7 if has_fulfillment_text else 0.6,
        "runet_signals.legal_hints" if page.legal_hints else "runet_signals.payment_hints" if page.payment_hints else "title",
    )
    _append_block(
        blocks,
        page,
        "messengers",
        has_messengers,
        0.8,
        "runet_signals.messenger_hints",
    )
    _append_block(
        blocks,
        page,
        "payment_options",
        page_type in payment_page_types and bool(page.payment_hints),
        0.8,
        "runet_signals.payment_hints",
    )
    _append_block(
        blocks,
        page,
        "legal_trust",
        page_type in legal_page_types and bool(page.legal_hints),
        0.85 if page_type == "about" else 0.8,
        "runet_signals.legal_hints",
    )
    _append_block(
        blocks,
        page,
        "secure_protocol",
        _is_secure_protocol(page),
        0.9 if _is_secure_protocol(page) else 0.0,
        "canonical_url" if page.canonical_url else "url",
    )
    _append_block(
        blocks,
        page,
        "strict_transport_security",
        _has_strict_transport_security(page),
        0.8 if _has_strict_transport_security(page) else 0.0,
        "transport_signals.strict_transport_security",
    )
    _append_block(
        blocks,
        page,
        "mixed_content_safe",
        _is_mixed_content_safe(page),
        0.8 if _is_mixed_content_safe(page) else 0.0,
        "transport_signals.mixed_content_urls" if not _is_mixed_content_safe(page) else None,
    )

    return PageBlocksDocument(
        schema_version=SCHEMA_VERSION,
        audit_id=page.audit_id,
        url=page.url,
        page_type=page_type,
        blocks=blocks,
        facts=facts,
        updated_at=utc_now_iso(),
    )
