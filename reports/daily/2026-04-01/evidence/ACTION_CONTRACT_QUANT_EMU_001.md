# ACTION_CONTRACT — QUANT_EMU_001

- **Type:** paper_extension
- **Owner:** QUANT
- **Change:** Keep `run_displacement_deepdive_addon.py` emulator grid in weekly audit bundle; compare p05 vs mean week-over-week.
- **Scope/duration:** 8 weeks; same k,m,N grid unless governance approves expansion.
- **Success metrics:** ['majority of grid cells remain mean_pnl_usd > 0', 'p05 does not worsen >25% vs baseline snapshot in DISPLACEMENT_EXIT_EMULATOR_RESULTS.json']
- **Kill criteria:** ['fewer than half of cells with mean_pnl_usd > 0 for two consecutive runs', 'best_cell mean_pnl_usd < 0']
- **Rollback:** Remove addon from cron; no trading config touched.
