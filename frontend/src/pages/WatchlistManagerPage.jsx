import { useEffect, useState } from "react";
import { api } from "../api/client";
import { PctChange, SourceBadge } from "../components/Badges";

export function WatchlistManagerPage() {
  const [watchlist, setWatchlist] = useState([]);
  const [todaysList, setTodaysList] = useState([]);
  const [newTicker, setNewTicker] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function load() {
    setLoading(true);
    Promise.all([api.watchlist(), api.todaysWatchlist()])
      .then(([wl, today]) => {
        setWatchlist(wl);
        setTodaysList(today);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!newTicker.trim()) return;
    await api.addToWatchlist(newTicker.trim().toUpperCase());
    setNewTicker("");
    load();
  }

  async function handleRemove(ticker) {
    await api.removeFromWatchlist(ticker);
    load();
  }

  async function handleToggleSetups(ticker, value) {
    await api.toggleSetupsWatchlist(ticker, value);
    load();
  }

  const setupsWatchlist = watchlist.filter((w) => w.in_setups_watchlist);

  return (
    <div>
      <div className="page-header">
        <h1>Watchlist Manager</h1>
        <p>Major watchlist (Sunday review) → setups watchlist (Monday curation) → today's final list (auto-promoted).</p>
      </div>

      {error && <div className="empty-state">Failed to load: {error}</div>}

      <div className="card">
        <h2>Major Watchlist ({watchlist.length})</h2>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          <input
            className="text-input"
            placeholder="Add ticker (e.g. AAPL)"
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
          />
          <button className="btn" type="submit">
            Add
          </button>
        </form>

        {!loading && watchlist.length === 0 && <div className="empty-state">No tickers yet — add your 40 names above.</div>}

        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>In Setups Watchlist</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((w) => (
                <tr key={w.ticker}>
                  <td className="ticker-cell">{w.ticker}</td>
                  <td>
                    <input
                      type="checkbox"
                      checked={w.in_setups_watchlist}
                      onChange={(e) => handleToggleSetups(w.ticker, e.target.checked)}
                    />
                  </td>
                  <td>
                    <button className="btn-outline btn" onClick={() => handleRemove(w.ticker)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card-grid">
        <div className="card">
          <h2>Setups Watchlist ({setupsWatchlist.length})</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 12.5, marginTop: -6 }}>
            The subset of your major watchlist with good setups (Monday curation).
          </p>
          {setupsWatchlist.length === 0 && <div className="empty-state">Check the box above to add names here.</div>}
          {setupsWatchlist.map((w) => (
            <div key={w.ticker} className="catalyst-item">
              {w.ticker}
            </div>
          ))}
        </div>

        <div className="card">
          <h2>Today's Final Watchlist ({todaysList.length})</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 12.5, marginTop: -6 }}>
            Auto-promoted from Triage: B- or better on both catalyst and setup grades.
          </p>
          {todaysList.length === 0 && <div className="empty-state">Nothing promoted yet — grade candidates in Triage.</div>}
          {todaysList.map((c) => (
            <div key={c.id} className="catalyst-item">
              <strong>{c.ticker}</strong> <SourceBadge source={c.source} /> — ${c.price.toFixed(2)} (<PctChange value={c.pct_change} />)
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
