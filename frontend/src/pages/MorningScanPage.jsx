import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CandidateTable } from "../components/CandidateTable";

const FILTERS = [
  { key: null, label: "All" },
  { key: "watchlist", label: "Watchlist" },
  { key: "broader_scan", label: "Market Scan" },
];

export function MorningScanPage() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sourceFilter, setSourceFilter] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .scanCandidates(sourceFilter)
      .then(setCandidates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sourceFilter]);

  return (
    <div>
      <div className="page-header">
        <h1>Morning Scan / Candidates</h1>
        <p>Today's auto-generated list — watchlist and broader market scan, filtered by setup + catalyst criteria.</p>
      </div>

      <div className="filter-bar">
        {FILTERS.map((f) => (
          <button
            key={f.label}
            className={`filter-chip${sourceFilter === f.key ? " active" : ""}`}
            onClick={() => setSourceFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading && <div className="empty-state">Loading…</div>}
      {error && <div className="empty-state">Failed to load: {error}</div>}
      {!loading && !error && <CandidateTable candidates={candidates} />}
    </div>
  );
}
