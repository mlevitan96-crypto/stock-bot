# Alpaca ~400-trade strict edge hunt — full board packet (SRE + CSA + Quant Officer)

**Packet timestamp (UTC):** 2026-04-01T18:57:48Z  
**Droplet root:** `/root/stock-bot`  
**Mission:** Single board-grade output — integrity first, edge-seeking (convert losses, amplify winners), no default “turn off” without mechanism proof.

**Authoritative inputs (this run):**

- `reports/daily/2026-04-01/evidence/ALPACA_STRICT_GATE_SNAPSHOT_20260401_185738Z.json`
- `reports/daily/2026-04-01/evidence/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_20260401_185738Z.json`
- `reports/daily/2026-04-01/evidence/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_20260401_185738Z.md`
- Exit attribution: `logs/exit_attribution.jsonl` + `logs/strict_backfill_exit_attribution.jsonl` (if present)

**Machine-readable recommendations:** `reports/daily/2026-04-01/evidence/ALPACA_BOARD_PACKET_RECOMMENDATIONS_20260401_185738Z.json`

---

## A) Executive verdict (one page)

### Gate status — **ARMED (learning-grade)**

| Field | Value |
|-------|--------|
| **LEARNING_STATUS** | **ARMED** |
| **trades_seen** | 400 |
| **trades_complete** | 400 |
| **trades_incomplete** | 0 |
| **Strict cohort trade ids (export)** | 400 (reconciled to `trades_seen`) |

**Certified vs review-only**

- **Certified for strict-chain completeness:** Yes — gate reports **zero incomplete** trades for the strict era cohort; promotion of **learning claims** that depend on strict completeness is **allowed** subject to normal governance.
- **Caveat (SRE):** Gate snapshot lists **400** `strict_cohort_trade_ids` but **399 are unique** — **one duplicate `trade_id`** appears twice in the cohort list. The edge script dedupes with a `set`, hence **399** analyzed rows (matches unique ids; **not** a missing exit row). **SRE-EDGE-001:** dedupe in `evaluate_completeness` collection or in export so `len(ids)==len(set(ids))`.

### PnL headline (edge analysis cohort, n=399 exits)

| Metric | Value |
|--------|--------|
| Sum PnL USD | **28.29** |
| Avg PnL USD | **0.071** |
| Median PnL USD | **0.18** |
| Win rate | **0.566** |
| Avg hold (min) | **66.0** |
| Tail (illustrative) | Worst **~−16.8** (NIO); best **~+10.8** (MRNA) |

### Where we win (top 3)

1. **Decay exits ~0.83–0.85** — strong positive avg PnL and win rate (n≥20 each).  
2. **Entry regime `mixed`** — bulk of book; positive avg expectancy vs **`unknown`**.  
3. **Long book** — carries aggregate PnL; shorts ~flat (not the primary leak).

### Where we lose (top 3)

1. **High decay exits `signal_decay(0.93–0.94)`** — negative expectancy clusters.  
2. **Low decay + `flow_reversal`** — poor win rate, negative avg PnL.  
3. **`entry_regime: unknown`** — ~41 trades, **−0.61** avg vs **+0.15** on `mixed` (telemetry / gating issue).

### Top 5 recommendations (profit impact + confidence)

| # | Recommendation | Expected impact (order of magnitude) | Confidence |
|---|----------------|--------------------------------------|------------|
| 1 | **GATE-IN + SIZE:** Favor entries that historically feed **0.83–0.85** decay exits **only when** `entry_regime=mixed` (paper A/B, +10% cap). | +$3–15 / session equiv. at current cadence | **Medium** |
| 2 | **CHANGE_EXIT:** Path rules for **0.93–0.94** decay (hold / MFE / drawdown-from-peak) before flat decay exit. | Cut **~$28–42** cumulative drag if half of toxic exits improved | **Medium** |
| 3 | **TELEMETRY + interim GATE:** Fix **entry_regime** stamp; **half size** while `unknown`. | **~$10–25** if unknown behaves like mixed post-fix | **Medium** |
| 4 | **CHANGE_EXIT:** **Confirmation** on `flow_reversal` + mid decay. | **$5–15** if false reversals reduced ~30% | **Low** |
| 5 | **GUARDRAIL (SRE):** Daily integrity artifact + alert on `trades_incomplete>0`; keep pre-gate backfill. | Integrity velocity; prevents silent corruption | **High** |

---

## B) SRE report (integrity and operability)

### Strict runlog effective — proof

Latest **`startup_banner`** on droplet (`logs/system_events.jsonl`):

```json
{"timestamp": "2026-04-01T18:37:13.944835+00:00", "subsystem": "telemetry_chain", "event_type": "startup_banner", "severity": "INFO", "details": {"phase2_telemetry_enabled": true, "strict_runlog_telemetry_enabled": true, "strict_runlog_effective": true, "run_jsonl_abspath": "/root/stock-bot/logs/run.jsonl"}}
```

**Interpretation:** At last bot start sampled, **`strict_runlog_effective: true`** — Phase2/strict runlog path is live for `run.jsonl` emission.

### Completeness status

- **Gate:** **400 seen / 400 complete / 0 incomplete** — strict learning chain **complete** for the cohort definition.  
- **Why incompletes existed historically:** Missing `exit_intent` join keys, metadata strips on reconcile, orders without `canonical_trade_id` — addressed by live fixes + backfill + integrity runner (see prior commits).  
- **Open item SRE-EDGE-001:** Strict cohort list has **one duplicate** `trade_id` (400 list entries, 399 unique): `open_SOFI_2026-04-01T15:25:47.839207+00:00` appears **twice** — dedupe at `evaluate_completeness` / export.

### Runlog coverage and retention

- **Risk:** Log rotation or disk pressure drops `run.jsonl` / `exit_attribution.jsonl` → false BLOCKED.  
- **Mitigation:** Retention policy docs, off-droplet backup of evidence bundles, integrity timer alerts.

### “Never again” controls

1. **Pre–strict-gate backfill** (`strict_chain_backfill_before_strict_gate`) before completeness evaluation in integrity cycle.  
2. **Live path:** `exit_intent` carries same join keys as v2 `exit_attribution` row; close `log_order` attaches metadata keys; reconcile persists `canonical_trade_id`.  
3. **Fail-closed:** Promotion / learning scripts should **refuse** “certified” narrative when `LEARNING_STATUS != ARMED` (enforce in CI or wrapper).  
4. **Alerts:** Telegram/integrity job on **incomplete > 0** or reconciliation boolean false.

### SRE recommendations (ranked)

| Rank | Item | Impact |
|------|------|--------|
| 1 | Close **SRE-EDGE-001** (400 vs 399) with a one-line audit script | High trust in quant tables |
| 2 | Daily **integrity markdown** to `reports/daily/.../evidence/` | Learning velocity |
| 3 | **Pager/alert** on gate flip BLOCKED | Prevents silent drift |
| 4 | **Retention + checksum** job on critical JSONL | Forensics |

---

## C) CSA report (signal truth and mechanisms)

### Signal / exit contribution highlights

- **Additive edge:** Decay bands **0.83–0.85**, **0.84**, **0.91–0.92** (positive slices with volume).  
- **Conditional:** Same **decay label family** spans **winners and losers** — toxicity is **state-dependent** (path, regime, flow), not “decay string = always bad.”  
- **Toxic conditional:** **0.93–0.94** and **0.64–0.65+flow_reversal** — require **exit policy** change, not signal kill.

### Regime / `unknown` bucket

- **Diagnosis:** **`unknown` is primarily telemetry gap** (missing stamp at entry), not proof that “mixed” model is wrong.  
- **Action:** Fix persistence; **interim sizing gate** — **not** disable longs.

### Exit reason toxicity (mechanism)

- **0.93–0.94:** V2 pressure exits fire **without enough path context** → locks in **adverse** outcomes on volatile names.  
- **flow_reversal + mid decay:** **Noise-sensitive** — exits **whipsaw** before trend resolves.

### CSA recommendations (ranked)

| Rank | Item | Expected impact | Risk |
|------|------|-----------------|------|
| 1 | Pair **CHANGE_EXIT** with **entry quality** features for 0.93+ | Fewer false exits | Slower risk-off |
| 2 | **Confirmation** layer for flow_reversal | Fewer chop losses | Delayed exit |
| 3 | **Regime stamp QA** dashboard | Removes unknown drag | Eng effort |

---

## D) Quant Officer report (edge extraction and action plan)

### Directional analysis

- **LONG:** **+$28.52** (279), avg **+0.10**.  
- **SHORT:** **−$0.23** (120), avg **−0.002** — **approximately breakeven**.  
- **Posture:** **Do not disable shorts.** Optional **conditional SIZE** only if future slice shows exit toxicity **conditional on short** (not visible here).

### Exit policy — CHANGE_EXIT proposals

1. **0.93–0.94:** Require **PnL path** rule (e.g. only allow if drawdown > X% from peak **or** hold > T min).  
2. **flow_reversal:** **Two-step** or **magnitude** threshold.  
3. **stale_alpha** (large losers in tails): Branch **stale** exit if **never** achieved min MFE (telemetry-dependent).

### Entry / regime — convert `unknown` losses

- **Telemetry:** `mark_open` / `_persist_position_metadata` must always receive **entry_regime**.  
- **Gating:** Half size when unknown until **5 sessions** with **unknown_rate < 1%**.

### Do more of what works

- **GATE-IN** larger size when: `entry_regime=mixed`, composite score in proven band, **and** historical exit bucket distribution skews to **0.83–0.85** (validate in replay before live).

### Quant recommendations (ranked)

Same as executive top 5; each tied to **verification** in `ALPACA_BOARD_PACKET_RECOMMENDATIONS_20260401_185738Z.json`.

---

## E) Board decision matrix (actionable)

| Decision ID | Lever type | Target | Mechanism (WHY) | Action (HOW) | Expected impact | Risk | Confidence | Owner | Verification |
|-------------|------------|--------|-----------------|--------------|-----------------|------|------------|-------|--------------|
| B-001 | GATE-IN / SIZE | Decay 0.83–0.85 + mixed regime | High win rate buckets | Paper A/B size +10% cap | +$3–15 / session equiv. | Overfit | Medium | Quant | 50 trades holdout |
| B-002 | CHANGE_EXIT | Decay 0.93–0.94 | Toxic expectancy | Path-dependent exit branch | −$28–42 drag reduction target | Tail risk | Medium | Quant + CSA | 30d replay |
| B-003 | TELEMETRY / GATE | entry_regime unknown | −$0.61 avg vs mixed | Fix stamp; half size interim | +$10–25 provisional | Block good trades | Medium | SRE + CSA | unknown→0 |
| B-004 | CHANGE_EXIT | flow_reversal + mid decay | Whipsaw | Confirmation delay | +$5–15 | Slow true reversal | Low | CSA | Labeled compare |
| B-005 | GUARDRAIL | Strict chain | Learning corruption | Daily integrity + alert | Integrity velocity | Alert noise | High | SRE | Staging inject |

---

## F) WHY ×3 + HOW appendix (top loss clusters)

### Cluster 1 — `signal_decay(0.93)` (n=21, avg −1.36)

| Level | Content |
|-------|---------|
| **WHAT** | Exits labeled 0.93 cluster lose ~$28.5 cumulative. |
| **WHY 1** | High decay score triggers exit **before** recovery or **after** giveback. |
| **WHY 2** | Single threshold maps **many** microstructures into one action. |
| **WHY 3** | No **path-dependent** branch in policy. |
| **HOW** | **CHANGE_EXIT** — add MFE/drawdown/hold gates; **replay** counterfactual. |
| **Data gap** | Bar MFE/MAE for each trade ideal. |
| **Experiment** | Shadow mode: log “would defer” vs actual for 2 weeks. |

### Cluster 2 — `signal_decay(0.94)` (n=8, avg −1.67)

| Level | Content |
|-------|---------|
| **WHAT** | Worst per-trade decay band expectancy. |
| **WHY 1** | Most aggressive decay exit. |
| **WHY 2** | Often overlaps **fast stop-out** names (SOFI, NIO examples). |
| **WHY 3** | No **symbol volatility** scaling on exit urgency. |
| **HOW** | **CHANGE_EXIT** — vol-scaled decay threshold; **GATE-IN** reduce entry size on high ATR names. |
| **Data gap** | ATR at entry in exit row. |
| **Experiment** | Bucket by ATR quartile. |

### Cluster 3 — `signal_decay(0.64)` (n=10, avg −1.39)

| Level | Content |
|-------|---------|
| **WHAT** | Low decay string yet **large** losses. |
| **WHY 1** | Exit reason string **understates** pressure (other fields drive exit). |
| **WHY 2** | **Chop** exits mid-range decay. |
| **WHY 3** | Composer surfaces **dominant** label only. |
| **HOW** | **CHANGE_EXIT** — use **composite exit score** + sub-reasons in policy, not string bucket alone. |
| **Data gap** | Structured `exit_reason_code` rollup in analysis. |
| **Experiment** | Re-bucket by `v2_exit_score` deciles. |

### Cluster 4 — `signal_decay(0.65)+flow_reversal` (n=12, win 25%)

| Level | Content |
|-------|---------|
| **WHAT** | Flow reversal exits **lose** disproportionately. |
| **WHY 1** | Reversal signal **noisy** intraday. |
| **WHY 2** | Immediate exit **no confirmation**. |
| **WHY 3** | Risk-off bias encoded as **urgent**. |
| **HOW** | **CHANGE_EXIT** — confirmation window; **DELAY_ENTRY** in reversal-prone tape. |
| **Data gap** | Timestamped flow impulse amplitude. |
| **Experiment** | A/B confirmation 1 bar vs 3 bars. |

### Cluster 5 — `entry_regime:unknown` (n=41, avg −0.61)

| Level | Content |
|-------|---------|
| **WHAT** | Unknown regime rows **drag** ~$25 vs mixed. |
| **WHY 1** | **No regime-aware** sizing or filtering. |
| **WHY 2** | Metadata **not stamped** on some paths. |
| **WHY 3** | Reconcile / edge cases **skip** regime persistence. |
| **HOW** | **TELEMETRY** fix + **GATE-IN** half size until clean. |
| **Data gap** | None once stamp fixed; verify rate. |
| **Experiment** | Before/after unknown rate dashboard. |

---

## G) Data integrity blocker list

**LEARNING_STATUS is ARMED** — **no BLOCKED promotion hold** on this dimension.

**Prerequisites already satisfied (this snapshot):**

- `trades_incomplete == 0`  
- Export reconciliation: `strict_cohort_len_equals_trades_seen` **true**, `complete_len_equals_trades_complete` **true**

**Follow-ups (non-blocking but required for “perfect” 400-table):**

1. **SRE-EDGE-001:** Dedupe strict cohort id list (400 entries, 399 unique today).  
2. If gate ever returns **BLOCKED:** run `strict_chain_historical_backfill.py`, verify live emitters, re-run export + analysis, **do not promote** until **ARMED**.

---

## Board consolidation

- **Certify:** Strict completeness **ARMED** for **400** trades — **learning-grade** integrity for this era.  
- **Edge posture:** **Amplify** 0.83–0.85 / mixed regime; **convert** 0.93–0.94 and flow_reversal via **exit engineering**; **fix** unknown regime via **telemetry + interim gate** — **no blind disable** of shorts or core signals.  
- **Next:** Resolve **SRE-EDGE-001**, execute replay for **B-002**, ship **telemetry** for **B-003**, enable **daily integrity** artifact (**B-005**).

---

*End of packet — 2026-04-01T18:57:48Z*
