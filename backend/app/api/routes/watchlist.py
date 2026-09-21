from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import WatchlistAddIn, WatchlistStockOut
from app.db.base import get_db
from app.db.models import WatchlistStock

router = APIRouter(prefix="/api/watchlist", tags=["watchlist-manager"])


@router.get("", response_model=list[WatchlistStockOut])
def list_watchlist(db: Session = Depends(get_db)):
    """Tab 3: Watchlist Manager -- the major watchlist (40 names, reviewed Sundays)."""
    return db.query(WatchlistStock).order_by(WatchlistStock.ticker).all()


@router.post("", response_model=WatchlistStockOut, status_code=201)
def add_to_watchlist(payload: WatchlistAddIn, db: Session = Depends(get_db)):
    """Manual add/remove in the UI (PLANNING.md Tab 3 -- no bulk import, no notes)."""
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=422, detail="Ticker required")
    existing = db.query(WatchlistStock).filter(WatchlistStock.ticker == ticker).first()
    if existing:
        return existing
    stock = WatchlistStock(ticker=ticker)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/{ticker}", status_code=204)
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(WatchlistStock).filter(WatchlistStock.ticker == ticker.upper()).first()
    if stock is None:
        raise HTTPException(status_code=404, detail="Ticker not on watchlist")
    db.delete(stock)
    db.commit()


@router.patch("/{ticker}/setups-watchlist", response_model=WatchlistStockOut)
def toggle_setups_watchlist(ticker: str, in_setups_watchlist: bool, db: Session = Depends(get_db)):
    """Marks/unmarks a major-watchlist name as part of the Monday-curated
    'setups watchlist' subset (PLANNING.md watchlist workflow)."""
    stock = db.query(WatchlistStock).filter(WatchlistStock.ticker == ticker.upper()).first()
    if stock is None:
        raise HTTPException(status_code=404, detail="Ticker not on watchlist")
    stock.in_setups_watchlist = in_setups_watchlist
    db.commit()
    db.refresh(stock)
    return stock
