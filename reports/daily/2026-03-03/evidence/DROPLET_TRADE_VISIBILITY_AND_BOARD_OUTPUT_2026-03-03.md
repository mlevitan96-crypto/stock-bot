# Droplet: Trade Visibility Data + Board Personas Output

**Run:** 2026-03-03 (trade visibility 48h window + board persona review on droplet).  
**Artifacts:** `reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md`, `reports/governance/board_review_latest.md`.

---

## 1. Data summary (last 48h on droplet)

| Metric | Value |
|--------|-------|
| **Trades closed** | 880 |
| Wins | 352 |
| Losses | 495 |
| **Win rate** | 40.0% |
| **Total P&L (USD)** | -$132.81 |
| **Sizing (qty)** | Avg 9.6, min 1, max 150 |

- **Entries/exits:** Exits dominated by `signal_decay` (various decay ratios) and some `stale_alpha_cutoff`, `flow_reversal`, `trail_stop`. See full breakdown in `reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md`.
- **By symbol:** INTC, COIN, MRNA, LCID, AMD, SLB, RIVN, NVDA, UNH, HOOD among top counts (see report for full list).

### 100-trade baseline (direction replay)

- **Exit attribution records (total):** 2,000  
- **Telemetry-backed** (have `direction_intel_embed.intel_snapshot_entry`): **0**  
- **Progress to 100:** 0/100 — direction replay not ready until telemetry-backed count >= 100 and >= 90% of exit_attribution are telemetry-backed.  
- **Action:** Ensure entry/exit telemetry writes `direction_intel_embed` (intel snapshot at entry) into exit_attribution so the 100-trade baseline can be reached and direction replay can run.

---

## 2. Board personas: changes we should be making

From `reports/governance/board_review_latest.md` (Adversarial, Quant, Product/Operator, Execution/SRE, Risk + Board verdict):

### Current governance snapshot (droplet)

- **Decision:** LOCK; **stopping_condition_met:** False.  
- **Baseline:** joined=2320, expectancy=-0.087621, win_rate=38.32%; giveback=None.  
- **Recommendation:** next_lever=entry, suggested_min_exec_score=2.9.  
- **Expectancy-gate diagnostic:** p50 entry_score / pct_marginal not yet populated — ensure expectancy_gate_diagnostic runs each cycle.

### Agreed top 3 and next (board + personas)

1. **Add down-weight worst signal as entry-lever option**  
   From signal_effectiveness/top5_harmful, pick the single worst signal; when lever=entry, allow overlay that down-weights it (e.g. -0.05). One cycle at a time; 100-trade gate. Supported: Strategic Phase B1, Quant, Product; Adversarial/SRE/Risk agree.

2. **Keep loop running; monitor with diagnostic and board review**  
   No structural change. Use expectancy_gate_diagnostic and board_review_latest to monitor. Supported: all personas.

3. **Ensure giveback populated when possible; use risk brake when needed**  
   (a) Verify giveback in effectiveness_aggregates when exit data has it; fix if still null. (b) When drawdown unacceptable, apply brake (MIN_EXEC_SCORE 3.0 or pause) and document. Supported: Quant, Execution/SRE, Risk.

**Next:** (1) Implement down-weight-worst-signal as entry option. (2) Continue loop; verify giveback on droplet. (3) Apply brake only when drawdown is unacceptable.

### Persona verdicts (short)

- **Adversarial:** Diagnostic not yet populated; ensure expectancy_gate_diagnostic runs each cycle.  
- **Quant:** Evidence pipeline in place; optional WTD effectiveness comparison and down-weight-worst-signal.  
- **Product/Operator:** Process aligned; one baseline, one lever, 100-trade gate. No process change required.  
- **Execution/SRE:** Diagnostic is live; fix if dashboard or gate logic diverges from attribution scores.  
- **Risk:** Brake optional; apply only if drawdown unacceptable and document.

---

## 3. How to re-run

```bash
# From repo root (pushes and deploys first if needed, then runs on droplet and fetches)
python scripts/run_trade_visibility_and_board_review_on_droplet.py
```

This runs `scripts/trade_visibility_review.py` (48h) and `scripts/governance/run_board_persona_review.py` on the droplet and fetches the reports into `reports/audit/` and `reports/governance/`.
