# Droplet runbook: Signals + Entries (no stop until trades or proof)

**Contract:** Droplet is canonical. Multi-model adversarial required. No strategy tuning. No "check the droplet" hand-offs — run these on the droplet and the scripts produce the evidence.

**Done when:** Either (A) SUBMIT_ORDER_CALLED > 0, or (B) CLOSED LOOPS CHECKLIST = PASS with signal-level proof explaining why not.

---

## Phase 1 — Verify droplet is ready

```bash
cd /root/stock-bot
git fetch && git reset --hard origin/main
python3 scripts/verify_droplet_script_presence.py
```

If any script is missing: fix by committing/pushing, then re-run.  
**Artifact:** `reports/investigation/DROPLET_SCRIPT_PRESENCE.md` (includes ls output + commands).

---

## Phase 2 — Force runtime signal truth (systemd, NOT shell)

1. Set env vars in the **stock-bot service** (systemd override or env file):
   - `EXPECTANCY_GATE_TRUTH_LOG=1`
   - `SIGNAL_SCORE_BREAKDOWN_LOG=1`
2. Restart the service.
3. Prove they are active:
   - `systemctl show stock-bot --property=Environment`
   - `PID=$(systemctl show stock-bot --property=MainPID --value); cat /proc/$PID/environ | tr '\0' '\n' | grep -E 'EXPECTANCY_GATE_TRUTH_LOG|SIGNAL_SCORE_BREAKDOWN_LOG'`

Then **run the bot** until:
- `logs/expectancy_gate_truth.jsonl` >= 200 lines
- `logs/signal_score_breakdown.jsonl` >= 100 candidates

```bash
python3 scripts/truth_log_enablement_proof_on_droplet.py
```

**Artifact:** `reports/investigation/TRUTH_LOG_ENABLEMENT_PROOF.md` (commands, counts, file paths).

---

## Phase 3 — Show the easy view (signals → score → gate)

```bash
cd /root/stock-bot
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 24
python3 scripts/signal_coverage_and_waste_report_on_droplet.py
```

These answer: which signals are missing/zero/crushed, which contribute, why composite < 2.5.  
**Artifacts:** `SIGNAL_PIPELINE_DEEP_DIVE.md/.json`, `SIGNAL_COVERAGE_AND_WASTE.md`, `expectancy_gate_truth_200.md`.

---

## Phase 4 — Entry path reconciliation

```bash
python3 scripts/order_reconciliation_on_droplet.py
```

Proves: submit decisions → submit calls → broker responses → fills; no fills without submit; no submit without decision.  
**Artifact:** `reports/investigation/ORDER_RECONCILIATION.md`.

---

## Phase 5 — Multi-model adversarial

```bash
python3 scripts/full_signal_review_on_droplet.py --days 7
```

Produces `reports/signal_review/multi_model_adversarial_review.md` with:
- Prosecution: one dominant root cause (cite SIGNAL_PIPELINE_DEEP_DIVE + ≥5 trace_ids)
- Defense: ≥2 alternative causes + falsification tests
- SRE: env vars, log freshness, coverage %, integrity
- Board verdict: one dominant choke, one minimal reversible fix (NOT threshold changes), numeric acceptance criteria

---

## Phase 6 — Closed loops enforcement

```bash
python3 scripts/run_closed_loops_checklist_on_droplet.py
```

Run until PASS. Checklist fails unless:
- Gate truth >= 200 lines, breakdown >= 100 candidates
- Signal inventory + usage map exist
- Deep dive + coverage/waste exist
- Adversarial cites those artifacts
- Entry reconciliation is clean

**Artifact:** `reports/investigation/CLOSED_LOOPS_CHECKLIST.md` (all PASS).

---

## Final required terminal output (on droplet)

When checklist PASS, the script prints:
- CLOSED LOOPS CHECKLIST: PASS
- Dominant choke point (specific signals or stage)
- Gate truth coverage + p10/p50/p90
- Top broken signals with missing/zero/crushed rates
- SUBMIT_ORDER_CALLED count
- FINAL VERDICT (one sentence)

---

## Full command sequence (copy-paste on droplet)

```bash
cd /root/stock-bot
git fetch && git reset --hard origin/main
python3 scripts/verify_droplet_script_presence.py
# Set EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1 in stock-bot systemd service; restart; run bot until gate truth >= 200, breakdown >= 100
python3 scripts/truth_log_enablement_proof_on_droplet.py
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/signal_inventory_on_droplet.py
python3 scripts/signal_usage_map_on_droplet.py
python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 24
python3 scripts/signal_coverage_and_waste_report_on_droplet.py
python3 scripts/order_reconciliation_on_droplet.py
python3 scripts/full_signal_review_on_droplet.py --days 7
python3 scripts/run_closed_loops_checklist_on_droplet.py
```

Repeat from Phase 2 (run bot until 200/100) if gate truth or breakdown counts are insufficient, then re-run from truth_log_enablement through checklist until PASS.
