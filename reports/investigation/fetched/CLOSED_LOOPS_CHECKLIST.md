# Closed loops checklist (Phase 5)

PASS/FAIL. Each item cites droplet evidence. Do not stop until all PASS.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/investigation_baseline_snapshot_on_droplet.py
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/full_signal_review_on_droplet.py --days 7
python3 scripts/run_closed_loops_checklist_on_droplet.py
```

---

| # | Item | Status | Droplet evidence |
|---|------|--------|------------------|
| 1 | Gate truth log exists and populated (≥200 lines) | FAIL | logs/expectancy_gate_truth.jsonl lines=0 |
| 2 | Gate truth coverage ≥ 95% | FAIL | signal_funnel.json gate_truth_coverage_pct=0.0% |
| 3 | Stage 5 from gate truth (not inferred) | FAIL | signal_funnel.json stage5_from_gate_truth=False |
| 4 | Ledger join explained/fixed or removed from critical path | FAIL | CONTRADICTIONS_CLOSED §1 or stage5_from_gate_truth |
| 5 | Pre-adjust definition proven (no silent defaults) | PASS | CONTRADICTIONS_CLOSED §2 or gate truth pre_score |
| 6 | Paper metric reconciled (candidates / submitted / fills) | PASS | paper_trade_metric_reconciliation.md |
| 7 | SUBMIT_ORDER_CALLED reconciles with submit_entry and broker | FAIL | submit_order_called.jsonl + ORDER_RECONCILIATION.md |
| 8 | No contradictory claims (e.g. 100% choke with 0% coverage) | FAIL | signal_funnel.md claim_100_choke |
| 9 | Governance fails loudly on low coverage / inferred / contradictions | FAIL | run_closed_loops_checklist_on_droplet.py exit code |

**Overall: FAIL — Gate truth coverage 0.0% < 95.0% (required for trustworthy choke claims); Gate truth lines 0 < 200 (recommended for 200-line report)**