from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.routes._common import serialize_candidate
from app.api.schemas import CandidateOut, GradeIn
from app.db.base import get_db
from app.db.models import Grade, ScanCandidate
from app.grading import is_valid_grade, qualifies_for_todays_watchlist

router = APIRouter(prefix="/api/triage", tags=["triage"])


def _today_candidates_query(db: Session):
    today = dt.date.today()
    return (
        db.query(ScanCandidate)
        .options(
            # selectinload avoids the cartesian-product duplication that
            # joinedload'ing two "many" relationships together causes -- see
            # scan.py for the full explanation.
            selectinload(ScanCandidate.setup_matches),
            selectinload(ScanCandidate.catalyst_tags),
            joinedload(ScanCandidate.grade),
        )
        .filter(ScanCandidate.scan_date == today)
    )


@router.get("/candidates", response_model=list[CandidateOut])
def get_triage_candidates(db: Session = Depends(get_db)):
    """Tab 2: Grading/Triage -- default sort is catalyst strength/RVOL, most 'in
    play' first (PLANNING.md Tab 2)."""
    candidates = _today_candidates_query(db).order_by(ScanCandidate.rvol.desc()).all()
    return [serialize_candidate(db, c) for c in candidates]


@router.post("/candidates/{candidate_id}/grade", response_model=CandidateOut)
def grade_candidate(candidate_id: int, grade_in: GradeIn, db: Session = Depends(get_db)):
    if not is_valid_grade(grade_in.catalyst_grade) or not is_valid_grade(grade_in.setup_grade):
        raise HTTPException(status_code=422, detail="Grade must be one of A+, A, A-, B+, B, B-, C+, C, C-, D")

    candidate = db.get(ScanCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    grade = db.query(Grade).filter(Grade.candidate_id == candidate_id).first()
    if grade is None:
        grade = Grade(candidate_id=candidate_id)
        db.add(grade)
    grade.catalyst_grade = grade_in.catalyst_grade
    grade.setup_grade = grade_in.setup_grade
    grade.graded_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(candidate)
    return serialize_candidate(db, candidate)


@router.get("/todays-watchlist", response_model=list[CandidateOut])
def get_todays_watchlist(db: Session = Depends(get_db)):
    """Auto-promotion: B- or better on BOTH catalyst and setup grades
    (PLANNING.md Tab 2 addendum)."""
    candidates = _today_candidates_query(db).all()
    promoted = [
        c
        for c in candidates
        if c.grade and qualifies_for_todays_watchlist(c.grade.catalyst_grade, c.grade.setup_grade)
    ]
    return [serialize_candidate(db, c) for c in promoted]
