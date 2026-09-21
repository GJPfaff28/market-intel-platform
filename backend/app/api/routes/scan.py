from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.routes._common import serialize_candidate
from app.api.schemas import CandidateOut
from app.db.base import get_db
from app.db.models import CandidateSource, ScanCandidate

router = APIRouter(prefix="/api/scan", tags=["morning-scan"])


@router.get("/candidates", response_model=list[CandidateOut])
def get_candidates(
    source: CandidateSource | None = Query(None, description="Filter: watchlist or broader_scan"),
    db: Session = Depends(get_db),
):
    """Tab 1: Morning Scan / Candidates -- one combined, sortable list with a
    source tag/filter (PLANNING.md Tab 1)."""
    today = dt.date.today()
    query = (
        db.query(ScanCandidate)
        .options(
            joinedload(ScanCandidate.setup_matches),
            joinedload(ScanCandidate.catalyst_tags),
            joinedload(ScanCandidate.grade),
        )
        .filter(ScanCandidate.scan_date == today)
    )
    if source is not None:
        query = query.filter(ScanCandidate.source == source)

    candidates = query.order_by(ScanCandidate.rvol.desc()).all()
    return [serialize_candidate(db, c) for c in candidates]
