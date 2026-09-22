"""Rule-based grade suggestions for the Triage tab (PLANNING.md Tab 2).

Computes a starting-point A+ to D grade for catalyst quality (per the user's
explicit rubric -- see _catalyst_grade_for_tag) and setup quality (confluence,
Day-3 confirmation, RVOL/move-size). This is a SUGGESTION the frontend uses to
pre-fill the Triage grading dropdowns -- the user still confirms or overrides it
and clicks Save before it counts toward the B-or-better auto-promotion to Today's
Watchlist (grading.py).
"""

from __future__ import annotations

from app.grading import GRADE_RANK, GRADE_SCALE

# Catalyst categories that count as "big news that impacts the business" for the
# A/A+ tier below. "earnings" is handled separately since it's the only category
# that's ever tagged kind="scheduled" in our data (see catalysts/scoring.py).
_HIGH_IMPACT_CATEGORIES = {"ma", "fda", "short_report"}
# "meaningful to the company, but doesn't alter it in any big way" -- the B tier.
_MODERATE_IMPACT_CATEGORIES = {"analyst", "guidance", "offering", "halt"}
# "other" (real, relevant news that doesn't match a known category) falls through
# to C -- "it's news, but it's not very impactful". "market_wide" (mistagged/
# generic roundup, see catalysts/scoring.py) is D -- news we can disregard.

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


def _catalyst_grade_for_tag(tag) -> str:
    """A/B/C/D rubric, per the user's explicit definition:
      A = big news that impacts the business and has NOT already been priced in.
          A+ specifically if it has a known timeline (a scheduled event, not a
          surprise -- in our data, only earnings is ever tagged kind="scheduled").
      B = news that's meaningful to the company, but doesn't alter it in any big way.
      C = there is news, but it's not very impactful.
      D = no news, or news that can be disregarded.
    """
    if tag.category == "market_wide":
        return "D"  # mistagged/generic roundup -- disregard, per catalysts/scoring.py

    if tag.priced_in_flag:
        # Big news that already ran into is priced in -- real, meaningful news, but
        # the opportunity is degraded (possible "sell the news"), not a clean A.
        return "C"

    if tag.category in _HIGH_IMPACT_CATEGORIES or tag.category == "earnings":
        return "A+" if tag.kind == "scheduled" else "A"

    if tag.category in _MODERATE_IMPACT_CATEGORIES:
        return "B"

    return "C"  # "other" -- news exists, but isn't very impactful


def suggest_catalyst_grade(candidate) -> str:
    tags = candidate.catalyst_tags
    if not tags:
        return GRADE_SCALE[0]  # no news at all -- D

    # Best tag wins -- one great catalyst shouldn't be dragged down to a lower
    # grade just because a weaker/irrelevant headline also showed up for the
    # same candidate.
    return max((_catalyst_grade_for_tag(t) for t in tags), key=lambda g: GRADE_RANK[g])


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
