# Telemetry Coverage Audit — SRE (Fail-Closed)

**Date:** 2026-03-09  
**Authority:** Droplet data authority per MEMORY_BANK / TELEMETRY_STANDARD.  
**Purpose:** Enumerate ALL telemetry sources; document what is captured, when, granularity, retention, failure behavior. FAIL CLOSED if any decision-affecting component has no telemetry or telemetry is lossy without detection.

---

## 1. Trade lifecycle

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Entry attribution | `logs/attribution.jsonl` | type=attribution, ts, direction, side, position_side, regime_at_entry, entry_score, symbol | On open (fill/confirm) | Per trade (open_* and closed) | Unbounded append | Best-effort append; no block |
| Exit attribution | `logs/exit_attribution.jsonl` | symbol, entry_ts, exit_ts, exit_reason, pnl, direction_intel_embed, exit_quality_metrics (MFE, MAE, profit_giveback), time_in_trade_minutes | On full close | Per trade | Unbounded | Append; schema enforced for direction_intel_embed |
| Master trade log | `logs/master_trade_log.jsonl` | trade_id, symbol, entry_ts, exit_ts, source | On full close | Per trade | Unbounded | Append |
| Exit event | `logs/exit_event.jsonl` | trade_id, symbol, entry_ts, exit_ts, exit_reason_code, direction_intel_embed | On exit (unified replay record) | Per exit | Unbounded | Append |
| Exit decision trace | `reports/state/exit_decision_trace.jsonl` | ts, trade_id, symbol, side, unrealized_pnl, price, hold_minutes, composite_score, signal_decay, exit_eligible, exit_conditions, signals (UW, momentum, volatility, trend) | Every N sec per open position (default 60s), before exit logic | Per open position sample | 7 days (prune) | Buffered; fail-open (drop on write error) |

**Fail-closed check:** Trade lifecycle has telemetry at entry, hold (exit_decision_trace), and exit. Exit decision trace is sampled and may drop on failure (fail-open); loss is not always detectable. **Gap:** No explicit "trace write failed" counter or alert.

---

## 2. Signal evaluation

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Signal context | `logs/signal_context.jsonl` | Full signal state at every trade decision (enter/blocked/exit) | On each decision | Per decision | Unbounded | Best-effort |
| Signal strength cache | `state/signal_strength_cache.json` | signal_strength, position_side, evaluated_at, signal_delta, signal_trend per symbol | Every exit-eval cycle for open positions | Per symbol (open position) | Overwritten | Write failure logged |
| Gate diagnostic | `logs/gate_diagnostic.jsonl` | gate_name, symbol, decision=blocked, details | When signal fails a gate | Per gate failure | Unbounded | Append |

**Fail-closed check:** Signal evaluation is logged at decision time (signal_context, gate_diagnostic). Signal strength cache is state, not append; no history of past strengths. **Gap:** No dedicated "signal evaluation request" vs "signal evaluation result" audit trail for every score computation.

---

## 3. PnL (realized, unrealized, MFE, MAE)

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Exit attribution | `logs/exit_attribution.jsonl` | pnl_usd / realized_pnl, exit_quality_metrics (mfe, mae, profit_giveback, time_in_trade_sec) | On close | Per trade | Unbounded | Append |
| Exit decision trace | `reports/state/exit_decision_trace.jsonl` | unrealized_pnl per sample | Every sample interval for open positions | Per position sample | 7 days | Fail-open |
| PnL reconciliation | `logs/pnl_reconciliation.jsonl` | Day/window vs attribution reconciliation | Dashboard /api/pnl/reconcile | Per reconcile run | Unbounded | Append |
| Alpaca positions | API | unrealized_pl, unrealized_plpc | On list_positions | Live only | N/A | API failure = logged, no persist |

**Fail-closed check:** Realized PnL and MFE/MAE are in exit_attribution. Unrealized is in trace (sampled) and from API (not persisted historically). **Gap:** No dedicated "unrealized PnL history" stream; only trace samples give a time series of unrealized.

---

## 4. Risk controls

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Blocked trades | `state/blocked_trades.jsonl` | reason, score, symbol, ts (blocked candidate) | When entry blocked (capacity, score, etc.) | Per blocked candidate | Unbounded | Append |
| Gate events | `logs/gate.jsonl` | Gate pass/fail per cycle | When gate evaluated | Per cycle/symbol | Unbounded | Append (if writer present) |
| Run log | `logs/run.jsonl` | trade_intent, exit_intent, cycle summaries | Per cycle | Per cycle | Unbounded | Append |
| Exit truth (v3) | `logs/exit_truth.jsonl` (or B2) | exit_pressure, threshold, decision, components, close_reason | When EXIT_PRESSURE_ENABLED, per evaluation | Per symbol evaluation | Unbounded | Append |
| B2 suppressed | `logs/b2_suppressed_signal_decay.jsonl` | B2 suppression of early signal_decay exit | When B2 suppresses exit | Per suppression | Unbounded | Append |

**Fail-closed check:** Blocked trades and gate logs exist. Gate.jsonl path may be logs/ or state/ in different scripts; canonical path should be in registry. **Gap:** Single source of truth for "why was this trade blocked" (blocked_trades.jsonl) is present; gate.jsonl usage is inconsistent.

---

## 5. CI / gating

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| CSA verdicts | `reports/audit/CSA_VERDICT_*.json` | Verdict, mission, findings | After CSA runs | Per mission | File per run | Write |
| Promotion trigger | `reports/audit/PROMOTION_TRIGGER_STATUS_*.json` | Triggers fired, trade counts, economic/structural | On promotion/exit-capture review run | Per run | File per date | Write |
| Telemetry integrity gate | Script + reports | Schema validation, required fields | CI / local | Per run | Report | Fail or pass |

**Fail-closed check:** CI/gating produces verdicts and trigger status; not a real-time stream. **Gap:** No single "gating_events.jsonl" that records every gate check (CI, deploy, promotion) with timestamp.

---

## 6. Infra (latency, cache, failures)

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| UW cache | `data/uw_flow_cache.json` | Symbol-level flow, conviction, sentiment, dark_pool, _last_update | UW daemon / poll | Per symbol (overwrite) | One file | Write; no history |
| UW API quota | `data/uw_api_quota.jsonl` | API call usage | Per UW call | Per call | Unbounded | Append |
| UW daemon/errors | `logs/uw_daemon.jsonl`, `logs/uw_errors.jsonl` | Daemon events, errors | Daemon | Per event | Unbounded | Append |
| Bot heartbeat | `state/bot_heartbeat.json` | Last heartbeat | HB interval | Overwrite | One file | Write |
| System events | `logs/system_events.jsonl` | Subsystem, event_type, severity, payload | log_system_event() | Per event | Unbounded | Append |
| Alert error | `logs/alert_error.jsonl` | Alert failures | On alert path | Per alert | Unbounded | Append |
| Run / cycle | `logs/run.jsonl` | Cycle summaries | Per trading cycle | Per cycle | Unbounded | Append |

**Fail-closed check:** Cache freshness is in uw_flow_cache (_last_update). No dedicated "latency per decision" stream. Failures are logged to various logs; no single failure aggregator. **Gap:** Latency of score computation, API latency, and "time from signal to order" are not systematically captured.

---

## 7. Scheduling / cron

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Learning scheduler | `state/learning_scheduler_state.json` | Weekly/biweekly/monthly cycle state | Scheduler run | Overwrite | One file | Write |
| log_event | Various | "weekly_cycle_started", "monthly_cycle_complete" etc. | Scheduler | Per event | In run/trading logs | Best-effort |
| Crontab | System | Schedule definition | N/A | N/A | System | N/A |

**Fail-closed check:** Scheduler state is file-based; no append-only audit of "cron fired at X". **Gap:** No cron_execution.jsonl (run id, schedule_name, start_ts, end_ts, success).

---

## 8. Data freshness

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| UW cache | `data/uw_flow_cache.json` | _last_update (or last_update) per symbol | Daemon update | Per symbol | One file | Write |
| Exit decision trace | `reports/state/exit_decision_trace.jsonl` | ts per sample | Each sample | Per sample | 7 days | Fail-open |
| Position metadata | `state/position_metadata.json` | entry_ts, entry_score, high_water, etc. | On entry / update | Per symbol | One file | Write |

**Fail-closed check:** Freshness is implicit in _last_update and trace ts. No dedicated "data_freshness.jsonl" (source, last_ts, age_sec). **Gap:** Stale cache detection is ad-hoc; no telemetry that "UW cache was stale at decision time".

---

## 9. Direction / intel (canonical)

| Stream | Path | What is captured | When | Granularity | Retention | Failure behavior |
|--------|------|------------------|------|-------------|-----------|------------------|
| Intel snapshot entry | `logs/intel_snapshot_entry.jsonl` | Pre-entry intel snapshot | At entry capture | Per entry | Unbounded | Append |
| Intel snapshot exit | `logs/intel_snapshot_exit.jsonl` | Exit intel snapshot | At exit capture | Per exit | Unbounded | Append |
| Direction event | `logs/direction_event.jsonl` | Components, entry/exit, symbol, timestamp | With snapshot | Per event | Unbounded | Append |
| Position intel snapshots | `state/position_intel_snapshots.json` | Join state keyed symbol:entry_ts | Temporary | Overwrite | Prune by age/closed | Write |

**Fail-closed check:** Direction intel is captured at entry and exit; exit_attribution must include direction_intel_embed (non-empty for telemetry-backed count). **Gap:** Empty intel_snapshot_entry is allowed; readiness counts only non-empty.

---

## 10. Summary — fail-closed verdict

| Category | Telemetry present | Lossy without detection? | Verdict |
|----------|-------------------|---------------------------|---------|
| Trade lifecycle | Yes (attribution, exit_attribution, master_trade_log, exit_event, exit_decision_trace) | Trace: fail-open (can drop) | **Gap:** Trace write failures not counted/alarmed |
| Signal evaluation | Partial (signal_context, gate_diagnostic, signal_strength cache) | Cache overwrite loses history | **Gap:** No full score-computation audit trail |
| PnL | Yes (exit_attribution + exit_quality_metrics; trace unrealized) | Unrealized only in trace (sampled) | **OK** for realized; unrealized is sampled only |
| Risk controls | Yes (blocked_trades, gate, exit_truth, B2) | No | **OK** |
| CI/gating | File-based verdicts | N/A | **OK** |
| Infra | Logs (uw, system_events, run); cache single file | No latency telemetry | **Gap:** No latency/freshness-at-decision stream |
| Scheduling | State file + log_event | No cron run log | **Gap:** No cron_execution audit |
| Data freshness | Implicit in cache _last_update, trace ts | Stale-at-decision not logged | **Gap:** Stale cache at decision time not captured |
| Direction intel | Yes (intel_snapshot_*, direction_event, exit direction_intel_embed) | No | **OK** |

**Overall:** Telemetry coverage is substantial. Decision-affecting components have telemetry except: (1) exit decision trace write failures are not detectable; (2) latency and "freshness at decision time" are not captured; (3) full signal-evaluation audit (every score computation) is partial; (4) cron/scheduler execution is not append-only audited.
