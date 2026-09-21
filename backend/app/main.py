from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import market_overview, scan, setting_up, setups, triage, watchlist
from app.db.base import get_db, init_db
from app.scan.orchestrator import run_morning_scan

app = FastAPI(title="Morning Scanner Dashboard API")

# Local-only tool: the React dev server (Vite default) and the built frontend both
# run on localhost, so a permissive local CORS policy is fine here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/scan/run")
def trigger_scan(db: Session = Depends(get_db)):
    """Manual trigger for the morning scan -- useful for testing without waiting
    for the 8:00 AM ET scheduled run. Same logic the scheduler calls."""
    return run_morning_scan(db)


app.include_router(market_overview.router)
app.include_router(scan.router)
app.include_router(triage.router)
app.include_router(watchlist.router)
app.include_router(setups.router)
app.include_router(setting_up.router)
