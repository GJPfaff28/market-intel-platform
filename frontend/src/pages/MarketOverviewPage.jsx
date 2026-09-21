import { useEffect, useState } from "react";
import { api } from "../api/client";
import { StatTile } from "../components/StatTile";

const DRIVER_LABELS = {
  dominant_stock: "Driven by a single stock",
  macro_policy: "Macro/policy driven",
  both: "Stock + macro driven",
  none: "No major catalyst",
};

export function MarketOverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .marketOverview()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="empty-state">Loading market overview…</div>;
  if (error) return <div className="empty-state">Failed to load: {error}</div>;

  const noData = !data.scan_date;

  return (
    <div>
      <div className="page-header">
        <h1>Market Overview</h1>
        <p>
          {data.scan_date
            ? `As of this morning's scan (${data.scan_date})`
            : "No scan has run yet — run the morning scan to populate this page."}
        </p>
      </div>

      {noData && (
        <div className="card">
          <div className="empty-state">
            Nothing here yet. Trigger a scan (backend: <code>POST /api/scan/run</code>, or wait for the
            8:00 AM ET scheduled job) once your Alpaca/Finnhub API keys are configured.
          </div>
        </div>
      )}

      {!noData && (
        <>
          <div className="card">
            <h2>Indices</h2>
            <div className="card-grid">
              {Object.entries(data.indices).map(([label, info]) => (
                <StatTile key={label} label={`${label} (${info.proxy_ticker})`} value={`$${info.price.toFixed(2)}`} pct={info.pct_change} />
              ))}
            </div>
          </div>

          <div className="card">
            <h2>Sector Performance &amp; Drivers</h2>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Sector</th>
                    <th>% Chg</th>
                    <th>Driver</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {data.sectors.map((s) => (
                    <tr key={s.sector_name}>
                      <td style={{ fontWeight: 600 }}>{s.sector_name}</td>
                      <td className={`pct ${s.pct_change >= 0 ? "pos" : "neg"}`}>
                        {s.pct_change >= 0 ? "+" : ""}
                        {s.pct_change.toFixed(2)}%
                      </td>
                      <td>{DRIVER_LABELS[s.driver_type] || s.driver_type}</td>
                      <td style={{ whiteSpace: "normal" }}>{s.driver_summary || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card-grid">
            <div className="card">
              <h2>Economic Calendar</h2>
              {data.econ_calendar.length === 0 && <div className="empty-state">No scheduled events.</div>}
              {data.econ_calendar.map((e, i) => (
                <div key={i} className="catalyst-item">
                  <strong>{e.date}</strong> — {e.event} {e.country ? `(${e.country})` : ""}
                </div>
              ))}
            </div>
            <div className="card">
              <h2>Earnings Calendar (Today + Week Ahead)</h2>
              {data.earnings_calendar.length === 0 && <div className="empty-state">No earnings scheduled.</div>}
              {data.earnings_calendar.map((e, i) => (
                <div key={i} className="catalyst-item">
                  <strong>{e.ticker}</strong> — {e.date} ({e.when})
                  {e.eps_estimate != null ? ` · EPS est. ${e.eps_estimate}` : ""}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
