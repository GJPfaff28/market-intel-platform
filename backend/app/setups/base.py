from __future__ import annotations

from dataclasses import dataclass

from app.db.models import SetupType, Timeframe


@dataclass
class SetupMatchResult:
    setup_type: SetupType
    timeframe: Timeframe
    detail: str
    day_number: int | None = None


@dataclass
class NearMissResult:
    setup_type: SetupType
    proximity_pct: float  # 0.02 == 2% away from triggering
    detail: str
