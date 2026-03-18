# Alpaca telemetry — supervisor retention fix (SRE)

**Date:** 2026-03-18  
**Issue:** On droplet restart, `startup_cleanup()` in `deploy_supervisor.py` truncated large `logs/*.jsonl` files including **`exit_attribution.jsonl`**, destroying forensic continuity and violating retention intent.

**Root cause:** Protection relied only on full relative path `filepath.as_posix() in RETENTION_PROTECTED`; any path variant or deployment cwd mismatch could skip protection. Alpaca telemetry logs were not listed.

**Fix (repo):**

1. **`RETENTION_PROTECTED`** extended with:
   - `logs/alpaca_entry_attribution.jsonl`
   - `logs/alpaca_unified_events.jsonl`
   - `logs/alpaca_exit_attribution.jsonl`
2. **`RETENTION_PROTECTED_BASENAMES`** — skip truncation/rotation if **`filepath.name`** matches any protected basename (fail-safe).

**Deploy:** After `git pull` / reset on droplet, next **`systemctl restart stock-bot`** will load the fixed supervisor; **do not** rely on pre-truncation history for pre-epoch proof.

**Related:** `scripts/alpaca_telemetry_forward_proof.py` now always writes **`ALPACA_TELEMETRY_FORWARD_PROOF_RESULT.md`** with **PENDING** when post-epoch exit count &lt; `--min-trades`.
