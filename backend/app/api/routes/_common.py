from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.api.schemas import CandidateOut, GradeOut
from app.db.models import Grade, ScanCandidate


def get_prior_grade(db: Session, ticker: str, before_date: dt.date) -> GradeOut | None:
    row = (
        db.query(Grade)
        .join(ScanCandidate, Grade.candidate_id == ScanCandidate.id)
        .filter(ScanCandidate.ticker == ticker, ScanCandidate.scan_date < before_date)
        .filter(Grade.catalyst_grade.isnot(None))
        .order_by(ScanCandidate.scan_date.desc())
        .first()
    )
    if row is None:
        return None
    return GradeOut.model_validate(row)


def serialize_candidate(db: Session, candidate: ScanCandidate) -> CandidateOut:
    out = CandidateOut.model_validate(candidate)
    out.prior_grade = get_prior_grade(db, candidate.ticker, candidate.scan_date)
    return out
