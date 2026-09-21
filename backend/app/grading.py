"""A+ to D letter grading scale (no F, no D+/D-), per PLANNING.md."""

GRADE_SCALE = ["D", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"]
GRADE_RANK = {grade: rank for rank, grade in enumerate(GRADE_SCALE)}

PROMOTION_THRESHOLD = "B-"


def is_valid_grade(grade: str) -> bool:
    return grade in GRADE_RANK


def meets_threshold(grade: str, threshold: str = PROMOTION_THRESHOLD) -> bool:
    if not is_valid_grade(grade):
        return False
    return GRADE_RANK[grade] >= GRADE_RANK[threshold]


def qualifies_for_todays_watchlist(catalyst_grade: str | None, setup_grade: str | None) -> bool:
    """Auto-promotion rule: B- or better on BOTH catalyst and setup grades."""
    if not catalyst_grade or not setup_grade:
        return False
    return meets_threshold(catalyst_grade) and meets_threshold(setup_grade)
