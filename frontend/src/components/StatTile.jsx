export function StatTile({ label, value, pct }) {
  const pctCls = pct == null ? "" : pct >= 0 ? "pos" : "neg";
  const pctSign = pct == null ? "" : pct >= 0 ? "+" : "";
  return (
    <div className="stat-tile">
      <div className="stat-tile__label">{label}</div>
      <div className="stat-tile__value">
        {value}
        {pct != null && (
          <span className={`pct ${pctCls}`} style={{ fontSize: 13, marginLeft: 8 }}>
            {pctSign}
            {pct.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
}
