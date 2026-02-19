# Research Table — Multi-Model Design (Phase 3)

## MODEL A (Data Engineer)

**Dataset schema:**
- **Identifiers:** date, symbol
- **Canonical 22 components:** flow, dark_pool, insider, iv_skew, smile, whale, event, motif_bonus, toxicity_penalty, regime, congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score, freshness_factor (float)
- **group_sums:** uw, regime_macro, other_components (float)
- **Composite:** composite_pre_norm, composite_post_norm (float)
- **Context:** block_reason (str), score_bucket (str)
- **Macro/regime (with horizons):** spy_1w_ret, spy_2w_ret, spy_1m_ret, spy_ma_distance_proxy, spy_ma_slope_proxy, vol_regime_proxy (e.g. VIX or SPY realized vol percentile), breadth_pct_above_50dma (float or null)
- **Labels:** forward_return_1d, forward_return_3d, forward_return_5d, forward_return_10d, forward_return_20d, mfe_proxy, mae_proxy (float; daily proxy if intraday unavailable)

**Storage:** Parquet, partitioned by date (e.g. year=YYYY/month=MM or date=YYYY-MM-DD).

**Performance / resumability:** Append by date partition; skip existing partitions if --resume; single process per run.

---

## MODEL B (Adversarial Auditor)

**Anti-leakage rules:**
- Features at time T must use only data available at or before T (e.g. composite at T, SPY returns up to T).
- Labels: forward_return_* must be computed from returns strictly after T (T+1 close to T+N close).
- No future snapshot or blocked_trade data in feature row for T.

**Survivorship:** Universe = symbols that appear in snapshot/blocked_trades; document "research table is blocked-candidate universe, not full universe."

**Missingness:** Log missingness by column and by time bucket; flag columns with >X% missing.

**Schema drift:** Enforce canonical key names (e.g. dark_pool not darkpool); schema_parity.json must list expected vs actual.

---

## MODEL C (Quant Researcher)

**Labels:** forward_return_1d/3d/5d/10d/20d = buy-and-hold return from row date close (or next open) to N sessions later. Direction from row (bullish/bearish) applied: long return for bullish, -1 * return for bearish if desired for signed label.

**Regime features:** SPY 1W/2W/1M returns (prior to T); vol regime = VIX level or SPY realized vol percentile (prior window); breadth = % of universe above 50 DMA if computable.

**Eval protocol:** Time-split train/val/test (e.g. 60/20/20 by date); walk-forward optional; report OOS lift by signal decile.

---

## MODEL D (Synthesis Chair)

**Approved:** Schema as above; Parquet by date; anti-leakage enforced; missingness and schema parity audited in Phase 4. Build script uses whatever date range is available (snapshot + bars); document range and row count in build_log.md.
