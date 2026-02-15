import { useApi, API_BASE } from "./useApi";
import type { PipelineState, Donation, Stats } from "./types";
import "./App.css";

/* ── Helpers ─────────────────────────────────────────────── */

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

const CAT_COLORS: Record<string, string> = {
  fruit: "#e8a87c",
  snack: "#c38d9e",
  drink: "#6fa2bd",
};

/* ── Pipeline Stage ──────────────────────────────────────── */

function PipelineStage({ state }: { state: PipelineState | null }) {
  const isActive = state != null && state.mode !== "idle" && state.mode !== "error";
  const showResult = state?.mode === "classified" && state.last_result;

  return (
    <section className="card pipeline">
      <div className="stage-header">
        <h2>
          <span className={`dot ${isActive ? "live" : ""}`} />
          Live Pipeline Stage
        </h2>
        {state && <span className="stage-status">{state.status_text}</span>}
      </div>

      <div className="stage-body">
        {/* MJPEG stream is always visible — no overlay blocks it */}
        <div className="camera-wrapper">
          <img
            className="camera-feed"
            src={`${API_BASE}/pipeline/stream`}
            alt="Live camera feed"
          />
        </div>

        {showResult && state.last_result && (
          <div className="result-panel fade-in">
            <div className="result-badge">Claude Classification Complete</div>
            <div className="result-grid">
              <ResultCell label="Item" value={state.last_result.item_name} />
              <ResultCell label="Category" value={state.last_result.category} />
              <ResultCell
                label="Est. Weight"
                value={
                  state.last_result.estimated_weight_lbs != null
                    ? `${state.last_result.estimated_weight_lbs} lbs`
                    : "—"
                }
              />
              <ResultCell
                label="Est. Expiry"
                value={state.last_result.estimated_expiry ?? "N/A"}
              />
              <ResultCell
                label="Donation"
                value={`#${state.last_result.donation_id}`}
              />
              <ResultCell label="Status" value={state.status_text} />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function ResultCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="result-cell">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

/* ── Stats ────────────────────────────────────────────────── */

function StatsGrid({ stats }: { stats: Stats | null }) {
  return (
    <div className="stats-grid">
      <div className="card stat">
        <div className="label">Total Items</div>
        <div className="big-number">{stats?.total_items ?? 0}</div>
      </div>
      <div className="card stat">
        <div className="label">Weight Collected</div>
        <div className="big-number">
          {stats?.total_weight_lbs ?? 0}
          <span className="unit"> lbs</span>
        </div>
      </div>
      <div className="card stat">
        <div className="label">Unique Donors</div>
        <div className="big-number">{stats?.unique_donors ?? 0}</div>
      </div>
    </div>
  );
}

/* ── Category Breakdown ───────────────────────────────────── */

function CategoryBreakdown({ stats }: { stats: Stats | null }) {
  const cats = stats?.by_category ?? {};
  const total = stats?.total_items || 1;

  return (
    <section className="card">
      <h2>Category Breakdown</h2>
      <div className="bars">
        {(["fruit", "snack", "drink"] as const).map((cat) => {
          const count = cats[cat] ?? 0;
          const pct = Math.max((count / total) * 100, 4);
          return (
            <div className="bar-row" key={cat}>
              <span className="bar-label">{cat}</span>
              <div
                className="bar"
                style={{ width: `${pct}%`, background: CAT_COLORS[cat] }}
              >
                {count}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* ── Donation Feed ────────────────────────────────────────── */

function DonationFeed({ donations }: { donations: Donation[] }) {
  const sorted = [...donations].reverse();

  return (
    <section className="card">
      <h2>
        <span className="dot live" /> Live Donation Feed
      </h2>

      {sorted.length === 0 ? (
        <div className="placeholder">
          <p>📦</p>
          <p>No donations yet. Waiting for first item...</p>
        </div>
      ) : (
        <div className="donation-list">
          {sorted.map((d) => (
            <div className="donation-card" key={d.id}>
              <div className="donation-header">
                <span className="dim">Donation #{d.id}</span>
                <span className="dim">{fmtTime(d.timestamp)}</span>
              </div>
              <div className="donation-name">{d.item_name}</div>
              <div className="donation-meta">
                <span className={`badge ${d.category}`}>{d.category}</span>
                <span>{d.estimated_weight_lbs ?? "?"} lbs</span>
                <span>{d.estimated_expiry ?? "N/A"}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ── App ──────────────────────────────────────────────────── */

export default function App() {
  const { stats, donations, pipeline, error } = useApi(600);

  return (
    <div className="container">
      <header className="header">
        <div className="logo-row">
          <div className="logo">🌲</div>
          <div>
            <h1>Project Lend</h1>
            <p className="subtitle">The autonomous food bank</p>
          </div>
        </div>
        <p className="partner">
          Powered by Claude AI · Ecumenical Hunger Program – Palo Alto
        </p>
      </header>

      {error && (
        <div className="card error-banner">
          <p>⚠️ {error}</p>
        </div>
      )}

      <PipelineStage state={pipeline} />
      <StatsGrid stats={stats} />
      <CategoryBreakdown stats={stats} />
      <DonationFeed donations={donations} />
    </div>
  );
}
