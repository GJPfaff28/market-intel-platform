const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${options.method || "GET"} ${path} failed: ${res.status} ${body}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  triggerScan: () => request("/api/scan/run", { method: "POST" }),

  marketOverview: () => request("/api/market-overview"),

  scanCandidates: (source) => request(`/api/scan/candidates${source ? `?source=${source}` : ""}`),

  triageCandidates: () => request("/api/triage/candidates"),
  gradeCandidate: (candidateId, catalystGrade, setupGrade) =>
    request(`/api/triage/candidates/${candidateId}/grade`, {
      method: "POST",
      body: JSON.stringify({ catalyst_grade: catalystGrade, setup_grade: setupGrade }),
    }),
  todaysWatchlist: () => request("/api/triage/todays-watchlist"),

  watchlist: () => request("/api/watchlist"),
  addToWatchlist: (ticker) => request("/api/watchlist", { method: "POST", body: JSON.stringify({ ticker }) }),
  removeFromWatchlist: (ticker) => request(`/api/watchlist/${ticker}`, { method: "DELETE" }),
  toggleSetupsWatchlist: (ticker, value) =>
    request(`/api/watchlist/${ticker}/setups-watchlist?in_setups_watchlist=${value}`, { method: "PATCH" }),

  setupCandidates: (setupType) => request(`/api/setups/${setupType}`),

  settingUp: (setupType) => request(`/api/setting-up${setupType ? `?setup_type=${setupType}` : ""}`),
};

export const SETUP_LABELS = {
  momentum_breakout: "Momentum / Breakout",
  day_2_3: "Day 2/3 Continuation",
  reversal: "Reversal / Mean-Reversion",
};

export const GRADE_OPTIONS = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D"];
