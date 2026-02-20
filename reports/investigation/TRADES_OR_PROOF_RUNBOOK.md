# Trades-or-proof investigation runbook (droplet only)

Do not stop until `scripts/run_closed_loops_checklist_on_droplet.py` exits 0 and prints **CLOSED LOOPS CHECKLIST: PASS**.

## Phase 1 — Make droplet whole

1. Commit and push from local so these exist on `origin/main`:
   - scripts/investigation_baseline_snapshot_on_droplet.py
   - scripts/run_closed_loops_checklist_on_droplet.py
   - scripts/expectancy_gate_truth_report_200_on_droplet.py
   - scripts/signal_score_breakdown_summary_on_droplet.py
   - scripts/full_signal_review_on_droplet.py (updated)
   - scripts/verify_droplet_script_presence.py
   - scripts/order_reconciliation_on_droplet.py
2. On droplet: `git pull origin main`
3. On droplet: `python3 scripts/verify_droplet_script_presence.py`
4. Write/update: **reports/investigation/DROPLET_SCRIPT_PRESENCE.md** (list files + ls output + droplet commands)

## Phase 2 — Enable truth logs (systemd)

1. Set `EXPECTANCY_GATE_TRUTH_LOG=1` and `SIGNAL_SCORE_BREAKDOWN_LOG=1` in the stock-bot service (override or .env), then restart.
2. Prove env vars in running process (systemctl show, /proc/<pid>/environ).
3. Run until logs/expectancy_gate_truth.jsonl ≥ 200 lines and logs/signal_score_breakdown.jsonl ≥ 100 lines.
4. Document: **reports/investigation/TRUTH_LOG_ENABLEMENT_PROOF.md**

See TRUTH_LOG_ENABLEMENT_PROOF.md for exact commands.

## Phase 3 — Easy view (signals → score → gate)

On droplet, in order:

```bash
cd /root/stock-bot
python3 scripts/investigation_baseline_snapshot_on_droplet.py
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/signal_score_breakdown_summary_on_droplet.py
python3 scripts/full_signal_review_on_droplet.py --days 7
```

Outputs: expectancy_gate_truth_200.md, signal_score_breakdown_summary.md, signal_funnel.md/.json.

## Phase 4 — Reconcile fills vs submits

On droplet:

```bash
python3 scripts/order_reconciliation_on_droplet.py
```

Writes: **reports/investigation/ORDER_RECONCILIATION.md** (SUBMIT_ORDER_CALLED, submit_entry, broker, fills for same window).

## Phase 5 — Multi-model adversarial + closed loops

1. full_signal_review_on_droplet.py (Phase 3) already updates multi_model_adversarial_review.md with gate truth and breakdown stats when present.
2. On droplet: `python3 scripts/run_closed_loops_checklist_on_droplet.py`
3. If exit non-zero: fix failing item(s), re-run phases as needed, repeat until PASS.

## Final required terminal output (when checklist PASS)

- CLOSED LOOPS CHECKLIST: PASS
- Dominant choke point: <stage>/<reason> count, %
- Gate truth coverage: X%
- score_used_by_gate p10 / p50 / p90
- Top 10 signals by contribution + missing/zero rates
- submit called: <count>
- FINAL VERDICT: <one sentence>
