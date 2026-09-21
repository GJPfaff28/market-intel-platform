"""Sector driver attribution for the Market Overview tab's daily sector breakdown
(PLANNING.md, Tab 4 -- all 11 GICS sectors, dual attribution: dominant-stock news
and/or sector macro/policy news).
"""

from __future__ import annotations

from dataclasses import dataclass

GICS_SECTORS = [
    "Information Technology",
    "Health Care",
    "Financials",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Utilities",
    "Real Estate",
    "Materials",
]

# Keyword hints used to match macro/policy headlines to the sector(s) they drive.
_SECTOR_MACRO_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Financials": ("federal reserve", "fomc", "interest rate", "fed rate", "yield curve", "bank regulation"),
    "Energy": ("oil price", "opec", "crude", "natural gas", "energy department"),
    "Health Care": ("fda", "cms", "drug pricing", "medicare", "medicaid"),
    "Real Estate": ("mortgage rate", "housing starts", "home sales"),
    "Utilities": ("interest rate", "regulatory rate case"),
    "Materials": ("tariff", "commodity price", "china demand"),
    "Information Technology": ("chip export", "semiconductor tariff", "ai regulation"),
    "Industrials": ("tariff", "manufacturing pmi", "supply chain"),
    "Consumer Discretionary": ("consumer spending", "retail sales"),
    "Consumer Staples": ("inflation", "cpi", "food prices"),
    "Communication Services": ("antitrust", "spectrum auction", "media regulation"),
}

DOMINANT_STOCK_WEIGHT_THRESHOLD = 0.02  # a single name moving the sector avg by 2%+ counts as "dominant"


@dataclass
class SectorDriver:
    driver_type: str  # "dominant_stock" | "macro_policy" | "both" | "none"
    summary: str | None


def attribute_sector_driver(
    sector_name: str,
    sector_pct_change: float,
    top_mover_ticker: str | None,
    top_mover_pct_change: float | None,
    top_mover_headline: str | None,
    macro_headlines: list[str],
) -> SectorDriver:
    dominant_stock_summary = None
    if (
        top_mover_ticker
        and top_mover_pct_change is not None
        and abs(top_mover_pct_change) >= abs(sector_pct_change) + DOMINANT_STOCK_WEIGHT_THRESHOLD * 100
    ):
        headline_part = f' — "{top_mover_headline}"' if top_mover_headline else ""
        dominant_stock_summary = f"{top_mover_ticker} ({top_mover_pct_change:+.1f}%){headline_part}"

    macro_summary = None
    keywords = _SECTOR_MACRO_KEYWORDS.get(sector_name, ())
    for headline in macro_headlines:
        text = headline.lower()
        if any(kw in text for kw in keywords):
            macro_summary = headline
            break

    if dominant_stock_summary and macro_summary:
        return SectorDriver("both", f"{dominant_stock_summary}; also: {macro_summary}")
    if dominant_stock_summary:
        return SectorDriver("dominant_stock", dominant_stock_summary)
    if macro_summary:
        return SectorDriver("macro_policy", macro_summary)
    return SectorDriver("none", None)
