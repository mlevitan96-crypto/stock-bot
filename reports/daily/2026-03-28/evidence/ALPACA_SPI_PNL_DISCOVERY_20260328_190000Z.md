# ALPACA SPI — PnL pipeline discovery (`20260328_190000Z`)

**Contracts:** All definitions reference `MEMORY_BANK.md` (Alpaca Signal Path Intelligence subsection under Alpaca quantified governance).

## Entry points (Alpaca PnL analysis)

| Component | Path | Role |
|-----------|------|------|
| **Primary artifact generator** | `scripts/audit/alpaca_pnl_massive_final_review.py` | Offline PnL review: reconciliation CSV/MD, truth bundle, analyses A–J (executed surfaces, signal attribution stub, exit forensics, etc.), quant angles, closeout with CSA verdict token. **Now also emits SPI** (`ALPACA_SPI_SECTION_<TS>.*`, `ALPACA_PNL_SIGNAL_PATH_INTELLIGENCE_<TS>.*`). |
| **Session orchestrator** | `scripts/audit/alpaca_pnl_market_session_unblock_pipeline.py` | ET session scope, truth JSON via `alpaca_forward_truth_contract_runner.py`, alignment, massive review handoff; evidence under `reports/daily/<ET-date>/evidence/`. |
| **Droplet session PnL bundle (example)** | `reports/daily/2026-03-27/evidence/_droplet_pnl_session_bundle.py` | Session PnL + strict gates (stdout JSON); **SPI is not embedded here** — use massive review for SPI. |
| **Truth / warehouse audits** | `scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py`, `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` | Broader truth packets; complementary to session PnL review. |

**Droplet repo root (operator):** `/root/trading-bot-current` or `/root/stock-bot` per deployment; `TRADING_BOT_ROOT` env passed to `--root` on the massive review script.

## Cohort selection (canonical trades, windowing)

1. **Strict era floor:** `STRICT_EPOCH_START` in `telemetry/alpaca_strict_completeness_gate.py` (`MEMORY_BANK.md` §1.1).
2. **Session / forward truth:** `alpaca_forward_truth_contract_runner.py` produces JSON with `final_gate.complete_trade_ids`, `OPEN_TS_UTC_EPOCH`, `EXIT_TS_UTC_EPOCH_MAX`, `window_start_epoch` / `window_end_epoch`.
3. **Massive review cohort mode:** `--cohort-ids` JSON must match `final_gate.complete_trade_ids`; `--window-start-epoch` / `--window-end-epoch` align with truth; `--root` points at the bot tree containing `logs/exit_attribution.jsonl`.
4. **Legacy mode:** Loads `reports/ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json` (path in script) when cohort files omitted — may block if missing.

## Signal attribution fields (for SPI bucketing)

Source: `logs/exit_attribution.jsonl` rows joined by `trade_id`. SPI uses read-only:

- `exit_contributions` (dominant key by max |weight|)
- Else `v2_exit_components`
- Else `signals` list
- Else bucket `attribution_unknown`

Schema background: `src/exit/exit_attribution.py`, `src/exit/exit_attribution_enrich.py`.

## Existing CSA / SRE hooks and verdict artifacts

- **PnL review closeout:** `ALPACA_PNL_REVIEW_CLOSEOUT_<TS>.md` — includes `CSA_VERDICT: PNL_REVIEW_COMPLETE` or `STILL_BLOCKED`; **now includes SPI artifact pointers** (non-blocking).
- **CSA packet stub:** `ALPACA_PNL_CSA_PACKET_<TS>.md`
- **SRE:** Session truth runner and `alpaca_pnl_cohort_alignment_check.py` / `alpaca_pnl_massive_final_review.py` blockers (B1–B9) enforce data alignment — SPI does not add new blockers.
- **Board / adversarial stubs:** `ALPACA_PNL_BOARD_PACKET_*`, `ALPACA_PNL_ADVERSARIAL_*`

## SPI placement

SPI consumes the **same** `complete_trade_ids` and `exit_attribution.jsonl` rows as reconciliation; no separate cohort.

**End of discovery.**
