# Exit design: multi-factor exits and learning

**Purpose:** Expert-style guidance on (1) using multiple reasons for exits instead of a single hard gate, and (2) tracking exit causes and using them to improve.

---

## 1. Should multiple reasons contribute to an exit?

**Yes.** Exits are better when they reflect **weight of evidence**, not a single binary trigger.

- **Single hard gate (e.g. “exit only on signal_decay &lt; 0.4”):** One factor can fire by noise; you exit too early or too late and you can’t tell which factor mattered.
- **Multi-factor:** You accumulate several signals (decay, flow reversal, drawdown, regime, time, etc.). The **decision** can be “exit when combined score &gt; threshold” and the **label** can list all contributors. That gives:
  - More robust decisions (less sensitivity to one noisy input).
  - Richer attribution (you see *why* this exit happened).
  - Better learning (you can tune weights and thresholds per factor using outcomes).

So: **multiple reasons contributing to both the decision and the label is the right direction.**

---

## 2. What we do today

**Label (close reason):** We already support **multiple reasons** in the close reason string. `build_composite_close_reason(exit_signals)` in `main.py` joins every applicable factor (e.g. `signal_decay(0.73)+flow_reversal`, `trail_stop(-1.2%)+drawdown(3.5%)`). So the dashboard “Close Reason” column can show several causes at once.

**Decision (when to close):** The exit loop is largely a **cascade of checks**: v2_exit score, regime protection, adaptive urgency, stale/time rules, then stop loss, trailing stop, signal-decay threshold, profit target. The **first** condition that says “close now” wins, and we then build the composite reason from **all** flags set so far (including e.g. `signal_decay` and `flow_reversal`). So we *do* accumulate multiple factors into the label, but the *trigger* is still “first rule that fires,” not a single combined score threshold.

**Implication:** We’re already multi-factor in **attribution**. To be multi-factor in **decision** as well, we’d add (or lean more on) a **combined exit score** (e.g. from `get_exit_urgency` / adaptive or from `compute_exit_score_v2`) and “close when score &gt; X” instead of relying only on the first cascade hit.

---

## 3. Are we tracking exit causes and using them to get better?

**Yes for tracking; partial for “getting better.”**

**Tracking:**

- **Exit attribution:** Every full close is logged with `close_reason` (composite string), `exit_reason_code` (taxonomy: e.g. intel_deterioration, stop, profit, trail_stop, displacement, time_exit, other), plus entry/exit snapshots and P&L. See `docs/ATTRIBUTION_EXIT_TAXONOMY.md` and `docs/ATTRIBUTION_SCHEMA_CANONICAL_V1.md`.
- **Exit effectiveness reports:** `scripts/analysis/run_effectiveness_reports.py` aggregates by **exit_reason_code** (and by signal for entry): frequency, avg realized P&L, avg profit giveback, % saved_loss, % left_money. So we *do* track which exit reasons are associated with better/worse outcomes. See `docs/ATTRIBUTION_EFFECTIVENESS_REPORTS.md`.
- **Entry vs exit blame:** For losing trades we split “weak entry” vs “exit timing” (e.g. high giveback / MFE-but-loss) so we can focus tuning on entry vs exit.
- **Counterfactuals:** We identify “hold longer would have helped” vs “exit earlier would have saved loss” from exit_quality_metrics.

**Getting better:**

- Today the effectiveness pipeline is **analysis-only** (“No tuning yet” in the docs). We have the data and the reports to see which exit reasons and regimes perform well or poorly, but we don’t yet auto-adjust thresholds or weights from that.
- **Concrete next steps to “get better”:**
  1. **Run effectiveness reports regularly** (e.g. weekly or after each backtest):  
     `python scripts/analysis/run_effectiveness_reports.py --start YYYY-MM-DD --end YYYY-MM-DD`
  2. **Review exit effectiveness** (frequency, avg_pnl, giveback, saved_loss, left_money) and **entry vs exit blame** to decide whether to tighten/loosen exits or improve entries.
  3. **Optionally:** Move toward a **single combined exit score** (e.g. weighted sum of decay, flow_reversal, drawdown, regime, time) and one or two thresholds (e.g. “exit_urgent” vs “exit_normal”) so multiple factors *directly* drive the decision, not only the label.
  4. **Later:** Use effectiveness stats (e.g. by exit_reason_code and regime) to suggest or automate threshold/weight tweaks (e.g. “exits with reason X have high giveback → relax that trigger in regime Y”).

---

## 4. Summary

| Question | Answer |
|----------|--------|
| Multiple reasons for exits? | **Yes** — we already do it in the **label**; moving the **decision** to a combined score would align trigger with attribution. |
| Tracking all causes? | **Yes** — composite close_reason, exit_reason_code, attribution, and effectiveness reports by exit reason. |
| Using that to get better? | **Partially** — we have the pipeline and reports; next step is to run them routinely and use results to tune (and optionally to drive exits via a combined score). |

Running effectiveness reports and reviewing exit effectiveness + entry/exit blame is the fastest way to start “getting better” from the exit causes we already track.
