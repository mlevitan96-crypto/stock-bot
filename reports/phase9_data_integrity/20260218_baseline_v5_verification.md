# Baseline v5 verification (2026-02-18)

**After droplet pull and run:**

```bash
cd /root/stock-bot
git pull origin main
python3 scripts/analysis/run_effectiveness_reports.py \
  --start 2026-02-01 --end $(date +%F) \
  --out-dir reports/effectiveness_baseline_blame_v5
```

## Verify

- [ ] `reports/effectiveness_baseline_blame_v5/entry_vs_exit_blame.json` exists and includes:
  - weak_entry_pct, exit_timing_pct, unclassified_pct
- [ ] unclassified_pct < 100% OR explicit "why still unclassified" with counts
- [ ] exit_quality_metrics coverage proof exists (Step 2) and giveback is either populated OR explicitly explainable

## Paste key excerpts

```json
// entry_vs_exit_blame.json (excerpt)
```

```text
// unclassified_pct and reason
```
