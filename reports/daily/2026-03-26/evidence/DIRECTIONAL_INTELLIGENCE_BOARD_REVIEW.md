# Directional Intelligence — Board Persona Review

**Context:** New directional intelligence has been added as **telemetry only** (pre-market, post-market, overnight, futures, volatility, breadth, sector, ETF flow, macro, UW). It is captured at entry and exit, stored in intel_snapshot_*.jsonl and direction_event.jsonl, and embedded in exit_attribution and exit_event. No live behavior changes.

**Task:** Each persona critiques data quality, signal redundancy, overfitting risk, operational risk, and strategic value for long vs short decisions. Then: which signals add value, which are redundant/noisy, which should dominate on crash days, which should suppress longs or favor shorts, and what failure modes remain.

---

## Equity Skeptic

**Data quality:** Pre-market and overnight currently use SPY/QQQ proxies (market_context_v2); breadth, sector ETF flow, and true futures (ES/NQ/RTY/VX) are stubs. So a large portion of the new “intelligence” is either duplicate of existing market_context or placeholder. Data quality is **mixed** until real breadth/futures/ETF flow feeds are wired.

**Signal redundancy:** Futures direction and overnight direction overlap heavily with existing market_trend and spy/qqq overnight returns already used in composite and regime. Adding them again as “direction components” is redundant unless we use them only in replay to **condition** direction (e.g. “allow short only when futures_direction == down”).

**Overfitting risk:** If we later let these components drive live direction, we risk overfitting to a short history. Replay should test regime-conditioned and futures/breadth-conditioned direction **out of sample** before any live use.

**Operational risk:** Low; telemetry-only. State file `position_intel_snapshots.json` could grow; recommend periodic prune by entry_ts age.

**Strategic value for long vs short:** High **potential**. On crash days, futures_direction and volatility_direction (and eventually breadth) should be the ones that **dominate** or at least **suppress longs** and **favor shorts**. Today they are not used in live logic; replay can quantify how much PnL improvement we’d get by conditioning direction on these.

**Which add value:** Overnight/futures (already proxied), volatility regime, and—once real data exists—breadth and sector rotation.  
**Which are redundant/noisy:** Post-market and some macro stubs until we have real post-market and macro event feeds.  
**Crash days:** Volatility + futures (down) + breadth (down) should dominate; longs suppressed, shorts favored.  
**Failure modes:** Stale or missing market_context makes premarket/overnight/futures components wrong; stub breadth/sector/ETF stay neutral and add no signal.

---

## Risk Officer

**Data quality:** Same as Skeptic: partial real data (market_context, regime), many stubs. For risk we care that **vol_regime** and **macro_risk_flag** are reliable; currently vol_regime comes from market_context (VXX/VXZ proxy), macro from MacroGate (FRED). Quality is acceptable for observability; not yet for sizing or hard gates.

**Signal redundancy:** Redundancy with existing regime and market_trend is acceptable **if** the canonical list is the single place replay and future logic look for “direction inputs.” Then we avoid multiple ad-hoc sources.

**Overfitting risk:** Replay experiments that weight or gate on these components must use train/validation split and avoid tuning on the same period used for reporting.

**Operational risk:** Append-only logs and one state file; low. Ensure log rotation or size caps for intel_snapshot_*.jsonl and direction_event.jsonl on long-running production.

**Strategic value for long vs short:** Direction components give a **clear audit trail**: why a trade was long or short in replay. For risk, the most valuable is **volatility_direction** and **macro_direction**: in high vol or macro_risk, we may want to suppress new longs or favor shorts. Today we do not act on them; replay should test.

**Which add value:** Volatility regime, macro (when available), overnight/futures proxy.  
**Which are redundant/noisy:** Duplicate of existing market_trend if used naively; post-market/ETF stubs until wired.  
**Crash days:** Vol and macro should dominate; suppress longs, favor shorts when vol_regime == high and macro_risk_flag true.  
**Failure modes:** FRED/macro unavailable → macro_direction neutral. Market context stale → premarket/overnight/futures wrong.

---

## Innovation Officer

**Data quality:** Good enough for **experimentation**. We can run replay with “direction = f(futures_direction, breadth_direction, vol_regime)” and measure hit rate and PnL without needing production-grade breadth/futures yet; stubs can be replaced incrementally.

**Signal redundancy:** Redundancy is acceptable for experimentation as long as we **name** the canonical set and treat it as the single interface for “directional intelligence.” New feeds (real breadth, real ES/NQ) can be added as new components or replacements for stubs.

**Overfitting risk:** High if we tune on same data we report on. Recommendation: **fixed train window**, **rolling validation**, and **kill criteria** (e.g. “if regime-conditioned direction does not improve Sharpe in 2 weeks of backtest, do not promote to live”).

**Operational risk:** Low; telemetry-only.

**Strategic value for long vs short:** High. Experiments to run: (1) long-only when futures_direction == up and vol_regime != high; (2) short-only when futures_direction == down and breadth_direction == down; (3) mixed with weights from contribution_to_direction_score. Measure PnL and win rate by regime.

**Which add value:** Futures (proxy), vol regime, overnight; later breadth and sector when real.  
**Which are redundant/noisy:** Stub breadth/sector/ETF until we have data.  
**Crash days:** Vol + futures + breadth should dominate; favor shorts, suppress longs.  
**Failure modes:** Stubs always neutral → no improvement until real data. Overfitting if we tune on test set.

---

## Customer Advocate

**Data quality:** From a “why did we go long on a down day?” perspective, the new telemetry gives a **trace**: we can see premarket_direction, futures_direction, volatility_direction at entry. That improves accountability. Quality is sufficient for explanation; not yet for changing behavior.

**Signal redundancy:** Some redundancy with existing regime/market_trend is acceptable if it simplifies **one** place to look for “what did we know at entry/exit.”

**Overfitting risk:** Not applicable to telemetry-only; becomes relevant only if we change live logic using these components.

**Operational risk:** Low. Customer-facing impact: none until we use this for decisions; then we must explain that “direction is also conditioned on futures/breadth/vol” in plain language.

**Strategic value for long vs short:** High for **transparency**. If we later add “suppress longs when vol_regime == high” or “favor shorts when breadth_direction == down,” we can point to these components in reports. Today the main win is **replay and audit**: “at entry, futures_direction was up, vol was mid, so the model had no reason to short.”

**Which add value:** All for audit/explanation; for actual PnL, futures/vol/overnight (and later breadth) matter most.  
**Which are redundant/noisy:** Duplicate narrative of market_trend until we use components explicitly for conditioning.  
**Crash days:** Vol and futures (down) should dominate; we should suppress longs and favor shorts; if we don’t, customer will ask “why were we long?” — the components document the decision basis.  
**Failure modes:** If data is wrong or stale, our explanation is wrong; need to validate sources before using for live logic.

---

## SRE

**Data quality:** Fetchers are defensive (never raise); missing data yields defaults. So from an SRE perspective, **availability** of the pipeline is good. Correctness of stub values (e.g. breadth always 1.0) is a product/data question.

**Signal redundancy:** Redundant signals do not add operational load beyond disk and one state file; acceptable.

**Overfitting risk:** N/A to SRE.

**Operational risk:** **Low.** New logs: intel_snapshot_entry.jsonl, intel_snapshot_exit.jsonl, direction_event.jsonl. State: position_intel_snapshots.json. Recommend: (1) log rotation or max size for the three jsonl files; (2) prune position_intel_snapshots.json by entry_ts (e.g. drop entries older than 30 days) to avoid unbounded growth. Capture is in the hot path (entry/exit) but is try/except wrapped and non-blocking.

**Strategic value for long vs short:** SRE does not prioritize strategy; from a **reliability** standpoint, the design is additive and fail-safe. If direction_intel capture fails, trading continues unchanged.

**Which add value / redundant / crash days:** Defer to other personas.  
**Failure modes:** Disk full (same as any log); state file corruption (rare); import errors if structural_intelligence or config.registry change — mitigate with try/except and defaults.

---

## Summary Table (Board Synthesis)

| Question | Consensus |
|----------|-----------|
| **Which intelligence signals add real value?** | Overnight/futures (proxy), volatility regime, macro (when available). Once real data: breadth, sector rotation, ETF flow. |
| **Which are redundant or noisy?** | Duplicate of market_trend/regime if used naively; post-market and stub breadth/sector/ETF until wired. |
| **Which should dominate on crash days?** | Volatility_direction (high), futures_direction (down), breadth_direction (down). |
| **Which should suppress longs?** | High vol_regime, macro_risk_flag, futures_direction == down, breadth_direction == down. |
| **Which should favor shorts?** | Same as above: vol + futures down + breadth down. |
| **What failure modes remain?** | Stale/missing market_context; stub components always neutral; overfitting if replay tunes on test set; state file growth; log growth without rotation. |

---

**Next steps (recommendations):**

1. **Replay:** Run backtests conditioning direction on futures_direction, vol_regime, and (when available) breadth; measure PnL and win rate by regime. No live change until evidence supports it.
2. **Data:** Wire real breadth (adv/dec, up/down volume) and optional real futures (ES/NQ) where available; replace stubs incrementally.
3. **Ops:** Add log rotation or size cap for intel_snapshot_*.jsonl and direction_event.jsonl; prune position_intel_snapshots.json by age.
4. **Governance:** Keep this intelligence **telemetry-only** until board approves a specific rule (e.g. “suppress new longs when vol_regime == high and futures_direction == down”) with backtest evidence.
