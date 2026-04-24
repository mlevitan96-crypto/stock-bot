# Alpaca Quant Advisory 360 — Tier-1 Desk Review & Red Team Cross-Pollination Spec

**Classification:** Internal — Board authorization for engineering tickets only.  
**Scope:** `stock-bot` Alpaca (equities) path: telemetry, ML cohort, UW integration, execution, governance.  
**Companion context (narrative only):** Kraken desk overhaul (unmanaged T+60m labels, continuous feature interaction matrix, telemetry-only shadow ML). This document maps **institutional parity targets** onto **this repository’s actual files**—not aspirational vapor.

---

## Executive summary

Alpaca today is **strong on telemetry integrity and fail-closed learning gates** (`telemetry/alpaca_strict_completeness_gate.py`, `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py`) but **weak on academically clean supervised targets** and **first-class cross-sectional feature design** at the level implied by “unmanaged labels + interaction matrix + shadow brain.” The Harvester cohort pipeline centers **`realized_pnl_usd`** and exit-attribution–joined features (`scripts/telemetry/alpaca_ml_flattener.py`, `src/ml/alpaca_cohort_train.py`). That is **economically honest for PnL attribution** but **statistically dangerous** as a primary ML target (policy leakage, exit-path endogeneity, selection on survival). UW signal mass arrives primarily as **nested blobs** (`entry_uw`, `direction_intel_embed`) flattened to `mlf_*` columns—not as a guaranteed, schema-stable **Gamma / Tide** contract. Execution and market-structure risks (SIP latency, PDT, wash sales, overnight gaps) are **partially instrumented** (slippage fields in orders path, truth warehouse) but **not holistically modeled** as hard constraints in the strategy loop.

**Bottom line:** Cross-pollination is a **multi-quarter** program: (1) define **unmanaged** price targets with **session/EOD capping**, (2) add an **explicit interaction / cross-term layer** (or regularized tabular interactions) on top of `mlf_*`, (3) ship a **read-only shadow scorer** that consumes the same telemetry as training, (4) extend **milestone Telegram** beyond current Z-count and shadow trade counts.

---

## 1. Current state & adversarial gap analysis

### 1.1 Target variable — are we still exit-biased?

**Yes, for the canonical “Harvester cohort” path.**

| Artifact | Role | Exit bias? |
|----------|------|------------|
| `scripts/telemetry/alpaca_ml_flattener.py` | Builds CSV rows from `logs/exit_attribution.jsonl`, emits `realized_pnl_usd`, hold time, exit MFE/MAE proxies | **High** — row universe is **closed trades** only. |
| `src/ml/alpaca_cohort_train.py` | **Requires** `realized_pnl_usd` as label column for default training filter | **Explicit** — docstring: drops rows without finite realized PnL. |
| `scripts/research/prepare_training_data.py` | Alternative **bar-first-touch** binary labels (TP before SL) from fetched 1m bars | **Lower** path-dependence vs raw PnL, still **path-modeled** (first touch semantics). |
| `scripts/research/alpha_arena_trainer.py` | Default `--target-col exit_mfe_pct` (MFE-style regression) | **Partial** — forward excursion inside trade, still **conditional on position held**. |

**Adversarial critique:** `realized_pnl_usd` conflates **alpha** with **microstructure, fees, borrow, spread, and exit policy** (displacement, score exits, time exits). Any model trained to predict it learns **policy + execution**, not “entry signal quality under unmanaged forward return.”

#### EOD-capped unmanaged target (equities) — design sketch

**Definition (institutional):** At decision time \(t\) (entry fill or “paper intent time” for shadow), define forward log return to horizon \(H\) using **official session bars** (RTH), **no peeking** beyond \(t\):

- **T+60m unmanaged:** \(y = \log(S_{t+60}) - \log(S_t)\) using **last trade or mid** consistent with your SIP entitlement; if session ends before 60m, cap at **last RTH print** (partial horizon flag).
- **EOD unmanaged:** \(y = \log(S_{\text{close}}) - \log(S_t)\) on **same session**; if overnight is out of scope for v1, set `horizon=EOD_SESSION` and **exclude** entries after `T_cut` (e.g. last 30–60m) to avoid “fake EOD” micro-moves.

**Implementation touchpoints (no code in this advisory):**

- **Bar source of truth:** align with `tests/test_alpaca_price_cache.py` / price cache ring buffer and Alpaca data API usage elsewhere; new module e.g. `src/ml/alpaca_unmanaged_labels.py` (new) orchestrating bar fetch + label join.
- **Join key:** reuse `src/telemetry/alpaca_trade_key.py` canonical keys; store `label_asof_ts`, `label_horizon`, `label_censor_reason` (halt, halt+auction, thin book, partial_minutes).
- **Do not** replace `realized_pnl_usd` overnight in `alpaca_cohort_train.py`; add **parallel columns** `target_ret_60m`, `target_ret_eod_rth` and gate training scripts on **label completeness** similar to strict PnL checks.

---

### 1.2 UW telemetry — Gamma, Tide, and the ML matrix

**Primary integration path today:** `scripts/telemetry/alpaca_ml_flattener.py`

- `ML_BLOB_KEYS = ("entry_uw", "v2_exit_components", "direction_intel_embed")` — nested dicts are flattened with `_flatten_leaves` → **`mlf_entry_uw_*`**, **`mlf_v2_exit_components_*`**, **`mlf_direction_intel_embed_*`** style prefixes (see `_prefix_mlf` usage in `build_rows`).
- There is **no** dedicated first-class column namespace like `uw_gamma_*` or `market_tide_*` in the flattener itself; **anything present** in `entry_uw` / embed trees becomes wide columns; **anything absent at log time is silently missing** (flatten of empty dict adds nothing).

**Risk — “mapped vs dropped”:**

1. **Writer path gap:** If Gamma/Tide are fetched in daemon or enrichers but **not copied** into `exit_attribution`’s `entry_uw` / `direction_intel_embed` at entry time, the flattener **cannot recover** them at cohort build time.
2. **Sparse / string-heavy payloads:** `_flatten_leaves` stringifies long lists; high-cardinality categorical Tide states may become **unusable** for linear / tree models without hashing.
3. **Join tier noise:** `mlf_scoreflow_join_tier` and scoreflow wide join logic can dominate variance; UW features may be **present but down-weighted** by missingness filters in `src/ml/alpaca_cohort_train.py` (`strict_scoreflow` mode drops rows with NaN features).

**Red team verdict:** “Successfully mapped” is **conditionally true** only if the **exit_attribution + entry snapshot** contract reliably embeds those APIs. Treat UW as **unstable dimensionality** until you add **explicit schema tests** (see Blueprint §2.2).

---

### 1.3 Adversarial threats — SIP latency, PDT, wash sales, overnight gaps

#### SIP feed latency & slippage

- **Instrumentation:** `src/telemetry/attribution_emit_keys.py` (`slippage_bps_vs_mid`), `logs/orders.jsonl` enrichment, `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` (slippage coverage gate), `telemetry/signal_context_logger.py` (mid/last at decisions).
- **Vulnerability:** **Paper vs SIP entitlement mismatch** — paper fills may not stress the same microstructure as live SIP; models trained on paper slippage proxies can **overfit zero slippage** regimes. Momentum audit text still references SIP verification (`momentum_filter_audit.py`); enforcement is **not centralized** in one execution invariant.

#### Pattern Day Trader (PDT)

- **Observation:** No first-class **Alpaca account PDT state machine** surfaced in strategy core from repo-wide grep; `archive/investigation_scripts/diagnose_alpaca_orders.py` reads `pattern_day_trader` as diagnostic.
- **Vulnerability:** **Silent behavior change** if account flags flip — risk limits may be enforced broker-side **after** the bot plans size. Missing: `state/pdt_risk.json` (conceptual) + daily sync from Alpaca account API + hard block in order router.

#### Wash sales

- **Observation:** No dedicated wash-sale engine in trading path from quick scan; tax lots and **30-day re-entry** are not modeled as a **strategy constraint**.
- **Vulnerability:** For taxable sleeves or unified book, **re-entry signals** can be structurally toxic; ML that ignores wash rules can advocate **illegal or uneconomic** churn.

#### Overnight gap risk

- **Observation:** Direction intel / overnight blocks exist in rich embeds (`direction_intel_embed` in exit path in `main.py` region near exit attribution), but **unmanaged EOD/T+60m targets** that include overnight are **not** the default training label.
- **Vulnerability:** Any “close-to-open” thesis without explicit **gap model** (earnings, ADR, macro) will be **fragile** on gap names; equities gap risk dominates crypto-style continuous session assumptions.

---

## 2. Cross-pollination blueprint — code-level specs

### 2.1 Target labeling — T+60m & EOD unmanaged

| Deliverable | New / changed files | Specification |
|-------------|---------------------|---------------|
| Bar-aligned label store | **New:** `src/ml/alpaca_unmanaged_labels.py`; **New:** `scripts/research/build_alpaca_unmanaged_labels.py` | Input: cohort CSV or JSONL of `(trade_id, symbol, entry_ts_utc, side)`. Output: `reports/research/alpaca_labels_unmanaged.parquet` (or `.jsonl`) with columns above + censor flags. |
| Cohort merge | **Modify:** `scripts/telemetry/alpaca_ml_flattener.py` | Optional `--join-labels PATH` to merge unmanaged targets **by trade_id** without folding them into `mlf_*` (keep `target_*` unprefixed for clarity). |
| Training | **Modify:** `src/ml/alpaca_cohort_train.py` | Add `--label-col` (default `realized_pnl_usd` for backward compat); same NaN / finiteness gates for new numeric targets. |
| Arena / brain | **Modify:** `scripts/research/alpha_arena_trainer.py` | Allow `--target-col target_ret_60m_rth` etc.; export bundle meta must record **horizon + session calendar**. |

**Session calendar:** use **NYSE** RTH as v1 default; parameterize for later ARCA extended.

---

### 2.2 Continuous feature interaction matrix

**Institutional intent:** beyond raw `mlf_*` mains, maintain **curated interactions** (e.g. `uw_flow_strength × regime_chop`, `composite × vol_regime`) with **stability controls** (variance inflation monitoring, ridge on interactions, or explicit GBM depth).

| Layer | Files | Action |
|-------|-------|--------|
| Contract | **New:** `telemetry/alpaca_ml_interaction_contract.json` | Named list `{name, expr, version}` where expr references **canonical** `mlf_*` stems post-flattener. |
| Materialization | **New:** `scripts/telemetry/alpaca_ml_interaction_expand.py` | Reads `alpaca_ml_cohort_flat.csv`, appends `mlx_*` columns, writes `reports/Gemini/alpaca_ml_cohort_flat_ix.csv`. |
| Training | **Modify:** `src/ml/alpaca_cohort_train.py`, `scripts/research/alpha_arena_trainer.py` | Feature modes: `strict_scoreflow`, `strict_scoreflow_ix` (ix only with whitelist). |

**UW Gamma / Tide explicit mapping (closes the “dropped?” gap):**

- **Modify:** `src/exit/exit_attribution_enrich.py` or the UW snapshot writer that fills `entry_uw` (trace from `main.py` / UW daemon) to always emit **stable keys**: `uw_gamma_skew`, `uw_tide_state`, `uw_tide_score` (examples—names to be fixed by data owners).
- **New test:** `tests/test_alpaca_ml_flattener_uw_contract.py` — golden JSON fixture → expected `mlf_entry_uw_*` subset non-empty when fixture includes Gamma/Tide.

---

### 2.3 Shadow scorer (telemetry-only “brain”) — joblib path

**Existing export path:** `scripts/research/alpha_arena_trainer.py` `--export-alpha10` writes a **joblib bundle** with `model`, `feature_names`, `impute_medians`, `target`, `kind`.

**Adaptation spec (no `paper_signal_scorer.py` in repo today):**

| Piece | File | Purpose |
|-------|------|---------|
| Loader | **New:** `src/ml/alpaca_shadow_scorer.py` | `load_bundle(path) -> predict_row(flat_dict) -> float` with **same imputation** as training (`impute_medians`). |
| Telemetry hook | **New:** `scripts/audit/alpaca_shadow_score_stream.py` OR **Modify:** `main.py` (behind env `ALPACA_SHADOW_SCORER_EMIT=1`) | After `append_score_snapshot` / `trade_intent`, append **read-only** `logs/shadow_ml_scores.jsonl` with `{ts, symbol, trade_id?, score_hat, bundle_version, feature_hash}`. |
| Governance | **Modify:** `telemetry/alpaca_strict_completeness_gate.py` (optional) | **Do not** block learning on shadow scores; at most **warn** if stream stale. |

**Note:** User prompt referenced `paper_signal_scorer.py` — **not present** in this tree; treat as **greenfield** name aligned to paper mode.

---

### 2.4 Milestone tracking — N-based Telegram for equities

**Existing mechanisms:**

- `telemetry/alpaca_shadow_trade_milestones.py` — **600 / 750 / 1000** canonical trade milestones; state `state/alpaca_shadow_trade_milestones.json`; invoked from exit attribution path in `main.py`.
- `scripts/telemetry_milestone_watcher.py` — **strict ML-ready Z** milestones (50…250), runs flattener, zero-tolerance tripwire, Telegram.

**Parity extension spec:**

| Need | Implementation |
|------|----------------|
| Configurable N-list | **Modify:** `telemetry/alpaca_shadow_trade_milestones.py` — load thresholds from `config/alpaca_milestones.json` (new) instead of hardcoded `THRESHOLDS`. |
| Separate counters | **Modify:** `scripts/telemetry_milestone_watcher.py` — distinct Telegram templates for **Z_ml_ready**, **N_exits**, **N_shadow_scores**, **DATA_READY streak**. |
| Quiet hours / dedupe | Reuse `telemetry/alpaca_telegram_integrity` patterns already referenced in watcher docstring. |

---

## 3. Execution roadmap

Each row: **action** — **primary files**.

### 3.1 Short-term (0–4 weeks)

1. **Label inventory & leakage audit** — Document every place `realized_pnl_usd` / `pnl` is used as target: `src/ml/alpaca_cohort_train.py`, `scripts/alpaca_ml_multi_signal.py`, `scripts/research/prepare_training_data.py`, `scripts/research/alpha_arena_trainer.py`.
2. **UW contract test** — Add flattener golden test + enforce stable keys at write time: `scripts/telemetry/alpaca_ml_flattener.py`, UW enrich path (`src/exit/exit_attribution_enrich.py`, `data/uw_flow_cache.json` consumers).
3. **Unmanaged label prototype (offline)** — `scripts/research/build_alpaca_unmanaged_labels.py` (new) + join to a **copy** of cohort CSV; no live behavior change.
4. **Shadow scorer read-only stream** — `src/ml/alpaca_shadow_scorer.py` (new) + `scripts/audit/alpaca_shadow_score_stream.py` (new) + optional `main.py` hook behind env.
5. **PDT / account risk snapshot** — New cron or systemd oneshot hitting Alpaca account endpoint, writing `state/alpaca_account_flags.json`; wire read-only dashboard + optional gate in `main.py` order submission path.

### 3.2 Medium-term (1–3 months)

1. **Promote unmanaged labels into training CLI** — `src/ml/alpaca_cohort_train.py`, `scripts/telemetry/alpaca_ml_flattener.py` merge path, calibration gate `src/ml/alpaca_harvester_calibration_gate.py`.
2. **Interaction matrix v1** — `scripts/telemetry/alpaca_ml_interaction_expand.py` (new) + `telemetry/alpaca_ml_interaction_contract.json` (new) + arena trainer feature mode.
3. **Walk-forward evaluation harness** — New `scripts/research/alpaca_walk_forward_cv.py` consuming flattened cohort + labels; prevent single-window overfit.
4. **Execution model enrichment** — Extend `logs/orders.jsonl` schema documentation and `src/telemetry/attribution_emit_keys.py` so every fill has **decision reference mid** where SIP allows; align with `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` gates.
5. **Wash / lot awareness (paper first)** — Design `state/tax_lot_shadow.jsonl` (new) + simulation in `scripts/audit/` — no live tax optimization until validated.

### 3.3 Long-term (3–9 months)

1. **Live shadow brain → promotion FSM** — Formalize promotion from `logs/shadow_ml_scores.jsonl` performance to **non-shadow** weights in `config/tuning/active.json` (governance already scattered in `docs/` + `config/strategy_governance.json` — consolidate).
2. **Multi-horizon label zoo** — T+5m / T+30m / T+60m / EOD / T+1 open with **explicit censoring**; multi-task learner in `scripts/research/` or `src/ml/`.
3. **Cross-sectional equity factors** — Optional external factor orthogonalization (industry, beta) — new `src/ml/alpaca_factor_residualize.py` feeding interaction expander.
4. **Production model registry** — Versioned artifacts under `artifacts/` with signed manifests (extend patterns seen under `artifacts/` in repo).
5. **Adversarial continuous evaluation** — Scheduled red-team scripts comparing **policy PnL** vs **unmanaged forward return** attribution gaps; output to `reports/research/`.

---

## 4. Jira-ready ticket stubs (for Swarm authorization)

| ID | Title | Acceptance criteria |
|----|-------|----------------------|
| ALP-ML-001 | Unmanaged T+60m / EOD label builder (offline) | Script + sample output; documented censor rules; no live trading changes. |
| ALP-ML-002 | Cohort merge for `target_ret_*` columns | Flattener or post-step merges labels; `alpaca_cohort_train` can train with `--label-col`. |
| ALP-UW-003 | Stable Gamma/Tide keys in `entry_uw` | Fixture test; non-empty `mlf_entry_uw_*` for Gamma/Tide in golden row. |
| ALP-SH-004 | `alpaca_shadow_scorer` joblib loader + JSONL stream | Deterministic scores on fixture; env-gated emit. |
| ALP-TG-005 | Configurable milestone thresholds | JSON config + Telegram dedupe preserved. |
| ALP-RISK-006 | PDT / account flags snapshot | State file + dashboard read; optional hard block. |
| ALP-IX-007 | Interaction contract v1 | `mlx_*` columns + one trained model ablation report. |

---

## 5. Closing adversarial statement

Cross-pollination is not **configuration**—it is **epistemology**. Until Alpaca’s primary supervised signal is **unmanaged forward return** (or strictly defined path experiments like `prepare_training_data.py`), the “ML brain” remains a **policy co-pilot** fitted to **past exits**, not a **signal discovery engine** under **institutional forward return**. The repository already contains the **telemetry discipline** to support the harder path; the gap is **label economics + explicit interaction governance**, not more JSONL volume.

---

*Prepared for Q-Ops Sovereign Board — Tier-1 Quant & Red Team. No runtime code changes in this deliverable.*
