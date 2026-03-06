# CSA Risk Acceptance — B2 Live Paper

**Date:** 2026-03-06  
**Reference:** CSA_TRADE_100_20260306-002808 (PROCEED)

## Summary of B2 change

- **Change:** Remove early signal_decay exits in live paper (B2_shadow promoted to LIVE PAPER).
- **Mechanism:** When B2 live paper is on, exits due to signal_decay with hold < 30 min are suppressed (no close); events logged to `logs/b2_suppressed_signal_decay.jsonl`. Exits are attributed with `variant_id: "B2_live_paper"`.
- **Scope:** LIVE PAPER only. No real capital; no change to non-B2 behavior.

## Risk notes

- **Bounded downside:** Paper only; rollback is one config/env flip + restart.
- **Rollback path:** `scripts/governance/rollback_b2_live_paper.py` (config); on droplet: `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false`, restart. See `reports/board/B2_LIVE_PAPER_PLAYBOOK_20260306.md`.
- **Monitoring:** Dashboard (Profitability & Learning, Learning & Readiness), exit_attribution.jsonl variant_id, b2_suppressed_signal_decay.jsonl volume.

## Sign-off

**Accepted for LIVE PAPER only.** No live capital until further governance approval.
