# Droplet script presence (Phase 1)

Verification after `git fetch && git reset --hard origin/main`. All required scripts must exist.

## Required scripts

- `scripts/verify_droplet_script_presence.py` — PRESENT
- `scripts/signal_inventory_on_droplet.py` — PRESENT
- `scripts/signal_usage_map_on_droplet.py` — PRESENT
- `scripts/truth_log_enablement_proof_on_droplet.py` — PRESENT
- `scripts/expectancy_gate_truth_report_200_on_droplet.py` — PRESENT
- `scripts/signal_pipeline_deep_dive_on_droplet.py` — PRESENT
- `scripts/signal_coverage_and_waste_report_on_droplet.py` — PRESENT
- `scripts/order_reconciliation_on_droplet.py` — PRESENT
- `scripts/full_signal_review_on_droplet.py` — PRESENT
- `scripts/run_closed_loops_checklist_on_droplet.py` — PRESENT
- `scripts/signal_score_breakdown_summary_on_droplet.py` — PRESENT

## ls output (scripts)

```
-rw-r--r-- 1 root root 3297 ... scripts/verify_droplet_script_presence.py
-rw-r--r-- 1 root root 5572 ... scripts/signal_inventory_on_droplet.py
-rw-r--r-- 1 root root 2814 ... scripts/signal_usage_map_on_droplet.py
-rw-r--r-- 1 root root 6383 ... scripts/truth_log_enablement_proof_on_droplet.py
-rw-r--r-- 1 root root 3863 ... scripts/expectancy_gate_truth_report_200_on_droplet.py
-rw-r--r-- 1 root root 12195 ... scripts/signal_pipeline_deep_dive_on_droplet.py
-rw-r--r-- 1 root root 5665 ... scripts/signal_coverage_and_waste_report_on_droplet.py
-rw-r--r-- 1 root root 6217 ... scripts/order_reconciliation_on_droplet.py
-rw-r--r-- 1 root root 38080 ... scripts/full_signal_review_on_droplet.py
-rw-r--r-- 1 root root 13435 ... scripts/run_closed_loops_checklist_on_droplet.py
-rw-r--r-- 1 root root 11037 ... scripts/signal_score_breakdown_summary_on_droplet.py
```

## DROPLET COMMANDS

```bash
cd /root/stock-bot
git fetch && git reset --hard origin/main
python3 scripts/verify_droplet_script_presence.py
```

**Result: PASS** — all required scripts present.
