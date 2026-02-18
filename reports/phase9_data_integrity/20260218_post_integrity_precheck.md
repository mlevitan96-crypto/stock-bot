# Post-integrity: blame classifiable + exit quality proof — precheck (2026-02-18)

## Multi-model review

| Lens | Note |
|------|------|
| **Adversarial** | Proving exit_quality on "new" exits requires a time boundary (last N lines after deploy). If no exits have occurred since deploy, we get 0 and must diagnose—not declare done. Making blame classifiable by adding entry_score can default to 0 and wrongly classify weak_entry; we should log the actual score when available, and only default when missing. |
| **Quant** | Blame rules: weak_entry = entry_score in (0, 3), exit_timing = giveback ≥ 0.3 or MFE > 0 with loss. Joined rows need entry_score from attribution context and giveback from exit_attribution. If attribution already has context.entry_score at the one call site (9459 → 9525), the join may still fail (key mismatch); we verify on droplet and ensure key is never omitted. |
| **Product** | Exit quality proof = non-zero with_exit_quality_metrics in newest lines. Blame fix = logging only; no trading logic change. Baseline v4 is the next authoritative run; next lever proposal is stub only. |

## Scope

1. **Prove exit_quality_metrics** on new exits (sample newest 500, count with exit_quality_metrics; if 0, diagnose).
2. **Blame classifiable:** Ensure entry_score is present in attribution (context.entry_score); add defensive default in log_attribution if missing so the key exists.
3. **Droplet:** Pull, re-run baseline v4, verify blame and exit_quality coverage.
4. **Next lever:** Multi-model choose one lever (entry or exit); write proposal stub only.
