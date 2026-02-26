from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from backend.db.models import Audit, Page

RULE_PRIORITY_MAP: dict[str, str] = {
    "ANA-01": "P1",
    "ANA-02": "P2",
    "ANA-03": "P2",
    "ANA-04": "P1",
    "ANA-05": "P1",
    "ANA-06": "P2",
    "ANA-07": "P2",
    "ANA-08": "P2",
}

UTILITY_PATH_HINTS: tuple[str, ...] = (
    "cart",
    "login",
    "signin",
    "signup",
    "checkout",
    "privacy",
    "policy",
    "terms",
    "account",
)


@dataclass(slots=True)
class RuleContext:
    audit: Audit
    pages: list[Page]


@dataclass(slots=True)
class IssueCandidate:
    rule_id: str
    title: str
    description: str
    recommendation: str
    affected_url: str | None
    page_id: int | None = None
    priority: str | None = None

    def resolve_priority(self) -> str:
        if self.priority:
            return self.priority
        return RULE_PRIORITY_MAP.get(self.rule_id, "P3")


class Rule(Protocol):
    rule_id: str

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]: ...


def get_rule_registry() -> list[Rule]:
    return [
        NoindexRule(),
        DuplicateContentRule(),
        MetaLengthRule(),
        CanonicalRule(),
        BrokenLinksRule(),
        SchemaPresenceRule(),
        SchemaValidationRule(),
        TrustSignalsRule(),
    ]


def _is_utility_url(url: str) -> bool:
    lowered = (urlparse(url).path or "").lower()
    return any(part in lowered for part in UTILITY_PATH_HINTS)


class NoindexRule:
    rule_id = "ANA-01"

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        disallow_patterns = []
        if isinstance(context.audit.meta, dict):
            disallow_patterns = context.audit.meta.get("robots_disallow_patterns", [])
        for page in context.pages:
            url = page.url
            if _is_utility_url(url):
                continue
            robots = (page.robots_meta or "").lower()
            if "noindex" in robots:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Страница закрыта от индексации",
                        description="Обнаружен meta robots noindex на индексируемой странице.",
                        recommendation="Уберите noindex для страниц, которые должны ранжироваться.",
                        affected_url=url,
                        page_id=page.id,
                    )
                )
                continue
            path = (urlparse(url).path or "").lower()
            if any(
                path.startswith(pattern.lower())
                for pattern in disallow_patterns
                if isinstance(pattern, str)
            ):
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Страница блокируется robots.txt",
                        description="URL совпадает с disallow-паттерном robots.txt.",
                        recommendation=(
                            "Проверьте robots.txt и откройте важные страницы для индексации."
                        ),
                        affected_url=url,
                        page_id=page.id,
                    )
                )
        return issues


class DuplicateContentRule:
    rule_id = "ANA-02"

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        title_map: dict[str, list[Page]] = {}
        h1_map: dict[str, list[Page]] = {}

        for page in context.pages:
            if page.title:
                key = page.title.strip().lower()
                title_map.setdefault(key, []).append(page)
            if page.h1:
                key = page.h1.strip().lower()
                h1_map.setdefault(key, []).append(page)

        for duplicate_pages in title_map.values():
            if len(duplicate_pages) < 2:
                continue
            for page in duplicate_pages:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Дублирующийся title",
                        description="Title повторяется на нескольких страницах.",
                        recommendation="Сделайте title уникальным под интент страницы.",
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )

        for duplicate_pages in h1_map.values():
            if len(duplicate_pages) < 2:
                continue
            for page in duplicate_pages:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Дублирующийся H1",
                        description="H1 повторяется на нескольких страницах.",
                        recommendation="Сделайте H1 уникальным и релевантным странице.",
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )

        return issues


class MetaLengthRule:
    rule_id = "ANA-03"

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        for page in context.pages:
            title_len = len((page.title or "").strip())
            if title_len and (title_len < 30 or title_len > 60):
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Некорректная длина title",
                        description="Длина title выходит за рекомендуемый диапазон 30-60.",
                        recommendation="Приведите длину title к диапазону 30-60 символов.",
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )

            md_len = len((page.meta_description or "").strip())
            if md_len and (md_len < 120 or md_len > 160):
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Некорректная длина meta description",
                        description="Длина meta description выходит за диапазон 120-160.",
                        recommendation="Приведите meta description к диапазону 120-160 символов.",
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )
        return issues


class CanonicalRule:
    rule_id = "ANA-04"

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        audit_host = (urlparse(context.audit.url).hostname or "").lower()

        for page in context.pages:
            canonical = (page.canonical or "").strip()
            if not canonical:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Отсутствует canonical",
                        description="На странице не указан canonical URL.",
                        recommendation=(
                            "Добавьте canonical, ведущий на каноническую версию страницы."
                        ),
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )
                continue

            canonical_host = (urlparse(canonical).hostname or "").lower()
            if canonical_host and audit_host and canonical_host != audit_host:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Canonical указывает на другой домен",
                        description=(
                            "Canonical ведет на внешний домен и может вывести страницу из индекса."
                        ),
                        recommendation=(
                            "Используйте canonical внутри целевого домена или self-canonical."
                        ),
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )

        return issues


class BrokenLinksRule:
    rule_id = "ANA-05"

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        for page in context.pages:
            status_code = int(page.status_code or 0)
            if status_code >= 400:
                issues.append(
                    IssueCandidate(
                        rule_id=self.rule_id,
                        title="Битая страница в обходе",
                        description=(
                            "Страница возвращает HTTP 4xx/5xx и ухудшает техническое качество."
                        ),
                        recommendation=(
                            "Исправьте URL или настройте корректный редирект на рабочую страницу."
                        ),
                        affected_url=page.url,
                        page_id=page.id,
                    )
                )

        if isinstance(context.audit.meta, dict):
            for item in context.audit.meta.get("crawl_errors", []):
                if not isinstance(item, dict):
                    continue
                url = item.get("url")
                error_text = str(item.get("error", "")).lower()
                if url and ("4" in error_text or "5" in error_text):
                    issues.append(
                        IssueCandidate(
                            rule_id=self.rule_id,
                            title="Ошибка обхода ссылки",
                            description="Во время краулинга зафиксирована ошибка перехода по URL.",
                            recommendation=(
                                "Проверьте проблемные ссылки и устраните источники ошибок."
                            ),
                            affected_url=url,
                        )
                    )

            redirect_chains = context.audit.meta.get("redirect_chains", {})
            if isinstance(redirect_chains, dict):
                for url, hops in redirect_chains.items():
                    if isinstance(url, str) and isinstance(hops, int) and hops >= 3:
                        issues.append(
                            IssueCandidate(
                                rule_id=self.rule_id,
                                title="Длинная цепочка редиректов",
                                description="Обнаружена цепочка редиректов длиной 3+ переходов.",
                                recommendation=(
                                    "Сократите цепочку до одного редиректа на целевой URL."
                                ),
                                affected_url=url,
                            )
                        )

        return issues


def _extract_schema_items(page: Page) -> list[dict]:
    payload = page.json_ld
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _normalize_types(raw_type: object) -> list[str]:
    if isinstance(raw_type, str):
        return [raw_type]
    if isinstance(raw_type, list):
        return [item for item in raw_type if isinstance(item, str)]
    return []


class SchemaPresenceRule:
    rule_id = "ANA-06"
    required_types = {"Organization", "FAQPage", "HowTo", "Article", "BreadcrumbList"}

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        found_types: set[str] = set()
        for page in context.pages:
            for item in _extract_schema_items(page):
                found_types.update(_normalize_types(item.get("@type")))

        issues: list[IssueCandidate] = []
        for missing_type in sorted(self.required_types - found_types):
            issues.append(
                IssueCandidate(
                    rule_id=self.rule_id,
                    title="Отсутствует обязательный Schema.org тип",
                    description=f"Не найден required schema type: {missing_type}.",
                    recommendation=(
                        f"Добавьте JSON-LD блок типа {missing_type} на релевантных страницах."
                    ),
                    affected_url=None,
                )
            )
        return issues


class SchemaValidationRule:
    rule_id = "ANA-07"
    required_fields: dict[str, tuple[str, ...]] = {
        "Organization": ("name", "url"),
        "FAQPage": ("mainEntity",),
        "HowTo": ("step",),
        "Article": ("headline",),
        "BreadcrumbList": ("itemListElement",),
    }

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        issues: list[IssueCandidate] = []
        for page in context.pages:
            for item in _extract_schema_items(page):
                for schema_type in _normalize_types(item.get("@type")):
                    required = self.required_fields.get(schema_type)
                    if not required:
                        continue
                    missing = [field for field in required if item.get(field) in (None, "", [])]
                    if missing:
                        missing_fields = ", ".join(missing)
                        issues.append(
                            IssueCandidate(
                                rule_id=self.rule_id,
                                title="Невалидная структура JSON-LD",
                                description=(
                                    f"Schema type {schema_type} не содержит обязательные поля: "
                                    f"{missing_fields}."
                                ),
                                recommendation=(
                                    f"Добавьте обязательные поля для {schema_type}: "
                                    f"{missing_fields}."
                                ),
                                affected_url=page.url,
                                page_id=page.id,
                            )
                        )
        return issues


class TrustSignalsRule:
    rule_id = "ANA-08"
    required_signals: dict[str, tuple[str, ...]] = {
        "contacts": ("contact", "contacts"),
        "about": ("about", "company", "about-us"),
        "privacy": ("privacy", "policy"),
        "requisites": ("requisites", "rekvizit", "terms"),
    }

    def evaluate(self, context: RuleContext) -> list[IssueCandidate]:
        paths = [(urlparse(page.url).path or "").lower() for page in context.pages]
        missing: list[str] = []
        for signal, hints in self.required_signals.items():
            if not any(any(hint in path for hint in hints) for path in paths):
                missing.append(signal)

        if not missing:
            return []

        missing_text = ", ".join(missing)
        return [
            IssueCandidate(
                rule_id=self.rule_id,
                title="Недостаточно коммерческих сигналов доверия",
                description=f"Не найдены важные trust-секции: {missing_text}.",
                recommendation=(
                    "Добавьте страницы контактов, о компании, политики и реквизитов "
                    "для повышения доверия и качества сайта."
                ),
                affected_url=None,
            )
        ]
