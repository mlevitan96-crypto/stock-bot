# Droplet-canonical investigation runbook

All evidence must come from the droplet. Run these in order.

## DROPLET COMMANDS (exact order)

### Phase 0 — Baseline

```bash
cd /root/stock-bot
python3 scripts/investigation_baseline_snapshot_on_droplet.py
# Output: reports/investigation/BASELINE_SNAPSHOT.md
```

### Phase 1 — Gate truth (≥200 lines)

1. Enable truth log and run paper/live until `logs/expectancy_gate_truth.jsonl` has ≥200 lines:

```bash
cd /root/stock-bot
export EXPECTANCY_GATE_TRUTH_LOG=1
# Run your paper/live loop (e.g. board/eod/start_live_paper_run.py or main.py) until 200+ lines
wc -l logs/expectancy_gate_truth.jsonl
```

2. Generate 200-line report:

```bash
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
# Output: reports/signal_review/expectancy_gate_truth_200.md
```

### Phase 2 — Funnel from gate truth

```bash
python3 scripts/full_signal_review_on_droplet.py --days 7
# Optional: --capture to run decision ledger capture first
# Outputs: signal_funnel.md/.json, paper_trade_metric_reconciliation.md, multi_model_adversarial_review.md
```

### Phase 3 — Close contradictions

After running Phase 0–2, fill `reports/investigation/CONTRADICTIONS_CLOSED.md` with root cause, fix, and **Droplet proof** (file path + counts/%) for:

1. Ledger join coverage 0%
2. Pre-adjust median 0.000
3. “Paper trades” vs submits (fixed by renamed metrics; document reconciliation)

Re-run full_signal_review and run_closed_loops_checklist so items 4–5 can PASS.

### Phase 5 — Closed loops checklist

```bash
python3 scripts/run_closed_loops_checklist_on_droplet.py
# Exits 1 if gate truth coverage < 95% or stage 5 not from gate truth when coverage sufficient
# Output: reports/investigation/CLOSED_LOOPS_CHECKLIST.md
```

### Required final terminal output (after all PASS)

Print or capture:

- CLOSED LOOPS CHECKLIST: PASS (all items)
- Dominant choke point: &lt;stage&gt;/&lt;reason&gt; count, %
- Gate truth coverage %: X%
- score_used_by_gate median/p10/p90 (from expectancy_gate_truth_200.md or funnel)
- submit called: count (from paper_orders_submitted)
- FINAL VERDICT: one sentence
