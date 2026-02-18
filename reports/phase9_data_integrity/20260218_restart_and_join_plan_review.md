# Restart and join plan review — multi-model oversight (2026-02-18)

## Goal

1. Prove **exit_quality_metrics** on NEW exits after a clean paper restart (no overlay).
2. Fix **join** so entry_vs_exit_blame is classifiable (unclassified_pct < 100% or explicit reason).

## Assumptions challenged

| Lens | Challenge | Minimal fix |
|------|-----------|-------------|
| **Adversarial** | "Paper didn’t restart" may be true, but even after restart, if exit record doesn’t carry **trade_id** matching the entry’s `open_SYMBOL_entry_ts`, the loader will only use key join (symbol\|entry_ts_bucket). Timestamp rounding or empty entry_timestamp on exit would keep joins failing. | Ensure exit record carries **trade_id** = `open_{symbol}_{context.entry_ts}` so loader can match by trade_id first; keep **entry_timestamp** for key fallback. |
| **Quant** | entry_score exists in attribution; 100% unclassified implies **joined rows** don’t get entry_score. So either (1) join doesn’t match (key/trade_id mismatch), or (2) matched entry doesn’t have entry_score in the shape the loader expects. | Loader already copies entry_score from matched entry; fix is join stability (trade_id on exit + **kwargs on build_exit_attribution_record so exit_quality_metrics/decision_id etc. are persisted). |
| **Product** | Restart without overlay is necessary but not sufficient; we must not change strategy logic—only logging/join. | Changes limited to: main.py (trade_id + entry_ts_iso_attr for exit record), exit_attribution.py (**kwargs merge + ATTRIBUTION_SCHEMA_VERSION). No tuning. |

## Plan

1. **Restart paper cleanly (droplet):** Kill tmux session, start `start_live_paper_run.py --date $(date +%Y-%m-%d)` with no overlay. Prove via tmux + state file (no GOVERNED_TUNING_CONFIG, no overlay).
2. **Prove exit_quality_metrics on new exits:** Marker (file size / line count), wait for new exits, sample tail 800, count with_exit_quality_metrics; if 0, diagnose (new exits? right file? high_water?).
3. **Fix join (code):**  
   - **Join key definition (scripts/analysis):** Primary = **trade_id** (entry: `open_SYMBOL_entry_ts`; exit: must carry same). Fallback = **symbol\|entry_ts_bucket(entry_timestamp)**.  
   - **Minimal fix:** Exit record gets **trade_id** = `open_{symbol}_{context.entry_ts}`; **build_exit_attribution_record** accepts **kwargs and merges into record (exit_quality_metrics, decision_id, trade_id, etc.).  
   - Commit: "Fix: make attribution ↔ exit_attribution join stable for blame classification". Push to main.
4. **Droplet pull + baseline v5:** Re-run effectiveness into `reports/effectiveness_baseline_blame_v5`; verify entry_vs_exit_blame (weak_entry_pct, exit_timing_pct, unclassified_pct) and exit_quality proof.
5. **Sign-off v5:** PASS only if exit_quality_metrics non-zero on new exits and blame classifiable (unclassified_pct < 100% or bounded with explicit reasons). If PASS, authorize exactly one tuning lever (entry OR exit). If FAIL, list blockers and STOP.

## Risks accepted

- Restart alone may not produce new exits immediately; proof may show "0 new exits in window" → document and re-sample after next exit.
- trade_id format must match exactly (`open_SYMBOL_<entry_ts_iso>`); entry side uses `open_{symbol}_{now_iso()}` at open, exit side uses `open_{symbol}_{context.entry_ts}` — same value when context.entry_ts was set at open.

## Code changes (implemented)

- **src/exit/exit_attribution.py:** Added `**kwargs` to `build_exit_attribution_record`, merge all kwargs into `rec`. Added `ATTRIBUTION_SCHEMA_VERSION = "1.0.0"`.
- **main.py:** When building exit attribution record, set `entry_ts_iso_attr = context.get("entry_ts")`, `open_trade_id = f"open_{symbol}_{entry_ts_iso_attr}"`, pass `trade_id=open_trade_id` into `build_exit_attribution_record`.
