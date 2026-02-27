# Profitability acceleration review — Multi-model + fast governance loop
## 2026-02-18

**Context:** Phases 0–9 complete; backtest does not apply exit overlays (degenerate for exit tuning). Paper run with score_deterioration 0.28 is live. We are losing money daily.  
**Goal:** Accelerate learning safely; stop bleeding first, then optimize.

---

## Multi-model review (5 questions)

---

### 1) Is exit tuning actually the bottleneck?

**Or are we picking bad trades (entry quality)? What evidence do we need TODAY?**

| Lens | Risks | Blind spots | Faster alternative | Do NOT |
|------|--------|-------------|--------------------|--------|
| **Adversarial** | We have been biasing toward exit levers (flow 0.22 LOCKed, score 0.28 in paper) without a single join-complete **entry_vs_exit_blame** baseline. If weak_entry dominates, we are optimizing the wrong lever and delaying the real fix. | Assuming “high giveback” implies exit is the problem; some giveback is inevitable with bad entries. | **Get blame once, immediately:** Run effectiveness from logs (full available window) and ensure join succeeds. If join fails, fix logging (entry_timestamp / trade_id in both attribution and exit_attribution) so one run produces entry_vs_exit_blame.json. | Do not run another exit-only cycle without at least one blame number. Do not LOCK more exit overlays on zero-delta backtest. |
| **Quant** | Recommendation logic is clear: exit_timing_pct ≥ weak_entry_pct → suggest exit; weak_entry_pct > exit_timing_pct → suggest entry. We have not fed it a valid baseline. Minimum evidence: one effectiveness run with joined_count ≥ 20 and total_losing_trades ≥ 5 so blame percentages are non-empty. | Small samples: blame with 3 losers is noise. Aim for ≥30 closed trades and ≥10 losers for a stable blame split. | Run effectiveness from logs with --start / --end covering the longest window where logs exist; if joined_count &lt; 30, document “provisional” and re-run daily until we have enough. | Do not treat blame from &lt;10 losing trades as definitive. |
| **Product** | Dashboard can show blame when data exists. If we never produce effectiveness from logs successfully on the droplet, the product is useless for this decision. | Droplet may have different log schema or paths; sync logs locally and run locally if needed to unblock. | **Single source of truth:** One designated effectiveness run (e.g. reports/effectiveness_baseline_blame) that is updated when we have new logs; use it for “entry vs exit?” and for pre-paper baseline. | Do not fragment into five different effectiveness dirs with no canonical “baseline” for comparison. |

**Synthesis for Q1:** Evidence needed **today**: one effectiveness run from logs that produces **entry_vs_exit_blame.json** with total_losing_trades ≥ 5 (ideally ≥10). Use it to decide: if weak_entry_pct &gt; exit_timing_pct → next lever is **entry** (down-weight worst signal); else exit levers remain justified. Do not add another exit overlay until this is done.

---

### 2) Given backtests cannot measure exit overlays: what is the FASTEST valid governance loop for exit levers? How to avoid waiting 7–14 days unnecessarily?

| Lens | Risks | Blind spots | Faster alternative | Do NOT |
|------|--------|-------------|--------------------|--------|
| **Adversarial** | “Fast” can mean deciding on 5 trades; that’s noise and can REVERT a good overlay or LOCK a bad one. Minimum sample size is non-negotiable. | Assuming calendar days are the right unit. Trade count is better: 50 closed trades with overlay is comparable across different activity levels. | **Evidence threshold by trade count, not days:** e.g. “LOCK or REVERT when paper period has ≥50 closed trades” (or 30 if we accept higher variance). Run effectiveness on **last N trades** (rolling) so we can evaluate as soon as N is reached. | Do not LOCK/REVERT on &lt;30 closed trades. Do not wait 14 days if we already have 80 trades. |
| **Quant** | Win rate and giveback need a minimum N for stability. Rule of thumb: 30 trades → ~18% standard error on win rate (binary); 50 → ~14%. So 50 is a reasonable “first decision” point; we can add “abort early” at 30 trades if delta is catastrophic (e.g. win rate down &gt;5%). | We don’t yet have “effectiveness on last N trades” in the script; we have --start/--end only. Adding --last-n would allow “effectiveness on last 50 closed trades” without guessing dates. | **Fast path:** Add `--last-n` to run_effectiveness_reports (load joined, sort by exit timestamp, take last N). Then: run effectiveness with --last-n 50 on logs; compare to baseline (effectiveness on same N from pre-paper period, or previous 50 trades). Decision in hours after 50th trade closes, not in 14 days. | Do not change the overlay mid-run to “speed up.” Do not evaluate on &lt;20 trades. |
| **Product** | Operators need a simple rule: “When do I run the check?” Answer: “When state says paper overlay is active and closed trade count since overlay start ≥ 50 (or 30 for early abort).” | No current state file that records “trades since overlay start.” We can use “effectiveness from logs for date range since overlay start” and count joined trades in that run. | Document: “Paper decision gate = first time we have ≥50 closed trades in the overlay window; then run effectiveness for that window and compare to baseline.” If 50 trades take 3 days, we decide in 3 days; if they take 12 days, we decide in 12 days. | Do not fix calendar “7–14 days” in stone; tie to trade count. |

**Synthesis for Q2:** Fastest **valid** loop: (1) Use **logs-based effectiveness** as the source of truth for exit overlays (no backtest compare). (2) Gate the decision on **trade count**: e.g. ≥50 closed trades in paper period (or ≥30 for early REVERT if metrics are clearly worse). (3) Add **--last-n** to run_effectiveness_reports so we can run “effectiveness on last N closed trades” without date guessing. (4) Run comparison: baseline effectiveness (pre-paper or previous N trades) vs proposed (paper period). Total time = time to accumulate N trades, not a fixed 7–14 days.

---

### 3) Minimum evidence to LOCK an exit overlay vs REVERT it early?

| Lens | Risks | Blind spots | Proposal | Do NOT |
|------|--------|-------------|----------|--------|
| **Adversarial** | LOCKing on too little evidence repeats the Phase 9 mistake. REVERTing too early kills a good overlay. Need symmetric, numeric criteria. | “No regression” is vague. We need: what delta in win_rate, giveback, PnL counts as regression? | **LOCK (minimum):** Paper-period effectiveness has ≥50 joined trades (or ≥30 if we accept provisional). Compare to baseline: win_rate change ≥ -2%, avg_profit_giveback change ≤ +0.05, total PnL not materially worse (e.g. not down &gt;20% vs baseline period). Regression guards pass if run. Document in change proposal + result doc. | Do not LOCK without a written comparison (baseline vs proposed metrics). Do not LOCK on “no data” or “recommendation empty.” |
| **Quant** | Early REVERT: if in the first 30 trades with overlay we see win_rate drop &gt;5% vs baseline or giveback spike &gt;0.10, we can REVERT early and restart paper without overlay. Saves capital in paper and avoids locking a bad lever. | Baseline must be comparable: same “last N” or same calendar window length. Comparing “last 50 with overlay” to “last 30 pre-overlay” is biased. | **REVERT early (abort):** After ≥30 closed trades with overlay: if win_rate (paper period) is &gt;3% below baseline win_rate, or avg_profit_giveback is &gt;0.05 above baseline → REVERT immediately, restart paper without overlay, document. **REVERT at decision gate:** At 50 trades, if falsification criteria (win_rate drop &gt;2%, giveback increase &gt;0.05, or guards fail) → REVERT. | Do not REVERT on &lt;20 trades unless delta is extreme (e.g. win rate &lt;0.25 and baseline was 0.35). Do not ignore guards. |
| **Product** | Operators need a checklist: “How many trades? Run effectiveness. Compare. LOCK or REVERT?” | No automated “trade count since overlay start” yet. Manual: run effectiveness with date range = overlay start to now; joined_count in output = trade count. | **Minimum evidence table:** (1) LOCK: ≥50 trades (or ≥30 provisional), comparison doc, win_rate delta ≥ -2%, giveback delta ≤ +0.05, guards pass. (2) REVERT early: ≥30 trades and (win_rate delta &lt; -3% or giveback delta &gt; +0.05). (3) REVERT at gate: at 50 trades, falsification hit. | Do not invent new criteria ad hoc; stick to the table. |

**Synthesis for Q3:** **LOCK:** ≥50 closed trades in paper period; baseline vs proposed comparison; win_rate change ≥ -2%; giveback change ≤ +0.05; PnL not materially worse; guards pass. **REVERT early:** ≥30 trades and (win_rate &lt; baseline - 3% or giveback &gt; baseline + 0.05). **REVERT at gate:** At 50-trade check, falsification criteria met. All decisions and numbers must be written in the change proposal / result doc.

---

### 4) Rolling effectiveness (N trades) instead of fixed time windows?

| Lens | Risks | Blind spots | Proposal | Do NOT |
|------|--------|-------------|----------|--------|
| **Adversarial** | “Last N trades” can span two regimes (pre- and post-overlay) if we don’t split by overlay start. So for paper evaluation we need “joined trades where exit_timestamp ≥ overlay_start,” not “last N from entire log.” | Mixing pre- and post-overlay in one “last 50” would dilute the effect. | **Rolling for decision:** “Paper period” = trades that closed **after** overlay start (state/live_paper_run_state.json or overlay start date). Run effectiveness on that subset only. “Last N” is then “last N of that subset.” For baseline, use “last N trades before overlay start” or “same date range length before overlay.” | Do not use “last 50 from entire log” for paper evaluation; that can include pre-overlay trades. |
| **Quant** | Implementation: load_joined_closed_trades returns list; order is by exit file order. We need to sort by exit timestamp (or timestamp), take last N. For “paper only” we need to filter by overlay_start ≤ exit_timestamp. So: either --last-n with optional --since-date, or --start/--end and we compute N from joined count. | Current script has no --last-n. Adding it is a small change: after loading joined, sort by timestamp, take last N (and optionally filter by since_date). | **Add --last-n [N]** to run_effectiveness_reports (and optionally --since-date YYYY-MM-DD for “only trades on or after this date”). Then: “effectiveness on last 50 trades since overlay start” = run with --since-date &lt;overlay_start&gt; and take last 50 from that (or run with date range and if joined_count ≥ 50, we already have it). Simpler: run with --start &lt;overlay_start&gt; --end today; if joined_count ≥ 50, use that; else “wait for more trades.” | Do not over-engineer; date range + joined_count ≥ 50 may be enough without --last-n if we have overlay start date. |
| **Product** | Rolling N is easier to explain: “We need 50 closed trades with the new config, then we compare.” | Dashboard could show “closed trades this week” or “since overlay”; not required for first loop. | **Adopt:** Use “paper period = start date of overlay to now.” Run effectiveness --start &lt;overlay_start&gt; --end today. Decision when joined_count ≥ 50 (or early REVERT when ≥30 and metrics worse). Optional: add --last-n for “effectiveness on last N trades globally” for ad-hoc checks. | Do not wait for a dashboard feature; use CLI and state file. |

**Synthesis for Q4:** Use **trade count** as the gate (e.g. ≥50 in paper period). “Paper period” = overlay start date to now. Run effectiveness with --start &lt;overlay_start&gt; --end today; joined_count in output = trade count. When joined_count ≥ 50, run comparison and LOCK or REVERT. **Optional:** Add --last-n to run_effectiveness_reports for “effectiveness on last N trades” (sort joined by timestamp, take last N) to support rolling checks without date math.

---

### 5) Are we missing a higher-EV move (e.g. disabling worst signal) that would reduce losses faster than exit tuning?

| Lens | Risks | Blind spots | Proposal | Do NOT |
|------|--------|-------------|----------|--------|
| **Adversarial** | If entry quality is the bottleneck, down-weighting or disabling the worst signal could reduce losses **immediately** (fewer bad trades) while exit tuning only affects when we close. We have not tested an entry lever yet. | We don’t know the worst signal without signal_effectiveness from a valid run. And “disable” might mean weight=0; we need to confirm the engine respects that and doesn’t break. | **As soon as we have blame + signal_effectiveness:** If weak_entry_pct &gt; exit_timing_pct, create one **entry** overlay: down-weight the worst signal (e.g. -0.05 or half weight) or set to 0 if schema allows. Run paper with that overlay only (no stacking with exit). Compare after 50 trades. That could stop more bleeding than exit tuning if the problem is entry. | Do not disable multiple signals at once. Do not skip the blame check. |
| **Quant** | signal_effectiveness ranks by win_rate, avg_MAE, avg_pnl. Worst signal has lowest win_rate, high MAE. generate_recommendation already picks top5_harmful; we could take the single worst (min win_rate, sufficient trade_count) and down-weight it. High EV if that signal is driving a large share of losses. | One signal might be “worst” in a small sample and actually positive in larger sample. Use min trade_count ≥ 5 or 10 for “worst” designation. | **Minimum evidence for entry lever:** entry_vs_exit_blame says weak_entry_pct &gt; exit_timing_pct; signal_effectiveness has at least one signal with trade_count ≥ 5 and win_rate &lt; 0.35 (or avg_pnl &lt; -X). Then one overlay: reduce that signal’s weight by a small delta (e.g. 0.05) or set to 0. One lever, one cycle. | Do not down-weight by &gt;50% in one go; small delta first. |
| **Product** | “Disable worst signal” is a clear narrative for the trading committee. It’s also reversible (overlay off = back to baseline). | We may not have entry overlay examples in config/tuning/overlays yet; check schema for entry_weights_v3 or similar. | **Adopt as next move if blame says entry:** After blame baseline shows weak_entry &gt; exit_timing, the **next** governed cycle should be an entry lever (worst signal down-weight), not a second exit lever. Paper run with that overlay; same 50-trade gate and comparison. | Do not do entry and exit overlays in the same cycle. |

**Synthesis for Q5:** Yes, we may be missing a higher-EV move. **If** entry_vs_exit_blame shows weak_entry_pct &gt; exit_timing_pct, then **entry** tuning (down-weight worst signal) could reduce losses faster than more exit tuning. Evidence needed: one effectiveness run with blame + signal_effectiveness; then if weak_entry dominates, create a single entry overlay (worst signal, small delta), run paper, same 50-trade comparison. Do not stack with exit overlay.

---

## Synthesis — Adopt / Defer / Avoid

| Adopt immediately | Defer | Explicitly avoid |
|-------------------|--------|-------------------|
| Get one blame baseline (effectiveness from logs, join working; ≥5 losers) | Full automation of “trade count since overlay” in dashboard | Another exit-only cycle without blame baseline |
| Gate exit-overlay decisions on **trade count** (e.g. ≥50; early REVERT at ≥30 if metrics worse) | Adding exit simulation to backtest (do later for runbook fidelity) | LOCK/REVERT on &lt;30 trades |
| Use logs-based effectiveness as primary evidence for exit levers; no backtest compare for exit | --last-n in run_effectiveness_reports (optional; date range + count works) | Stacking exit + entry overlays |
| LOCK/REVERT criteria: win_rate ≥ -2%, giveback ≤ +0.05, comparison doc, guards | Multi-window / sensitivity tooling | Changing overlay mid-run |
| If blame says weak_entry &gt; exit_timing → next cycle = **entry** lever (down-weight worst signal) | | Fixing “7–14 days” in stone; use 50-trade gate |
| Abort early: REVERT if ≥30 trades and win_rate &lt; baseline - 3% or giveback &gt; baseline + 0.05 | | |

---

## Fast path forward (24–72 hours)

**Concrete steps we can execute in the next 24–72 hours:**

1. **Produce blame baseline (within 24 h)**  
   - On droplet or locally (with synced logs): run  
     `python scripts/analysis/run_effectiveness_reports.py --start YYYY-MM-DD --end YYYY-MM-DD --out-dir reports/effectiveness_baseline_blame`  
     for the longest date range where logs exist (e.g. last 14–30 days).  
   - Ensure `entry_vs_exit_blame.json` is produced and has total_losing_trades ≥ 5.  
   - If join fails (joined_count 0 or very low): fix logging so exit_attribution and attribution have matching entry_timestamp or trade_id; re-run.  
   - Run `python scripts/governance/generate_recommendation.py --effectiveness-dir reports/effectiveness_baseline_blame --out reports/effectiveness_baseline_blame`.  
   - **Decision:** If weak_entry_pct &gt; exit_timing_pct → plan **next** cycle as **entry** lever (down-weight worst signal from signal_effectiveness). If exit_timing_pct ≥ weak_entry_pct → continue with exit-lever paper check.

2. **Define paper decision gate for current score_deterioration 0.28 run**  
   - **Gate:** First time we have **≥50 closed trades** in the paper period (overlay start to now).  
   - **How to check:** Run effectiveness with --start &lt;overlay_start_date&gt; --end today; read joined_count from output or EFFECTIVENESS_SUMMARY.  
   - When joined_count ≥ 50: run generate_recommendation; compare to baseline (reports/effectiveness_baseline_blame or pre-paper effectiveness).  
   - **LOCK** if: win_rate change ≥ -2%, giveback change ≤ +0.05, PnL not materially worse; document in reports/PROFITABILITY_PAPER_RUN_2026-02-18.md.  
   - **REVERT** if: win_rate drop &gt;2%, giveback increase &gt;0.05, or guards fail; restart paper without overlay and document.

3. **Early REVERT (optional but recommended)**  
   - When joined_count in paper period first reaches **≥30**: run effectiveness for that period; compare win_rate and giveback to baseline.  
   - If win_rate &lt; baseline - 3% or giveback &gt; baseline + 0.05 → **REVERT immediately**, restart paper without overlay, document. No need to wait for 50.

4. **Evidence thresholds (trade count, metrics)**  
   - **Minimum for blame baseline:** joined_count ≥ 20, total_losing_trades ≥ 5.  
   - **Minimum for LOCK:** paper period joined_count ≥ 50 (or ≥30 provisional); comparison doc; win_rate delta ≥ -2%; giveback delta ≤ +0.05.  
   - **Early REVERT:** paper period ≥ 30 and (win_rate delta &lt; -3% or giveback delta &gt; +0.05).  
   - **Do not LOCK** without a written comparison and these thresholds.

5. **No new overlays mid-run**  
   - Do not add or stack overlays until the current score_deterioration 0.28 paper run has been decided (LOCK or REVERT at 50-trade gate or early REVERT at 30).

---

## GO / NO-GO

**GO**, with the following scope.

- **Execute** the fast path above: (1) produce blame baseline in 24–72 h; (2) define and apply 50-trade gate (and optional 30-trade early REVERT) for the current paper run; (3) document LOCK/REVERT in the paper run doc with comparison and thresholds.  
- **Do not** run the full droplet runbook (baseline vs proposed backtest) for exit levers; backtest compare remains degenerate.  
- **Prefer** logs-based effectiveness over backtests for exit levers; use trade-count gates; abort early if falsification is hit; do not stack exit levers; do not introduce new overlays mid-run.

---

## Conditional authorization — confirmation of immediate next actions

**If GO (as above), the following are the immediate next actions:**

1. **Within 24 h:** Run effectiveness from logs for the longest available window; ensure join works and entry_vs_exit_blame.json exists with ≥5 losers. Write output to reports/effectiveness_baseline_blame (or equivalent). Run generate_recommendation. Record weak_entry_pct vs exit_timing_pct and decide whether the next cycle (after current paper run) is entry or exit.  
2. **Ongoing:** Check paper-period trade count (effectiveness --start &lt;overlay_start&gt; --end today; use joined_count). When ≥30: run effectiveness and compare; early REVERT if win_rate &lt; baseline - 3% or giveback &gt; baseline + 0.05. When ≥50: run full comparison, LOCK or REVERT per criteria, update reports/PROFITABILITY_PAPER_RUN_2026-02-18.md.  
3. **No execution** of baseline vs proposed backtest on droplet for exit overlays; no new overlays until current paper run is decided.

Execution rules respected: logs-based effectiveness for exit levers; rolling trade-count gates; early abort on falsification; no stacking; no new overlays mid-run.

---

## Emotional reality

We are losing money every day. This review:

- **Speeds up** by tying the decision to **trade count** (50 or 30) instead of a fixed 7–14 days, and by **getting blame once** so we don’t tune the wrong side.  
- **Keeps discipline** by requiring minimum evidence (50 trades, comparison doc, numeric thresholds) and early REVERT when metrics are clearly worse.  
- **Avoids desperation** by not stacking levers, not LOCKing without comparison, and by checking entry vs exit before committing to more exit-only tuning.

Stop bleeding first: get blame, then either fix entry (if weak_entry dominates) or validate exit overlay (if exit_timing dominates) with a clear, evidence-based gate.
