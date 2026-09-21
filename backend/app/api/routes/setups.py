from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.routes._common import serialize_candidate
from app.api.schemas import CandidateOut
from app.db.base import get_db
from app.db.models import ScanCandidate, SetupMatch, SetupType

router = APIRouter(prefix="/api/setups", tags=["setups"])


@router.get("/{setup_type}", response_model=list[CandidateOut])
def get_setup_candidates(setup_type: SetupType, db: Session = Depends(get_db)):
    """Tab 5: Setups -- per-pattern sub-view. Includes both watchlist and
    broader-scan stocks, same universe as Morning Scan (PLANNING.md Tab 5)."""
    today = dt.date.today()
    candidates = (
        db.query(ScanCandidate)
        .join(SetupMatch, SetupMatch.candidate_id == ScanCandidate.id)
        .options(
            # selectinload avoids the cartesian-product duplication that
            # joinedload'ing two "many" relationships together causes -- see
            # scan.py for the full explanation.
            selectinload(ScanCandidate.setup_matches),
            selectinload(ScanCandidate.catalyst_tags),
            joinedload(ScanCandidate.grade),
        )
        .filter(ScanCandidate.scan_date == today, SetupMatch.setup_type == setup_type)
        .order_by(ScanCandidate.rvol.desc())
        .all()
    )
    return [serialize_candidate(db, c) for c in candidates]
