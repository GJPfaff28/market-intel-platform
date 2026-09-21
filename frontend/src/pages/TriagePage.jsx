import { useEffect, useState } from "react";
import { api, GRADE_OPTIONS } from "../api/client";
import { CatalystBadge, GradePill, PctChange, SetupBadge, SourceBadge, TimeframeBadge } from "../components/Badges";
import { dedupeSetupMatches } from "../utils";

function qualifies(grade) {
  const rank = ["D", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"];
  if (!grade?.catalyst_grade || !grade?.setup_grade) return false;
  return rank.indexOf(grade.catalyst_grade) >= rank.indexOf("B-") && rank.indexOf(grade.setup_grade) >= rank.indexOf("B-");
}

export function TriagePage() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [draftGrades, setDraftGrades] = useState({ catalyst_grade: "", setup_grade: "" });
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    api
      .triageCandidates()
      .then(setCandidates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const selected = candidates.find((c) => c.id === selectedId);

  function selectCandidate(c) {
    setSelectedId(c.id);
    setDraftGrades({
      catalyst_grade: c.grade?.catalyst_grade || c.suggested_catalyst_grade || "",
      setup_grade: c.grade?.setup_grade || c.suggested_setup_grade || "",
    });
  }

  async function saveGrade() {
    if (!draftGrades.catalyst_grade || !draftGrades.setup_grade) return;
    setSaving(true);
    try {
      const updated = await api.gradeCandidate(selectedId, draftGrades.catalyst_grade, draftGrades.setup_grade);
      setCandidates((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Grading / Triage</h1>
        <p>
          Sorted by catalyst strength / RVOL — most "in play" first. Grade catalyst + setup quality (A+ to D). B- or
          better on both auto-promotes to Today's Watchlist.
        </p>
      </div>

      {loading && <div className="empty-state">Loading…</div>}
      {error && <div className="empty-state">Failed to load: {error}</div>}

      {!loading && !error && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Source</th>
                <th>Setup</th>
                <th>Price</th>
                <th>% Chg</th>
                <th>RVol</th>
                <th>Catalyst Grade</th>
                <th>Setup Grade</th>
                <th>Today's List?</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => (
                <tr key={c.id} className={selectedId === c.id ? "selected" : ""} onClick={() => selectCandidate(c)}>
                  <td className="ticker-cell">{c.ticker}</td>
                  <td>
                    <SourceBadge source={c.source} />
                  </td>
                  <td style={{ whiteSpace: "normal", maxWidth: 220 }}>
                    {dedupeSetupMatches(c.setup_matches).map((m, i) => (
                      <span key={i} style={{ display: "inline-block", marginBottom: 2 }}>
                        <SetupBadge setupType={m.setup_type} dayNumber={m.day_number} />
                      </span>
                    ))}
                  </td>
                  <td>${c.price.toFixed(2)}</td>
                  <td>
                    <PctChange value={c.pct_change} />
                  </td>
                  <td>{c.rvol.toFixed(1)}x</td>
                  <td>
                    <GradePill
                      grade={c.grade?.catalyst_grade || c.suggested_catalyst_grade}
                      suggested={!c.grade?.catalyst_grade}
                    />
                  </td>
                  <td>
                    <GradePill
                      grade={c.grade?.setup_grade || c.suggested_setup_grade}
                      suggested={!c.grade?.setup_grade}
                    />
                  </td>
                  <td>{qualifies(c.grade) ? "✅" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <div className="detail-panel">
          <div className="detail-panel__grid">
            <div>
              <h2 style={{ fontSize: 16, marginTop: 0 }}>
                {selected.ticker} — ${selected.price.toFixed(2)} (<PctChange value={selected.pct_change} />)
              </h2>
              <p style={{ color: "var(--text-muted)", fontSize: 12.5 }}>
                RVol {selected.rvol.toFixed(1)}x · Avg Vol {selected.avg_volume.toLocaleString()} · Day Vol{" "}
                {selected.day_volume.toLocaleString()}
                {selected.float_shares ? ` · Float ~${(selected.float_shares / 1_000_000).toFixed(1)}M` : ""}
              </p>

              <h3 style={{ fontSize: 12.5, textTransform: "uppercase", color: "var(--text-muted)" }}>Setup Match</h3>
              {dedupeSetupMatches(selected.setup_matches).map((m, i) => (
                <div key={i} className="catalyst-item">
                  <SetupBadge setupType={m.setup_type} dayNumber={m.day_number} /> <TimeframeBadge timeframe={m.timeframe} />
                  <div style={{ marginTop: 4, color: "var(--text-muted)" }}>{m.detail}</div>
                </div>
              ))}

              <h3 style={{ fontSize: 12.5, textTransform: "uppercase", color: "var(--text-muted)" }}>Catalysts</h3>
              {selected.catalyst_tags.length === 0 && <div className="empty-state">No catalyst detected.</div>}
              {selected.catalyst_tags.map((tag, i) => (
                <div key={i} className="catalyst-item">
                  <CatalystBadge kind={tag.kind} /> {tag.summary}
                  {tag.priced_in_flag && <span className="badge badge-priced-in" style={{ marginLeft: 6 }}>Priced in?</span>}
                </div>
              ))}
            </div>

            <div>
              <h3 style={{ fontSize: 12.5, textTransform: "uppercase", color: "var(--text-muted)" }}>Grade this candidate</h3>
              {!selected.grade?.catalyst_grade && !selected.grade?.setup_grade && (
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: -4, marginBottom: 12 }}>
                  Pre-filled with the program's suggested grade — review and adjust before saving.
                </p>
              )}
              <div style={{ display: "flex", gap: 16, marginBottom: 14 }}>
                <label>
                  <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginBottom: 4 }}>Catalyst Grade</div>
                  <select
                    className="grade-select"
                    value={draftGrades.catalyst_grade}
                    onChange={(e) => setDraftGrades((d) => ({ ...d, catalyst_grade: e.target.value }))}
                  >
                    <option value="">—</option>
                    {GRADE_OPTIONS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginBottom: 4 }}>Setup Grade</div>
                  <select
                    className="grade-select"
                    value={draftGrades.setup_grade}
                    onChange={(e) => setDraftGrades((d) => ({ ...d, setup_grade: e.target.value }))}
                  >
                    <option value="">—</option>
                    {GRADE_OPTIONS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <button className="btn" onClick={saveGrade} disabled={saving || !draftGrades.catalyst_grade || !draftGrades.setup_grade}>
                {saving ? "Saving…" : "Save Grade"}
              </button>
              {selected.prior_grade && (
                <p style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
                  Prior grade: {selected.prior_grade.catalyst_grade} catalyst / {selected.prior_grade.setup_grade} setup
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
