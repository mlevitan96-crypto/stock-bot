# Alpaca strict era policy (CSA) — STOP-GATE 0

**TS:** `20260327_0200Z`

## Selected policy: **POLICY C (explicit operator)**

Every certification and strict gate invocation MUST pass an explicit `open_ts_epoch` / `--strict-epoch-start` (UTC). **No hidden defaults** for certification runs.

## Operational mappings (documented, not silent)

| Mode | How `strict_epoch_start` is chosen | Label |
|------|-------------------------------------|--------|
| **Live forward (deploy-anchored)** | `DEPLOY_TS_UTC_EPOCH` from `/tmp/alpaca_deploy_ts_utc.txt` after deploy, or `--deploy-epoch` | Live-forward cohort |
| **Rolling replay** | `now_utc - slice_hours * 3600` via `--slice-hours` | `CODE_COMPLETE_REPLAY` |
| **Replay auto-era** | `min(open_epoch)` among last 50 exits with `exit_ts` in `[now - slice_hours, now]` via `--replay-era-auto` | `CODE_COMPLETE_CERTIFIED_REPLAY_ERA_NOT_LIVE_FORWARD` |

POLICY A/B behaviors are **expressed only** through explicit flags above (deploy file = anchoring; slice hours = rolling).

## Dashboard note

`dashboard.py` may still evaluate with module constant `STRICT_EPOCH_START` for **visibility**; certification artifacts in this mission use **explicit** epochs from the replay bundle / CLI.

---

*Approved for this closure run.*
