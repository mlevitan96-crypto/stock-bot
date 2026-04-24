# DISPLACEMENT_DEEPDIVE_FINAL_VERDICT

**Evidence date (ET):** 2026-04-01  
**Output directory:** `reports/daily/2026-04-01/evidence/`  
**Droplet path:** `/root/stock-bot/reports/daily/2026-04-01/evidence/`

---

## Can we separate GOOD vs BAD displacement blocks?

**YES (weak, explanatory).** Phase 11 concludes **A** in `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`: univariate splits on decision-time features yield positive impurity reduction; **generalization is not proven** (see `BOARD_QUANT_DISPLACEMENT_DEEPDIVE.md`).

## If YES — top 3 conditional rules (from ranked univariate rules, same file)

1. **`distance_to_min_exec_score` (dist_thr) ≤ 2.3856** → BAD rate **53.38%** vs **> 2.3856** → BAD rate **65.88%** (largest impurity reduction ~0.0065).  
   **Expected impact / risk:** Flags “far above min exec score” blocks as higher counterfactual-win rate at 60m; **risk** — threshold is sample-specific; time/symbol split accuracies do not validate a fixed cutoff.

2. **`hour_utc` ≤ 15** → BAD rate **51.21%** vs **> 15** → BAD rate **58.84%**.  
   **Expected impact / risk:** Late-session displacement blocks associate with higher BAD rate under the 60m label; **risk** — confounded with symbol/session mix.

3. **`score_snapshot_joined` false (0)** → BAD rate **57.99%** vs **true** → BAD rate **52.36%**.  
   **Expected impact / risk:** Missing snapshot join correlates with worse labeled outcome; **risk** — join failure may be MNAR (missing not at random).

## If NO — missing features / UW

**N/A** for this run: conclusion **A**; UW was **not** required. See `UW_CAPTURE_SKIPPED.md` and `DISPLACEMENT_SEPARATION_WITH_UW.json` (not run).

## Does opportunity persist under exit emulator?

**YES.** `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`: **`opportunity_persists_majority_positive_mean_cells`: true** — **11 / 18** grid cells have **`mean_pnl_usd` > 0**; **tail** remains severe (**p05** highly negative in all cells). See `BOARD_QUANT_DISPLACEMENT_DEEPDIVE.md`.

---

## Exactly ONE paper-only change (single lever)

**Lever:** Add a **paper-only displacement review checklist** triggered when **all** hold: `displacement_blocked` **and** `distance_to_min_exec_score > 2.3856` **and** `hour_utc > 15` **and** `score_snapshot_joined == false` — requiring human/board sign-off before any future **code** change to displacement priority (no auto-trading change).

- **Verify:** Manually sample 20 rows matching the filter from `DISPLACEMENT_OVERRIDE_MAP.json` and confirm filter logic matches stored fields; confirm no rows use post-decision data in the filter (CSA memo).  
- **Rollback:** Retire the checklist section from the runbook / remove the filter from reporting-only SQL or doc — **zero** runtime behavior to revert.

---

**Cross-checks:** CSA/SRE/Quant memos: `BOARD_CSA_DISPLACEMENT_DEEPDIVE.md`, `BOARD_SRE_DISPLACEMENT_DEEPDIVE.md`, `BOARD_QUANT_DISPLACEMENT_DEEPDIVE.md`.
