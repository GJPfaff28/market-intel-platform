"""Rule-based grade suggestions for the Triage tab (PLANNING.md Tab 2).

Computes a starting-point A+ to D grade for catalyst quality and setup quality from
the same signals a trader would look at: catalyst type / float amplification /
priced-in for catalyst quality, setup confluence / confirmation / RVOL for setup
quality. This is a SUGGESTION the frontend uses to pre-fill the Triage grading
dropdowns -- the user still confirms or overrides it and clicks Save before it
counts toward the B-or-better auto-promotion to Today's Watchlist (grading.py). The
scoring below is intentionally simple and inspectable (not a black box) so the
thresholds can be tuned once real grading feedback comes in.
"""

from __future__ import annotations

from app.grading import GRADE_SCALE

LOW_FLOAT_SHARES = 20_000_000
HIGH_FLOAT_SHARES = 300_000_000

# Points awarded for the single best-scoring catalyst tag on a candidate (not
# summed across tags, so five generic headlines can't out-score one real one).
_CATEGORY_POINTS = {
    "ma": 3,
    "fda": 3,
    "short_report": 3,
    "earnings": 2,
    "analyst": 2,
    "guidance": 1,
    "offering": 1,
    "halt": 1,
    "other": 0,
    "market_wide": 0,  # mistagged/generic roundup -- see catalysts/scoring.py
}

_GRADE_THRESHOLDS = [
    (7, "A+"),
    (6, "A"),
    (5, "A-"),
    (4, "B+"),
    (3, "B"),
    (2, "B-"),
    (1, "C+"),
    (0, "C"),
    (-1, "C-"),
]


def _points_to_grade(points: float) -> str:
    for threshold, grade in _GRADE_THRESHOLDS:
        if points >= threshold:
            return grade
    return GRADE_SCALE[0]  # "D"


def _volume_and_move_bonus(rvol: float, pct_change: float) -> float:
    bonus = 0.0
    if rvol >= 3.0:
        bonus += 1.0
    elif rvol >= 2.0:
        bonus += 0.5
    if abs(pct_change) >= 10:
        bonus += 1.0
    elif abs(pct_change) >= 5:
        bonus += 0.5
    return bonus


def _float_bonus(float_shares: float | None) -> float:
    if float_shares is None:
        return 0.0
    if float_shares < LOW_FLOAT_SHARES:
        return 1.0  # low float amplifies the move, per PLANNING.md catalyst philosophy
    if float_shares > HIGH_FLOAT_SHARES:
        return -0.5
    return 0.0


def suggest_catalyst_grade(candidate) -> str:
    tags = candidate.catalyst_tags
    if not tags:
        return GRADE_SCALE[0]  # no catalyst at all -- not genuinely "in play"

    best_category_points = max(_CATEGORY_POINTS.get(t.category, 0) for t in tags)
    any_priced_in = any(t.priced_in_flag for t in tags)

    points = best_category_points
    if any_priced_in:
        points -= 2  # PLANNING.md: a stock that already ran into the event may be "sold the news"

    points += _volume_and_move_bonus(candidate.rvol, candidate.pct_change)
    points += _float_bonus(candidate.float_shares)

    return _points_to_grade(points)


def suggest_setup_grade(candidate) -> str:
    matches = candidate.setup_matches
    if not matches:
        return GRADE_SCALE[0]

    unique_setup_types = {m.setup_type for m in matches}
    points = 2.0 * len(unique_setup_types)  # confluence: multiple setups triggering = stronger

    # Day 3 is only ever recorded once the Day 2 higher-low is already confirmed on
    # completed bars (setups/day2_3.py) -- a firmer signal than a same-day-only read.
    if any(getattr(m, "day_number", None) == 3 for m in matches):
        points += 1.0

    points += _volume_and_move_bonus(candidate.rvol, candidate.pct_change)

    return _points_to_grade(points)
