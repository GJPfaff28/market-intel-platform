from __future__ import annotations

import datetime as dt
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import MarketOverviewOut, SectorOverviewOut
from app.db.base import get_db
from app.db.models import MarketOverviewSnapshot, SectorOverview

router = APIRouter(prefix="/api/market-overview", tags=["market-overview"])


@router.get("", response_model=MarketOverviewOut)
def get_market_overview(db: Session = Depends(get_db)):
    today = dt.date.today()
    snapshot = db.query(MarketOverviewSnapshot).filter(MarketOverviewSnapshot.scan_date == today).first()
    sectors = db.query(SectorOverview).filter(SectorOverview.scan_date == today).all()

    return MarketOverviewOut(
        scan_date=snapshot.scan_date if snapshot else None,
        indices=json.loads(snapshot.indices_json) if snapshot else {},
        sectors=[SectorOverviewOut.model_validate(s) for s in sectors],
        econ_calendar=json.loads(snapshot.econ_calendar_json) if snapshot else [],
        earnings_calendar=json.loads(snapshot.earnings_calendar_json) if snapshot else [],
    )
