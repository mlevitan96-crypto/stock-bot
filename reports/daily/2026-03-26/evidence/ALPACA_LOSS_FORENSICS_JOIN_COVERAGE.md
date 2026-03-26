# Alpaca Loss Forensics — Join Coverage

**Gate metric (forensics):** log join OR exit row carries `entry_uw` + `entry_regime` (canonical exit_attribution embeds entry context).

- **Frozen exits:** 2000
- **With entry path intel (gate):** 1351 (67.5%)
- **Strict log-only join (attribution/unified/entry_attr):** 898 (44.9%)
- **Embedded-only (no log line, entry_uw+regime on exit):** 453
- **Threshold:** 80.0% (mission)
- **alpaca_unified_events.jsonl:** missing/empty
- **alpaca_entry_attribution.jsonl:** missing/empty

## Join sources (log lines; excludes embedded-only)

- no_log_join_exit_embedded: 1102
- attribution.jsonl: 898
