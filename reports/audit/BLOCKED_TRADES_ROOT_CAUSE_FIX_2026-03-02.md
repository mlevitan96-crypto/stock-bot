# Blocked Trades Root Cause Fix (2026-03-02)

## Why trades were blocked (no workaround)

1. **Score killed to 0.172 at expectancy gate**  
   `apply_uw_to_score()` was **rejecting** any candidate whose UW root-cause data had `uw_signal_quality_score` below 0.25 (e.g. 0.172). It returned `-inf` (or a heavily penalized score), so the composite-approved score (2.7–4.x) was replaced before the expectancy gate and every candidate failed `score_floor_breach`.

2. **Passthrough was env-dependent**  
   Passthrough only ran when `UW_MISSING_INPUT_MODE=passthrough` was in the process environment. If `.env` wasn’t loaded in the right order or the service didn’t see it, the mode stayed `reject` and the score was still killed.

3. **UW daemon not running**  
   If `uw-flow-daemon.service` wasn’t installed or enabled on the droplet, the cache didn’t update and signals stayed stale. Deploy now copies the unit, enables it, and restarts it.

## Fixes applied (root cause, not workaround)

### 1. `board/eod/live_entry_adjustments.py` — never kill strong composite scores

- **When** UW data exists but `use_quality < 0.25` (e.g. 0.172), we used to always reject and return `-inf`.
- **Now:** Before rejecting, we check **`composite_score >= _get_min_exec_score()`** (e.g. 2.5).  
  - If true: **return `(composite_score, details)`** with `uw_low_quality_preserved_strong_composite` so the expectancy gate sees the real composite score and orders can be placed.  
  - If false: keep existing reject behavior.
- So composite-approved clusters (already above the execution floor) are **never** down-scored or rejected by UW low quality. No env var required.

### 2. Passthrough uses env at call time

- `UW_MISSING_INPUT_MODE` is now read **inside `apply_uw_to_score()`** with `os.environ.get("UW_MISSING_INPUT_MODE", "reject")` so the current environment (e.g. after `load_dotenv()`) is always used, regardless of import order.

### 3. Deploy ensures UW daemon is running

- **`droplet_client.py` `deploy()`:**  
  - Copies `deploy/systemd/uw-flow-daemon.service` to `/etc/systemd/system/` if present.  
  - Runs `systemctl daemon-reload`, `enable`, `start`, `restart`, and checks `is-active`.  
- So after each deploy, the UW daemon is installed (if the unit file is in the repo), enabled, and restarted.

### 4. Script to inspect blocked trades

- **`scripts/fetch_recent_blocked_trades_from_droplet.py`**  
  - Fetches the last N lines of `state/blocked_trades.jsonl` from the droplet.  
  - Prints symbol, reason, score, composite_pre_norm, composite_post_norm.  
  - Prints `uw-flow-daemon.service` status.  
- Usage: `python scripts/fetch_recent_blocked_trades_from_droplet.py [N]` (default N=20).

## What you should see after deploy

- **blocked_trades:** New entries should **not** all be `score_floor_breach` with `score=0.172`. Scores at the expectancy gate should be composite scores (2.7–4.x) when the cluster was composite-approved.
- **run.jsonl:** `orders` can be ≥ 1 when symbols pass composite and expectancy gates.
- **UW daemon:** `systemctl is-active uw-flow-daemon.service` → `active` after deploy.

## Verification

1. Deploy: push code, run deploy (e.g. via `DropletClient().deploy()`).
2. Fetch blocked trades: `python scripts/fetch_recent_blocked_trades_from_droplet.py 30`.
3. After a cycle or two: `tail -1 logs/run.jsonl` on droplet; confirm `orders` when conditions are met.
4. Check daemon: on droplet, `systemctl status uw-flow-daemon.service`.
