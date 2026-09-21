from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class SetupMatchOut(BaseModel):
    setup_type: str
    timeframe: str
    day_number: int | None
    detail: str

    class Config:
        from_attributes = True


class CatalystTagOut(BaseModel):
    kind: str
    category: str
    summary: str
    priced_in_flag: bool

    class Config:
        from_attributes = True


class GradeOut(BaseModel):
    catalyst_grade: str | None
    setup_grade: str | None

    class Config:
        from_attributes = True


class CandidateOut(BaseModel):
    id: int
    ticker: str
    source: str
    price: float
    pct_change: float
    rvol: float
    avg_volume: int
    day_volume: int
    market_cap: float | None
    float_shares: float | None
    setup_matches: list[SetupMatchOut]
    catalyst_tags: list[CatalystTagOut]
    grade: GradeOut | None
    prior_grade: GradeOut | None = None
    suggested_catalyst_grade: str | None = None
    suggested_setup_grade: str | None = None

    class Config:
        from_attributes = True


class GradeIn(BaseModel):
    catalyst_grade: str
    setup_grade: str


class NearMissOut(BaseModel):
    ticker: str
    setup_type: str
    proximity_pct: float
    price: float
    pct_change: float
    rvol: float
    detail: str | None

    class Config:
        from_attributes = True


class WatchlistStockOut(BaseModel):
    ticker: str
    in_setups_watchlist: bool
    added_at: dt.datetime

    class Config:
        from_attributes = True


class WatchlistAddIn(BaseModel):
    ticker: str


class SectorOverviewOut(BaseModel):
    sector_name: str
    pct_change: float
    driver_type: str
    driver_summary: str | None

    class Config:
        from_attributes = True


class MarketOverviewOut(BaseModel):
    scan_date: dt.date | None
    indices: dict
    sectors: list[SectorOverviewOut]
    econ_calendar: list[dict]
    earnings_calendar: list[dict]
