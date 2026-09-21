import { useEffect, useState } from "react";
import { api, SETUP_LABELS } from "../api/client";
import { PctChange, SetupBadge } from "../components/Badges";

const SETUP_TYPES = ["momentum_breakout", "day_2_3"];

export function SettingUpPage() {
  const [activeSetup, setActiveSetup] = useState(null);
  const [nearMisses, setNearMisses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .settingUp(activeSetup)
      .then(setNearMisses)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [activeSetup]);

  return (
    <div>
      <div className="page-header">
        <h1>Setting Up</h1>
        <p>Near-miss stocks — within ~2-3% of triggering a setup, but not there yet. Kept separate from confirmed Setups matches.</p>
      </div>

      <div className="filter-bar">
        <button className={`filter-chip${activeSetup === null ? " active" : ""}`} onClick={() => setActiveSetup(null)}>
          All
        </button>
        {SETUP_TYPES.map((s) => (
          <button
            key={s}
            className={`filter-chip${activeSetup === s ? " active" : ""}`}
            onClick={() => setActiveSetup(s)}
          >
            {SETUP_LABELS[s]}
          </button>
        ))}
      </div>

      {loading && <div className="empty-state">Loading…</div>}
      {error && <div className="empty-state">Failed to load: {error}</div>}

      {!loading && !error && nearMisses.length === 0 && <div className="empty-state">Nothing watching right now.</div>}

      {!loading && !error && nearMisses.length > 0 && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Setup</th>
                <th>Proximity</th>
                <th>Price</th>
                <th>% Chg</th>
                <th>RVol</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {nearMisses.map((nm, i) => (
                <tr key={i}>
                  <td className="ticker-cell">{nm.ticker}</td>
                  <td>
                    <SetupBadge setupType={nm.setup_type} />
                  </td>
                  <td>{(nm.proximity_pct * 100).toFixed(1)}%</td>
                  <td>${nm.price.toFixed(2)}</td>
                  <td>
                    <PctChange value={nm.pct_change} />
                  </td>
                  <td>{nm.rvol.toFixed(1)}x</td>
                  <td style={{ whiteSpace: "normal" }}>{nm.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
