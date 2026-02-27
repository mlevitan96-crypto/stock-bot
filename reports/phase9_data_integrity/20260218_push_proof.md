# Push proof (2026-02-18)

## Final commit hash(es)

- **Branch (pushed):** `data-integrity/high-water-giveback` → commit **9b6c638** — "Fix: ensure exit_quality_metrics emitted for giveback computation"
- **main (pushed):** Fast-forward merge of branch into main; **origin/main** = **9b6c638**

## Method

- Created branch `data-integrity/high-water-giveback` from local main, rebased onto `origin/main`, pushed branch.
- Checked out main, `git reset --hard origin/main`, `git merge --ff-only data-integrity/high-water-giveback`, `git push origin main`.
- **Direct push to main** (no PR); workflow allowed fast-forward.

## Confirmation that origin/main contains the fix

- **main.py:** Both call sites set `info["high_water"] = self.high_water.get(symbol, ...)` before `log_exit_attribution`; guard `log_event("data_integrity", "exit_quality_high_water_unavailable", ...)` when high_water unavailable.
- **scripts/analysis:** Added in follow-up commit **515bcf1** (run_effectiveness_reports.py, attribution_loader.py); writes `unclassified_count` / `unclassified_pct` in blame and `effectiveness_aggregates.json`. Droplet pulled and re-ran baseline v3 successfully after this push.
