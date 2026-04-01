from __future__ import annotations


GAP_LABELS = {
    "messengers": "мессенджеры и быстрые каналы связи",
    "proof": "социальное доказательство",
    "secure_protocol": "безопасный протокол HTTPS",
    "strict_transport_security": "политика Strict-Transport-Security",
    "contacts": "понятные контакты",
    "pricing": "ценностная и ценовая ясность",
    "process_steps": "пошаговый сценарий работы",
    "terms": "условия и правила взаимодействия",
    "legal_trust": "юридические сигналы доверия",
    "payment_options": "варианты оплаты",
    "service_scope": "границы услуги",
    "availability": "доступность предложения",
    "fulfillment": "процесс выполнения и получения результата",
    "mixed_content_safe": "отсутствие mixed-content риска",
    "faq": "блоки быстрых ответов и FAQ",
}

PAGE_TYPE_LABELS = {
    "homepage": "главная страница",
    "service": "сервисная страница",
    "about": "страница о компании",
    "careers": "страница карьеры и вакансий",
    "pricing": "страница с ценами",
    "case_study": "кейс / история проекта",
    "portfolio": "портфолио / проекты",
    "category": "коммерческая категория",
    "contacts": "контакты",
    "delivery": "доставка",
    "return_policy": "возвраты и гарантии",
    "wholesale": "оптовое предложение",
    "product": "карточка продукта",
    "article": "информационная страница",
    "generic": "универсальная страница",
}

HEALTH_BAND_LABELS = {
    "strong": "сильный уровень",
    "moderate": "рабочий уровень",
    "limited": "зона улучшений",
    "weak": "слабый уровень",
}

SITE_PROFILE_LABELS = {
    "service": "сервисный сайт",
    "ecommerce": "коммерческий сайт",
    "mixed": "смешанный сайт",
}

PHRASE_TRANSLATIONS = {
    "crawl observed both http and https urls; normalize redirects, canonical tags, sitemap, and internal links to https": "В ходе обхода сайта одновременно встретились http и https URL; нужно выровнять редиректы, canonical, sitemap и внутренние ссылки на https.",
    "http and https variants found": "В аудите одновременно обнаружены http и https варианты URL.",
    "crawl did not use sitemap-seeded urls; review robots.txt and sitemap availability": "Обход сайта не использовал URL из sitemap; нужно проверить robots.txt и доступность sitemap.",
    "Redirect all http URLs to https with a permanent 301/308 response": "Настроить постоянный 301/308-редирект со всех http URL на https.",
    "Set canonical URLs to the https version only": "Перевести canonical на https-версию URL.",
    "Ensure sitemap and internal links point to https URLs": "Обновить sitemap и внутренние ссылки так, чтобы они вели только на https URL.",
    "Enable Strict-Transport-Security on HTTPS responses": "Включить Strict-Transport-Security для HTTPS-ответов.",
    "Remove http:// asset, script, stylesheet, and media references from HTTPS pages": "Убрать http:// ссылки на ассеты, скрипты, стили и медиа с HTTPS-страниц.",
    "Improve protocol trust, canonical consistency, and readiness signals": "Повысить доверие к протоколу, выровнять canonical и усилить сигналы готовности сайта.",
    "Improve content completeness and readiness signals": "Повысить полноту контента и усилить сигналы готовности сайта.",
    "approved package artifacts": "утвержденных артефактов пакета",
    "approved package": "утвержденного пакета",
    "report input": "отчетный входной пакет",
    "backlog": "план работ",
    "AI-readiness": "цифровой готовности сайта",
    "lead value index": "индекс потенциала заявок",
    "agentic and lead-oriented AI scenarios": "AI-сценариев, связанных с обращениями и следующими шагами пользователя",
    "AI-ready scenarios": "сценариев, где сайт должен быть понятен AI-системам",
    "coverage-gap": "критичных пробелов покрытия",
    "The main delivery risk is": "Главный риск сейчас —",
    "The strongest near-term opportunity is to tighten business-critical pages across": "Главная возможность роста — усилить ключевые бизнес-страницы по направлениям",
    "while preserving the current crawl coverage of": "без потери текущего охвата обхода сайта в",
    "HTML pages.": "HTML-страниц.",
    "Recommended next step: convert the top": "Следующий шаг: перевести в работу",
    "priority actions into a scoped implementation plan starting with": "приоритетных действий и начать план внедрения с",
    "This service audit reviewed": "Аудит сервисного сайта охватил",
    "This ecommerce audit reviewed": "Аудит коммерческого сайта охватил",
    "This mixed audit reviewed": "Аудит смешанного сайта охватил",
    "and currently shows": "и сейчас показывает",
    "client-readiness": "уровень клиентской готовности",
    "High Contradictions": "Критичные противоречия",
    "Top Gaps": "Главные разрывы",
    "Focus Areas": "Ключевые зоны внимания",
    "Action Plan": "План действий",
    "What Already Works": "Что уже работает",
    "Priority Pages": "Приоритетные страницы",
    "Priority Recommendations": "Приоритетные рекомендации",
    "Evidence Sources": "Источники доказательств",
    "Executive Summary": "Краткий вывод",
    "Discovery Sources": "Источники discovery",
    "Discovery Mode": "Режим обнаружения страниц",
    "Crawl Warnings": "Предупреждения по обходу",
    "Pages": "Страницы",
    "Lead Value Index": "Индекс потенциала заявок",
    "Package Status": "Статус пакета",
    "Site Profile": "Профиль сайта",
    "Health Band": "Состояние",
    "P0 Coverage Targets": "P0-цели покрытия",
    "Page Type": "Тип страницы",
    "Coverage Score": "Покрытие",
    "Missing": "Не хватает",
    "Scores": "Индексы",
    "Expected impact": "Ожидаемый эффект",
    "Related findings": "Связанные проблемы",
    "crawl included non-html fetches; review fetch_log for low-value targets": "В обход попали не-HTML ответы; нужно проверить fetch_log и отфильтровать низкоценные цели.",
    "crawl policy filtered more urls than were persisted as html pages": "Политика обхода отфильтровала больше URL, чем было сохранено HTML-страниц.",
    "mixed": "смешанный",
    "sitemap-led": "с упором на sitemap",
    "homepage-led": "с упором на ссылки с сайта",
    "submitted-only": "только исходный URL",
    "none": "нет",
}

TASK_TITLE_BY_PHRASE = {
    "Redirect all http URLs to https": "Выравнивание протокола, canonical и HTTPS-контура",
    "Redirect all http URLs to https with a permanent 301/308 response": "Выравнивание протокола, canonical и HTTPS-контура",
    "Set canonical URLs to the https version only": "Выравнивание протокола, canonical и HTTPS-контура",
    "Ensure sitemap and internal links point to https URLs": "Выравнивание протокола, canonical и HTTPS-контура",
    "Enable Strict-Transport-Security on HTTPS responses": "Усиление транспортной безопасности",
    "Remove http:// asset, script, stylesheet, and media references from HTTPS pages": "Устранение mixed-content и небезопасных asset-ссылок",
}


def translate_gap(label: str) -> str:
    return GAP_LABELS.get(label, label.replace("_", " "))


def translate_page_type(label: str) -> str:
    return PAGE_TYPE_LABELS.get(label, label.replace("_", " "))


def translate_health_band(label: str) -> str:
    return HEALTH_BAND_LABELS.get(label, label)


def translate_site_profile(label: str) -> str:
    return SITE_PROFILE_LABELS.get(label, label)


def translate_phrase(text: str) -> str:
    translated = PHRASE_TRANSLATIONS.get(text, text)
    replacements = (
        ("AI-readiness", "цифровой готовности сайта"),
        ("lead value index", "индекс потенциала заявок"),
        (" coverage-gap", " критичных пробелов покрытия"),
        ("coverage-gap", "критичных пробелов покрытия"),
        ("agentic and lead-oriented AI-scenarios", "AI-сценариев, связанных с обращениями и следующими шагами пользователя"),
        ("agentic and lead-oriented AI-сценариев", "AI-сценариев, связанных с обращениями и следующими шагами пользователя"),
        ("AI-ready scenarios", "сценариев, где сайт должен быть понятен AI-системам"),
        ("report input", "отчетный входной пакет"),
        ("approved package artifacts", "утвержденных артефактов пакета"),
        ("approved package", "утвержденного пакета"),
    )
    for old, new in replacements:
        translated = translated.replace(old, new)
    return translated


def translate_gaps(labels: list[str]) -> list[str]:
    return [translate_gap(str(label)) for label in labels]


def recommendation_title(title: str) -> str:
    return TASK_TITLE_BY_PHRASE.get(title, title)
