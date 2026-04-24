# Alpaca Tiered Board Review — Design Proposal

**Purpose:** Governance design that tiers Alpaca rolling reviews, maps shadow experiments into governance inputs, and proposes an Alpaca-native tiered board review model. **Design only** — no implementation, no code/cron/promotion changes. Scope is Alpaca US equities; this document does not describe other venues.

**Source:** Synthesis from `docs/ALPACA_ROLLING_REVIEWS_AND_SHADOW_EXPERIMENTS.md` and MEMORY_BANK Alpaca governance entries.

---

## 1. Overview

Alpaca today has multiple rolling windows (1d–7d EOD, 5d PnL, 30d/last-N comprehensive review, 25-trade fast-lane, weekly ledger) and multiple shadow surfaces (telemetry shadow variants, state/shadow A1–C2 and shadow comparison, fast-lane, snapshot profiles, exit-lag shadow, etc.). CSA runs every 100 trades and optionally weekly; it consumes board review and shadow comparison when present but does not consume short-horizon rolling metrics directly. This design proposes:

- **Tier 1 (short horizon):** 1d, 3d, 5d, and 25-trade fast-lane — early signal, daily/cycle health.
- **Tier 2 (medium horizon):** 7d, 30d calendar, last-N-exits (e.g. last100/last387) — Board alignment, counter-intel, learning telemetry.
- **Tier 3 (long horizon):** last387 (or larger), weekly ledger, stability/cluster-risk — promotion context, convergence checks.

Rolling reviews are mapped into these tiers with strengths, weaknesses, and data reliability. Shadow experiments are classified into **governance inputs** (state/shadow A1–C2 + shadow comparison), **diagnostic only** (telemetry shadow.jsonl, snapshot profiles, exit-lag, ShadowTradeLogger), and **excluded from promotion** (fast-lane and snapshot profiles as separate surfaces). The Board Review Packet, CSA/SRE roles, promotion gate, and heartbeat are specified at design level only. Implementation phases are outlined without prescribing code or cron.

---

## 2. Tier Definitions (Alpaca-Specific)

| Tier | Horizon | Primary window(s) | Purpose |
|------|---------|-------------------|---------|
| **Tier 1** | Short | 1d, 3d, 5d calendar; 25-trade cycles | Early signal: PnL trend, exit/blocked mix, cycle health. Answers: “Is the last day/week/cycle degrading?” |
| **Tier 2** | Medium | 7d, 30d calendar; last100, last387 exits | Board alignment: same cohort as learning; counter-intelligence, replay readiness, how_to_proceed. Answers: “What does the Board see for the cohort we optimize on?” |
| **Tier 3** | Long | last387 (or last750), 7-day weekly ledger, stability/cluster-risk | Promotion and convergence: multi-day evidence, persona memos, shadow comparison baseline. Answers: “Is there enough stable evidence to consider advancing a shadow or changing lever?” |

**Cadence (Alpaca-native):**

- **Tier 1:** Updated on droplet at least daily (daily pack, 5d rolling PnL every 10 min); 25-trade cycle on 15-min cron. No requirement to run Board on Tier 1 alone.
- **Tier 2:** Built on demand or on a schedule (e.g. before CSA every-100 or weekly); 7d/30d/last-N from `build_30d_comprehensive_review.py` and `board/eod/rolling_windows.py`.
- **Tier 3:** Weekly ledger + CSA weekly review; last387 (or chosen cohort) as the canonical “learning and Board same scope”; stability and cluster-risk when available for rolling promotion review.

**Convergence concept (design only):** Tiers are consistent when Tier 1 does not contradict Tier 2/3 (e.g. Tier 1 5d PnL negative while Tier 2 last387 shows positive total PnL is a divergence to explain, not an automatic block). Convergence rules are in §6.

---

## 3. Rolling Review Mapping

### 3.1 Tier 1 (Short Horizon)

| Review | Window(s) | Inputs available | Strengths | Weaknesses | Missing surfaces | Data reliability |
|--------|-----------|------------------|-----------|------------|------------------|------------------|
| EOD rolling windows (1/3/5/7 day) | 1d, 3d, 5d, 7d | attribution, exit_attribution, blocked_trades, system_events (signal) | Same pipeline as Board; win rate, PnL, exit/blocked reason, signal_decay rate | Full 1/3/5/7 set not always in board bundle today; 7d overlaps Tier 2 | Tier 1 summary artifact (1d/3d/5d) for Board cover page | High: canonical logs |
| 5-day rolling PnL | 5d | exit_attribution, attribution fallback, daily_start_equity | Append-only, pruned, cron every 10 min; CSA-auditable | Not consumed by CSA/Board narrative today | Explicit inclusion in Tier 1 Board summary | High |
| Trade visibility review | since-hours / since-date | attribution, exit_attribution, direction_readiness | Executed-in-window, 100-trade baseline progress | Manual/scripted; not cron | Scheduled Tier 1 run (e.g. daily) | High |
| Fast-lane 25-trade | 25 trades/cycle | exit_attribution (go-forward) | Rolling cycle PnL; dashboard; shadow-only | Not fed into CSA; cycle count varies by activity | Tier 1 “cycle health” line in packet | High for cycle ledger |
| Daily intelligence pack | 1 day | attribution, exit_attribution, telemetry, blocked, profitability, regime | Unified daily pack; EOD and learning | Single day, not rolling over multiple days | Use as Tier 1 “today” snapshot | High |

**Tier 1 summary (design):** A Tier 1 surface would aggregate: (1) 1d/3d/5d PnL and win rate from rolling_windows, (2) 5d rolling PnL state (or link to it), (3) daily pack “today” summary, (4) fast-lane last cycle (or cumulative) when available. Blocked counts and exit reason mix for 1d/3d/5d complete the picture. No new scripts or cron are specified; this describes what *would* be included in a Tier 1 view.

### 3.2 Tier 2 (Medium Horizon)

| Review | Window(s) | Inputs available | Strengths | Weaknesses | Missing surfaces | Data reliability |
|--------|-----------|------------------|-----------|------------|------------------|------------------|
| 30d / last-N comprehensive review | 30d calendar or last100/last387/last750 | attribution, exit_attribution, blocked_trades; optional rolling_30 from rolling_windows | Counter-intel, learning telemetry, how_to_proceed; aligns Board and learning cohort | Optional 30d rolling key; parallel reviews build multiple scopes but CSA often gets only last387 | Explicit 7d and 30d (or last100) as Tier 2 variants | High |
| EOD 7-day window | 7d | Same as 1/3/5/7 | Comparable to weekly; signal survivorship 7d | Currently in same module as 1/3/5; 7d is boundary Tier 1/Tier 2 | Use 7d as Tier 2 short end | High |
| Rolling promotion review (inputs) | Date-scoped stability + cluster-risk | STABILITY_ANALYSIS, CLUSTER_RISK_OVER_TIME | Feeds CSA_BOARD_REVIEW; shadow_only | Depends on upstream stability/cluster scripts | Ensure Tier 2 board packet can reference CSA_BOARD_REVIEW when present | Medium (depends on upstream) |

**Tier 2 summary (design):** Tier 2 is the primary Board and CSA input: last387 (or last100 for faster feedback) comprehensive review, with 7d and 30d available for comparison. Counter-intelligence, opportunity-cost ranked reasons, and learning telemetry (replay readiness) are already in the bundle. No new implementation prescribed.

### 3.3 Tier 3 (Long Horizon)

| Review | Window(s) | Inputs available | Strengths | Weaknesses | Missing surfaces | Data reliability |
|--------|-----------|------------------|-----------|------------|------------------|------------------|
| last387 / last750 comprehensive review | last N exits | Same as Tier 2 | Same cohort as learning; stable exit count | Static once built; no rolling “last 387” by calendar | Tier 3 = canonical promotion cohort | High |
| Weekly trade decision ledger | 7 days | Ledger from exits/attribution/blocked; evidence paths | Weekly summary for CSA weekly review | Evidence collection and staging manual/scheduled | Weekly ledger as Tier 3 evidence bundle | High |
| CSA weekly review | Weekly | Board review, shadow comparison, weekly context, SRE | Full CSA verdict and findings for the week | Not a “rolling” metric; point-in-time weekly | Tier 3 verdict + persona memos | High |
| Rolling promotion review (output) | End-date | CSA_BOARD_REVIEW | Ranked configs, shadow_only | No gating | Tier 3 “promotable ideas” input | Medium |

**Tier 3 summary (design):** Tier 3 is the long-horizon, promotion-relevant view: last387 (or chosen N) as the canonical cohort, weekly ledger and CSA weekly run, and when available stability/cluster-risk and CSA_BOARD_REVIEW for promotable ideas. Convergence (e.g. Tier 1 5d vs Tier 3 last387 PnL sign) is a design concern in §6.

---

## 4. Shadow Experiment Mapping

### 4.1 Governance inputs (included in board review / CSA)

| Shadow | Role | Surface in board review | CSA interpretation | SRE validation |
|--------|------|-------------------------|---------------------|-----------------|
| **State/shadow A1–C2** | Policy shadows (displacement, max positions, expectancy floor, exit timing, good vetoes vs missed winners) | Via SHADOW_COMPARISON_LAST387: ranked_by_expected_improvement, nomination (Advance/Hold/Discard), risk_flags, persona_verdicts | Use nomination and proxy_pnl_delta for advance/hold/discard; treat missing shadow comparison as finding; risk asymmetry when nomination is Advance | Validate state/shadow/*.json present and readable; shadow comparison build succeeds; no live writes from shadow scripts |
| **Shadow comparison (last387)** | Single synthesis artifact for Board and CSA | Board Review Packet section “Shadow comparison” with ranking and nomination | Primary shadow input for promotion context; add finding if missing | Ensure artifact exists and is fresh when promotion is in scope |

**Design rule:** Only the cohort shadow comparison (A1–C2 → SHADOW_COMPARISON_LAST387) is a **governance input**. CSA and Board packet should reference it explicitly; SRE validates artifact presence and build success, not economic correctness.

### 4.2 Diagnostic only (surfaced but not promotion-gating)

| Shadow | Role | Surface in board review | CSA interpretation | SRE validation |
|--------|------|-------------------------|---------------------|-----------------|
| **Telemetry shadow variants** (logs/shadow.jsonl) | Live-cycle would_enter/would_exit/blocked per variant | Post-market §7; POSTMARKET_SHADOW_ANALYSIS.md; daily shadow confirmation | Informative for “what worked”; not used for advance/hold/discard | Log file exists and appendable; no orders from shadow |
| **Exit-lag shadow / intraday surgical** | Exit timing replay per date | EXIT_LAG_SHADOW_RESULTS; CSA_EXIT_LAG_MULTI_DAY_VERDICT when run | Exit experiment verdict is separate from cohort shadow comparison | Shadow-only; no live exit logic change |
| **ShadowTradeLogger** (data/shadow_trades.jsonl) | Rejected-signal log | Optional “blocked quality” diagnostic | Not used for promotion | Optional; no gating |
| **Droplet daily shadow confirmation** | Real vs shadow symbol overlap | SHADOW_TRADING_CONFIRMATION_YYYY-MM-DD.md | Confirms v2 hypothetical path active | Report generated when script runs |

**Design rule:** These appear in reports and optional Board packet appendices (e.g. “Daily shadow confirmation,” “Post-market shadow summary”). CSA may cite them in narrative but does not use them for verdict. SRE checks log/report presence and no execution impact.

### 4.3 Excluded from promotion (display / diagnostic only)

| Shadow | Reason |
|--------|--------|
| **Fast-lane 25-trade** | Separate experiment lane; dashboard/cockpit only; not part of SHADOW_COMPARISON_LAST387. Design: can appear in Tier 1 “cycle health” but never in promotion gate. |
| **Shadow snapshot profiles** | NO-APPLY; outcome attribution and blocked-trade intel deltas are hypothetical. Diagnostic only. |
| **Snapshot outcome attribution / BLOCKED_TRADE_INTEL** | Shadow profile deltas; no execution gating. |
| **Cluster/shortlist scripts** (emit_cluster_recommendations, emit_promotion_shortlist, etc.) | Diagnostics and shortlist; no gating. |

**Design rule:** Fast-lane and snapshot-profile outputs are never inputs to the promotion gate or to CSA advance/hold/discard. They may be referenced in Board packet as “Additional diagnostics.”

### 4.4 Shadow divergence (CSA interpretation — design)

- **Cohort shadow (A1–C2) vs baseline:** CSA already uses nomination and proxy_pnl_delta. Design: “Shadow divergence” = nomination suggests Advance but Tier 2/3 PnL or risk flags are weak. CSA should call out divergence in findings and lean toward HOLD unless risk acceptance documents it.
- **Telemetry shadow (shadow.jsonl) vs executed:** Large “would_enter” count with few real orders is a signal for Board narrative (e.g. “Gates blocking most shadow variants”); not a direct CSA verdict input.
- **Missing shadow comparison:** CSA adds finding “Produce shadow comparison before any promotion”; verdict can still be PROCEED for non-promotion missions.

### 4.5 SRE validation of shadow completeness (design)

- **Required when promotion in scope:** state/shadow/*.json (or subset A1–C2) present; build_shadow_comparison_last387 run success; SHADOW_COMPARISON_LAST387.json exists and non-empty.
- **Optional always:** logs/shadow.jsonl writable; no process placing orders from shadow code paths.
- **Failure mode:** If shadow comparison build fails, SRE records in SRE_STATUS/SRE_EVENTS; CSA can treat as missing data for promotion missions.

---

## 5. Governance Surfaces

Required intelligence surfaces for the Alpaca tiered board review (design):

| Surface | Source | Tier(s) | Purpose |
|---------|--------|---------|---------|
| **Executed trades** | logs/attribution.jsonl, logs/exit_attribution.jsonl (canonical) | 1, 2, 3 | PnL, win rate, exit reason, hold time |
| **Blocked trades** | state/blocked_trades.jsonl | 1, 2, 3 | Blocking patterns, opportunity-cost ranking (Tier 2/3) |
| **Counterfactuals** | Counter-intel in comprehensive review (opportunity_cost_ranked_reasons); C2 shadow (good vetoes vs missed winners) | 2, 3 | “Would-have” context; C2 is proxy only |
| **Shadow experiments** | state/shadow/*.json → SHADOW_COMPARISON_LAST387.json | 2, 3 | Advance/Hold/Discard; ranked shadows; risk flags |
| **Attribution** | exit_attribution (v2), attribution (fallback); daily pack | 1, 2, 3 | Closed trade truth; telemetry-backed count for replay readiness |
| **SRE health** | SRE_STATUS.json, SRE_EVENTS.jsonl, GOVERNANCE_AUTOMATION_STATUS.json | All | Escalation and anomaly context; CSA reads SRE |

Optional / diagnostic: telemetry shadow (shadow.jsonl), fast-lane ledger, snapshot profiles, exit-lag verdicts, daily shadow confirmation. These are not required for the minimal Board packet but can be attached as appendices.

---

## 6. Convergence Model

**Concept:** Tiers should not contradict each other without explanation. Alpaca cadence is trade-count and calendar (daily/weekly); convergence is advisory, not automatic blocking.

**Design rules:**

1. **Tier 1 vs Tier 2:** If Tier 1 5d PnL is negative and Tier 2 last387 (or 30d) PnL is positive, Board packet should note “Short-term (5d) underperforming vs cohort (last387).” No auto-block; CSA may lower confidence or add finding.
2. **Tier 1 vs Tier 3:** If Tier 1 fast-lane last cycle is strongly negative while Tier 3 weekly ledger is positive, same: note divergence for human review.
3. **Tier 2 vs Tier 3:** Tier 2 and Tier 3 share last387 (or same N); they should match when built from same inputs. If 7d vs last387 exit count diverges (e.g. 7d has few exits), note “Low activity in 7d window.”
4. **Convergence checklist (design):** A future “convergence” step could produce a one-line summary: Tier1_5d_sign, Tier2_last387_sign, Tier3_nomination, SRE_status. Green = same sign and no anomaly; Yellow = mixed or missing data; Red = contradiction plus anomaly. Not implemented here; design only.

---

## 7. Board Review Packet Structure (Alpaca-Specific)

Proposed structure for a single Alpaca Board Review Packet (design only):

1. **Cover / tier summary**
   - Tier 1: 1d/3d/5d PnL and win rate (from rolling_windows or link); 5d rolling state link; fast-lane last cycle or cumulative (optional).
   - Tier 2: Primary cohort (e.g. last387) scope, total PnL, win rate, exit/blocked counts; link to full comprehensive review JSON/MD.
   - Tier 3: Weekly ledger summary if applicable; shadow comparison nomination; CSA verdict summary.

2. **Executed trades and attribution**
   - Counts and PnL by tier scope; link to canonical logs (exit_attribution, attribution).

3. **Blocked trades and counter-intelligence**
   - Blocking patterns; opportunity-cost ranked reasons (from comprehensive review); C2 shadow note if present.

4. **Shadow comparison**
   - Ranked_by_expected_improvement; nomination (Advance/Hold/Discard); risk_flags; persona_verdicts excerpt. If missing: “Shadow comparison not run; required before promotion.”

5. **Learning and replay readiness**
   - Telemetry-backed exit count; ready_for_replay (e.g. ≥100 exits, ≥90% telemetry); how_to_proceed bullets.

6. **SRE and automation**
   - SRE_STATUS overall; GOVERNANCE_AUTOMATION_STATUS anomalies if any; link to SRE_EVENTS tail.

7. **Appendices (optional)**
   - Post-market shadow summary (shadow.jsonl); daily shadow confirmation; fast-lane cycle table; exit-lag verdict; snapshot/blocked-trade intel.

No new script or format is specified; this describes the *content* order and what each section would contain from existing artifacts.

---

## 8. CSA / SRE Personas (Alpaca)

**Scope:** US equities, **lower-frequency session-based** trading (calendar sessions, sparse fills vs continuous markets). **Alpaca-only**; these personas do not reference other venues. Definitions here are **persona, responsibilities, and narrative outputs only** — no strategy, execution, sizing, routing, threshold, or learning-gate relaxation.

### 8.1 CSA — Chief Strategy Auditor, Economic Truth Guardian (Alpaca)

**Mission:** Ensure learning reflects durable economic edges over time, not sparse or lucky outcomes.

**Primary focus:** Signal durability across sessions; regime stability over longer horizons; avoiding overfitting to low-frequency wins.

**Responsibilities:** Certify learning readiness from **LIVE-TRADE ENTRY/EXIT INTENT + REALIZED OUTCOME**; detect false confidence from sparse data; identify signal decay by time-of-day or regime; surface missed opportunity zones due to conservative gating (observational — CSA does not change gates or levers).

**Non-responsibilities:** No portfolio construction; no capital allocation; no execution timing.

**Verdicts (learning / narrative layer):**

- `CSA_LEARNING_UNBLOCKED_LIVE_TRUTH_CONFIRMED`
- `CSA_LEARNING_BLOCKED` — cite `trade_ids` and missing decision truth where applicable
- `CSA_PASS_WEAK` — include a time-weighted risk note

**Self-audit:** What assumption am I making about regime persistence? What evidence would show this edge is decaying?

**Inputs (unchanged):** Board review JSON (Tier 2/3 cohort: last387 or 30d); shadow comparison JSON when promotion is in scope; SRE status and events; automation evidence; optional context JSON (e.g. weekly).

**Findings (unchanged):** Assumptions, missing data (e.g. “Produce shadow comparison before any promotion”), counterfactuals, value leaks, risk asymmetry, escalation triggers; SRE interpretation when anomalies present.

**Shadow (unchanged):** Use nomination and `proxy_pnl_delta` for advance/hold/discard; call out divergence between shadow nomination and Tier 2/3 PnL or risk; do not use telemetry `shadow.jsonl` or fast-lane for verdict.

**Cadence (unchanged):** Every 100 trades; weekly. No new cadence in this design.

### 8.2 SRE — Site Reliability Engineer, Operational Integrity Sentinel (Alpaca)

**Mission:** Ensure observability remains trustworthy across sessions and market boundaries.

**Primary focus:** Session-aware telemetry; market open/close transitions; overnight state correctness.

**Responsibilities:** Validate session-aware joins; detect partial-day silence; ensure telemetry completeness across market hours; confirm no stale state persists overnight.

**Non-responsibilities:** No strategy review; no learning decisions.

**Verdicts (learning-pipeline / narrative layer):**

- `SRE_LEARNING_PIPELINE_HEALTHY`
- `SRE_PIPELINE_DEGRADED` (non-blocking)
- `SRE_PIPELINE_UNHEALTHY` (blocking)

**Self-audit:** What could fail quietly across sessions? What state might persist longer than intended?

**Shadow validation (unchanged):** When promotion is in scope, validate shadow comparison build and artifact presence; record failure in SRE_EVENTS; do not block CSA run.

**Outputs (unchanged):** `SRE_STATUS.json`, `SRE_EVENTS.jsonl`; `SRE_AUTOMATION_ANOMALY_<date>.md` when governance status is anomalous. Correlation with governance automation unchanged. **No execution gating from SRE artifacts** (existing principle). CSA consumes SRE outputs for escalation and narrative.

### 8.3 Preserved hard gates and machine semantics (unchanged)

- **CSA:** `enforce_csa_gate.py` and related tooling continue to use legacy verdict strings in `CSA_VERDICT_*.json` (**PROCEED | HOLD | ESCALATE | ROLLBACK**) and existing risk-acceptance rules. §8.1 learning-layer labels are **additive** for narrative alignment; they do **not** replace, bypass, or weaken those gates.
- **SRE:** Existing `SRE_STATUS.json` fields, anomaly conventions, and consumption by convergence / promotion advisory scripts remain **unchanged**. §8.2 labels describe how SRE summarizes pipeline health in review prose; they do not by themselves alter schemas or automation until an explicit approved change says otherwise.

---

## 9. Promotion Gate (Design Only)

- **Principle:** No automatic promotion. Gate is human-in-the-loop with CSA and optional SRE as inputs.
- **Design:** Promotion gate *concept* for Alpaca:
  - **Required inputs:** Tier 2 or Tier 3 board review (last387 or chosen cohort); SHADOW_COMPARISON_LAST387 with nomination; CSA verdict for that mission.
  - **Gate logic (design only):** PROCEED + nomination “Advance” + no SRE anomaly block → human may approve promotion (e.g. to live paper test). HOLD/ESCALATE/ROLLBACK or missing shadow comparison → require CSA_RISK_ACCEPTANCE or explicit override; no auto-promotion.
  - **Enforce script (existing):** enforce_csa_gate.py already blocks on verdict and risk acceptance; design only adds that “promotion” path is gated by shadow comparison presence and nomination when advancing a shadow. No code change specified.

---

## 10. Heartbeat (Design Only)

- **Concept:** A lightweight, periodic signal that Tier 1 (and optionally Tier 2) data and shadow comparison are fresh.
- **Design (Alpaca-native):**
  - **Tier 1 heartbeat:** Timestamp of last 5d rolling PnL update; timestamp of last daily pack for today (or last run). Optional: last fast-lane cycle id and cumulative PnL. No new cron; use existing cron outputs’ mtimes or manifest.
  - **Tier 2/3 heartbeat:** Timestamp of last comprehensive review build (e.g. last387); timestamp of last shadow comparison build; timestamp of last CSA run (e.g. CSA_VERDICT_LATEST.json mtime).
  - **Artifact (design only):** A small JSON (e.g. BOARD_REVIEW_HEARTBEAT.json) with keys: tier1_last_5d_ts, tier1_last_daily_pack_ts, tier2_last_review_ts, tier2_last_shadow_ts, tier3_last_csa_ts, tier3_last_weekly_ts. SRE or dashboard could read it to show “last updated” and alert if stale. No implementation in this task.

---

## 11. Implementation Phases (Design Only)

Phases are descriptive only; no code or cron is added by this document.

- **Phase 0 (current state):** As in inventory: 5d rolling PnL and rolling_windows exist; comprehensive review and shadow comparison feed CSA; no Tier 1 summary in Board packet; fast-lane and 5d not in CSA narrative.
- **Phase 1 — Tier 1 surface:** Expose Tier 1 summary (1d/3d/5d from rolling_windows, 5d state, optional fast-lane one-liner) in a single artifact or Board packet section; no new cron. Optional: dashboard or cockpit section “Tier 1” with links.
- **Phase 2 — Packet structure:** Align Board Review Packet (and any generator) with §7 order: cover/tier summary, executed/blocked, shadow comparison, learning, SRE, appendices. Use existing artifacts; no new promotion logic.
- **Phase 3 — Convergence and heartbeat:** Optional convergence one-pager (Tier1 vs Tier2 vs Tier3 sign/status); optional BOARD_REVIEW_HEARTBEAT.json and SRE/dashboard consumption. Design only.
- **Phase 4 — Promotion gate tightening:** If desired, document that promotion path requires shadow comparison and use nomination in enforce_csa_gate or human checklist; no automatic promotion.

Scope remains Alpaca-only. All references are to existing Alpaca paths and scripts in the inventory.

---

## 12. Document history (patch notes)

| Date | Change |
|------|--------|
| **2026-03-27** | **Alpaca governance personas — CSA + SRE (strategic upgrade):** §8 rewritten for session-based equities: CSA as Economic Truth Guardian (durable edges, sparse-data discipline, learning-layer verdicts `CSA_LEARNING_*` / `CSA_PASS_WEAK`); SRE as Operational Integrity Sentinel (session boundaries, overnight state, pipeline verdicts `SRE_LEARNING_PIPELINE_*` / `SRE_PIPELINE_*`). Added §8.3 affirming **unchanged** `enforce_csa_gate.py` semantics and `SRE_STATUS` / tooling consumption. No new personas, no duplicate files, no strategy or gate relaxation. |
