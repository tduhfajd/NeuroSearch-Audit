from __future__ import annotations

from dataclasses import dataclass

PACKAGE_START = "Start"
PACKAGE_GROWTH = "Growth"
PACKAGE_AUTHORITY = "Authority"


@dataclass(slots=True)
class PackageDecision:
    package_name: str
    rationale: str
    trigger_metrics: dict[str, int]


def choose_package(*, p0_count: int, p1_count: int, p2_count: int) -> PackageDecision:
    trigger_metrics = {"P0": p0_count, "P1": p1_count, "P2": p2_count}

    if p0_count >= 3 or (p0_count >= 1 and p1_count >= 4):
        return PackageDecision(
            package_name=PACKAGE_AUTHORITY,
            rationale="Высокий критический риск (P0) и значимый объем P1.",
            trigger_metrics=trigger_metrics,
        )

    if p0_count >= 1 or p1_count >= 4 or (p1_count >= 2 and p2_count >= 4):
        return PackageDecision(
            package_name=PACKAGE_GROWTH,
            rationale="Нужна приоритетная стабилизация по P0/P1 и базовая AI-оптимизация.",
            trigger_metrics=trigger_metrics,
        )

    return PackageDecision(
        package_name=PACKAGE_START,
        rationale="Преобладают улучшения невысокой критичности, достаточно стартового пакета.",
        trigger_metrics=trigger_metrics,
    )
