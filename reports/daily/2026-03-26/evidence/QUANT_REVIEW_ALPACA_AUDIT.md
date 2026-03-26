# Quant Officer Review — Alpaca Data Readiness & Audit

**UTC:** 2026-03-20  
**Inputs:** `ALPACA_TRADE_SUFFICIENCY_VERDICT.md`, `ALPACA_DATA_INTEGRITY_RESULTS.md`, `ALPACA_FULL_PNL_ATTRIBUTION_AUDIT.md`

---

## Analytical validity

1. **Sample size:** **2,204** unique closed trades on **`exit_attribution.jsonl`** — **adequate** for aggregate PnL, win/loss, and coarse exit-reason attribution.  
2. **Defective rows:** **2** rows with missing core fields — **exclude** from precision metrics until repaired.  
3. **Cross-log joins:** Low master↔exit overlap **does not** invalidate per-row PnL in exit file; it **invalidates** naive multi-ledger reconciliation without ID harmonization.  
4. **Win rate ~40%** with **loss count &gt; win count** on window — analytics should stress **tail risk** and **expectancy**, not headline win rate alone.  
5. **“Would-have” / bar replay:** Not run — **insufficient** to claim bar-path counterfactuals in this packet; schedule replay pipeline when permitted.

---

## Sign-off

**Analytical validity for scoped exit-file PnL audit:** **ACCEPT** with **2-row quarantine** caveat.  
**Full Kraken parity** (multi-ledger + bar replay): **PARTIAL** — pending reconciliation + replay runs.

---

*Quant Officer*
