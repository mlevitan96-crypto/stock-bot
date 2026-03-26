# Kraken defect backlog (ranked)

**TS:** `20260326_2315Z`

| ID | Symptom | Root cause | Proof needed | Fix plan | Acceptance | Risk |
|----|---------|------------|--------------|----------|------------|------|
| KRA-001 | Cannot run `kraken_data_telegram_certification_suite.py` | **File does not exist** in repository | `reports/KRAKEN_BASELINE_20260326_2315Z.json` | Implement suite + strict tail gate + index schema per CSA contract | Suite exits 0 with captured JSON; Telegram path proven | N/A until implemented |
| KRA-002 | No strict tail completeness evaluator in Python | Never landed / named differently | Grep + surface map | Add `telemetry/kraken_strict_completeness_gate.py` (or equivalent) reading defined jsonl/index | `incomplete==0` on golden slice | Low if read-only |
| KRA-003 | Milestone Telegram (250/500) unproven | No Kraken notifier; Alpaca uses 100/500 | N/A | Mirror `notify_alpaca_trade_milestones.py` pattern for Kraken ledger **or** align milestone spec | Dedupe state + sendMessage proof | Token exposure — use env + dry-run |

**Phase 4:** No Kraken code changes in this sweep.
