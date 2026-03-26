# SRE Review: Alpaca data path integrity & signal granularity

**Mission:** DATA PATH INTEGRITY & SIGNAL GRANULARITY CONFIRMATION  
**Timestamp:** 20260314  
**Authority:** SRE embedded reviewer (veto authority).

---

## 1. Does the pipeline read real droplet data?

**YES.** Phase 1 (pipeline read reconciliation) was run against the live droplet:

- Inventory script and pipeline Step 1 (with `--diagnostic`) were executed on the droplet.
- **File path opened:** `logs/exit_attribution.jsonl` (primary).
- **Source line count** (exit_attribution.jsonl) and **TRADES_FROZEN.csv data row count** are consistent (e.g. ~2000 source lines, ~1999 CSV data rows after header; minor drop possible from blank/no_exit_ts).
- No evidence that the pipeline reads a different path or a local-only copy; the same repo paths are used on the droplet.

---

## 2. Are artifacts stable and non-destructive?

**YES.** Phase 5 (retention & overwrite safety) verdict: **APPEND_ONLY_OK**.

- **Logs:** `exit_attribution.jsonl`, `master_trade_log.jsonl`, `attribution.jsonl` are append-only; no truncation or overwrite observed.
- **Frozen artifacts:** Each pipeline run creates a **new** timestamped directory `reports/alpaca_edge_2000_<TS>`. TRADES_FROZEN.csv and INPUT_FREEZE.md are written once per run. Prior runs are not overwritten.
- No detection of pruning or deletion of prior dataset dirs in the audit window (14 days).

---

## 3. Operational risk assessment

| Risk | Level | Notes |
|------|--------|------|
| Wrong data source | Low | Paths declared and confirmed; pipeline reads canonical exit_attribution. |
| Silent filtering / schema drift | Low | Step 1 diagnostic shows drop reasons (blank, json_error, not_dict, no_exit_ts); no unexplained mass drops. |
| Overwrite of logs or prior runs | Low | Append-only logs; timestamped frozen dirs. |
| Join key drift | Low | trade_key derivation is consistent (Phase 2); 0% join coverage for entry/exit frozen is due to empty canonical attribution files, not key error. |
| Pipeline run without droplet data | Mitigated | Diagnostic and inventory scripts are run on droplet via DropletClient; evidence is from real droplet. |

---

## Verdict

- **Pipeline reads real droplet data:** Confirmed.  
- **Artifacts are stable and non-destructive:** Confirmed (APPEND_ONLY_OK).  
- **Operational risk:** Low for data path integrity and retention. No changes to strategy or execution logic; diagnostics and reporting only.
