# Morning Scanner Dashboard

A PC-based morning scanner that screens your watchlist plus the broader market
against 3 trading setups and a catalyst/news engine, then gives you a dashboard to
triage and grade the results into a final daily watchlist. See `PLANNING.md` for the
full spec this was built from.

Two pieces, run separately:

- **`backend/`** — Python/FastAPI API + the scan logic + SQLite database.
- **`frontend/`** — React dashboard (dark theme) that talks to the backend.

---

## 1. Getting API keys

The scanner needs two free accounts. Neither requires a paid plan to get started.

### Alpaca (market data + news)

1. Go to https://alpaca.markets and sign up (a free "Paper Trading" account is
   enough — you don't need to fund it or connect a bank).
2. From the dashboard, go to **API Keys** and generate a new key pair.
3. Copy the **Key ID** and **Secret Key** — you'll paste these into `backend/.env`.

Free tier gives you real-time IEX quotes and Benzinga-powered news headlines. If you
later want full-exchange (SIP) real-time data, Alpaca's paid "Algo Trader Plus" tier
is $99/mo — not required to run this.

### Finnhub (earnings calendar, analyst actions, market cap)

1. Go to https://finnhub.io/register and sign up.
2. Your API key is shown on the dashboard homepage after signup — no card required.

Some endpoints (economic calendar, upgrade/downgrade history) are gated on Finnhub's
paid tiers; the scanner is written to fail soft (skip that piece, not crash) if your
plan doesn't include them.

### Wire the keys in

```bash
cd backend
cp .env.example .env
# open .env and paste in ALPACA_API_KEY, ALPACA_SECRET_KEY, FINNHUB_API_KEY
```

---

## 2. Running it locally

### First-time setup (do this once)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../frontend
npm install
```

The database (`backend/scanner.db`) is created automatically the first time the
backend runs.

### Every time after that: double-click `start-dashboard.bat`

No commands to remember. From the repo's root folder, double-click
**`start-dashboard.bat`**. It opens two windows (backend + frontend) and your
browser automatically at http://localhost:5173. Leave both windows open while you
use the dashboard; close them (or Ctrl+C in each) when you're done.

The dashboard opens on **Market Overview** (the landing tab) — it'll be empty until
you've run a scan (see below).

If you'd rather run the two pieces by hand (e.g. to see their logs directly), each
has its own shortcut too — `backend\start-backend.bat` and
`frontend\start-frontend.bat` — or the manual commands:

```bash
# backend, in its own terminal
cd backend
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
uvicorn app.main:app --port 8000

# frontend, in a second terminal
cd frontend
npm run dev
```

### Add your watchlist

Go to the **Watchlist Manager** tab and add your 40 tickers (or however many you're
starting with). This is a manual add/remove list, same as the planning doc decided.

### Run a scan manually (before setting up the schedule)

Double-click **`run-scan.bat`** from the repo's root (needs the backend window
already running). It can take 2-3 minutes — that's expected, the free-tier APIs are
rate-limited. Refresh the dashboard once it finishes.

Or by hand:

```bash
curl -X POST http://localhost:8000/api/scan/run
```

or open http://localhost:8000/docs and hit `POST /api/scan/run` from the Swagger UI.

---

## 3. Scheduling the morning scan (Windows Task Scheduler)

The plan calls for the scan to run automatically at **8:00 AM ET** every weekday, so
results are already sitting there when you open the dashboard — no notifications, no
manual trigger needed day-to-day.

1. Open **Task Scheduler** (Start menu → search "Task Scheduler").
2. **Create Task…** (not "Basic Task" — you want the extra options).
3. **General** tab: name it `Morning Scanner Scan`. Check "Run whether user is
   logged on or not" if you want it to fire even if you're not at the PC yet.
4. **Triggers** tab → **New…** → Daily, start time **8:00:00 AM**, and set it to
   repeat on weekdays. (Set your Windows timezone correctly, or adjust the time for
   ET if your PC is on a different zone.)
5. **Actions** tab → **New…**:
   - **Program/script**: the full path to `python.exe` inside `backend/venv/Scripts/`
     (e.g. `C:\path\to\market-intel-platform\backend\venv\Scripts\python.exe`)
   - **Add arguments**: `-m app.scheduler.run_morning_scan`
   - **Start in**: the full path to the `backend` folder
     (e.g. `C:\path\to\market-intel-platform\backend`)
6. Save. Test it once with **Run** in Task Scheduler and confirm
   `backend/scanner.db` gets updated (or check the dashboard).

The frontend doesn't need to be running for the scheduled scan to work — it just
needs the backend's `app` package and `.env` to be present. Open the dashboard
whenever you sit down; the data will already be there.

---

## 4. Growing the scan universe

The broader-market scan (as opposed to your watchlist) reads from
`backend/data/universe.csv` — a starter list of ~120 liquid tickers across all 11
GICS sectors, shipped so the scanner works out of the box without extra setup. That's
why a scan reports a `tickers_evaluated` count around 100-150 (your watchlist plus this
starter list) instead of covering the whole market.

To scan the real full market instead, run the built-in refresh script — it pulls
NASDAQ's free, public list of every listed US ticker (thousands of names) and saves it
alongside the starter list:

```
cd backend
venv\Scripts\activate          (Windows)   or   source venv/bin/activate   (Mac/Linux)
python -m app.scan.refresh_universe
```

This writes `backend/data/universe_full.csv`. From then on, every scan automatically
merges it with the curated `universe.csv` — no further setup needed, and `git pull`
won't touch it (it's per-machine and gitignored). Re-run the command occasionally to
pick up newly listed/delisted tickers.

Only `universe.csv`'s curated names carry a GICS sector, so newly discovered tickers
from `universe_full.csv` won't show up in the Market Overview tab's sector breakdown —
they'll still be scanned for setups and catalysts like any other candidate.

---

## 5. Known MVP limitations (from PLANNING.md's implementation notes)

- **Setup 1 (Momentum/Breakout)** "close above the level" is evaluated against the
  most recently completed daily bar, since the scan runs pre-market. The intraday
  hold/confirmation once the market opens is a judgment call for you, not something
  the scan can see yet.
- **Setup 3 (Reversal)**'s "distance from 8 EMA" extension threshold
  (`EMA8_EXTENSION_PCT` in `backend/app/setups/reversal.py`) is a starting default
  (10%) — the planning rounds specified the indicators but not this exact number.
  Tune it once you're seeing real candidates.
- **Sector driver attribution** (Market Overview tab) pulls a general market news feed
  (Alpaca, no symbol filter) each morning and matches headlines against a per-sector
  keyword list (`app/catalysts/sectors.py`) for the macro/policy half, plus a
  per-ticker headline lookup for the dominant-stock half. The keyword list is a
  reasonable starting set, not exhaustive — expand `_SECTOR_MACRO_KEYWORDS` if you
  notice a real driver getting missed.
- **Float shares** are approximated from Finnhub's shares-outstanding figure (its
  free tier doesn't expose true free-float).
- **Data stack** is the free Alpaca + Finnhub tier. If scan coverage/speed proves
  insufficient, `backend/app/data_providers/` is structured so a Massive/Polygon
  provider can be added alongside `alpaca.py` without touching the setup/catalyst
  logic — see PLANNING.md's data source notes.
