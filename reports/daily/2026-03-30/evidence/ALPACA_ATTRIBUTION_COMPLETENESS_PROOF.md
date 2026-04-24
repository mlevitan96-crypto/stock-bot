# ALPACA ATTRIBUTION COMPLETENESS (forward trades)

## Where entry metadata is created

- **Intent telemetry:** `main._emit_trade_intent` → `logs/run.jsonl` (`feature_snapshot`, `thesis_tags`, `score`, `canonical_trade_id`, optional `final_decision_primary_reason` from `telemetry.decision_intelligence_trace`).
- **Order guard:** `main.AlpacaExecutor.submit_entry` aborts without positive `entry_score` and non-unknown `market_regime` (`CRITICAL_missing_entry_score_abort`, `CRITICAL_missing_market_regime_abort`).
- **Attribution log:** `log_attribution` / `jsonl_write('attribution', ...)` with `entry_score`, `regime`, components (`main.py` entry path ~10600+).

## `entry_reason` mapping

- Repo uses **`final_decision_primary_reason`** (when intelligence trace present) and **`blocked_reason`** / **`gate_summary`** — not a field literally named `entry_reason`.

## Recent `trade_intent` sample (entered): **0** rows

- With `final_decision_primary_reason` set: **0**

> No `entered` trade_intent rows in last sample window — **code-path verification only** for tomorrow’s trades.

## Dry-run emission (no broker orders)

- Probe exit code: **0**
```text
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
emit_ok

```

