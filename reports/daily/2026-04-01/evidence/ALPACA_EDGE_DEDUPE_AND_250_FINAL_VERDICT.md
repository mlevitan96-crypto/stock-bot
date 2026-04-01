# Final verdict — edge dedupe + 250 + Telegram (evidence-only)

**Evidence root:** `reports/daily/2026-04-01/evidence/`  
**Droplet HEAD:** `0d9ec04088ec28cb15d2995df1fcba7b5736f3a7`  
**ET date:** 2026-04-01  

| Question | YES / NO | Evidence |
|----------|----------|----------|
| **SRE-EDGE-001 fixed and verified?** | **YES** | `check_strict_cohort_dedup.py` **EXIT 0**; `cohort_len == unique_len == 399`; gate reports `exit_attribution_duplicate_trade_id_rows_removed: 1` → `ALPACA_SRE_EDGE_001_VERIFY.md` |
| **Session armed for current ET anchor (`arm_epoch_utc` present)?** | **NO** | `state/alpaca_milestone_integrity_arm.json` has `arm_epoch_utc: null` for `session_anchor_et: 2026-04-01` → `ALPACA_INTEGRITY_ARM_STATE_PROOF.md` |
| **250 milestone eligible right now?** | **NO** | `unique_closed_trades: 0` under `integrity_armed` because arm epoch unset; `should_fire_milestone_250: false` → `ALPACA_250_MILESTONE_ELIGIBILITY_PROOF.md` |
| **If not eligible, exact reason?** | — | **Armed missing:** `arm_epoch_utc` not set (not “already fired” — `fired_milestone` is false). |
| **Telegram prod restricted to integrity only?** | **NO** | `alpaca-postclose-deepdive.timer` **enabled/active**; service runs `alpaca_postclose_deepdive.py` which calls `send_governance_telegram` → `ALPACA_TELEGRAM_PROD_ENABLEMENT_PROOF.md` |

## Supporting artifacts

- `ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_20260401_191124Z.json` (gate export)
- `ALPACA_EDGE_DEDUPE_AND_250_CONTEXT.md` (Phase 0)
- `../2026-04-02/evidence/ALPACA_SRE_EDGE_001_FIX.md` (code change description)
