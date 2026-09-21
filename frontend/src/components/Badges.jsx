import { SETUP_LABELS } from "../api/client";

export function SourceBadge({ source }) {
  return (
    <span className={`badge badge-source-${source}`}>
      {source === "watchlist" ? "Watchlist" : "Market Scan"}
    </span>
  );
}

export function SetupBadge({ setupType, dayNumber }) {
  const label = SETUP_LABELS[setupType] || setupType;
  return (
    <span className="badge badge-setup">
      {label}
      {dayNumber ? ` (Day ${dayNumber})` : ""}
    </span>
  );
}

export function TimeframeBadge({ timeframe }) {
  const label = { day_trade: "Day Trade", swing: "Swing", both: "Day/Swing" }[timeframe] || timeframe;
  return <span className="badge badge-setup">{label}</span>;
}

export function CatalystBadge({ kind }) {
  return <span className={`badge badge-${kind}`}>{kind === "scheduled" ? "Scheduled" : "Unscheduled"}</span>;
}

export function GradePill({ grade, suggested }) {
  if (!grade) return <span className="grade-pill" style={{ opacity: 0.4 }}>—</span>;
  if (suggested) {
    return (
      <span className="grade-pill" style={{ borderStyle: "dashed", opacity: 0.75 }} title="Suggested by program — not yet confirmed">
        {grade}*
      </span>
    );
  }
  return <span className="grade-pill">{grade}</span>;
}

export function PctChange({ value }) {
  const cls = value >= 0 ? "pos" : "neg";
  const sign = value >= 0 ? "+" : "";
  return <span className={`pct ${cls}`}>{sign}{value.toFixed(2)}%</span>;
}
