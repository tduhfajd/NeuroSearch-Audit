from __future__ import annotations

from pathlib import Path

from python.common.contracts import TechnicalPageInput, load_json
from python.semantic.page_blocks import build_page_blocks


def _blocks_by_type(document: dict) -> dict[str, dict]:
    return {block["type"]: block for block in document["blocks"]}


def test_build_page_blocks_consumes_runet_signals() -> None:
    payload = load_json(Path("testdata/fixtures/semantic/technical_page.sample.json"))
    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)
    facts = {(fact["fact_type"], fact["value"]) for fact in document["facts"]}

    assert document["page_type"] == "service"
    assert blocks["contacts"]["present"] is True
    assert blocks["contacts"]["evidence"][0]["field"] == "runet_signals.phones"
    assert blocks["messengers"]["present"] is True
    assert blocks["payment_options"]["present"] is True
    assert blocks["legal_trust"]["present"] is True
    assert blocks["pricing"]["present"] is True
    assert blocks["terms"]["present"] is True
    assert blocks["service_scope"]["present"] is True
    assert blocks["secure_protocol"]["present"] is True
    assert blocks["strict_transport_security"]["present"] is True
    assert blocks["mixed_content_safe"]["present"] is True
    assert ("contact_phone", "79991234567") in facts
    assert ("contact_email", "hello@example.com") in facts
    assert ("messenger", "telegram") in facts
    assert ("payment_option", "сбп") in facts
    assert ("legal_hint", "возврат") in facts
    assert ("price", "25 000 руб.") in facts
    assert ("timeline", "5 дней") in facts
    assert ("geo", "по россии") in facts
    assert ("terms", "по договору") in facts
    assert any(fact["fact_type"] == "transport_policy" for fact in document["facts"])


def test_build_page_blocks_adds_deeper_commerce_blocks() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260312T120000Z_abc1234",
        "url": "https://example.com/product/123",
        "source": "crawl",
        "title": "Купить куклу в наличии",
        "meta": {"description": "Доставка и оплата"},
        "headings": {"h1": ["Кукла"], "h2": ["Характеристики"]},
        "schema_hints": [],
        "runet_signals": {"payment_hints": ["оплата"], "legal_hints": ["доставка"]},
    }
    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)

    assert document["page_type"] == "product"
    assert blocks["availability"]["present"] is True
    assert blocks["fulfillment"]["present"] is True


def test_infer_page_type_recognizes_service_pricing_and_about_pages() -> None:
    pricing_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260312T120000Z_abc1234",
        "url": "https://example.com/czeny",
        "source": "crawl",
        "title": "Цены на услуги",
        "meta": {"description": "Стоимость услуг"},
        "headings": {"h1": ["Цены"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }
    about_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260312T120000Z_abc1234",
        "url": "https://example.com/o-kompanii",
        "source": "crawl",
        "title": "О компании",
        "meta": {"description": "О нас"},
        "headings": {"h1": ["О компании"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }

    pricing_doc = build_page_blocks(TechnicalPageInput.from_json(pricing_payload)).to_json()
    about_doc = build_page_blocks(TechnicalPageInput.from_json(about_payload)).to_json()

    assert pricing_doc["page_type"] == "pricing"
    assert about_doc["page_type"] == "about"


def test_infer_page_type_recognizes_case_study_and_portfolio_pages() -> None:
    case_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/case/launch",
        "source": "crawl",
        "title": "Кейс запуска проекта",
        "meta": {"description": "История проекта"},
        "headings": {"h1": ["Кейс"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }
    portfolio_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/portfolio",
        "source": "crawl",
        "title": "Портфолио проектов",
        "meta": {"description": "Наши проекты"},
        "headings": {"h1": ["Портфолио"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }

    case_doc = build_page_blocks(TechnicalPageInput.from_json(case_payload)).to_json()
    portfolio_doc = build_page_blocks(TechnicalPageInput.from_json(portfolio_payload)).to_json()

    assert case_doc["page_type"] == "case_study"
    assert portfolio_doc["page_type"] == "portfolio"


def test_infer_page_type_recognizes_service_slugs_and_article_posts() -> None:
    service_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/marketing",
        "source": "crawl",
        "title": "Маркетинг для бизнеса",
        "meta": {"description": "Услуги маркетинга"},
        "headings": {"h1": ["Маркетинг"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }
    article_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/tpost_abcd1234-novost",
        "source": "crawl",
        "title": "Новости компании",
        "meta": {"description": "Новости"},
        "headings": {"h1": ["Новости"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }

    service_doc = build_page_blocks(TechnicalPageInput.from_json(service_payload)).to_json()
    article_doc = build_page_blocks(TechnicalPageInput.from_json(article_payload)).to_json()

    assert service_doc["page_type"] == "service"
    assert article_doc["page_type"] == "article"


def test_infer_page_type_does_not_treat_domain_name_as_service_signal() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://mediaservicellc.ru/form",
        "source": "crawl",
        "title": "Форма",
        "meta": {"description": ""},
        "headings": {"h1": ["Форма"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }

    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()

    assert document["page_type"] == "generic"


def test_build_page_blocks_uses_commercial_signals_for_service_blocks() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/uslugi",
        "source": "crawl",
        "title": "Услуги компании",
        "meta": {"description": "Работаем по договору по России"},
        "headings": {"h1": ["Услуги"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
        "commercial_signals": {
            "price_hints": ["от 50 000 ₽"],
            "timeline_hints": ["10 дней"],
            "geo_hints": ["по России"],
            "offer_terms": ["по договору"],
        },
    }

    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)

    assert document["page_type"] == "service"
    assert blocks["pricing"]["present"] is True
    assert blocks["pricing"]["evidence"][0]["field"] == "commercial_signals.price_hints"
    assert blocks["terms"]["present"] is True
    assert blocks["terms"]["evidence"][0]["field"] == "commercial_signals.offer_terms"
    assert blocks["service_scope"]["present"] is True


def test_build_page_blocks_uses_refined_service_company_rules() -> None:
    pricing_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/czeny",
        "source": "crawl",
        "title": "Цены на услуги",
        "meta": {"description": "Стоимость и условия"},
        "headings": {"h1": ["Цены"], "h2": []},
        "schema_hints": [],
        "runet_signals": {"phones": ["79991234567"], "legal_hints": ["договор"]},
        "commercial_signals": {"price_hints": ["от 50 000 ₽"], "offer_terms": ["по договору"]},
    }
    about_payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/o-kompanii",
        "source": "crawl",
        "title": "О компании",
        "meta": {"description": "Клиенты и реквизиты"},
        "headings": {"h1": ["О компании"], "h2": []},
        "schema_hints": [],
        "runet_signals": {"phones": ["79991234567"], "legal_hints": ["инн"]},
    }

    pricing_doc = build_page_blocks(TechnicalPageInput.from_json(pricing_payload)).to_json()
    about_doc = build_page_blocks(TechnicalPageInput.from_json(about_payload)).to_json()
    pricing_blocks = _blocks_by_type(pricing_doc)
    about_blocks = _blocks_by_type(about_doc)

    assert pricing_doc["page_type"] == "pricing"
    assert pricing_blocks["pricing"]["present"] is True
    assert pricing_blocks["terms"]["present"] is True
    assert pricing_blocks["contacts"]["present"] is True
    assert about_doc["page_type"] == "about"
    assert about_blocks["legal_trust"]["present"] is True
    assert about_blocks["contacts"]["present"] is True


def test_infer_page_type_distinguishes_careers_from_about() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/karera-v-kompanii",
        "source": "crawl",
        "title": "Карьера в компании",
        "meta": {"description": "Вакансии"},
        "headings": {"h1": ["Карьера"], "h2": []},
        "schema_hints": [],
        "runet_signals": {"legal_hints": ["инн"]},
    }

    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()

    assert document["page_type"] == "careers"


def test_infer_page_type_handles_policy_sitemap_and_promotions_before_pricing() -> None:
    cases = [
        ("https://example.com/privacy-policy", "Политика конфиденциальности", "return_policy"),
        ("https://example.com/karta-sajta", "Карта сайта", "generic"),
        ("https://example.com/akczii", "Акции и спецпредложения", "category"),
    ]

    for url, title, expected in cases:
        payload = {
            "schema_version": "1.0.0",
            "audit_id": "aud_20260313T120000Z_abc1234",
            "url": url,
            "source": "crawl",
            "title": title,
            "meta": {"description": ""},
            "headings": {"h1": [title], "h2": []},
            "schema_hints": [],
            "runet_signals": {},
        }
        document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
        assert document["page_type"] == expected


def test_build_page_blocks_uses_textual_service_signals_for_faq_process_and_proof() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260313T120000Z_abc1234",
        "url": "https://example.com/marketing",
        "source": "crawl",
        "title": "Маркетинг: этапы работы, отзывы и частые вопросы",
        "meta": {"description": "Как работаем с клиентами"},
        "headings": {"h1": ["Маркетинг"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
        "commercial_signals": {
            "price_hints": [],
            "timeline_hints": ["от 2 недель"],
            "geo_hints": [],
            "offer_terms": [],
        },
    }

    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)

    assert document["page_type"] == "service"
    assert blocks["faq"]["present"] is True
    assert blocks["process_steps"]["present"] is True
    assert blocks["proof"]["present"] is True


def test_build_page_blocks_marks_insecure_protocol_gap() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260312T120000Z_abc1234",
        "url": "http://example.com/",
        "source": "crawl",
        "title": "Главная",
        "meta": {"description": "Описание"},
        "canonical_url": "http://example.com",
        "headings": {"h1": ["Главная"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
    }
    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)

    assert document["page_type"] == "homepage"
    assert blocks["secure_protocol"]["present"] is False
    assert blocks["secure_protocol"]["evidence"] == []


def test_build_page_blocks_marks_missing_hsts_and_mixed_content_risk() -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260312T120000Z_abc1234",
        "url": "https://example.com/",
        "source": "crawl",
        "title": "Главная",
        "meta": {"description": "Описание"},
        "canonical_url": "https://example.com",
        "headings": {"h1": ["Главная"], "h2": []},
        "schema_hints": [],
        "runet_signals": {},
        "transport_signals": {
            "strict_transport_security": "",
            "mixed_content_urls": ["http://cdn.example.com/app.js"],
        },
    }
    document = build_page_blocks(TechnicalPageInput.from_json(payload)).to_json()
    blocks = _blocks_by_type(document)

    assert blocks["strict_transport_security"]["present"] is False
    assert blocks["mixed_content_safe"]["present"] is False
