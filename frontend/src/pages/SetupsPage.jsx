import { useEffect, useState } from "react";
import { api, SETUP_LABELS } from "../api/client";
import { CandidateTable } from "../components/CandidateTable";

const SETUP_TYPES = ["momentum_breakout", "day_2_3", "reversal"];

export function SetupsPage() {
  const [activeSetup, setActiveSetup] = useState(SETUP_TYPES[0]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .setupCandidates(activeSetup)
      .then(setCandidates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [activeSetup]);

  return (
    <div>
      <div className="page-header">
        <h1>Setups</h1>
        <p>Click a pattern to see only stocks currently matching it — watchlist + broader market scan combined.</p>
      </div>

      <div className="filter-bar">
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
      {!loading && !error && <CandidateTable candidates={candidates} />}
    </div>
  );
}
