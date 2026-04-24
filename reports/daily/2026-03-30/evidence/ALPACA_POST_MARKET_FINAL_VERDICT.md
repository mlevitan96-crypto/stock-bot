# ALPACA POST-MARKET FINAL VERDICT (CSA + SRE)

- UTC: `2026-03-30T20:30:09Z`
- ET report folder: `2026-03-30`

## Per-phase verdict

- **Phase 0 — Context & safety:** PASS — see dedicated artifact in this folder
- **Phase 1 — Engine SRE:** FAIL — see dedicated artifact in this folder
- **Phase 2 — Exit integrity:** PASS — see dedicated artifact in this folder
- **Phase 3 — Metadata truth:** FAIL — see dedicated artifact in this folder
- **Phase 4 — Liquidation safety:** PASS — see dedicated artifact in this folder
- **Phase 5 — Exit tuning governance:** FAIL — see dedicated artifact in this folder
- **Phase 6 — Dashboard truth:** FAIL — see dedicated artifact in this folder

## Overall

**FAIL**

## Blockers (if FAIL)

- Phase 1: abnormal run cadence, or risk_freeze set on latest complete cycles, or insufficient run.jsonl signal.
- Phase 3: hollow/missing metadata fields on open positions (see METADATA artifact).
- Phase 5: governance files missing, or git shows exit-related commits today, or changelog absent.
- Phase 6: dashboard unreachable, API error, P&L mismatch vs broker, missing current_score, or `metadata_gap_flags` non-empty (legacy / incomplete row).

## Proven vs assumed

- **Proven:** Droplet command output, Alpaca REST clock/positions, local log tails, systemd/journal excerpts, dry-run liquidation JSON, dashboard JSON when reachable.
- **Assumed:** US holiday / early-close nuances not fully modeled by `get_clock()` beyond Alpaca’s own calendar; journal `--since today` uses machine timezone.
