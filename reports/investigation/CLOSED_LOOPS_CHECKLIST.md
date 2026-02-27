# Closed loops checklist (Phase 5)

PASS/FAIL. Each item cites droplet evidence. Do not stop until all PASS.

## DROPLET COMMANDS (run in order until PASS)

```bash
cd /root/stock-bot
git fetch && git reset --hard origin/main
python3 scripts/verify_droplet_script_presence.py
python3 scripts/signal_inventory_on_droplet.py
python3 scripts/signal_usage_map_on_droplet.py
# Set EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1 in stock-bot systemd service; restart; run until gate truth >= 200, breakdown >= 100
python3 scripts/truth_log_enablement_proof_on_droplet.py
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 24
python3 scripts/signal_coverage_and_waste_report_on_droplet.py
python3 scripts/order_reconciliation_on_droplet.py
python3 scripts/full_signal_review_on_droplet.py --days 7
python3 scripts/run_closed_loops_checklist_on_droplet.py
```

---

| # | Item | Status | Droplet evidence |
|---|------|--------|------------------|
| 1 | Gate truth log exists and populated (≥200 lines) | FAIL | logs/expectancy_gate_truth.jsonl lines=0 |
| 2 | Breakdown candidates ≥ 100 | FAIL | logs/signal_score_breakdown.jsonl candidates=0 |
| 3 | SIGNAL_INVENTORY exists | PASS | reports/signal_review/SIGNAL_INVENTORY.json |
| 4 | SIGNAL_USAGE_MAP exists | PASS | reports/signal_review/SIGNAL_USAGE_MAP.json |
| 5 | SIGNAL_PIPELINE_DEEP_DIVE exists | PASS | reports/signal_review/SIGNAL_PIPELINE_DEEP_DIVE.md |
| 6 | Adversarial review cites those artifacts | PASS | multi_model_adversarial_review.md |
| 7 | Gate truth coverage ≥ 95% | FAIL | signal_funnel.json gate_truth_coverage_pct=0.0% |
| 8 | Stage 5 from gate truth (not inferred) | FAIL | signal_funnel.json stage5_from_gate_truth=False |
| 9 | Ledger join explained/fixed or removed from critical path | FAIL | CONTRADICTIONS_CLOSED §1 or stage5_from_gate_truth |
| 10 | Pre-adjust definition proven (no silent defaults) | PASS | CONTRADICTIONS_CLOSED §2 or gate truth pre_score |
| 11 | Paper metric reconciled (candidates / submitted / fills) | FAIL | paper_trade_metric_reconciliation.md |
| 12 | SUBMIT_ORDER_CALLED reconciles with submit_entry and broker | FAIL | submit_order_called.jsonl + ORDER_RECONCILIATION.md |
| 13 | Entry reconciliation is clean (decisions → submit → broker → fills) | PASS | ORDER_RECONCILIATION.md verdict CLEAN/EXPLAINED |
| 14 | No contradictory claims (e.g. 100% choke with 0% coverage) | FAIL | signal_funnel.md claim_100_choke |
| 15 | Governance fails loudly on low coverage / inferred / contradictions | FAIL | run_closed_loops_checklist_on_droplet.py exit code |

**Overall: FAIL — Gate truth coverage 0.0% < 95.0% (required for trustworthy choke claims); Gate truth lines 0 < 200 (recommended for 200-line report); Breakdown candidates 0 < 100 (required for signal deep dive)**
