# Deploy plan review — multi-model oversight (2026-02-18)

## Plan

1. **Local:** Create branch `data-integrity/high-water-giveback`, rebase onto `origin/main`, push branch; then merge to main and push (or open PR).
2. **Droplet:** Stash local drift, `git pull origin main`, confirm fix present (grep high_water, exit_quality_high_water_unavailable, effectiveness script).
3. **Droplet:** Confirm paper run (no overlay), sample latest exit_attribution for exit_quality_metrics.
4. **Droplet:** Re-run baseline v3 effectiveness; verify aggregates + blame unclassified_pct + giveback.
5. **Re-sign:** Update sign-off to PASS only if criteria met.

## Multi-model review

| Lens | Risk / note |
|------|-------------|
| **Adversarial** | Rebase could conflict if origin touched same main.py regions (e.g. log_exit_attribution, displacement exit). If we force-push or overwrite history, others could be disrupted; we only push a new branch and merge, no force to main. Stashing on droplet avoids losing local changes but we must not pull with unstaged changes that could conflict. |
| **Quant** | Once deployed, new exits will get info["high_water"] from executor; giveback will be computable when high_water > entry. Existing log lines will not change; only new exits after deploy will have exit_quality_metrics. Baseline v3 re-run will still include old exits (no giveback) and new ones (giveback if any); so avg_profit_giveback may remain sparse until enough new exits accumulate. |
| **Product** | Unclassified_pct and effectiveness_aggregates.json make the report auditable; we do not change classification rules. Sign-off PASS requires unclassified_pct present and (giveback populated OR verified reason); we may PASS with "giveback sparse but exit_quality_metrics now present in new logs" if that is the verified state. |

## Risks accepted

- Rebase conflicts in main.py: resolve manually, keep both high_water injection and any origin changes.
- Giveback still N/A in aggregates if no new exits yet: document in verification; PASS only if we have confirmed exit_quality_metrics in new logs (non-zero coverage) and unclassified_pct present.
