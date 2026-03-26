# Dashboard rationalization — summary (20260325_1900Z)

## 1) Tabs removed and why

| Removed (UI) | Why |
|--------------|-----|
| **Natural Language Auditor (XAI)** | STALE / non-authoritative for decisions: narrative explanations without strict join to exit_attribution strict cohort; duplicated “why” hints better served by explicit log-backed columns on Closed Trades. Backend routes `/api/xai/*` remain for scripts; no tab. |
| **Telemetry Health** (More ▾) | MERGED into **System Health & Data Integrity**: canonical log table, direction readiness, contract gate, and droplet analysis now ship in one governed panel via `/api/dashboard/data_integrity` (plus bundle pointer from `/api/telemetry/latest/index`). Standalone `/api/telemetry_health` kept for compatibility. |

## 2) Tabs kept and why

| Tab | Purpose | Primary data path | Status |
|-----|---------|-------------------|--------|
| Positions | Live book | `GET /api/positions` (Alpaca + `state/position_metadata.json`) | VALID — source + INCOMPLETE markers documented |
| Closed Trades | Ledger + strict badge | `GET /api/stockbot/closed_trades` (attribution / exit_attribution / telemetry JSONL) | VALID |
| **System Health** (new top-level) | Integrity cockpit | `GET /api/dashboard/data_integrity` + index pointer | VALID |
| Executive Summary | Rolling P&amp;L / narrative summary | `GET /api/executive_summary` | VALID — banner: not strict cohort |
| SRE Monitoring | Runtime health | `/api/sre/health`, telemetry computed, version | VALID |
| More: Signal Review, Trading Readiness, Telemetry, Learning &amp; Readiness, Profitability &amp; Learning, Fast-Lane | As before | Per existing endpoints | **Retired options-sleeve analytics UI and its HTTP routes removed** (hard decommission 2026-03-25); promotion snapshot is file-backed inside Learning & Readiness only |

## 3) New integrity signals added

- **Alpaca strict**: `LEARNING_STATUS`, `learning_fail_closed_reason`, `trades_seen` / `complete` / `incomplete` from read-only `evaluate_completeness(..., STRICT_EPOCH_START)` (same module as audits; dashboard does not mutate learning).
- **Kraken / direction readiness**: `state/direction_readiness.json` surfaced with explicit note that it is *not* the Alpaca strict cohort.
- **Canonical log staleness**: mtime per canonical JSONL.
- **Join coverage**: last 100 `exit_attribution.jsonl` field presence matrix (existing `_compute_visibility_matrix`).
- **Temporal / structural flags**: strict gate `precheck` + `learning_fail_closed_reason`.
- **Closed trades API**: `alpaca_strict_summary`, `response_generated_at_utc`, per-row `strict_alpaca_chain`, `data_sources`, `entry_reason_display`, `fees_display`.

## 4) Remaining known limitations

- **Executive “Recent Trades”** still a shorter slice than Closed Trades; justified as timeframe summary — full lifecycle + strict badge lives on **Closed Trades**.
- **Per-row COMPLETE** for Alpaca strict is only certain when `LEARNING_STATUS === ARMED` and `trades_seen > 0`; otherwise rows may show `UNKNOWN`, `VACUOUS_STRICT_COHORT`, or `EXCLUDED_PREERA` (honest, no silent OK).
- **Open positions fees**: often `INCOMPLETE` if Alpaca SDK / metadata does not expose accrued fees on the position object.
- **`/api/dashboard/data_integrity` can be slow** on large JSONL (full strict gate scan); tab refresh every 2 minutes.

## 5) Confirmation of zero impact to trading/learning

- **Files touched**: `dashboard.py`, `scripts/verify_dashboard_contracts.py`, this report pair under `reports/`.
- **No edits** to `main.py`, execution paths, schedulers, or telemetry gate **logic** (`telemetry/alpaca_strict_completeness_gate.py` unchanged). Dashboard **calls** `evaluate_completeness` read-only for display.
