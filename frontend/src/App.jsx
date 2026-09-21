import { NavLink, Route, Routes } from "react-router-dom";
import { MarketOverviewPage } from "./pages/MarketOverviewPage";
import { MorningScanPage } from "./pages/MorningScanPage";
import { TriagePage } from "./pages/TriagePage";
import { WatchlistManagerPage } from "./pages/WatchlistManagerPage";
import { SetupsPage } from "./pages/SetupsPage";
import { SettingUpPage } from "./pages/SettingUpPage";

const NAV_ITEMS = [
  { to: "/", label: "Market Overview", end: true },
  { to: "/scan", label: "Morning Scan" },
  { to: "/triage", label: "Grading / Triage" },
  { to: "/watchlist", label: "Watchlist Manager" },
  { to: "/setups", label: "Setups" },
  { to: "/setting-up", label: "Setting Up" },
];

export default function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <div className="app-nav__brand">
          Morning<span>Scan</span>
        </div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `app-nav__link${isActive ? " active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<MarketOverviewPage />} />
          <Route path="/scan" element={<MorningScanPage />} />
          <Route path="/triage" element={<TriagePage />} />
          <Route path="/watchlist" element={<WatchlistManagerPage />} />
          <Route path="/setups" element={<SetupsPage />} />
          <Route path="/setting-up" element={<SettingUpPage />} />
        </Routes>
      </main>
    </div>
  );
}
