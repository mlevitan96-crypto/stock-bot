# Data Integrity Plan — Multi-Model + Plugin Orchestrator

**Mission:** Find and fix ALL telemetry/data-integrity wiring so every canonical record is captured, mapped, embedded, and replay-ready—without breaking trading.

**Hard constraints:** No silent behavior changes in trading decisions; every change validated by unit tests, spine tests, droplet verification, schema audits, dashboard endpoint checks; path moves require updating every reader and downstream artifact generator; prefer additive + backward-compatible fields.

---

## Phase 0 — Multi-Model Reconciliation

### Model A (Implementation Engineer) — Summary

- **Truth roots:** Trade lifecycle = `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/master_trade_log.jsonl`, `logs/exit_event.jsonl`. Direction/intel = `logs/intel_snapshot_entry.jsonl`, `logs/intel_snapshot_exit.jsonl`, `logs/direction_event.jsonl`, `state/position_intel_snapshots.json`.
- **Writers traced:** `main.py` (attribution append on entry; exit block: build_exit_attribution_record, append_exit_attribution, append_exit_event, append_master_trade, capture_exit_intel_telemetry); `src/exit/exit_attribution.py` (append_exit_attribution, append_exit_signal_snapshot, append_exit_event); `src/intelligence/direction_intel.py` (append_intel_snapshot_entry, append_intel_snapshot_exit, store_entry_snapshot_for_position); `utils/master_trade_log.py` (append_master_trade).
- **Fix focus:** Entry capture must run on every position open (currently called after mark_open but can raise silently; intel_snapshot_entry.jsonl missing on droplet). Exit must attach direction_intel_embed (entry snapshot loaded from state; key = symbol:entry_ts[:19]). Use canonical top-level fields (direction, side, position_side) in attribution/exit_attribution/exit_event; keep legacy nesting for backward compatibility.
- **Schema:** Centralize in `src/contracts/telemetry_schemas.py`; validate in `scripts/audit/telemetry_contract_audit.py`.

### Model B (Adversarial Reviewer) — Summary

- **Assumptions challenged:** (1) Entry capture runs on “fill” path only—reconciliation/fill-recovery paths may open positions without calling capture_entry_intel_telemetry. (2) entry_ts at exit comes from context; if metadata and in-memory opens diverge after restart, lookup fails. (3) Readers: dashboard (executive_summary, closed_trades, /api/positions), governance (direction_readiness, effectiveness), replay (load_30d_backtest_cohort, reconstruct_direction_30d), report generators (trade_visibility_review, build_30d_comprehensive_review), EOD (run_stock_quant_officer_eod), verify scripts—all must be in IO map. (4) Double-append: master_trade_log can be appended in two code paths (entry+exit) for same trade_id—need single-append contract per trade_id. (5) Schema drift: exit_attribution built by build_exit_attribution_record; direction_intel_embed added in main.py; direction_readiness expects embed.intel_snapshot_entry; any reader expecting old nesting must be listed.
- **Hidden readers (≥5):** (1) Dashboard `/api/stockbot/closed_trades` and executive summary read attribution. (2) Governance direction_readiness reads exit_attribution for telemetry_trades. (3) Replay load_30d_backtest_cohort and reconstruct_direction_30d read exit_attribution + direction_intel_embed. (4) Board EOD run_stock_quant_officer_eod reads attribution, exit_attribution, master_trade_log. (5) effectiveness reports and attribution_loader join attribution + exit_attribution. (6) trade_visibility_review and audit_direction_intel_wiring read exit_attribution and intel_snapshot_entry.jsonl.
- **Risks:** Look-ahead (none if telemetry is append-only and no decision reads these logs). Missing fields (direction_intel_embed missing → 0/100 readiness). Double-append (master_trade_log: currently appended at full-close only in main.py; entry-side append in same flow—verify single record per trade_id).

### Model C (SRE/Reliability) — Summary

- **Hot-path safety:** All appends are in try/except and never raise; path is config.registry or env (EXIT_ATTRIBUTION_LOG_PATH, MASTER_TRADE_LOG_PATH). Log growth: intel_snapshot_*.jsonl and direction_event.jsonl will grow; add rotation/size caps and prune position_intel_snapshots.json by age/closed trades.
- **Idempotency:** append_* are append-only; no dedup in writer. Single-append for master_trade_log: enforce in code (append once per trade_id at close) and add test.
- **Crash safety:** No fsync; acceptable for audit logs. position_intel_snapshots.json is read/write; use atomic write if we change it.
- **Droplet:** Verify after deploy: intel_snapshot_entry.jsonl exists and has records; exit_attribution has direction_intel_embed with non-empty intel_snapshot_entry; direction_readiness > 0; dashboard banner shows X/100.

---

## Canonical Truth Roots

| Root | Path | Purpose |
|------|------|---------|
| Trade lifecycle | logs/master_trade_log.jsonl | One record per trade (full close payload); append once at exit. |
| | logs/attribution.jsonl | Entry-side attribution (open_* + closed records). |
| | logs/exit_attribution.jsonl | Exit-side attribution; must include direction_intel_embed. |
| | logs/exit_event.jsonl | Unified replay record; must include direction_intel_embed when present. |
| Direction / intel | logs/intel_snapshot_entry.jsonl | One row per entry capture. |
| | logs/intel_snapshot_exit.jsonl | One row per exit capture. |
| | logs/direction_event.jsonl | Direction events (entry/exit). |
| | state/position_intel_snapshots.json | Temporary join state (symbol:entry_ts → snapshot); prune by age/closed. |

---

## Writers / Readers Map (Summary)

| File | Writers | Readers (examples) |
|------|---------|--------------------|
| attribution.jsonl | main.py (attribution append) | executive_summary_generator, dashboard /api, comprehensive_learning_orchestrator_v2, pnl_reconciler, score_autopsy, effectiveness, EOD, replay |
| exit_attribution.jsonl | main.py (append_exit_attribution) | direction_readiness, trade_visibility_review, audit_direction_intel_wiring, replay loaders, governance, EOD, verify_full_exit_telemetry |
| master_trade_log.jsonl | main.py (append_master_trade at close) | generate_snapshot_outcome_attribution, EOD, run_v2_synthetic_trade_test, run_regression_checks |
| exit_event.jsonl | main.py (append_exit_event) | verify_full_exit_telemetry, replay |
| intel_snapshot_entry.jsonl | direction_intel.append_intel_snapshot_entry (from capture_entry_intel_telemetry) | audit_direction_intel_wiring |
| intel_snapshot_exit.jsonl | direction_intel.append_intel_snapshot_exit | audit (optional) |
| direction_event.jsonl | direction_intel.append_direction_event | replay / direction |
| position_intel_snapshots.json | direction_intel store_entry_snapshot_for_position, load_entry_snapshot_for_position | capture_exit_intel_telemetry (read at exit) |

*Full map:** scripts/audit/build_telemetry_io_map.py → reports/audit/TELEMETRY_IO_MAP.md*

---

## Risk List + Mitigations

| Risk | Mitigation |
|------|------------|
| Entry capture never runs (exception swallowed) | Call capture_entry_intel_telemetry in fill path with same entry_ts as persisted in metadata; log on exception; add test “entry capture invoked on position open”. |
| Exit embed missing (0/100 readiness) | Ensure capture_exit_intel_telemetry runs and receives entry_ts from context; state key symbol:entry_ts[:19] matches; add test “exit embeds direction_intel_embed when entry snapshot exists”. |
| entry_ts mismatch (entry vs exit) | Use single source: persist entry_ts in metadata in mark_open; pass that same value into capture_entry_intel_telemetry (e.g. read from metadata after mark_open or pass now from caller used by both). |
| Double-append master_trade_log | Contract: append once per trade_id at full close; add guard/test. |
| Schema drift / old readers | Add canonical top-level fields (direction, side, position_side); keep legacy nesting; document in DATA_CONTRACT_CHANGELOG; update readers to prefer canonical. |
| Log growth / disk | Add rotation or size caps for intel_snapshot_*.jsonl and direction_event.jsonl; prune position_intel_snapshots.json by age (e.g. 30d) and closed trades. |
| Hot-path regression | No logic change in scoring/execution; telemetry only; all appends already in try/except. |

---

## Exact Proofs Required to Merge

1. **Unit tests:** Schema validators on sample records; “entry capture invoked on position open” (mock fill path); “exit embeds direction_intel_embed when entry snapshot exists”; “master_trade_log single-append contract”.
2. **Spine tests:** Existing pytest spine (exit_attribution, effectiveness, attribution_loader) must pass.
3. **Offline audits:** ensure_telemetry_paths.py, verify_full_exit_telemetry.py, verify_replay_readiness.py, telemetry_contract_audit.py, audit_direction_intel_wiring.py — all pass.
4. **Droplet verification:** Deploy; run short window or synthetic lab; confirm intel_snapshot_entry.jsonl exists with records; exit_attribution has direction_intel_embed with non-empty intel_snapshot_entry; direction_readiness counter > 0; dashboard banner shows X/100.
5. **Dashboard endpoints:** /api/positions, /api/stockbot/closed_trades, /api/executive_summary, /api/direction_banner — respond and show no regression.
6. **Schema audit:** reports/audit/TELEMETRY_CONTRACT_AUDIT.md generated; no blocking missing fields/wrong nesting for canonical logs.

---

## Artifacts to Produce

| Artifact | Phase |
|----------|--------|
| reports/audit/DATA_INTEGRITY_PLAN.md | 0 (this doc) |
| src/contracts/telemetry_schemas.py | 1 |
| scripts/audit/telemetry_contract_audit.py | 1 |
| reports/audit/TELEMETRY_CONTRACT_AUDIT.md | 1 (script output) |
| scripts/audit/build_telemetry_io_map.py | 2 |
| reports/audit/TELEMETRY_IO_MAP.md | 2 (script output) |
| Entry/exit wiring fixes in main.py, direction_intel | 3 |
| docs/DATA_CONTRACT_CHANGELOG.md | 4 |
| reports/audit/DATA_INTEGRITY_PROOF.md | 5 |
| reports/board/DATA_INTEGRITY_BOARD_REVIEW.md | 6 |
| SAFE_TO_APPLY checklist / BLOCKERS | 7 |

---

*Generated by data-integrity orchestrator (Phase 0).*
