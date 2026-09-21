# Morning Scanner Dashboard — Planning Document

Status: **PLAN LOCKED (15 rounds) — nothing built yet.** All scope, trading-logic,
tab-layout, visual-design, and infrastructure decisions below have been answered and
confirmed by the user. Build has not started; the user will separately confirm when
to begin implementation and in what order.

Goal: A PC-based morning scanner that runs before/at market open, screens the market
(watchlist + broader universe) against 3 defined trading setups and a news/catalyst
engine, and surfaces a short, high-signal list — replacing manual headline-reading and
forcing the 40-stock watchlist to "work" every day. Pairs with a separately-built
dashboard (Yahoo Finance-style visual language, but with custom modules Yahoo doesn't
have).

---

## Decisions confirmed so far

### Scope / Universe
- **Scan target:** Watchlist (40 stocks) **+** a broader market scan for new
  "in-play" candidates outside the watchlist. Shown as separate sections/results,
  not merged into one list.

### Trading style / timeframe
- Both **day trading (intraday)** and **swing trading (days-to-weeks)** are in scope.
- Each flagged stock must be labeled with which timeframe the setup applies to —
  the dashboard should not assume one timeframe for everything.

### The 3 main setups (working names — exact rules TBD in a later round)
1. **Momentum / Breakout** — breaking out of range/prior high/consolidation on strong volume.
2. **Day 2 / Day 3 continuation** — continuation setup following an initial momentum/breakout
   day (classic multi-day momentum structure).
3. **Reversal / Mean-reversion** — oversold bounce, VWAP reclaim, support/resistance
   rejection, exhaustion reversal.

Each of these will get its own detailed rule-definition round later (indicators,
price/volume thresholds, chart pattern logic) before anything is built.

### Catalyst / "in play" news philosophy
Not a simple checklist — defined more precisely per user's notes:
- A catalyst = a specific event/data release/corporate action that triggers a
  **meaningful** price move, distinct from everyday noise.
- Two categories to detect:
  - **Scheduled:** earnings, FDA/PDUFA dates, FOMC decisions, major macro prints (e.g. NFP).
  - **Unscheduled:** M&A bids, short-seller reports, surprise guidance cuts,
    unexpected partnerships, executive departures, etc.
- **Float size is a first-class signal** — the same headline means very different things
  on a 5M-float name vs. a mega-cap. Catalyst detection should carry/estimate float
  context, not just headline text.
- **"Priced in" awareness** — the tool should be able to flag if a stock already ran
  significantly into a known scheduled event (so a beat/approval may sell off, "sell
  the news"), rather than just tagging "earnings today = bullish."
- Logging/tagging catalyst type per flagged stock matters (for the user's own future
  review), not just a yes/no "has news" flag.

---

### Run mode
- **Scheduled auto-run + web dashboard.** A background scheduled task runs the scan
  (pre-market), and the dashboard is a local web app the user opens to view results
  already generated — not something triggered manually each time.

### Brokerage accounts on file (context, not data sources)
- Baird, JPMorgan, Webull. Baird/JPM are traditional wealth-management accounts —
  no usable retail market-data API. Webull has an OpenAPI but market data requires
  its own separate paid subscription even though the user already has an account —
  doesn't save money over a dedicated data vendor, so not preferred.

### Data source recommendation (researched, pending user pick — see Round 3)
- **Alpaca** (free tier): real-time IEX quotes + free Benzinga-powered news API. $0/mo.
  Paid tier (Algo Trader Plus, $99/mo) adds full-exchange (SIP) real-time data.
- **Finnhub** (free tier): earnings calendar, analyst upgrades/downgrades, insider
  activity — useful for catalyst detection. $0/mo.
- **Polygon / massive.com** Starter plan: $29/mo, unlimited calls, 15-min delayed —
  fine for a pre-market screener since market is closed anyway. Real-time tier is $199/mo.
- **Benzinga Pro**: real-time news terminal, $197/mo — too expensive for stated
  "low amount" budget, ruled out.

### Watchlist workflow (important — shapes the whole dashboard, not just a scan)
User's actual process:
1. **Major watchlist** — reviewed every **Sunday** (broad list, relationship to the
   "40 stocks" mentioned originally needs clarifying — see Round 3).
2. **Setups watchlist** — Monday, user grades the major watchlist down to names with
   good setups.
3. **Morning scan (this tool)** — each morning, auto-generate a list of stocks meeting
   the setup + catalyst parameters (from watchlist tiers above, plus the broader
   market scan for new candidates).
4. **User grading step** — user manually grades the catalyst quality and the daily
   chart setup quality for each candidate *inside the dashboard*.
5. **Today's watchlist** — final, narrowed-down actionable list for the trading day,
   produced by the grading step.
- This means the dashboard isn't just a read-only scanner — it needs an interactive
  grading/triage workflow, and a concept of multiple watchlist tiers (major → setups →
  daily candidates → today's final list), not just one flat list.

---

### Data stack — DECIDED
- **Free stack: Alpaca (free/IEX) + Finnhub (free).** $0/mo to start.
- Briefing.com ("Briefing In Play") investigated as a conceptual match but **skipped
  entirely** — no self-serve API (manual application, case-by-case approval), so it's
  not part of the plan at all, not even as a later add-on.
- Massive.com/Polygon Starter ($29/mo) remains a known upgrade path if the free stack's
  screening coverage/speed proves insufficient once we're testing — not committed now.

### Broader market scan filters — DECIDED
- Price: **$8 and up** (no ceiling specified).
- Minimum average daily volume: **2,000,000 shares/day**.
- Minimum **Relative Volume (RVOL): 2.0x** (today's volume pace vs. its own average) —
  this is a same-day liquidity/interest filter, distinct from the avg-volume floor.

### Watchlist tiers — DECIDED
- The **40 stocks = the major watchlist** (reviewed every Sunday). The "setups
  watchlist" (Monday) is the smaller graded subset of those 40. The morning scan is a
  separate, additional layer on top (see workflow above).

### Grading scale — DECIDED
- **A+, A, A-, B+, B, B-, C+, C, C-, D.** No F. No D+/D-. (D is the floor, not graded
  further.) Applied separately to catalyst quality and chart setup quality per stock.

### Dashboard tabs — DECIDED (list; each gets its own detailed design round)
1. **Morning Scan / Candidates** — today's auto-generated list (core output).
2. **Grading / Triage workspace** — score catalyst + setup quality, narrow to today's
   final watchlist.
3. **Watchlist manager** — major watchlist (40) / setups watchlist / today's final list.
4. **Market overview (Yahoo-style)** — indices, sectors, gainers/losers, breadth.
5. **Setups tab** — clickable sub-views per setup (Momentum/Breakout, Day 2/3,
   Reversal/Mean-reversion) that filter to only stocks currently matching that specific
   setup. Added mid-round by user, not originally in the candidate list.
6. **Setting Up** — near-miss stocks approaching (but not yet meeting) a setup's
   criteria. Added mid-round by user; kept separate from the Setups tab.

---

## Setup definitions (detailed rules)

### Setup 1: Momentum / Breakout — DECIDED
- **Breakout reference level (either qualifies):** top of a multi-day
  consolidation/range, OR a 52-week/all-time high.
- **Volume confirmation:** the scan-wide 2.0x RVOL floor is sufficient — no extra
  setup-specific volume bar.
- **Timeframe:** daily chart identifies the base/candidate; intraday chart confirms the
  actual breakout trigger moment. (Both used, different jobs.)
- **Confirmation rule:** price must **close** above the level, not just wick/touch
  through it — fewer false positives.
  - *Implementation nuance to resolve during build:* "close above" likely means daily
    close for the setup/base-level qualification (known pre-market from yesterday's
    data) and intraday bar close for real-time trigger confirmation during the session
    — needs a precise technical spec when we get to build, not a planning blocker.

### Setup 2: Day 2 / Day 3 Continuation — DECIDED (one detail open)
- **Day 1 qualifying event (either qualifies):** a big % gainer on volume, OR a
  breakout day (per Setup 1's definition).
  - **OPEN: exact % threshold for "big % gainer"** — not yet specified, needed before
    build.
- **Continuation confirmation:** Day 2 (or Day 3) must print a **higher low** than
  Day 1 — this is the specific signal, not just "holding gains" generically.
- **Day count window:** **strictly Day 2-3 only** — Day 4+ is explicitly excluded from
  this setup (too extended, per user).

### Setup 2 addendum — DECIDED
- Day 1 "big % gainer" threshold: **4% for large caps, 8% for small caps**, split at a
  **$2B market cap** cutoff (≥$2B = large cap = 4% threshold; <$2B = small cap = 8%
  threshold).

### Setup 3: Reversal / Mean-Reversion — DEFINED, THEN DISABLED (see below)
- **Trigger (both required together):** climactic/exhaustion reversal — a stock that's
  been extended for multiple sessions shows exhaustion — combined with a technical
  extension measure: **distance from the 8 EMA** and **trading outside the 20-day
  Bollinger Bands**.
- **Direction:** **both** — flags oversold bounce-up candidates AND topping-out/fade-down
  candidates.
- **Timeframe:** **daily chart only** — no intraday component for this setup (unlike
  Setup 1, which uses daily+intraday together).
- **DISABLED post-launch:** after using the live dashboard, user asked to drop this
  setup entirely and focus only on Momentum/Breakout and Day 2/3 Continuation. The
  rule definition above is kept for reference and the code
  (`app/setups/reversal.py`) is left in place, tested and working — it's just no
  longer called from `app/setups/engine.py`. Easy to re-enable later if wanted.

---

## Visual design — DECIDED (specifics)
- **Density:** cleaner/more spaced out overall, EXCEPT scan/candidate data tables,
  which can stay dense/packed since that's where the information value is.
- **Theme:** **dark theme** (pre-market/early-morning use case).
- **Accent color:** explicitly **NOT** Yahoo's purple — user wants a different accent
  color. **Exact color still open — next round.**
- Overall: styled after Yahoo Finance's layout/information conventions, but not a
  visual clone — user wants pieces Yahoo doesn't have (per original request) and its
  own color identity.

---

## Visual design — accent color DECIDED
- **Royal blue (primary) + yellow (accent).** Not Yahoo's purple. Red/green stay
  reserved for price-move direction (gain/loss) — royal blue/yellow used for UI
  elements (active tab, buttons, highlights), not price data, to avoid confusion.

---

## Tab 1: Morning Scan / Candidates — DECIDED (layout)
- **Visible per-row (at a glance, before clicking in):**
  - Setup type matched (Momentum/Breakout, Day 2/3, Reversal) + timeframe (day trade
    vs. swing).
  - Catalyst summary (short headline/tag: earnings, upgrade, M&A, etc. + scheduled vs.
    unscheduled).
  - Key stats: price, % change, RVOL, volume (float shown if available from data source).
- **Layout:** **one combined, sortable list** (not split into separate panels/sub-tabs)
  with a **source tag/filter** (watchlist vs. broader market scan) so it can be
  filtered down when needed, without being visually split by default.
- **Grading display:** if a stock was graded before (e.g. from the Sunday/Monday
  watchlist review), show that **prior grade as reference context** on this tab — but
  the Triage tab still produces a **fresh grade each morning**, it doesn't just reuse
  the old one.

---

## Tab 2: Grading / Triage workspace — DECIDED (layout)
- **Flow:** table view by default (overview of all candidates); clicking a row expands
  into a detail panel (chart + catalyst detail) to actually grade that stock.
- **Promotion to Today's Watchlist:** **grade-threshold auto-promote** — stocks meeting
  a defined grade threshold (on both catalyst and setup grades) automatically land on
  Today's Watchlist, no separate manual "add" click needed.
  - **OPEN: exact threshold value** (e.g. B- or better on both?) — not yet specified.
- **Notes field:** **none** — grades only, no free-text journal field, keeps triage fast.
- **Default sort order:** by **catalyst strength/RVOL** — most "in play" names first,
  so the most important candidates get triaged first if time is short.

---

## Tab 2 addendum — DECIDED
- Auto-promotion threshold: **B- or better on BOTH catalyst grade and setup grade.**

## Tab 3: Watchlist Manager — DECIDED (layout)
- **Editing the major watchlist (40 names):** simple **manual add/remove in the UI**
  (type a ticker to add, click to remove). No bulk import, no per-stock notes field.

## Tab 5: Setups tab — DECIDED (scope)
- Each setup sub-view (Momentum/Breakout, Day 2/3, Reversal) includes **both**
  watchlist and broader-market-scan stocks — same universe as Morning Scan, just
  filtered/organized by pattern type instead of shown as one list.

## Tab 6: "Setting Up" — NEW TAB (added mid-round by user)
- A dedicated tab for **near-miss stocks** — approaching a setup's trigger criteria but
  not fully qualifying yet (e.g. approaching a breakout level, nearing Day 2 higher-low
  confirmation, extension building toward Reversal criteria but not confirmed).
- Kept **separate** from the Setups tab (which only shows fully-qualified, triggered
  setups) rather than shown as a sub-section within it.
- Detailed criteria for what counts as "near" each setup's threshold — TBD in a later
  round alongside final setup-algorithm specs.

## Tab 4: Market Overview — DECIDED (this is the dashboard's landing/home tab)
- **Contents:**
  - Major indices (S&P 500, Nasdaq, Dow, Russell 2000) with pre-market futures.
  - Sector performance (leaders/laggards pre-market).
  - Economic calendar (scheduled macro catalysts — FOMC, NFP, CPI, etc.).
  - Earnings calendar — **today's earnings + the week ahead** (separate from the
    general econ calendar; ties to the "earnings" catalyst type).
  - **Full sector overview (expanded, not a separate tab):** all **11 GICS sectors**
    covered daily (not just movers — shows "no major catalyst" when nothing's driving
    a sector), each with its "driver" attribution:
    - A dominant stock's news dragging the whole sector (e.g. a mega-cap's
      earnings/guidance move), **and/or**
    - Macro/policy news specific to that sector (e.g. Fed decision → Financials, oil
      prices → Energy, FDA news → Healthcare).
    - Both attribution types can apply; not mutually exclusive.
  - This **replaces/absorbs** the earlier, narrower "1 big news item for top 2
    performing sectors weekly" idea — full daily sector coverage supersedes it.
- **Role:** this is the **landing/home tab** — first thing shown when the dashboard
  opens each morning. Morning Scan/Candidates is a click away, not the default view.

---

## Tab 6 addendum — DECIDED
- Near-miss proximity bar: **tight — within ~2-3% of the full trigger** (exact metric
  per setup — e.g. % from breakout level, % toward higher-low confirmation, proximity
  to 8 EMA/Bollinger Band extension — to be pinned down in the technical spec during
  build, but the tolerance itself is tight/strict, not loose).

---

## Operations — DECIDED
- **Alerting:** **none.** No desktop notifications, no alerts — user opens the
  dashboard themselves each morning and the pre-run scan results are just there.
- **Run time:** scheduled scan runs **8:00 AM ET** each morning (via Windows Task
  Scheduler), well ahead of the 9:30 AM open, using max available pre-market data.
- **API accounts:** user doesn't have Alpaca/Finnhub accounts yet — **walkthrough
  needed at build time**, not now.
- **Relationship to existing dashboard:** **standalone, separate application** — this
  scanner is NOT merging into or feeding the user's other Yahoo Finance-style
  dashboard. Used side by side as two separate tools.

## Tech stack — APPROVED
- **Backend:** Python + FastAPI.
- **Scheduler:** Windows Task Scheduler triggers the pre-market scan script (8:00 AM ET).
- **Storage:** SQLite (local, file-based — single-user tool, no server needed).
- **Frontend:** React app served locally, for the interactive parts (sortable/filterable
  tables, expandable Triage detail rows, grade dropdowns), dark theme, royal
  blue/yellow accents, Yahoo Finance-inspired density conventions per tab.
- **Data layer:** Alpaca (free/IEX + news) + Finnhub (free) behind an abstraction layer,
  so Massive/Polygon Starter ($29/mo) can be swapped in later without a rewrite if the
  free tier proves insufficient.

---

## Open questions / not yet decided
- None outstanding from the planning rounds so far — see "Ready to build?" note below.
- Minor implementation nuances flagged inline above (e.g. exact intraday vs. daily
  "close above level" mechanics for Setup 1, exact per-setup near-miss metric for
  Tab 6) will be pinned down as part of the technical spec once building starts, not
  planning blockers.
- Alerting (in-app only vs. notification of some kind) — user said PC-focused, not phone.
- How the finished dashboard hands off to / integrates with the user's separately-built
  Yahoo Finance-style dashboard.
- Tech stack for implementation (not yet discussed — will confirm once functional scope
  is fully settled).

---

## Round log
- **Round 1 (scope & trading substance):** scan universe, trading style, setup
  categories, catalyst philosophy — captured above.
- **Round 2 (infrastructure):** data budget context, run mode, watchlist workflow
  revealed to be multi-stage (major → setups → daily candidates → today's list).
- **Round 3 (research + refinement):** researched Alpaca/Finnhub/Massive/Benzinga
  pricing; confirmed 40 = major watchlist; grading scale started; price floor $8.
- **Round 4 (decisions locked):** Briefing.com skipped; volume/RVOL filters set;
  grading scale finalized; dashboard tab list finalized (5 tabs incl. user-added
  Setups tab).
- **Round 5 (Setup 1 rules):** Momentum/Breakout fully defined — captured above.
- **Round 6 (Setup 2 rules):** Day 2/3 continuation mostly defined — % threshold for
  Day 1 still open.
- **Round 7 (Setup 3 + Setup 2 close-out):** Reversal/Mean-Reversion fully defined;
  market-cap cutoff for Setup 2 thresholds set at $2B.
- **Round 8 (visual design):** density, theme, and accent-color direction set — exact
  accent color still open.
- **Round 9 (accent color + Morning Scan tab design):** royal blue/yellow accent
  chosen; Tab 1 (Morning Scan/Candidates) layout fully defined — captured above.
- **Round 10 (Triage tab design):** Tab 2 layout defined — grade-threshold auto-promote
  chosen, exact threshold still open.
- **Round 11 (threshold + Tabs 3/5/6):** promotion threshold set (B- both grades);
  Watchlist Manager and Setups tab scope defined; new "Setting Up" tab (Tab 6) added
  for near-miss stocks.
- **Round 12 (Market Overview tab):** Tab 4 fully defined and confirmed as the
  dashboard's landing/home tab.
- **Round 13 (operations):** alerting, integration-with-existing-dashboard decided —
  standalone/separate app, no notifications.
- **Round 14 (tech stack + wrap-up):** stack approved (FastAPI + SQLite + React + Task
  Scheduler), run time set to 8:00 AM ET, near-miss bar set to tight (~2-3%).
- **Round 15 (sector overview addition):** user added a full daily sector-driver
  breakdown, expanding Tab 4's sector section — all 11 GICS sectors, dual attribution
  logic (dominant stock news + sector macro/policy news). Supersedes the earlier
  "top 2 sectors weekly" idea.
- **Post-launch (live dashboard use):** after building and using the real thing, user
  disabled Setup 3 (Reversal/Mean-Reversion) to focus only on Momentum/Breakout and
  Day 2/3 Continuation. Also fixed several live-testing bugs (Alpaca snapshot parsing,
  Finnhub rate limiting, mistagged/roundup news attribution, a joinedload cartesian
  duplication bug, a same-day re-run race condition) and added a PM Vol % column.
