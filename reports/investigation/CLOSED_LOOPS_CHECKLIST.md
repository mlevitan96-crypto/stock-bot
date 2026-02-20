# Closed loops checklist (Phase 5)

PASS/FAIL. Each item must cite droplet evidence (file path + counts/%). Do not stop until all PASS.

## DROPLET COMMANDS (reference)

```bash
cd /root/stock-bot
python3 scripts/investigation_baseline_snapshot_on_droplet.py
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py   # after >= 200 truth lines
python3 scripts/full_signal_review_on_droplet.py --days 7
```

---

| # | Item | Status | Droplet evidence |
|---|------|--------|------------------|
| 1 | Gate truth log exists and is populated daily (≥200 lines in test window) | FAIL | logs/expectancy_gate_truth.jsonl line count |
| 2 | Gate truth coverage ≥ 95% for the funnel window | FAIL | reports/signal_review/signal_funnel.json gate_truth_coverage_pct |
| 3 | Expectancy gate outcome is computed from gate truth (not inferred) | FAIL | signal_funnel.json stage5_from_gate_truth |
| 4 | Ledger join coverage explained and either fixed or removed from critical path | FAIL | reports/investigation/CONTRADICTIONS_CLOSED.md §1 |
| 5 | Pre-adjust score definition proven (field source + availability rate; no silent default-to-zero) | FAIL | CONTRADICTIONS_CLOSED.md §2 + funnel pre_score_availability_rate_pct |
| 6 | “Paper trades” metric renamed and reconciled: candidates_evaluated vs paper_orders_submitted vs paper_fills | FAIL | reports/signal_review/paper_trade_metric_reconciliation.md |
| 7 | Submit telemetry truth: SUBMIT_ORDER_CALLED count reconciles with submit_entry and broker responses | FAIL | logs/submit_order_called.jsonl vs orders.jsonl |
| 8 | No contradictory claims in reports (e.g. “100% choke” with 0% coverage) | FAIL | reports/signal_review/signal_funnel.md claim_100_choke |
| 9 | Daily governance hooks fail loudly if gate truth coverage < threshold, inferred metrics used, or contradictions detected | FAIL | (Script/CI exit non-zero when checks fail) |

---

*Update Status and Droplet evidence after each droplet run until all PASS.*
