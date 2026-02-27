# Signal contribution nuclear audit — Results review (multi-model AFTER)

**Date:** 2026-02-18  
**Artifacts:** reports/signal_audit/20260218/ (00_summary.md … 08_verdict.md)

---

## Audit outcome

- **Verdict:** FAIL  
- **Reason:** No sample data (sample_size 0). Composite distribution empty; diagnostic on droplet either could not load data/uw_flow_cache.json or returned no symbols (cache structure or path).
- **Dead or muted:** 0 (none identified; audit did not reach value/contribution analysis).

---

## Multi-model (after)

### Adversarial: How could scoring lie silently?

- With sample_size 0 we did not prove signals execute or contribute. **Remaining risk:** Signals could be dead/muted but we have no evidence either way. Re-run after ensuring diagnostic has access to live cache (same path as main.py) and cache has symbol entries.
- If cache is present but keys are not symbol strings, diagnostic would see symbols = []; fix by aligning cache key iteration with how main.py loads the cache.

### Quant: Are distributions sane?

- No distribution was computed. Once sample_size > 0, re-check: composite min/max/mean, % below 2 and below 3, and per-signal value audit (min/max/mean, % zero) for sanity.

### Product: Are outputs interpretable?

- Report bundle (00–08) is in place. Verdict and summary clearly state FAIL and “no sample data.” Next run should populate 01–07 so product can see which signals (if any) are dead or muted.

---

## Top 3 corrective actions (if FAIL)

1. **Ensure diagnostic runs with valid cache on droplet:** Confirm data/uw_flow_cache.json exists on droplet and is non-empty; run `python3 scripts/signal_audit_diagnostic.py` from repo root so path resolution is correct. If the script was not on the droplet (not yet pushed), push scripts/signal_audit_diagnostic.py and scripts/run_signal_contribution_audit_on_droplet.py and re-run.
2. **Align cache key handling with main:** If cache format uses nested or different keys, adapt the diagnostic’s symbol list (e.g. use same loader as telemetry.get_uw_flow_cache() or load from same path and key structure).
3. **Re-run audit after fix:** Run `python scripts/run_signal_contribution_audit_on_droplet.py` again; confirm sample_size > 0 and review 03–07 for dead/muted signals and distribution.

---

## Verdict

- Flow restored: **N/A** (no data).
- Distribution sane: **N/A**.
- Threshold tuning: **Not done** (audit only).
