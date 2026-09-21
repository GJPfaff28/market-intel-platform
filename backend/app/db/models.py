from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CandidateSource(str, enum.Enum):
    WATCHLIST = "watchlist"
    BROADER_SCAN = "broader_scan"


class Timeframe(str, enum.Enum):
    DAY_TRADE = "day_trade"
    SWING = "swing"
    BOTH = "both"


class SetupType(str, enum.Enum):
    MOMENTUM_BREAKOUT = "momentum_breakout"
    DAY_2_3 = "day_2_3"
    REVERSAL = "reversal"


class CatalystKind(str, enum.Enum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"


class DriverType(str, enum.Enum):
    DOMINANT_STOCK = "dominant_stock"
    MACRO_POLICY = "macro_policy"
    BOTH = "both"
    NONE = "none"


class WatchlistStock(Base):
    """The 40-name major watchlist, reviewed Sundays. Manual add/remove."""

    __tablename__ = "watchlist_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    in_setups_watchlist: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class ScanCandidate(Base):
    """One row per ticker per morning scan run."""

    __tablename__ = "scan_candidates"
    __table_args__ = (UniqueConstraint("scan_date", "ticker", name="uq_candidate_date_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_date: Mapped[dt.date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    source: Mapped[CandidateSource] = mapped_column(String(20))

    price: Mapped[float] = mapped_column(Float)
    pct_change: Mapped[float] = mapped_column(Float)
    rvol: Mapped[float] = mapped_column(Float)
    avg_volume: Mapped[int] = mapped_column(Integer)
    day_volume: Mapped[int] = mapped_column(Integer, default=0)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    float_shares: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    setup_matches: Mapped[list["SetupMatch"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    catalyst_tags: Mapped[list["CatalystTag"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    grade: Mapped["Grade | None"] = relationship(back_populates="candidate", uselist=False, cascade="all, delete-orphan")


class SetupMatch(Base):
    """Which setup(s) a candidate matched, plus the timeframe that setup applies to."""

    __tablename__ = "setup_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("scan_candidates.id"))
    setup_type: Mapped[SetupType] = mapped_column(String(30))
    timeframe: Mapped[Timeframe] = mapped_column(String(20))
    day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # for Day 2/3 setup
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # human-readable "why it matched"

    candidate: Mapped[ScanCandidate] = relationship(back_populates="setup_matches")


class CatalystTag(Base):
    """News/catalyst context attached to a candidate."""

    __tablename__ = "catalyst_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("scan_candidates.id"))
    kind: Mapped[CatalystKind] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(40))  # earnings, fda, fomc, ma, short_report, analyst, guidance, other
    summary: Mapped[str] = mapped_column(Text)
    priced_in_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    candidate: Mapped[ScanCandidate] = relationship(back_populates="catalyst_tags")


class Grade(Base):
    """User-assigned grades for a candidate on a given scan day. Fresh each morning."""

    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("scan_candidates.id"), unique=True)
    catalyst_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    setup_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    graded_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    candidate: Mapped[ScanCandidate] = relationship(back_populates="grade")


class NearMiss(Base):
    """'Setting Up' tab: stocks close to (but not yet meeting) a setup's trigger."""

    __tablename__ = "near_misses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_date: Mapped[dt.date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    setup_type: Mapped[SetupType] = mapped_column(String(30))
    proximity_pct: Mapped[float] = mapped_column(Float)  # how close to the trigger, e.g. 0.02 = 2%
    price: Mapped[float] = mapped_column(Float)
    pct_change: Mapped[float] = mapped_column(Float)
    rvol: Mapped[float] = mapped_column(Float)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class SectorOverview(Base):
    """Daily driver attribution for each of the 11 GICS sectors."""

    __tablename__ = "sector_overview"
    __table_args__ = (UniqueConstraint("scan_date", "sector_name", name="uq_sector_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_date: Mapped[dt.date] = mapped_column(Date, index=True)
    sector_name: Mapped[str] = mapped_column(String(40))
    pct_change: Mapped[float] = mapped_column(Float)
    driver_type: Mapped[DriverType] = mapped_column(String(20))
    driver_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketOverviewSnapshot(Base):
    """Cached daily market overview data (indices, econ calendar, earnings calendar)."""

    __tablename__ = "market_overview_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_date: Mapped[dt.date] = mapped_column(Date, unique=True, index=True)
    indices_json: Mapped[str] = mapped_column(Text)
    econ_calendar_json: Mapped[str] = mapped_column(Text)
    earnings_calendar_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
