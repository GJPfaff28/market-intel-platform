import { useMemo, useState } from "react";
import { CatalystBadge, GradePill, PctChange, SetupBadge, SourceBadge, TimeframeBadge } from "./Badges";

const COLUMNS = [
  { key: "ticker", label: "Ticker" },
  { key: "source", label: "Source" },
  { key: "setups", label: "Setup" },
  { key: "catalyst", label: "Catalyst" },
  { key: "price", label: "Price" },
  { key: "pct_change", label: "% Chg" },
  { key: "rvol", label: "RVol" },
  { key: "day_volume", label: "Volume" },
  { key: "prior_grade", label: "Prior Grade" },
];

function sortValue(candidate, key) {
  switch (key) {
    case "setups":
      return candidate.setup_matches?.[0]?.setup_type || "";
    case "catalyst":
      return candidate.catalyst_tags?.[0]?.summary || "";
    case "prior_grade":
      return candidate.prior_grade?.catalyst_grade || "";
    default:
      return candidate[key];
  }
}

export function CandidateTable({ candidates, onSelectTicker, selectedTicker }) {
  const [sortKey, setSortKey] = useState("rvol");
  const [sortDir, setSortDir] = useState("desc");

  const sorted = useMemo(() => {
    const copy = [...candidates];
    copy.sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      if (av === bv) return 0;
      const cmp = av > bv ? 1 : -1;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [candidates, sortKey, sortDir]);

  function handleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  if (candidates.length === 0) {
    return <div className="empty-state">No candidates yet. Run the morning scan to populate this list.</div>;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th key={col.key} onClick={() => handleSort(col.key)} style={{ cursor: "pointer" }}>
                {col.label}
                {sortKey === col.key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((c) => (
            <tr
              key={c.id}
              className={selectedTicker === c.ticker ? "selected" : ""}
              onClick={() => onSelectTicker?.(c.ticker)}
            >
              <td className="ticker-cell">{c.ticker}</td>
              <td>
                <SourceBadge source={c.source} />
              </td>
              <td>
                {c.setup_matches.map((m, i) => (
                  <span key={i} style={{ marginRight: 6 }}>
                    <SetupBadge setupType={m.setup_type} dayNumber={m.day_number} />
                  </span>
                ))}
                {c.setup_matches[0] && <TimeframeBadge timeframe={c.setup_matches[0].timeframe} />}
              </td>
              <td style={{ maxWidth: 260, whiteSpace: "normal" }}>
                {c.catalyst_tags[0] ? (
                  <>
                    <CatalystBadge kind={c.catalyst_tags[0].kind} /> {c.catalyst_tags[0].summary}
                    {c.catalyst_tags[0].priced_in_flag && <span className="badge badge-priced-in" style={{ marginLeft: 6 }}>Priced in?</span>}
                  </>
                ) : (
                  <span className="empty-state" style={{ padding: 0 }}>
                    —
                  </span>
                )}
              </td>
              <td>${c.price.toFixed(2)}</td>
              <td>
                <PctChange value={c.pct_change} />
              </td>
              <td>{c.rvol.toFixed(1)}x</td>
              <td>{c.day_volume.toLocaleString()}</td>
              <td>
                <GradePill grade={c.prior_grade?.catalyst_grade} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
