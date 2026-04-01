#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_input import ensure_approved, load_json
from scripts.delivery_i18n import translate_gap, translate_page_type, translate_phrase, translate_site_profile
from scripts.generate_client_report import main as generate_client_report_main


SCHEMA_VERSION = "2.0.0"

INDEX_INTERPRETATIONS = {
    "AI Readiness": "Насколько сайт в целом готов к устойчивой интерпретации, доверию и использованию в AI-сценариях.",
    "Generative Visibility": "Насколько сайт пригоден быть источником для генеративной выдачи и AI-рекомендаций.",
    "Answer Fitness": "Насколько сайт умеет быстро, однозначно и полезно отвечать на вопрос пользователя.",
}

CHECK_DIMENSIONS = [
    ("AI Readiness", "Сводный показатель по измеряемым legacy-факторам, связанным с технической, контентной и смысловой готовностью сайта."),
    ("Generative Visibility", "Показатель пригодности сайта для генеративной выдачи, AI-рекомендаций и AI-обзоров."),
    ("Answer Fitness", "Показатель того, насколько сайт помогает быстро закрывать вопрос пользователя содержанием и структурой страницы."),
]

GAP_EXPLANATIONS = {
    "messengers": "на сайте не хватает быстрых и привычных каналов связи, через которые клиент может сразу перейти к диалогу",
    "proof": "сайт слабо подтверждает компетенцию кейсами, цифрами, клиентами или иными доказательствами результата",
    "secure_protocol": "технический контур не доведен до единой безопасной https-версии сайта",
    "strict_transport_security": "сервер не закрепляет безопасный режим через HSTS, из-за чего протокольное доверие остается слабее нужного",
    "contacts": "контактный контур раскрыт неравномерно и может требовать лишних усилий от клиента",
    "pricing": "ценностная и ценовая ясность раскрыта недостаточно, поэтому часть спроса теряется до обращения",
    "process_steps": "клиент не видит понятного сценария работы и этапов взаимодействия",
    "terms": "условия сотрудничества и важные правила взаимодействия объяснены недостаточно явно",
    "service_scope": "границы услуги, состав работ и результат раскрыты не до конца",
    "legal_trust": "юридические и доверительные сигналы присутствуют, но не доведены до сильного стандарта",
}

BUSINESS_IMPACT_BY_PAGE_TYPE = {
    "homepage": "Главная страница влияет на первое доверие, понимание предложения и вероятность обращения в первую сессию.",
    "service": "Сервисные страницы влияют на понимание услуги, ценности и следующий шаг клиента.",
    "about": "Страница о компании влияет на доверие к исполнителю, зрелость образа компании и готовность к диалогу.",
    "careers": "Карьерные страницы влияют на восприятие компании как работодателя, но обычно не являются главным коммерческим контуром.",
    "pricing": "Страница с ценами влияет на коммерческую ясность, квалификацию спроса и качество первичного обращения.",
    "case_study": "Кейс влияет на доказательность экспертизы и снижает барьер перед обращением.",
    "portfolio": "Портфолио влияет на доверие к опыту команды и помогает клиенту соотнести задачу со своими ожиданиями.",
    "contacts": "Контакты и быстрые каналы связи влияют на переход от интереса к диалогу.",
    "category": "Коммерческие категории влияют на видимость спроса и распределение трафика по предложениям.",
    "product": "Карточки предложения влияют на коммерческую ясность и конверсию из интереса в запрос.",
    "delivery": "Страницы условий и доставки влияют на снятие сомнений и качество лидов.",
    "return_policy": "Страницы гарантий и возвратов влияют на доверие и снижение барьеров к покупке или обращению.",
    "wholesale": "Оптовые страницы влияют на коммерческую ясность и качество B2B-запросов.",
    "generic": "Эта группа страниц влияет на общую объяснимость сайта для клиента и систем.",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_expert_report(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    schema_versions = manifest.setdefault("schema_versions", {})
    schema_versions["expert_report"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "exports/expert_report.json",
        "category": "export",
        "required": False,
        "schema": "expert_report",
        "checksum": sha256_file(package_dir / "exports" / "expert_report.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_client_report(package_dir: Path) -> None:
    report_path = package_dir / "exports" / "client_report.json"
    if report_path.exists():
        return
    exit_code = generate_client_report_main(["generate_client_report.py", str(package_dir)])
    if exit_code != 0:
        raise RuntimeError("client report generation failed before expert report build")


def russian_gap(label: str) -> str:
    return translate_gap(label)


def health_zone(value: float) -> str:
    if value >= 0.8:
        return "сильный уровень"
    if value >= 0.6:
        return "рабочий уровень"
    if value >= 0.4:
        return "зона улучшений"
    return "слабый уровень"


def format_score(value: float) -> str:
    return f"{round(value * 100, 1):.1f} / 100"


def summarize_gap(gap: str) -> str:
    label = russian_gap(gap)
    explanation = GAP_EXPLANATIONS.get(gap, "критичный бизнес-сигнал раскрыт не в полном объеме")
    return f"Блок «{label}» сейчас проседает: {explanation}."


def build_indices(report_input: dict) -> list[dict]:
    indices = []
    legacy_scores = report_input.get("indices", {}).get("legacy_scores", [])
    for item in legacy_scores:
        key = str(item.get("label", ""))
        value = float(item.get("score", 0.0))
        measured_factor_count = int(item.get("measured_factor_count", 0))
        total_factor_count = int(item.get("total_factor_count", 0))
        indices.append(
            {
                "label": key,
                "value": round(value * 100, 1),
                # Оставляем только человекочитаемое пояснение и зону,
                # не упоминая «покрытие факторов», чтобы не вводить новый термин.
                "interpretation": INDEX_INTERPRETATIONS[key] + f" Текущее состояние: {health_zone(value)}.",
            }
        )
    return indices


def build_limitations(review_brief: dict) -> list[dict]:
    limitations: list[dict] = []
    global_tech_gaps: list[str] = []
    GLOBAL_TECH_KEYS = {"secure_protocol", "strict_transport_security", "mixed_content_safe"}

    focus_areas = list(review_brief.get("focus_areas", []))
    priority_pages = list(review_brief.get("priority_pages", []))
    page_lookup = {str(item.get("page_type")): item for item in priority_pages}
    for area in focus_areas[:3]:
        page_type = str(area.get("page_type", "generic"))
        raw_missing = [str(item) for item in area.get("top_missing", [])[:4]]
        # Локальные для типа страницы пробелы (то, что реально относится к содержанию страницы).
        missing = [gap for gap in raw_missing if gap not in GLOBAL_TECH_KEYS]
        # Глобальные технические пробелы (HTTPS/HSTS и смешанный контент) собираем отдельно,
        # чтобы не мешать их в разделы про конкретные типы страниц.
        tech_missing = [gap for gap in raw_missing if gap in GLOBAL_TECH_KEYS]
        global_tech_gaps.extend(tech_missing)

        page = page_lookup.get(page_type, {})
        limitations.append(
            {
                "area": area.get("label") or translate_page_type(page_type).capitalize(),
                "what_was_checked": (
                    f"Анализировались страницы типа «{translate_page_type(page_type)}», их покрытие ключевыми блоками, "
                    "наличие доверительных и технических сигналов, а также готовность страницы объяснять предложение."
                ),
                "observations": [
                    summarize_gap(gap) for gap in missing
                ] or ["На страницах этой группы не хватает части поддерживающих сигналов."],
                "business_impact": BUSINESS_IMPACT_BY_PAGE_TYPE.get(page_type, BUSINESS_IMPACT_BY_PAGE_TYPE["generic"]),
                "recommended_direction": (
                    "Усилить структуру страницы, закрыть недостающие блоки и проверить, что ключевой сценарий обращения виден без дополнительных действий."
                ),
            }
        )
    crawl_quality = review_brief.get("crawl_quality", {})
    # Глобальная проблема протокола и канонизации (http/https вперемешку).
    if crawl_quality.get("protocol_duplication"):
        limitations.append(
            {
                "area": "Протокол и канонизация",
                "what_was_checked": "Проверялись протокол сайта, canonical-сигналы, внутренняя ссылочная дисциплина и технические предупреждения обхода.",
                "observations": [
                    "В пакете одновременно встречаются http и https URL.",
                    "Это означает, что часть технического доверия и единообразия адресов пока не выровнена.",
                ],
                "business_impact": "Нестабильный протокольный контур снижает доверие поисковых и AI-систем и создает риск распыления сигналов.",
                "recommended_direction": "Выбрать единственную https-версию сайта и выровнять под нее редиректы, canonical, sitemap и внутренние ссылки.",
            }
        )
    # Глобальная проблема безопасного протокола и HSTS (даже без смешанного протокола),
    # если такие пробелы встречаются в ключевых зонах.
    if global_tech_gaps:
        limitations.append(
            {
                "area": "Безопасный протокол и HSTS",
                "what_was_checked": "Проверялись безопасность протокола (HTTPS), наличие HSTS и использование только защищённых ресурсов на ключевых страницах.",
                "observations": [
                    "Сайт не в полной мере закрепляет безопасный https-контур и политику Strict-Transport-Security на всех важных страницах."
                ],
                "business_impact": "Недостаточно защищённый протокол снижает доверие поисковых и AI-систем и создаёт риски для восприятия бренда.",
                "recommended_direction": (
                    "Закрепить единый безопасный https-контур и политику HSTS для ключевых страниц, убедиться в отсутствии небезопасных http-ресурсов."
                ),
            }
        )
    return limitations[:4]


def build_priority_workstreams(review_brief: dict) -> list[dict]:
    workstreams = []
    top_gaps = [str(item) for item in review_brief.get("top_gaps", [])]
    crawl_quality = review_brief.get("crawl_quality", {})
    has_protocol_duplication = bool(crawl_quality.get("protocol_duplication"))

    # Техническая целостность и единый протокол поднимаем только,
    # если есть реальный смешанный протокольный сигнал или gap по secure_protocol.
    # Одного лишь отсутствия HSTS (strict_transport_security) здесь недостаточно,
    # чтобы утверждать про «смешанный протокольный сигнал».
    if has_protocol_duplication or any(gap in top_gaps for gap in ("secure_protocol", "mixed_content_safe")):
        workstreams.append(
            {
                "name": "Техническая целостность и единый протокол",
                "problem": "Сайт отдает смешанный протокольный сигнал и не закрепляет доверительный https-контур до конца.",
                "actions": [
                    "Настроить редиректы с http на https.",
                    "Перевести canonical, sitemap и внутренние ссылки только на https-версию.",
                    "Включить HSTS и убрать небезопасные asset-ссылки, если они есть.",
                ],
                "result": "Сайт перестает дробить технические сигналы и становится надежнее для систем и пользователей.",
            }
        )
    if any(gap in top_gaps for gap in ("proof", "messengers", "contacts", "legal_trust")):
        workstreams.append(
            {
                "name": "Доверие и снятие барьеров к обращению",
                "problem": "Ключевые страницы не добирают доверия и не переводят пользователя в быстрый контакт.",
                "actions": [
                    "Добавить кейсы, цифры, отзывы, подтверждения опыта.",
                    "Усилить контактный слой и быстрые каналы связи.",
                    "Вывести важные юридические и организационные сигналы доверия в явный блок.",
                ],
                "result": "Растет вероятность обращения с первой сессии и снижается число сомнений до диалога.",
            }
        )
    if any(gap in top_gaps for gap in ("pricing", "process_steps", "service_scope", "terms", "faq")):
        workstreams.append(
            {
                "name": "Упаковка услуги и сценарий движения клиента",
                "problem": "Сайт не до конца объясняет состав услуги, этапы, цену и логику движения клиента к заявке.",
                "actions": [
                    "Переупаковать ключевые сервисные страницы по структуре «что делаем -> как работаем -> что получает клиент».",
                    "Добавить блоки условий, диапазонов стоимости, этапов и часто задаваемых вопросов.",
                    "Выстроить понятный CTA-сценарий на главной и приоритетных страницах.",
                ],
                "result": "Сайт становится понятнее, а коммерческий спрос теряется меньше.",
            }
        )
    return workstreams[:3]


def build_roadmap(review_brief: dict) -> list[dict]:
    top_gap = russian_gap(str(review_brief.get("top_gaps", ["ключевые сигналы"])[0]))
    return [
        {
            "window": "Этап 1",
            "goal": "Убрать главные блокеры доверия и технической ясности",
            "actions": [
                "Выравниваем протокол, канонизацию и базовую техническую целостность сайта.",
                f"Закрываем приоритетный разрыв вокруг блока «{top_gap}».",
                "Фиксируем стандарт сильной главной и основных сервисных страниц.",
            ],
            "result": "Сайт перестает терять часть сигнала на базовом уровне и получает управляемый фундамент для дальнейших улучшений.",
        },
        {
            "window": "Этап 2",
            "goal": "Усилить сервисные и коммерческие страницы",
            "actions": [
                "Раскрываем структуру услуг, этапы работы, подтверждения результата и условия взаимодействия.",
                "Масштабируем улучшения на ключевые сервисные шаблоны и страницы спроса.",
            ],
            "result": "Предложение бизнеса становится понятнее для клиента и лучше интерпретируется системами.",
        },
        {
            "window": "Этап 3",
            "goal": "Закрепить качество и перейти к регулярному улучшению",
            "actions": [
                "Повторно проверяем улучшенные страницы и устраняем остаточные пробелы.",
                "Вводим цикл контроля качества для новых и обновляемых страниц.",
            ],
            "result": "Сайт получает повторяемый стандарт качества, а рост становится менее случайным и более управляемым.",
        },
    ]


def build_measurement(report_input: dict, review_brief: dict) -> list[str]:
    legacy_scores = {
        str(item.get("label")): float(item.get("score", 0.0))
        for item in report_input.get("indices", {}).get("legacy_scores", [])
    }
    return [
        f"Изменение индекса AI Readiness относительно текущей точки {format_score(float(legacy_scores.get('AI Readiness', 0.0)))}.",
        f"Изменение индекса Generative Visibility относительно текущей точки {format_score(float(legacy_scores.get('Generative Visibility', 0.0)))}.",
        f"Изменение индекса Answer Fitness относительно текущей точки {format_score(float(legacy_scores.get('Answer Fitness', 0.0)))}.",
        f"Сокращение числа приоритетных (P0) пробелов в ключевых блоках с текущего уровня {review_brief.get('summary', {}).get('p0_coverage_targets', 0)}.",
    ]


def build_expert_report(package_dir: Path) -> dict:
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    site = report_input.get("site", {})
    top_gaps = [russian_gap(str(item)) for item in review_brief.get("top_gaps", [])[:3]]
    p0_targets = int(review_brief.get("summary", {}).get("p0_coverage_targets", 0))
    overview = report_input.get("summary", {}).get("overview", "")
    executive_summary = [
        overview,
        "Проблема сайта не в полном отсутствии фундамента, а в том, что часть целевого спроса и доверия теряется на ключевых страницах.",
        f"Самые заметные ограничения сейчас сосредоточены вокруг блоков: {', '.join(top_gaps) if top_gaps else 'ключевых сигналов доверия и структуры'}.",
        "Это означает, что сайт можно усиливать поэтапно, без полной переделки с нуля, но с обязательной фиксацией стандартов для основных шаблонов.",
    ]
    if p0_targets > 0:
        executive_summary.append(
            f"Сейчас зафиксировано {p0_targets} приоритетных (P0) пробелов в ключевых блоках — это самые критичные недостающие элементы на важных страницах."
        )
    strengths = list(report_input.get("strengths", [])) or [
        "Сайт уже индексируется и отдает рабочий набор страниц для анализа.",
        "Базовый каркас сайта существует, поэтому речь идет о доработке, а не о полной сборке заново.",
        "Пакет аудита уже дает доказательную базу для поэтапного плана внедрения.",
    ]
    constraints = list(report_input.get("constraints", []))
    constraints.append("Документ построен только на утвержденном audit_package и не добавляет неподтвержденные факты вручную.")
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": review_brief["audit_id"],
        "package_status": review_brief["package_status"],
        "site": site,
        "sections": {
            "executive_summary": executive_summary,
            "what_was_evaluated": [
                {"label": label, "description": description} for label, description in CHECK_DIMENSIONS
            ],
            "indices": build_indices(report_input),
            "strengths": strengths,
            "limitations": build_limitations(review_brief),
            "priority_workstreams": build_priority_workstreams(review_brief),
            "roadmap_30_60_90": build_roadmap(review_brief),
            "measurement": build_measurement(report_input, review_brief),
            "constraints": constraints,
        },
    }


def render_markdown(report: dict) -> str:
    sections = report["sections"]
    lines = [
        f"# Аудит сайта {report['site']['primary_domain']}",
        "",
        "## Как читать этот документ",
        "",
        "Формат документа:",
        "",
        "- сначала краткий вывод и сводные индексы;",
        "- затем подробный разбор ограничений и приоритетов работ;",
        "- в конце — план действий по этапам и показатели, по которым можно отслеживать эффект.",
        "",
        "Кратко как проходил аудит:",
        "",
        "- обход сайта и сбор HTML-страниц и структуры ссылок;",
        "- технический анализ: протокол (HTTP/HTTPS), каноникал, sitemap, статус-коды и базовое качество страниц;",
        "- смысловой анализ: типы страниц, ключевые блоки (ценность, процесс, цены, FAQ, доверие, контакты и др.);",
        "- извлечение сущностей и фактов (что, где, для кого и на каких условиях вы предлагаете);",
        "- расчёт покрытий и противоречий по ключевым бизнес-сигналам;",
        "- построение индексов готовности (SEO, GEO, AEO, AIO, LEO) и приоритизация доработок.",
        "",
        "Как понимать индексы:",
        "",
        "- AI Readiness показывает общую готовность сайта к корректному чтению и использованию в AI-сценариях;",
        "- Generative Visibility — вероятность того, что сайт станет источником для генеративных ответов и обзоров;",
        "- Answer Fitness — насколько страницы помогают давать быстрые и однозначные ответы на вопросы клиентов;",
        "- значения ниже 40 — критическая зона, 40–59 — зона улучшений, 60–79 — рабочий уровень, 80+ — сильный уровень.",
        "",
        "## Краткий вывод",
        "",
    ]
    for item in sections["executive_summary"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Что оценивалось", ""])
    for item in sections["what_was_evaluated"]:
        lines.append(f"- **{item['label']}**: {item['description']}")
    lines.extend(["", "## Сводные индексы состояния", "", "| Индекс | Значение | Интерпретация |", "|---|---:|---|"])
    for item in sections["indices"]:
        lines.append(f"| {item['label']} | {item['value']:.1f} / 100 | {item['interpretation']} |")
    lines.extend(["", "## Сильные стороны", ""])
    for item in sections["strengths"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Ключевые ограничения, которые сейчас мешают росту", ""])
    for item in sections["limitations"]:
        lines.append(f"### {item['area']}")
        lines.append(f"**Что анализировалось:** {item['what_was_checked']}")
        lines.append("")
        lines.append("**Наблюдения:**")
        # Добавляем пустую строку перед каждым пунктом, чтобы в итоговом PDF
        # каждый пункт визуально начинался с новой строки и не сливался в один абзац.
        for note in item["observations"]:
            lines.append("")
            lines.append(f"- {note}")
        lines.append("")
        lines.append(f"**На что влияет:** {item['business_impact']}")
        lines.append("")
        lines.append(f"**Что делать:** {item['recommended_direction']}")
        lines.append("")
    lines.extend(["## Приоритеты работ", ""])
    for item in sections["priority_workstreams"]:
        lines.append(f"### {item['name']}")
        lines.append(f"**Проблема:** {item['problem']}")
        lines.append("")
        lines.append("**Что нужно сделать:**")
        for action in item["actions"]:
            # Добавляем пустую строку перед каждым пунктом, чтобы списки шагов
            # в PDF не сливались в один абзац и были визуально разбиты.
            lines.append("")
            lines.append(f"- {action}")
        lines.append("")
        lines.append(f"**Ожидаемый эффект:** {item['result']}")
        lines.append("")
    lines.extend(["## План действий", ""])
    for item in sections["roadmap_30_60_90"]:
        lines.append(f"### {item['window']}: {item['goal']}")
        for action in item["actions"]:
            lines.append(f"- {action}")
        lines.append(f"- Практический результат этапа: {item['result']}")
        lines.append("")
    lines.extend(["## Как будет измеряться эффект", ""])
    for item in sections["measurement"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Глоссарий",
            "",
            "- **SEO** — классическая поисковая оптимизация: техническое состояние сайта, индексация, структура и релевантность страниц и контента запросам пользователя.",
            "- **GEO** — Generative Engine Optimization: подготовка сайта к видимости и цитируемости в генеративных ответах и AI‑рекомендациях.",
            "- **AEO** — Answer Engine Optimization: подход к контенту, при котором страницы строятся так, чтобы быстро отвечать на конкретный вопрос пользователя.",
            "- **AIO** — AI Interpretation Optimization: подготовка структуры, смыслов и сигналов сайта так, чтобы алгоритмы и AI‑модели правильно понимали, что именно предлагает компания и чем подтверждаются её утверждения.",
            "- **LEO** — Lead Enablement Optimization: подготовка сайта и данных к сценариям, где в генерации лидов участвуют AI‑интерфейсы, рекомендательные системы и цифровые ассистенты.",
            "- **Сервисная страница** — страница, которая подробно описывает одну из ключевых услуг компании.",
            "- **Информационная страница** — статья или раздел, объясняющий тему, контекст или ответы на вопросы, а не конкретную услугу.",
            "- **Социальное доказательство** — кейсы, отзывы, цифры, логотипы клиентов и другие подтверждения опыта.",
            "- **Слабый уровень** — состояние, когда фундамент есть, но сайт сильно теряет в доверии, структуре и сценариях обращения.",
            "- **Зона улучшений** — состояние, когда базовый уровень есть, но нужно доработать структуру, доверие и содержание.",
            "- **Рабочий уровень** — состояние, когда сайт в целом выполняет свою задачу, но остаётся потенциал точечных улучшений.",
            "- **Сильный уровень** — состояние, когда структура, доверие и сигналы качества доведены до устойчивого стандарта.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_expert_report.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("expert report generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    ensure_client_report(package_dir)
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    report = build_expert_report(package_dir)
    (exports_dir / "expert_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (exports_dir / "expert_report.md").write_text(render_markdown(report), encoding="utf-8")
    sync_manifest_expert_report(package_dir)
    print("expert report generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
