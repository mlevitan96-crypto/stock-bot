# Project Apex — Alpaca V2 Harvester 360° Profitability Audit

**Classification:** Strategic advisory (read-only). No trading logic, thresholds, or production configuration were modified to produce this document.  
**Audience:** Operator / institutional review (Tier-1 framing).  
**Scope:** Alpaca Equities — V2 Harvester path (`main.py`, telemetry, strict cohort, truth warehouse), with explicit linkage to the **404-row** flattened ML cohort vs **canonical** post-epoch counts where they diverge.  
**Date:** 2026-04-21 (authoritative calendar per operator environment).

---

## Executive summary

The **404-trade** `alpaca_ml_cohort_flat.csv` cohort is **not** the same object as “all strict-era closes”: the flattener applies **join geometry** (entry snapshots, scoreflow, dedupe), so **404 < 424** canonical unique exits on the droplet is expected and does **not** by itself prove dashboard “health.” Health requires **joint** checks: strict completeness gate, **DATA_READY** semantics, **realized PnL** vs **blocked volume**, and **gate overlap** (Alpha 10 vs Alpha 11).

**Top finding:** Profitability is unlikely to be unlocked by a single model tweak until **(a)** measurement of *economic* edge per regime is separated from *telemetry coverage* gaps, and **(b)** overlapping entry vetoes (RF MFE + UW flow floor + displacement + score floor) are quantified as **marginal** blockers, not only marginal acceptances.

---

## Phase 1 — The 360° diagnostic

### 1.1 Strategic (Q) — Alpha 10 vs Alpha 11 and “opportunity starvation”

| Layer | Mechanism | Pathology risk |
|-------|-----------|----------------|
| **Alpha 10** | `check_alpha10_mfe_gate` vetoes when RF-predicted `exit_mfe_pct` &lt; `ALPHA10_MIN_MFE_PCT` (default **0.2**; fail-open on inference errors). | **Model risk:** trained cohort may not match post–`STRICT_EPOCH_START` feature geometry; veto can be **systematically misaligned** with live microstructure. |
| **Alpha 11** | `check_alpha11_flow_strength_gate` — blocks when UW `flow_strength` &lt; `ALPHA11_MIN_FLOW_STRENGTH` (default **0.985**); **missing** flow → **allow** with skip reason. | **Asymmetric starvation:** hard floor on flow when present; **missing** telemetry bypasses — creates a **bimodal** entry set (strong-filtered vs unfiltered holes). |

**Verdict (Q):** Yes — **over-filtering is plausible** when two independent gates stack before portfolio/displacement logic. “Opportunity starvation” should be measured as **incremental block rate** of Alpha 11 *given* Alpha 10 pass, and vice versa, on the **404** cohort and on **rejected** intents (if logged).

**88% slippage threshold (truth warehouse):** Lowering paper gates from **90% → 88%** does **not** assert fills got worse; it admits that **~12%** of historical exits lack computable **reference price / signal_context** joins for *slippage labeling* in the mission. That is a **measurement** relaxation, not proof of **systematic decay** in broker fill quality. Treat it as **“cost of noise”** in attribution completeness (see §1.4), not as MAR.

---

### 1.2 Technical (Core Engineer) — SIP WebSocket vs REST, pegging, decimals

**SIP WebSocket (`AlpacaStreamManager` + `PriceCache`):**

- Bars are retained per symbol with **receive-time freshness** (`get_fresh_bars_df` uses `max_age_sec`, default **60s** from stream ingest).
- Feed selection and **IEX failover** on auth errors are explicit design paths (`stream_manager.py`, `stream_feed.py`).

**REST fallback:** `MEMORY_BANK_ALPACA.md` documents `fetch_bars_safe` preferring in-memory cache when fresh, else REST — with **CRITICAL_DATA_STALE** logging when both fail. That is **seconds-to-tens-of-seconds** class latency, not sub-ms.

**“Front-run on mid-point pegs”:** The codebase does not implement exchange co-location or custom pegging engines; any “front-run” concern is **second-order** (NBBO drift between signal time and submit). **Prove with:** order timestamps vs `signal_context` / `entry_snapshots` mid fields — not asserted here.

**Decimal / rounding (`log_exit_attribution` payloads in `main.py`):** Prices and PnL fields are emitted with **`round(..., 4)`** (and similar) on several paths. On **sub-$5** names, **4dp** can quantize meaningful **bps** of notional; on large caps it is negligible. **Prove with:** distribution of `abs(round(p,4)-p)/mid` by price decile on the 404 cohort.

---

### 1.3 Data / ML (Data Engineer) — OFI vs exit MFE on the “pure” cohort

**Facts from implementation:**

- **OFI** (`ofi_l1_roll_60s_sum` / `ofi_l1_roll_300s_sum`) is written to **`logs/entry_snapshots.jsonl`** at submit time (`entry_snapshot_logger.py`); `MEMORY_BANK_ALPACA.md` states **telemetry-only** (no entry gate).
- **Exit MFE** for training surfaces flows through **exit quality / flattener** labels (e.g. `exit_mfe_pct` in Alpha 10 training narrative), not through a single blessed correlation table in-repo.

**Droplet-reported join reality (post–epoch forensic window):** The flattener run cited in operations noted **`entry_snapshot_join_pct` ~73%** with **canonical_trade_key=0** and **order-id fallback** carrying matches — meaning **OFI columns are dense only on the subset that joins**, not uniformly on all 404 rows.

**Verdict (Data):** **No** — we do **not** yet have a repo-checked, peer-reviewed proof that OFI sums **correlate** with exit MFE on the homogeneous cohort. Default hypothesis: **signal is thin or regime-local**; alternative: join noise dominates. **Fast path to truth:** one offline notebook/script (read-only) computing Spearman / rolling IC of `mlf_ofi_*` vs `exit_mfe_pct` with **regime buckets** (VIX proxy, time-of-day). *Out of scope for this markdown-only deliverable.*

---

### 1.4 Operations / risk (SRE) — `DATA_READY: YES` and the cost of 88%

**What `DATA_READY: YES` means (and does not):** Per `MEMORY_BANK_ALPACA.md` §1.2 / `docs/DATA_READY_RUNBOOK.md`, **`DATA_READY: YES` ≠ `LEARNING_STATUS: READY`**. The warehouse mission proves **joinability** for packets and coverage metrics at configured thresholds — not that every strict trade is ML-complete.

**88% gate:** If measured slippage/snapshot-exit coverage is **88.40%** at default **90%**, lowering to **88%** passes the gate while retaining **~11.6%** of exits as **not computably audited** for that dimension.

| Cost of noise (conceptual) | Effect |
|----------------------------|--------|
| **Attribution** | PnL stories and slippage histograms **skip tail** of “unknown slippage” exits. |
| **Promotion** | Board / gate narratives may **overstate** execution hygiene unless the missing slice is disclosed. |
| **Research** | ML features that depend on **signal_context** near exit are **biased** toward the joinable subset. |

**Mitigation (ops):** Treat **88%** as a **documented exception** with a **remediation ticket** ( widen `orders` / `signal_context` windows or fix root join ) rather than a permanent target.

---

## Phase 2 — Persona ideation ($1M pitch format)

Each persona: **two** high-impact, actionable ideas.

### Q — Macro / strategy

1. **Regime-conditioned risk budget:** Scale max concurrent names and per-trade risk by a **small set** of observable regimes (e.g. VIX quartile + breadth). *Impact:* MAR ↑ by cutting left-tail clusters in chop; **medium confidence*, **medium** horizon.

2. **Sector / factor crowding cap:** Hard cap simultaneous exposure to correlated sectors (XL* + single-names). *Impact:* MAR ↑ via **diversification of shock**; **high** implementability on paper.

### Core Engineer — Execution & infrastructure

1. **Staleness-aware bar path:** Log and alert when **stream bar age** exceeds `ALPACA_STREAM_BAR_MAX_AGE_SEC` before REST fallback on entry-heavy symbols. *Impact:* Fewer “stale composite” entries; MAR **modest** ↑; **short** horizon.

2. **Price tick quantization audit:** Replace blanket `round(...,4)` with **symbol-tick-aware** quantization for names under e.g. $10. *Impact:* bps-level **execution accuracy** on tail tickers; **medium** horizon.

### Data Engineer — Telemetry & ML

1. **OFI × regime interaction features:** Add explicit **interaction terms** (OFI × time-of-day × vol bucket) in flattener export only after IC screen. *Impact:* Sharper signal if edge is local; else discard. **Medium** horizon.

2. **Join coverage as a first-class column:** Export `mlf_join_tier` / missingness flags into board packets so models **cannot** silently train on biased subsets. *Impact:* fewer false promotions; **MAR protected** (risk reduction).

### Innovation Officer — Asymmetric / optional

1. **Earnings window sub-strategy:** Tag and optionally **down-weight** entries into names with **elevated earnings proximity** unless reward explicitly compensates (vol targeting). *Impact:* tail risk ↓; **medium** evidence needed.

2. **Synthetic counterfactual PnL labels:** Use bar-path replay for **blocked** intents (where logs allow) to estimate **opportunity cost** of gates vs realized path. *Impact:* settles starvation debate with **dollars**; **long** horizon.

---

## Phase 3 — Master roadmap: path to profitability

### Overall top five (merged ranking)

| Rank | Idea | Owner | Horizon | Profit / MAR impact (expected) |
|------|------|-------|---------|----------------------------------|
| **1** | **Marginal gate attribution** — measure block rates for Alpha10 ∩ Alpha11 ∩ displacement on same cohort | Q + Data | **0–7d** | **MAR:** high clarity, **profit:** indirect until gates tuned |
| **2** | **Join coverage as explicit ML + board fields** | Data | **1–3w** | **MAR:** avoids false confidence; **profit:** prevents bad promotions |
| **3** | **Stream staleness + REST path metrics on entry** | Core | **0–7d** | **MAR:** modest ↑; **profit:** small but clean |
| **4** | **Regime-conditioned risk budget** | Q | **1–3w** | **MAR:** meaningful ↑ in multi-regime samples |
| **5** | **Tick-aware price quantization on low-priced names** | Core | **1–3w** | **Profit:** bps-level on tail; **MAR:** neutral–slight ↑ |

### Short-term (0–7 days) — parameters & measurement

- Re-baseline **DATA_READY** vs **strict gate** on the same calendar window; publish **missing 12%** slice characteristics.
- **Gate overlap** dashboard: counts of `alpha10_mfe_too_low` vs `alpha11_flow_strength_below_gate` vs `displacement_blocked` (from logs / blocked reports).

### Medium-term (1–3 weeks) — telemetry & features

- OFI **IC screen** + optional interaction expansion in flattener **after** statistical sign-off.
- **Sector crowding caps** + correlation matrix in risk checks.

### Long-term (1+ months) — architecture & model promotions

- **Counterfactual blocked-intent replay** pipeline (heavy engineering; high narrative value).
- **Promotion gate** that requires **join tier** and **strict completeness** green *simultaneously* before model or score-policy promotion.

---

## Phase 4 — Synthesis & operator actions

1. **Stop equating “404 healthy” with “engine profitable.”** 404 is **ML-join-complete strict opens**; profitability is an **economic** claim requiring PnL, MAR, and regime conditioning.  
2. **Treat 88% slippage pass as technical debt**, not a victory lap — document the **excluded slice** in every board packet until back above **90%** (or consciously adopt **88%** as policy with CSA sign-off).  
3. **Stack rank gates by marginal lift**, not intuition — Alpha 10 and Alpha 11 may both be valuable, but together they may **dominate** expectancy in ways invisible to each gate in isolation.  
4. **Instrument execution path latency** (stream age at submit, REST fallback rate) before debating “front-running” at the institutional level.

---

## References (in-repo)

- `src/alpha10_gate.py` — RF MFE floor, fail-open semantics.  
- `src/alpha11_gate.py` — UW flow-strength floor, missing-flow allow.  
- `src/alpaca/stream_manager.py`, `src/market_intelligence/ofi_tracker.py` — SIP / OFI telemetry path.  
- `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` — `DATA_READY` / slippage coverage gates.  
- `scripts/telemetry/alpaca_ml_flattener.py` — strict cohort flattening; join metrics printed at end of run.  
- `MEMORY_BANK_ALPACA.md` — OFI telemetry-only policy, `fetch_bars_safe` / stale data contract, displacement narrative.  
- `docs/DATA_READY_RUNBOOK.md` — `DATA_READY` vs strict learning distinction.

---

*End of report — Project Apex Alpaca 360° Profitability Audit.*
