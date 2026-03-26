# Cursor Proposal Review: Unusual Whales MCP Integration

**Document type:** Board / CSA / SRE review only — NOT implementation  
**Reviewed against:** MEMORY_BANK.md, ARCHITECTURE_CONTRACTS_CURRENT.md, uw_flow_daemon.py, entry_intelligence_parity_audit.py, API_ENDPOINT_ANALYSIS.md  
**Date:** 2026-03-16

---

## 1. Accuracy check: current UW usage vs proposal claims

### 1.1 Proposal claim: “REST ingestion is complete and correct”

**Verdict: Substantially accurate, with minor corrections.**

| Proposal list | Actual usage (codebase) |
|--------------|-------------------------|
| Options flow (full tape) | ✅ `uw_flow_daemon` → `/api/option-trades/flow-alerts` per ticker; normalized → `data/uw_flow_cache.json` |
| Dark pool prints | ✅ `get_dark_pool_levels` → `/api/darkpool/{ticker}`; stored as `dark_pool` in cache |
| Greek exposure | ✅ Both `/api/stock/{ticker}/greeks` and `/api/stock/{ticker}/greek-exposure` polled; merged into `greeks` |
| IV rank / IV surfaces | ✅ IV rank: `/api/stock/{ticker}/iv-rank` in daemon. IV skew/smile are **computed** in `uw_enrichment_v2` from cache (not separate UW “IV surfaces” endpoint) |
| ETF tide / sector tide | ✅ Market tide: daemon polls `/api/market/market-tide`. Sector tide: `signals/uw_macro.py` uses `/api/market/sector-tide` (and `sector_tide_tracker.py` + `state/sector_tide_state.json`). ETF flow: `/api/etfs/{ticker}/in-outflow` in daemon |
| Market tide | ✅ Daemon polls `get_market_tide()` → stored globally and per-ticker in cache |
| OI change, max pain, FTDs, short data | ✅ Daemon: `oi_change`, `max_pain`, `shorts_ftds` (FTDs) per ticker; short data also in `signals/uw_macro.py` |
| Earnings, fundamentals, insider, congress | ✅ Insider: daemon `/api/insider/{ticker}`. Calendar (earnings/events): `/api/calendar/{ticker}`. Congress: **market-wide** `/api/congress/recent-trades`, then summarized per ticker (no per-ticker congress endpoint; API_ENDPOINT_ANALYSIS notes per-ticker congress 404) |
| Historical + real-time signals | ✅ Cache is the single source; main.py + dashboard read cache. Real-time = daemon poll cadence (e.g. option_flow 150s, market_tide 600s) |

**Corrections to keep in mind:**

- Congress and institutional are **not** per-ticker REST endpoints in practice: congress is `recent-trades` (global) then distributed; institutional is `/api/institution/{ticker}/ownership`.
- IV “surfaces” in scoring are enrichment-derived (iv_skew, smile_slope), not a separate UW REST category.
- MEMORY_BANK §7.8 specifies a **central UW client** (`src/uw/uw_client.py`), endpoint validation against OpenAPI spec, and `state/uw_cache/` for v2 intelligence; the **daemon** is the canonical poller writing `data/uw_flow_cache.json`. So “REST ingestion” is split: daemon for trading cache, and (where implemented) `src/uw` for validated, rate-limited intel passes.

---

## 2. Answers to the 10 board questions

1. **Does MCP improve governance clarity?**  
   **Partially.** Governance today is driven by MEMORY_BANK, runbooks, CSA/SRE verdicts, and droplet state. MCP could give Cursor/agents direct, on-demand reads of UW-shaped data during board reviews, which might reduce “where do I get this?” friction. It does **not** by itself improve clarity of **who may change trading behavior**; that still requires strict boundaries (see safeguards).

2. **Does MCP reduce friction for CSA/SRE investigations?**  
   **Yes, if scoped to read-only.** “Show me dark pool clusters for NVDA today” or “IV term structure anomalies” are exactly the kind of ad hoc queries that today require either reading cache files or re-running scripts. An MCP tool that returns current (or cached) UW data in a consistent schema would reduce friction, provided it does not bypass the daemon/cache for the **trading** path.

3. **Does MCP help generate better experiments or signal candidates?**  
   **Possibly.** Hypothesis generation and shadow experiments today use cache + logs + scripts. MCP could expose the same data to Cursor in a structured way for “what if we weighted X more?” or “which symbols had unusual flow today?”. Benefit is incremental; the main lever remains deterministic scoring and backtest/replay, not MCP itself.

4. **Does MCP reduce or increase architectural complexity?**  
   **Increases it.** It adds: another integration surface, another auth/identity path, another failure mode (MCP server down, schema drift). MEMORY_BANK already constrains UW to a single daemon, central client, and cache. MCP would be a **parallel** path for **non-trading** use only.

5. **Should MCP be allowed to request data during board reviews?**  
   **Yes, with constraints.** Allowed only for **read-only, human/agent review**. Not allowed to feed any live trading or scoring path. Data should be clearly labeled as “for review” (e.g. snapshot or TTL-bound) so it cannot be mistaken for canonical ingestion.

6. **Should MCP be used for daily Telegram governance updates?**  
   **Optional, not required.** Telegram content is currently driven by scripts and droplet state. MCP could be one **source** for “current UW view” when drafting updates, but the same data is already available from cache/state. Use only if it clearly reduces operator work and does not add critical-path dependency.

7. **Should MCP be isolated to research-only mode?**  
   **Recommended.** Treat MCP as a research/governance/CSA-SRE tool only. No use in the deterministic trading engine, no use in backtest/replay scoring, no use in promotion gates. Isolation reduces risk of agentic drift and keeps the “single source of truth” (REST → daemon → cache → engine) intact.

8. **Does MCP introduce any risk of bypassing deterministic ingestion?**  
   **Yes, if misused.** Risk is **mitigated** by: (a) never allowing MCP to write to `data/uw_flow_cache.json` or to any path consumed by `main.py`/scoring; (b) never allowing MCP to trigger or replace daemon polls for trading; (c) documenting in MEMORY_BANK that trading reads **only** from daemon-populated cache. With those safeguards, the risk is low.

9. **Is the REST ingestion layer sufficient for all trading needs?**  
   **Yes.** MEMORY_BANK and ARCHITECTURE_CONTRACTS_CURRENT state that UW ingestion is `uw_flow_daemon.py` → cache; scoring and gates consume that cache. No trading need identified that requires a second, real-time UW path. MCP does not replace or extend the trading data layer.

10. **Should MCP be added to the shadow experiment environment?**  
    **Optional.** If shadow experiments remain in use and Cursor/agents need to query UW-shaped data for analysis, MCP could be added there with the same read-only, non-trading rules. Not required for current v2-only, paper-only setup described in MEMORY_BANK.

---

## 3. CSA adversarial critique

- **No new data:** MCP does not add data we don’t already have via REST + cache. Any “unified schema” benefit is about **agent ergonomics**, not information gain.
- **Governance creep:** If MCP is used for “governance-grade reporting” or Telegram, we must ensure it never becomes the **authoritative** source for “what the system did.” Authority stays in logs, state, and cache written by the daemon/engine.
- **Schema drift:** If Unusual Whales MCP server’s schema diverges from our cache shape, agents could draw wrong conclusions. Prefer MCP responses that are either clearly “for review” or aligned with our existing cache schema.
- **Rate limits and quota:** Our daemon already manages UW API quota and rate limits. MCP usage must not compete with the daemon (e.g. same API key, same daily cap). Either MCP uses a separate key/quota for non-trading use or we explicitly cap MCP-driven UW calls so daemon remains priority.

---

## 4. SRE reliability assessment

- **Single point of failure:** Adding an MCP server is another process to run, monitor, and secure. It should be **optional** for core trading: if MCP is down, trading and CSA/SRE investigations via cache/scripts must still work.
- **Observability:** Any MCP use of UW data should be logged (e.g. “MCP read request for symbol X”) so we can audit agent behavior and avoid confusion with daemon-originated traffic.
- **No critical path:** MCP must not be in the startup or health path of the trading engine or the UW daemon. Health checks (e.g. `state/uw_daemon_health_state.json`, dashboard) must not depend on MCP.
- **Boundary clarity:** Operational runbooks (e.g. FULL_DAY_TRADING_INTELLIGENCE_AUDIT_RUNBOOK, DROPLET_CSA_AND_COCKPIT) should state that UW data for **trading** comes only from the daemon and cache, and that MCP is for review/investigation only.

---

## 5. Board synthesis

- The proposal correctly separates **deterministic trading** (REST → daemon → cache → engine) from an **agentic intelligence layer** (MCP for governance, CSA/SRE, research). That separation is aligned with MEMORY_BANK and ARCHITECTURE_CONTRACTS_CURRENT.
- Benefits are real but modest: better agent ergonomics for ad hoc queries and board reviews, and possible use in experiment generation and Telegram drafting. They do not justify weakening the existing UW contracts (single daemon, single cache, no live trading from MCP).
- The main risk is **agentic drift**: MCP being used to influence trading or to bypass cache. That is mitigated by strict boundaries and documentation, not by blocking MCP entirely.

---

## 6. Verdict, rationale, safeguards, scope, risk, complexity, governance

### Verdict: **ADOPT WITH CONSTRAINTS**

- **Rationale:** MCP as a **read-only, non-trading** interface for governance, CSA/SRE, and research is consistent with current architecture and can reduce friction. It does not replace or extend the trading data layer. Adoption should be conditional on clear constraints and safeguards.

### Required safeguards

1. **Trading boundary (hard):**  
   - MCP **must not** write to `data/uw_flow_cache.json`, `state/uw_flow_daemon.lock`, or any path consumed by `main.py` or composite scoring for trading or backtest.  
   - MCP **must not** trigger or substitute for `uw_flow_daemon` polling.  
   - MEMORY_BANK (or a dedicated section) must state that **trading** reads UW data only from daemon-populated cache.

2. **Read-only and labeling:**  
   - MCP tools that return UW-derived data must be read-only and must not be used to drive orders, scoring, or gates.  
   - Responses should be labeled (e.g. “for review / not for trading”) where applicable.

3. **Quota and rate limits:**  
   - If MCP calls UW API, use a separate key or a strictly capped quota so daemon polling remains priority and is not starved.

4. **Operational isolation:**  
   - MCP server must not be in the critical path of trading engine or daemon startup/health.  
   - Runbooks must document that UW data for trading comes only from daemon/cache.

5. **Observability:**  
   - Log MCP-initiated UW data requests (e.g. symbol, purpose) for audit and to avoid confusion with daemon traffic.

### Recommended integration scope

- **In scope:** Governance and board review packets; CSA/SRE investigations (e.g. “dark pool clusters for NVDA today”, “IV anomalies”); research and experiment generation; optional use when drafting daily Telegram governance updates.
- **Out of scope:** Any use in the deterministic trading engine; composite scoring; backtest/replay; promotion gates; writing or mutating cache/state used by the engine.

### Risk assessment

| Risk | Level | Mitigation |
|------|--------|------------|
| MCP used to bypass deterministic ingestion | Medium | Hard boundary: no writes to cache; no substitution for daemon; MEMORY_BANK update. |
| Schema drift vs cache | Low | Prefer MCP responses aligned with existing cache schema or clearly “review-only”. |
| Quota contention with daemon | Medium | Separate key or capped MCP quota; daemon has priority. |
| MCP as single point of failure for ops | Low | MCP optional; investigations can fall back to cache/scripts. |

### Complexity assessment

- **Added:** One integration surface (MCP server), one auth/identity path, one failure mode, runbook and MEMORY_BANK updates.
- **Unchanged:** Daemon, cache, scoring, gates, and trading loop. So complexity is **moderate increase** in the overall system, with trading path unchanged.

### Governance impact summary

- **Positive:** Clearer separation between “data for trading” (daemon/cache) and “data for analysis” (MCP); potential for faster board/CSA/SRE reviews and more structured experiment ideas.
- **Risks to manage:** Governance docs and runbooks must explicitly state that MCP is not authoritative for trading and that authority remains with daemon, cache, and engine.
- **Recommendation:** Document the MCP boundary and safeguards in MEMORY_BANK (e.g. new subsection under §7.8 or §2) and in the relevant audit runbooks so future Cursor and human operators enforce the same contract.

---

## 7. Summary

- The proposal’s description of **current UW usage** is **substantially accurate**; the only nuances are congress/institutional endpoint shape, IV skew/smile coming from enrichment, and sector/ETF tide sources (daemon + uw_macro + sector_tide_tracker).
- **Verdict: ADOPT WITH CONSTRAINTS.** MCP as a read-only, agentic intelligence layer for governance, CSA/SRE, and research is supported, provided hard boundaries (no writing to cache, no replacement of daemon, no use in trading/scoring) and quota/observability safeguards are in place.
- **No code or integration** was implemented in this review; this document is for Board, CSA, and SRE review only, as requested.
