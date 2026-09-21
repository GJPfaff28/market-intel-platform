from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import NearMissOut
from app.db.base import get_db
from app.db.models import NearMiss, SetupType

router = APIRouter(prefix="/api/setting-up", tags=["setting-up"])


@router.get("", response_model=list[NearMissOut])
def get_near_misses(
    setup_type: SetupType | None = Query(None),
    db: Session = Depends(get_db),
):
    """Tab 6: Setting Up -- near-miss stocks within ~2-3% of a setup's trigger,
    kept separate from the fully-qualified Setups tab (PLANNING.md Tab 6)."""
    today = dt.date.today()
    query = db.query(NearMiss).filter(NearMiss.scan_date == today)
    if setup_type is not None:
        query = query.filter(NearMiss.setup_type == setup_type)
    return query.order_by(NearMiss.proximity_pct.asc()).all()
