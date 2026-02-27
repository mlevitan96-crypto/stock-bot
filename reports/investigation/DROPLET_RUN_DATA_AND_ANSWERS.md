# Droplet run — data and answers (0 trades)

**Last run:** 2026-02-20 (via `scripts/run_investigation_on_droplet_and_fetch.py`).  
**Source:** Commands executed on droplet via SSH; reports fetched to `reports/investigation/fetched/`.

---

## Why we have 0 trades (droplet-proven)

| Finding | Value |
|--------|--------|
| **Dominant choke** | **5_expectancy_gate** — **expectancy_gate:score_floor_breach** |
| **Choke count** | 2,922 (100% of candidates) |
| **Post-adjust composite at gate** | p10 = 0.172, p50 = 0.172, p90 = 0.316 |
| **% above MIN_EXEC_SCORE (2.5)** | 0.0% (pre and post) |
| **SUBMIT_ORDER_CALLED** | 0 |
| **submit_entry log lines (7d)** | 334 (block/audit path; no live submit) |
| **Fills in orders.jsonl (7d)** | 5,092 (historical; not from this run’s submits) |

**Answer:** Every candidate is blocked at the **expectancy gate** because **composite score &lt; 2.5**. The gate is behaving as designed; the blocker is **score level**, not gate logic. Median composite at the gate is **0.172**; no candidate reaches 2.5 in this window.

---

## What ran on the droplet (this run)

| Step | Result |
|------|--------|
| Git pull | Already up to date |
| Script presence | PASS (required scripts present) |
| Baseline snapshot | Wrote BASELINE_SNAPSHOT.md |
| Full signal review | Wrote funnel, adversarial, paper reconciliation |
| Order reconciliation | submit_called=0, fills=5092 (historical) |
| Closed loops checklist | FAIL (gate truth 0 lines, breakdown 0 lines) |
| Expectancy gate truth 200 | Skipped (0 lines; need 200) |
| Signal breakdown summary | Skipped (0 lines; need 100) |

Gate truth and signal breakdown logs are **0 lines** because **EXPECTANCY_GATE_TRUTH_LOG** and **SIGNAL_SCORE_BREAKDOWN_LOG** are not yet set in the **stock-bot systemd service** on the droplet.

---

## What to do next (to get signal-level proof or trades)

### Option A — Enable truth logging, then re-run (recommended)

1. **On the droplet**, set env vars in the stock-bot **service** (systemd override, not shell):

   ```bash
   sudo mkdir -p /etc/systemd/system/stock-bot.service.d
   sudo tee /etc/systemd/system/stock-bot.service.d/override.conf << 'EOF'
   [Service]
   Environment="EXPECTANCY_GATE_TRUTH_LOG=1"
   Environment="SIGNAL_SCORE_BREAKDOWN_LOG=1"
   EOF
   sudo systemctl daemon-reload
   sudo systemctl restart stock-bot
   ```

2. **Let the bot run** until:
   - `logs/expectancy_gate_truth.jsonl` ≥ 200 lines  
   - `logs/signal_score_breakdown.jsonl` ≥ 100 lines  

   Check: `wc -l /root/stock-bot/logs/expectancy_gate_truth.jsonl /root/stock-bot/logs/signal_score_breakdown.jsonl`

3. **Re-run investigation** (from this repo, with droplet_config.json):

   ```bash
   python scripts/run_investigation_on_droplet_and_fetch.py
   ```

   Or use the one-shot script that enables, waits, and re-runs:

   ```bash
   python scripts/enable_truth_logs_on_droplet_and_re_run.py
   ```

4. After that, you will have:
   - **expectancy_gate_truth_200.md** (p10/p50/p90, pass rate)  
   - **SIGNAL_PIPELINE_DEEP_DIVE** (per-signal missing/zero/contribution, dominant failure mode)  
   - **SIGNAL_COVERAGE_AND_WASTE** (broken vs healthy signals)  
   - **CLOSED_LOOPS_CHECKLIST** (PASS when gate truth ≥200 and breakdown ≥100)

That gives **signal-level proof** for why composite stays below 2.5 (which signals are missing, zero, or crushed).

### Option B — Fix the score (only after proof)

- **Do not** change MIN_EXEC_SCORE, gates, or risk controls without evidence.  
- After Option A, use SIGNAL_PIPELINE_DEEP_DIVE and SIGNAL_COVERAGE_AND_WASTE to see:
  - Which signals are missing or zero (fix data/inputs).  
  - Which are crushed by normalization (fix pipeline or weights).  
- One **minimal reversible** experiment (per Board verdict): fix a single broken signal or normalization step and re-run; no threshold changes.

---

## Board verdict (from adversarial review)

- **ONE dominant choke:** 5_expectancy_gate — expectancy_gate:score_floor_breach. Composite below MIN_EXEC_SCORE (2.5); post-adjust median 0.17.
- **ONE minimal reversible experiment:** Enable expectancy-gate and signal breakdown logging (≥200 and ≥100 lines); confirm pre vs post and per-signal contributions. No threshold or weight changes.
- **Numeric acceptance criteria:** (1) Gate truth log ≥200 lines with (composite_score, MIN_EXEC_SCORE, gate_outcome). (2) Signal breakdown ≥100 candidates. (3) Post-adjust median and % above 2.5 match funnel for same window.

---

## Fetched artifacts (this run)

| File | Fetched |
|------|---------|
| BASELINE_SNAPSHOT.md | Yes |
| CLOSED_LOOPS_CHECKLIST.md | Yes |
| DROPLET_SCRIPT_PRESENCE.md | Yes |
| ORDER_RECONCILIATION.md | Yes |
| TRUTH_LOG_ENABLEMENT_PROOF.md | Yes |
| signal_funnel.md / .json | Yes |
| paper_trade_metric_reconciliation.md | Yes |
| multi_model_adversarial_review.md | Yes |
| signal_score_breakdown_summary.md | No (0 breakdown lines) |
| expectancy_gate_truth_200.md | No (0 gate truth lines) |
| SIGNAL_PIPELINE_DEEP_DIVE.md | No (not yet run on droplet with new script) |
| SIGNAL_COVERAGE_AND_WASTE.md | No (same) |

---

## Summary

- **0 trades** because **100% of candidates** are blocked at the expectancy gate (composite &lt; 2.5; median 0.172).
- **Signal-level root cause (from droplet cache):** See **`reports/investigation/SIGNAL_FLOW_FINDINGS.md`**. Droplet's uw_flow_cache was fetched; diagnostic run locally with that cache. **Six signals are 100% zero** (whale, motif_bonus, congress, shorts_squeeze, institutional, calendar)—wired into the trade engine but **not receiving data** (expanded_intel / UW pipeline not populating them). Dark pool is "missing" for SPY/QQQ/COIN/NVDA/TSLA. Composite mean on 50 symbols is **0.937**; flow and event contribute but the six zeroed signals plus low dark_pool keep scores below 2.5.
- **Next step:** Populate expanded_intel and UW pipeline so congress, shorts, institutional, market_tide, calendar, whale, motif get real data; optionally enable truth logs for ongoing proof.
