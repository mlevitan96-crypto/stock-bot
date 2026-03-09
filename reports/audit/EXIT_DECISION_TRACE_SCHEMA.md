# Exit Decision Trace — Canonical Schema

**Purpose:** Append-only, per-open-position sample trace for exit learning. CSA-auditable; runtime-safe (buffered, fail-open).

**Path:** `reports/state/exit_decision_trace.jsonl`

**Rules:**
- Append-only (one JSON object per line).
- Sample every N seconds per trade (configurable; default 60s via `EXIT_TRACE_SAMPLE_INTERVAL_SEC`).
- Bounded retention: prune records older than 7 days (configurable via `EXIT_TRACE_RETENTION_DAYS`).

---

## Record schema (one line = one JSON object)

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | UTC ISO timestamp of sample |
| `trade_id` | string | Stable trade id (e.g. `open_SYMBOL_<entry_ts_iso>`) |
| `symbol` | string | Ticker |
| `side` | string | `long` or `short` |
| `unrealized_pnl` | float | Unrealized P&L USD (or derived from pnl_pct) |
| `price` | float | Current price at sample |
| `hold_minutes` | float | Minutes since entry |
| `composite_score` | float | Current composite (v2) score |
| `signal_decay` | float | Ratio current_score / entry_score |
| `exit_eligible` | boolean | True if any exit condition would fire (e.g. v2_exit_score >= threshold) |
| `exit_conditions` | object | Booleans per condition (see below) |
| `signals` | object | Granular signal snapshot (see below) |

### exit_conditions

| Key | Type | Description |
|-----|------|-------------|
| `signal_decay` | boolean | Score decay below threshold (e.g. ratio < 0.70) |
| `flow_reversal` | boolean | Flow sentiment opposite to position direction |
| `stale_alpha` | boolean | Time-based stale (e.g. age > TIME_EXIT_MINUTES) |
| `risk_stop` | boolean | Trailing/drawdown stop would fire |

### signals

Nested by source. All values numeric unless noted.

#### signals.UW

| Sub-field | Type | Description |
|-----------|------|-------------|
| `flow` | float | Flow strength / conviction (0–1 scale) |
| `dark_pool` | float | Dark pool bias (-1 to 1) or notional proxy |
| `imbalance` | float | Put/call or flow imbalance proxy |
| `velocity` | float | Flow velocity / change rate (if available) |
| `confidence` | float | Confidence or conviction (0–1) |

#### signals.momentum

Per-component momentum metrics (best-effort from v2_inputs).

#### signals.volatility

e.g. `realized_vol_20d`, `realized_vol_5d` (from v2_inputs / symbol risk).

#### signals.trend

Regime/sector or trend label (string) or numeric proxy.

---

## Versioning

- Schema version: `1`
- Record may include `schema_version: 1` for future compatibility.

## Retention and sampling

- **Sampling:** At most one record per `trade_id` per `EXIT_TRACE_SAMPLE_INTERVAL_SEC` seconds (default 60).
- **Pruning:** On append, optionally prune lines with `ts` older than 7 days (configurable).
- **Fail-open:** If write fails, trading continues; no exception propagates.

---

## Write-health telemetry (fail-detection)

**Path:** `reports/state/exit_trace_write_health.jsonl`

One record per trace write attempt (per flush): `ts`, `trade_id` (first in batch), `attempted`, `written` (true/false), `error_type`, `error_msg` (truncated). Append-only; 7-day retention. Ensures no silent trace write failures: every attempt is recorded; `written=false` is immediately observable and CSA-auditable.
