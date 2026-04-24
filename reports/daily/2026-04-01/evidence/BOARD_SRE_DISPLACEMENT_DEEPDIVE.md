# BOARD_SRE — Displacement deep dive

**Scope:** Phases 10–12 as run on droplet (`run_displacement_deepdive_addon.py`); Phase 13 UW sink **not** deployed (see `UW_CAPTURE_SKIPPED.md`).

## Disk / rotation

- **Current run:** Primary bulk artifact is `DISPLACEMENT_OVERRIDE_MAP.json` (~8 MB pulled for 2026-04-01 evidence pack from droplet). Markdown summaries are small.
- **UW path (if ever enabled):** `logs/uw_signal_context.jsonl` would require **logrotate** or size-based rotation (e.g. daily slice + compress), retention aligned with `DATA_RETENTION_POLICY.md`, and exclusion from unbounded growth on long-running engines.

## CPU / IO impact

- **Addon batch:** One-off read of `blocked_trades.jsonl`, counterfactual JSON, score snapshots, and `alpaca_bars.jsonl`; CPU is bounded by row count and bar scans (5705 displacement rows in this evidence). Suitable for scheduled post-close job, not hot path.
- **Continuous UW sink (not deployed):** Per-intent append is low CPU if JSON serialization is bounded; IO is **one append per decision** — watch fd/fsync policy and SSD wear on high-frequency symbols.

## Failure modes and rate limits

- **Missing files:** Script fails closed if required inputs absent (documented in script usage).
- **Partial bar coverage:** Rows without bars skip emulator cells; `n` in grid matches covered rows (5705 in `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`).
- **API rate limits:** Not applicable to this offline addon; live UW capture would need backoff if UW provider is remote (not in scope for this run).
