# Alpaca — CSA learning-ready closeout

**TS:** `20260326_2315Z`

## Verdict

### **STILL_BLOCKED**

## Consolidated blockers

| # | Blocker | Example / detail | Recoverable? |
|---|---------|------------------|--------------|
| 1 | Strict learning cohort **empty or not proven complete** on captured baselines | `reports/ALPACA_BASELINE_20260326_2315Z.json`: `trades_seen=0`, `LEARNING_STATUS=BLOCKED` | Yes — use droplet logs with post-era opens + rerun gate |
| 2 | Replay lab did not show **non-empty** complete cohort | `reports/ALPACA_REPLAY_LAB_GATE_20260326_2315Z.json`: `trades_seen=0` (era filter) | Yes — supply replay slice with opens ≥ floor |
| 3 | Live-forward **non-vacuous** proof **not captured** this session | `reports/audit/ALPACA_FORWARD_POLL_PROOF_20260326_2315Z.md` | Yes — run `alpaca_forward_poll_droplet.py` |
| 4 | Prior **legacy** incompletes may remain | Quarantined per contract; not forward-certified | Partial — additive backfill only with CSA mission |

## Positive evidence (not sufficient for final)

- Strict gate + forward audit scripts exist and run deterministically.
- Dashboard surfaces BLOCKED / errors without claiming certification.

## Binary label

**STILL_BLOCKED**
