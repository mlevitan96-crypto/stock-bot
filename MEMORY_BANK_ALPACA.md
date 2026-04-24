# MEMORY_BANK_ALPACA.md
# Master Operating Manual for Cursor + Trading Bot
# Version: 2026-04-24 (Side-aware parity architecture + Shadow Vanguard)
# Last Updated: 2026-04-24 (Maintenance Log: V2 short AI quarantine active; split-brain challenger active in shadow)

---
# ⚠️ MEMORY BANK — DO NOT OVERWRITE ⚠️
# Cursor MUST load this file before ANY code changes.
# Cursor MUST update this file when ANY new system behavior is added.
# This file is the single source of truth for all system architecture and behavior.
---

---

# 0. CURSOR BEHAVIOR CONTRACT (TOP‑LEVEL GOVERNING RULE)
**Cursor MUST read and follow this section BEFORE doing anything else.  
This section overrides all other rules.**

## 0.1 THE GOLDEN WORKFLOW RULE  
**Every task MUST follow this exact cycle:**

### **USER → CURSOR → GITHUB → DROPLET → GITHUB → CURSOR → USER**

Cursor MUST:
- push all code changes to GitHub  
- trigger droplet deployment immediately  
- wait for deployment + verification to finish  
- pull results back from GitHub  
- analyze results  
- only then respond to the user  

Cursor MUST NOT:
- skip GitHub  
- skip droplet  
- skip verification  
- respond early  
- ask the user to run commands manually  
- assume the droplet is up to date  
- assume GitHub has the latest code  

**NO TASK IS COMPLETE UNTIL THE FULL CYCLE IS COMPLETE.**

---

## 0.2 MANDATORY CURSOR RESPONSIBILITIES  
Cursor MUST:
- ALWAYS push code to GitHub before deployment  
- ALWAYS trigger droplet deployment via SSH  
- ALWAYS wait for verification results  
- ALWAYS pull results from GitHub  
- ALWAYS analyze verification output  
- ALWAYS complete the entire workflow before responding  
- ALWAYS sync production checkouts with **`git fetch origin && git reset --hard origin/main`** (never rely on soft `git pull` alone for app code — see **`.cursorrules`** `immutable_production_gitops`).  

Cursor MUST NOT:
- ask the user to run commands  
- ask the user to copy/paste output  
- skip any step  
- report partial completion  
- rely on local files for production data  
- mask errors or hide failures  
- edit application source directly on production droplets (SSH vim/scp into the repo tree); uncommitted server drift is not truth and is **eradicated** on the next compliant deploy.  

---

## 0.25 ALPACA SOVEREIGN BOARD (Q-OPS) AND DECISION HIERARCHY

**Effective:** 2026-04-15  

- **Persona:** Alpaca Sovereign Board — Q-Ops senior advisor for **Equities** on the Alpaca execution path. **Adversarial review** is mandatory for material Alpaca work (entries, exits, risk, promotions, telemetry that gates learning).  
- **Decision hierarchy (strict order, never invert):** **Safety** → **Correctness** → **Profitability** → **Operability** → **Velocity**.  
- **Compliance NO-GOs (authoritative detail in `.cursorrules`):** No new or modified discretionary **entry** logic in the **first or last 15 minutes** of regular U.S. equity session without documented **SIP (or equivalent) latency/staleness** checks and tests. No logic that can violate **PDT** or **Wash Sale** rules without explicit account/tax handling and operator acknowledgment.  
- **Quant evidence:** Changes to **trailing stops** or **take-profit / profit-target** levels require prior **MFE/MAE** (or bar-backed excursion) analysis on the current cohort; cite the artifact (e.g. `scripts/_tmp_mfe_mae_analysis.py` output / `config/overlays/mfe_mae_exit_overlay.json`). Exit tuning detail remains under **alpaca-exit-tuning-skill**.  
- **Cursor index:** `.cursor/ALPACA_GOVERNANCE_LAYER.md` lists agents, skills, commands, and governance violations.

---

## 0.3 FAILURE MODE RULE  
If any step fails, Cursor MUST:
1. Stop immediately  
2. Report the failure  
3. Diagnose the cause  
4. Fix the issue  
5. Restart the full workflow  

Cursor MUST NOT:
- continue after a failed step  
- ignore verification failures  
- assume success  

---

# 1. PURPOSE & SCOPE
This document defines:
- how Cursor MUST behave  
- how the trading bot MUST operate  
- how deployments MUST occur  
- how data MUST be sourced  
- how signals MUST be processed  
- how reports MUST be generated  

Cursor MUST treat this document as the **authoritative rule set** for all actions.

## 1.0 Alpaca V2 Harvester phase — hardened entry snapshots (current — 2026-04-08)

- **Phase / status:** **Alpaca V2 Harvester** with **hardened entry snapshots** — same paper / **V5.0 Passive Hunter** execution as before; **additive** telemetry now captures **full composite components at broker submit** in `logs/entry_snapshots.jsonl` so ML features are **100% dense at entry** (join on `entry_order_id`) instead of relying only on post-hoc `scoring_flow` time-window joins (~31% historical coverage on some hosts).
- **Milestones (Telegram):** **`scripts/telemetry_milestone_watcher.py`** advances **only** the **strict ML cohort Z count** — not gross `entries_and_exits` rows. Z means: after **`scripts/telemetry/alpaca_ml_flattener.py`** builds **`reports/Gemini/alpaca_ml_cohort_flat.csv`**, a row counts only if it passes **`ml.alpaca_cohort_train.load_and_filter`** (`strict_scoreflow`: finite **`realized_pnl_usd`**, all **`mlf_scoreflow_components_*`** + **`mlf_scoreflow_total_score`**) **and** entry time is on/after the watcher cutoff (**`max(TELEMETRY_MILESTONE_SINCE_DATE` 00:00 UTC, `STRICT_EPOCH_START`)**). Telegram thresholds: **50, 100, 150, 200, 250** (deduped keys in **`data/.milestone_state.json`**; lower milestone must send before higher). SPI CSV checks are **stdout diagnostic only** (no SPI Telegram gate).
- **Zero-tolerance SRE guard (cross-firm standard):** Same watcher (module **`telemetry/alpaca_zero_tolerance_tripwire.py`**) evaluates the **last 3 deduped** closes in **`logs/exit_attribution.jsonl`**. If any row lacks finite PnL (**`realized_pnl_usd` or `pnl`**), or **`entry_uw.earnings_proximity`** / **`entry_uw.sentiment_score`** are missing or non-finite, send immediately: **`🚨 [ALPACA DATA DEGRADATION] UW telemetry or PnL missing in recent stock trades. Pipeline leaking.`** Repeat alerts for the **same** failure detail are rate-limited by **`ZERO_TOLERANCE_ALERT_COOLDOWN_SEC`** (default 1800s); a **new** detail triggers immediately. Fewer than 3 deduped closes → skip (no false alarm on greenfield). **This tripwire does not inspect `MIN_EXEC_SCORE` or composite at entry** — lowering the score floor (e.g. to 1.6) does **not** by itself cause degradation alerts; false positives would only come from missing exit PnL or missing/non-finite `entry_uw` on recent closes.
- **Calibration gate / Harvester cohort (operational reality — 2026-04-09):** **Calibration gate failed:** ML retrain on the **~400-trade Harvester** strict cohort did **not** promote; **edge decay was driven by execution vetoes and portfolio constraints**, not by feature-engine failure (see forensic audits: blocked expectancy replay, 360 audit).
- **Score floor override (operational — 2026-04-09):** **`MIN_EXEC_SCORE`** was reduced from **3.2 → 1.6** on the droplet via systemd drop-in **`/etc/systemd/system/stock-bot.service.d/zzz-min-exec-score.conf`** (merged `Environment=MIN_EXEC_SCORE=1.6`), after blocked-trade replay showed **`expectancy_blocked:score_floor_breach`** cohort positive under the toy bar-replay assumptions. **Rollback:** remove or supersede that drop-in, `daemon-reload`, restart **`stock-bot.service`**.
- **Current primary volume blocker (operational — 2026-04-09):** **`displacement_blocked`** — portfolio **capacity saturation** and opportunity **displacement** dominate blocked volume vs score-floor vetoes at scale; expect more displacement decisions as lower scores fill slots (see **`main.py` `find_displacement_candidate`** — score-ranked tiers + age/P&L gates for legacy path).
- **Self-healing supervisor (Kraken port — skeleton):** **`src/self_healing_supervisor.py`** is a **non-wired** architectural stub toward Kraken-style quarantine / SAFE MODE (rate limits) / orphan cleanup. Integration into **`main.py`** / **`deploy_supervisor.py`** is **not** active until a follow-on change; use **`get_self_healing_supervisor()`** only from future call sites.
- **Canonical logs:** `logs/exit_attribution.jsonl` (closed trades), **`logs/entry_snapshots.jsonl`** (entry-time composite + components at submit), `logs/run.jsonl`, `logs/signal_context.jsonl`, plus warehouse/replay outputs under `reports/` and `replay/` per §1.2.
- **Orders log semantics (`logs/orders.jsonl`) — dashboard trade volume (2026-04-21):** A **trade** for **daily volume / Command Center charts** is defined strictly as a **unique broker `order_id` (or Alpaca `id`)** in a row that represents a **terminal filled** outcome (`status == filled`, or app actions `submit_limit_filled` / `submit_limit_final_filled`, or `close_position` with positive fill fields). **Never** use raw JSONL row counts, `filled_qty` spikes, or `type=fill` alone as a proxy for trade count — the log records **lifecycle updates, partial fills, and retries** that duplicate the same `order_id`. Dedupe with `len(set(order_ids))` per calendar day (America/New_York). Audit: **`scripts/audit/audit_orders_jsonl_daily_dedup.py`**.
- **SIP L1 OFI on entry snapshots (2026-04-15):** **`logs/entry_snapshots.jsonl`** rows written at broker submit may include **`ofi_l1_roll_60s_sum`** and **`ofi_l1_roll_300s_sum`** — rolling sums of Level-1 order-flow imbalance fed from the Alpaca MD WebSocket **`quotes`** channel (`T`=`q`). **`OFITracker`** lives in **`src/market_intelligence/ofi_tracker.py`**; ingest and subscribe wiring in **`src/alpaca/stream_manager.py`**. **Telemetry only for ML observation** (no entry gate, score, or sizing). Full channel math, paths, and policy: **§1.2 → “Real-time stock data (SIP WebSocket + REST hybrid)”** (subsection **L1 Order Flow Imbalance**).
- **Harvester exports (Gemini / board tooling):** `reports/Gemini/entries_and_exits.csv`, `reports/Gemini/signal_intelligence_spi.csv` — generated by **`scripts/extract_gemini_telemetry.py`** (Harvester-era rows only when extractor applies the strict epoch floor). **Flat ML cohort CSV:** `reports/Gemini/alpaca_ml_cohort_flat.csv` from the flattener (feeds Z counting).
- **Integrity + Telegram (parallel):** **`scripts/run_alpaca_telegram_integrity_cycle.py`** + **`config/alpaca_telegram_integrity.json`** — integrity-gated **100-checkpoint** and **250** milestone when `milestone_counting_basis` is **`integrity_armed`**; state under `state/alpaca_milestone_*.json`. See **Alpaca Telegram + data integrity cycle** below.
- **Not primary for this phase:** **Fast-Lane 25-trade shadow** cycles (historical / opt-in; see condensed DEPRECATED note under quantified governance).
- **Alpha 10 — live ML inference gate (Equities / Alpaca — 2026-04-14):** Optional **entry veto** using a **`RandomForestRegressor`** trained offline on strict cohort CSV target **`exit_mfe_pct`** (favorable move % at close, from **`exit_quality_metrics`** via flattener — not a live peek at the future at decision time; the **label** is historical-only; the **features** are entry-time `mlf_*` + intel/UW/scoreflow, with the same leakage guard as **`scripts/research/alpha_arena_trainer.py`**). **Artifacts:** bundle **`models/alpha10_rf_mfe.joblib`** (joblib dict: `model`, `feature_names`, `impute_medians`, meta). **Regenerate:** `python scripts/research/alpha_arena_trainer.py --export-alpha10 models/alpha10_rf_mfe.joblib` (requires `reports/Gemini/alpaca_ml_cohort_flat.csv` from **`scripts/telemetry/alpaca_ml_flattener.py`**). **Runtime:** **`src/ml/alpha10_inference.py`** (`predict_mfe`, `build_entry_telemetry_row`); gate **`src/alpha10_gate.py`**; wired in **`main.py`** immediately before **`submit_entry`**. **Policy:** if predicted MFE is **strictly below** **`ALPHA10_MIN_MFE_PCT`**, block with reason **`alpha10_mfe_too_low`**. **Code default** remains **0.2** (`src/alpha10_gate.py`); **Alpaca droplet (authorized forward-test, mid-day 2026-04-14):** **`ALPHA10_MIN_MFE_PCT=0.17`** in **`/root/stock-bot/.env`** — lowered to reflect **lower-volatility mid-day** telemetry and to **forward-test live entries** after the **`evaluate_exits` / `now_iso` shadowing** fix restored the exit engine (CSA: tuning is **environment-driven**, not a repo default change). **Fail-open:** any load/predict exception → **allow** the trade and log **`alpha10_gate` / `inference_fail_open`** at **CRITICAL** in **`logs/system_events.jsonl`**. **Env:** **`ALPHA10_GATE_ENABLED`** (default on), **`ALPHA10_MIN_MFE_PCT`**, **`ALPHA10_MODEL_PATH`** (optional path override). **Data-integrity context:** cohort quality still depends on **Broker Epoch Bridge** / strict **`trade_key`** alignment, the **~1000-trade** strict learning narrative for panel confidence, and **Truth Warehouse** + flattener freshness for labels — the gate does **not** substitute for **`DATA_READY`** or strict completeness.
- **Deployment (no `deploy_production.py` in repo):** Ship **`main`** + **`models/alpha10_rf_mfe.joblib`** to the droplet via **`git push`** then on **`alpaca`**: `cd /root/stock-bot && git fetch && git reset --hard origin/main` (or equivalent), then **`sudo systemctl restart stock-bot.service`** (and dashboard only if you run a separate dashboard unit). Ensure **`joblib`** / scikit-learn stack exists wherever **`python`** runs the bot.

### 1.0.2 Side-aware parity architecture + Shadow Vanguard (2026-04-24)

- **Systemic parity audit complete (Phases 1-3):** Core position math now centralizes long/short semantics in **`src/core/position_math.py`**; dynamic trailing stops have mirrored short-side ratchets; `main.py` exit math uses side-aware PnL, favorable extremes, stop hits, and `abs(qty)` for partial scale-outs. Broker reality now requires Alpaca short entries to be **`shortable` AND `easy_to_borrow`** unless explicit **`HTB_OVERRIDE`** is set; invalid buying power fails closed instead of falling back to synthetic capital. Default/touch execution pricing now uses **Buy/Cover = Ask** and **Sell/Short = Bid** via **`src/execution/touch_pricing.py`**, and slippage telemetry prefers decision-time touch references.
- **ML parity / train-serve contract:** Side-aware feature geometry is centralized in **`src/core/ml_feature_normalization.py`**. The flattener applies **`normalize_features_for_side()`** before committing ML rows, and live V2 inference applies the same function before DMatrix construction. The taxonomy is explicit: directional flow/sentiment/momentum/tide/gamma-style features invert for shorts; identity, time, size, volatility, categorical, join/source, and encoding fields pass through.
- **V2 Short AI quarantine:** The live V2 hard gate remains **quarantined for short/sell entries** until a promoted retrain proves profitable. Runtime reason code: **`v2_short_gate_quarantined_until_retrain`**. Long-side V2 behavior remains governed by `V2_LIVE_GATE_ENABLED` / `V2_LIVE_GATE_FAIL_OPEN`.
- **Shadow Vanguard / split-brain challenger:** `scripts/quant/train_vanguard_v2_agent.py --train-challenger-split-brain` trains experimental long and short challenger models without overwriting primary V2 artifacts. Runtime shadow scoring in **`telemetry/shadow_evaluator.py`** loads **`models/vanguard_challenger_long.json`** and **`models/vanguard_challenger_short.json`** and appends only to **`logs/shadow_executions.jsonl`** when Challenger approves a candidate the primary bot ignored. Shadow executions include simulated entry, TP, SL, direction, proba, and threshold; they **must not** flow into `logs/exit_attribution.jsonl`, orders, or the primary DATA_READY loop.
- **Operator workflow:** Monday review compares live closed trades in **`logs/exit_attribution.jsonl`** against shadow candidates in **`logs/shadow_executions.jsonl`**. Promotion requires positive out-of-sample shadow PF and board approval; shadow evidence is observational until promoted.

### 1.0.3 Paper ML gate — RTH EOD labels, UW×macro interaction matrix, shadow inference, ML milestones (2026-04-14)

- **RTH-capped unmanaged labels (`target_ret_eod_rth`):** Strict flattened cohorts may carry an **end-of-regular-session return** label for ML (RTH-capped, unmanaged / observational definition as exported in Gemini flat CSVs). Training and arena exports that target this column use the same **leakage and chronology filters** as **`scripts/research/alpha_arena_trainer.py`** (no exit-state features in the entry-only set; chrono-leak column names stripped). This label is **not** a live oracle at entry time; it is a **historical training target** joined after the trade closes.
- **Continuous feature interaction matrix (`mlx_*`):** **`scripts/telemetry/alpaca_ml_interaction_expand.py`** expands **`uw_gamma_skew`** and **`uw_tide_score`** against resolved macro drivers (**`mlf_scoreflow_total_score`**, first CSV header containing **`vxx_vxz_ratio`**, first containing **`futures_direction_delta`**), emitting product columns **`mlx_uw_gamma_skew_x_*`** and **`mlx_uw_tide_score_x_*`**. Expanded training surfaces include e.g. **`reports/Gemini/alpaca_ml_cohort_flat_UW_IX.csv`** (UW + interactions).
- **Shadow Brain bundle + on-the-fly inference:** **`scripts/research/alpha_arena_trainer.py --export-paper-ml-gate`** fits a **RandomForest** on the chosen strict cohort CSV and writes **`models/paper_ml_gate/alpaca_eod_model.joblib`** (gitignored binary) + **`models/paper_ml_gate/manifest.json`**. Runtime telemetry-only scoring is **`src/ml/alpaca_shadow_scorer.py`**: lazy-loads the joblib bundle, rebuilds **`mlf_*`** / **`uw_*`** from the live entry snapshot (scoreflow components, entry UW backfill, direction-intel embed), **recomputes all `mlx_*` products on the fly** to match training geometry, then **`predict`** — **no position sizing or entry veto** unless separately promoted. **`main.py`** calls the scorer only when **`ALPACA_SHADOW_ML_TELEMETRY_ONLY=1`** (or true/yes/on); it appends **`ml_expected_eod_return`** to **`logs/run.jsonl`** (`msg: alpaca_shadow_ml`) and **`submit_entry`** telemetry. Optional path override: **`ALPACA_PAPER_ML_GATE_MODEL`**.
- **Telegram milestone watcher (shadow ML row counts):** **`scripts/audit/alpaca_shadow_ml_milestone_watcher.py`** tails **`logs/run.jsonl`** (override: **`ALPACA_SHADOW_ML_LOG`**), persists append-offset state in **`data/.alpaca_shadow_ml_milestone_state.json`**, and sends Telegram at **N = 10, 100, and 250** deduped cumulative rows carrying finite **`ml_expected_eod_return`**. Systemd: **`deploy/systemd/alpaca-shadow-ml-milestone-watcher.service`** + **`.timer`** (periodic oneshot). This is **orthogonal** to **`scripts/telemetry_milestone_watcher.py`** strict **Z** milestones (50–250).

## 1.1 Alpaca strict learning era (CSA)

- **STRICT_EPOCH_START (UTC epoch seconds):** `1775581260` (`2026-04-07T17:01:00Z`). Canonical: `telemetry/alpaca_strict_completeness_gate.py` (`STRICT_EPOCH_START`). Reset for Alpaca V2 UW telemetry era; prior cohort excluded from strict counts.
- **Strict cohort (entry-based):** When `evaluate_completeness` is called with `open_ts_epoch` set, terminal closes are kept only if exit time `>= open_ts_epoch`. Among those, a trade is in the strict cohort only if the open instant parsed from `trade_id` (`open_<SYM>_<ISO8601>`) is also `>= open_ts_epoch`. Earlier opens are excluded (`PREERA_OPEN`) and do not count as `trades_seen` or incomplete.

### 1.1.1 Alpaca ML pipeline readiness — displacement IDs, telemetry economics, run log rotation (2026-04-15)

- **Displacement ID inheritance (strict truth chain):** `_emit_close_or_flip_strict_truth_chain` and related close paths were hardened so **`canonical_trade_id` / `trade_key` stay aligned with live position reality** — derived from **open instant + normalized side** (`build_trade_key`) and **`POSITION_METADATA`** merges, so **intent**, **`orders.jsonl`**, **`exit_intent`**, and **`exit_attribution.jsonl`** do not **split identities** across displacement closes, market fallback, or API-error retries. Displacement exits additionally call **`log_order`** with the same keys before **`log_exit_attribution`** so broker-order rows join the strict gate.
- **Telemetry logging and economics (ML-ready exits):** Silent **`except` / pass** on attribution and JSONL write paths in **`main.py`** (e.g. **`log_order`**, **`log_exit_attribution`**, **`close_position_*`**, strict-chain **`jsonl_write`**) were replaced or supplemented with **`log_system_event`** so SRE sees failures instead of silent telemetry loss. **`AlpacaExecutor._alpaca_order_fees_and_slippage_bps`** re-fetches the filled **`Order`** and records **commission / regulatory fee fields when present**, plus **limit vs fill slippage (bps)** when **`limit_price`** exists; values flow into **`log_exit_attribution`** → **`exit_attribution.jsonl`** (`fees_usd`, `exit_slippage_bps`) and into **`src/exit/exit_attribution.py`** unified **`emit_exit_attribution`** (no longer hard-zero fees when the row carries economics).
- **Run JSONL rotation (strict window retention):** Defaults in **`main.py`** — **`RUN_JSONL_ROTATE_MAX_BYTES`** default **500MB**, **`RUN_JSONL_ROTATE_BACKUP_COUNT`** default **30** — so stitched / strict daily **`run.jsonl`** history survives long enough for **`telemetry/alpaca_strict_completeness_gate.py`** cohort joins without premature truncation (overridable via environment).

### 1.1.2 Governance: Q-Ops Sovereign Board activation — Alpha 11 Institutional Alpha

**Effective:** 2026-04-14 (narrative reset; strict cohort is source of truth)

- **Mission reset:** Learning, board forensics, and promotion narratives default to the **high-fidelity strict-complete cohort** only — i.e. `telemetry/alpaca_strict_completeness_gate.evaluate_completeness(..., collect_complete_trade_ids=True)` **joined** to deduped closes in **`logs/exit_attribution.jsonl`**. Gross exports (e.g. wide `entries_and_exits` pulls) are **supporting** evidence, not the primary panel when they disagree with strict completeness.
- **Decision hierarchy (hardcoded, never invert):** **Safety** → **Correctness** → **Profitability** → **Operability** → **Velocity** (same order as **`.cursorrules`** `decision_hierarchy` and **§0.25**).
- **Personas (roles, not separate processes):**
  - **Q-Ops Sovereign Board (primary):** Adversarial **NO-GO until proven** stance on material Alpaca changes; owns compliance/session-edge/SIP evidence and strict-ledger correctness.
  - **AI Board (Section 2 charter):** Advisory synthesis; **cannot** override Safety/Correctness or compliance NO-GOs.
  - **Operator / CSA:** Execution of deploy, env, and acknowledged risk acceptance.
- **Alpha 11 — Institutional Alpha (UW lane):** Phase label for **institutional telemetry** wired into entries/exits: persisted **`entry_uw` / `exit_uw`**, composite confirmation (incl. **flow**, **gamma/GEX regime**, **dark pool** where enabled), plus **`uw_flow_cache`** / **`uw_flow_daemon`** HTTP refresh paths. **Unusual Whales MCP** (when connected in Cursor — e.g. **Market Tide**, **Spot GEX**, **Dark Pool** tools) is the **board / research overlay** for macro and cross-sectional context; it does **not** replace droplet **`exit_attribution`** rows or strict gate membership.
- **Cohort DNA audit (automated):** Run on the droplet with production logs — `PYTHONPATH=. python3 scripts/_tmp_alpha11_163_good_stuff_audit.py --root /root/stock-bot --out-json reports/alpha11_163_good_stuff_audit.json` — to summarize win/loss splits, **MFE%** cliffs from **`exit_quality_metrics`**, and attribution-family sums on the **strict-complete** set only.

## 1.2 Alpaca truth warehouse — DATA_READY baseline (do not drift)

**Purpose:** Before profitability narratives, board packets, or learning promotion, the repo defines a **single scripted path** that proves telemetry + broker data are **joinable** for PnL attribution (fees, slippage, signal snapshots, UW/blocked context). This section is the **contract**; detail and commands live in **`docs/DATA_READY_RUNBOOK.md`**.

### Canonical artifacts (code + docs)

| Item | Role |
|------|------|
| `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` | **Only** authoritative runner for warehouse **`DATA_READY: YES/NO`**, coverage %, blockers, PnL/board packets. Exit **2** when fail-closed. |
| `docs/DATA_READY_RUNBOOK.md` | Operator runbook: droplet command, env, strict gate vs warehouse, order of operations. |
| `main.py` (exit `log_signal_context`) | **New** closes should log **`mid` / `last`** (from executed prices when needed) so `signal_context.jsonl` joins stay honest. **Restart bot after deploy** (see below). |
| `src/exit/exit_attribution.py` | Canonical **`exit_ts`** and exit rows; mission prefers **`exit_ts`** over legacy timestamp fields. |

### Droplet — authoritative run (production logs)

```bash
cd /root/stock-bot
git pull origin main
# Keys: systemd loads /root/stock-bot/.env; manual runs should have APCA_* or ALPACA_KEY/ALPACA_SECRET in env
PYTHONPATH=. python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --root /root/stock-bot --days 90 --max-compute
```

- **Never** treat a one-off **scp** copy of the mission script as source of truth; droplet **`main`** must match GitHub or metrics drift without review.
- After **`main.py`** or exit-path changes: **`sudo systemctl restart stock-bot`** so new logging is live. If the supervisor/dashboard split leaves an orphan on port 5000, follow **Stale dashboard PIDs** later in this file (search within `MEMORY_BANK_ALPACA.md`).

### API keys (mission + broker REST)

The mission fills missing keys by merging **only unset** vars from, in order: repo **`/root/stock-bot/.env`**, then **`/root/.alpaca_env`**. It accepts **`ALPACA_KEY` / `ALPACA_SECRET`** as well as **`APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`**. If `.alpaca_env` is Telegram-only, Alpaca keys must come from **`.env`** (same as `stock-bot.service` **EnvironmentFile**).

### Real-time stock data (SIP WebSocket + REST hybrid) — April 2026 architecture

- **Unified production stream (live and paper):** Alpaca market-data WebSocket for **retail paper and live** uses the **same production** host. The URL must be **`wss://stream.data.alpaca.markets/v2/{feed}`** where `{feed}` is **`sip`** or **`iex`** (per subscription / entitlements). **Do not** point paper trading at a separate “sandbox” market-data host for stream auth.
- **The sandbox stream trap:** **`stream.data.sandbox.alpaca.markets`** is **not** valid for typical retail paper accounts used with **`paper-api.alpaca.markets`**. Using it causes a **`402 Auth Failed`** loop on the WebSocket. Code: `src/alpaca/stream_feed.py`, `src/alpaca/stream_manager.py` — production stream host unless an explicit opt-in (e.g. **`ALPACA_MARKET_DATA_STREAM_SANDBOX=1`**) is documented for special cases.
- **Entitlements vs REST:** Alpaca **trading** REST can succeed while **stream** auth fails if **market data streaming** is not enabled in the Alpaca dashboard for that **key set**, or the account lacks the right data subscription for the chosen **`sip` / `iex`** feed.
- **Implementation:** `AlpacaStreamManager` / stream feed use the **unified** production URL above with the same **key/secret** as REST (plus documented WS handshake headers where applicable). Docs: [Real-time Stock Data](https://docs.alpaca.markets/docs/real-time-stock-pricing-data).
- **Channels:** Subscribes to **`trades`** (`T`=`t`), **`bars`** (minute aggregates, `T`=`b` / `u` for updated bars), and **`quotes`** (`T`=`q`, NBBO: **`bp` / `ap` / `bs` / `as`** per Alpaca streaming stock docs). Legacy “AM” naming maps to the **`bars`** channel.
- **L1 Order Flow Imbalance (OFI) — telemetry only (2026-04-15):** **`src/market_intelligence/ofi_tracker.py`** defines **`OFITracker`**, a thread-safe Level-1 OFI engine. **`src/alpaca/stream_manager.py`** (`AlpacaStreamManager`) routes each SIP **`quotes`** message into **`ofi_tracker.on_quote(...)`**, which applies the standard bid/ask price-and-size event decomposition (bid event **e_t** vs ask event **f_t**, increment **OFI_t = e_t − f_t**) and maintains **rolling sums of per-tick OFI** over **60 seconds** and **300 seconds** per symbol (windows keyed on ingest monotonic time). At broker **`submit_entry`**, **`main.py`** reads those rolling sums for the entry symbol and stashes **`ofi_l1_roll_60s_sum`** and **`ofi_l1_roll_300s_sum`** on **`AlpacaExecutor._pending_entry_snapshot`**; **`telemetry/entry_snapshot_logger.py`** copies them into **`logs/entry_snapshots.jsonl`** on successful order submit (same row as **`msg: entry_snapshot`** / composite components). **Policy:** this path is **TELEMETRY ONLY** for ML observation and cohort enrichment — it **does not** gate, score, size, or otherwise alter live execution; no Alpha gate or composite hook consumes these fields until explicitly promoted.
- **Symbol universe (whitelist):** Union of **open positions**, **`uw_flow_cache`** keys (non-`_`), **`SPY`**, and **`ALPACA_STREAM_EXTRA_SYMBOLS`** (comma-separated), capped by **`ALPACA_STREAM_MAX_SYMBOLS`** (default **200**, max **500**). Does **not** bypass strict learning-era rules elsewhere (stream is market-data only).
- **Bar reads:** `main.fetch_bars_safe` tries the in-memory **`PriceCache`** first for **`1Min`** when the stream is enabled and the latest bar update is within **`ALPACA_STREAM_BAR_MAX_AGE_SEC`** (default **60**); otherwise **`REST.get_bars`**. If both fail, logs **`CRITICAL_DATA_STALE`** to **`logs/system_events.jsonl`** (subsystem **`data`**).
- **Env:** **`ALPACA_STREAM_ENABLED`** default **`1`** (set **`0`** to disable). Optional **`ALPACA_DATA_STREAM_URL`** override. Dependency: **`websockets`** pinned **`>=9,<11`** with **`alpaca-trade-api`** (see **`requirements.txt`**).
- **After deploy:** `pip install -r requirements.txt` (or `pip install websockets`) on the droplet venv, then **`sudo systemctl restart stock-bot`**. Look for **`alpaca_stream` / `sip_started`** in run logs.

### Gates and defaults (paper vs live)

- **Coverage windows (override via env):** `ALPACA_TRUTH_CONTEXT_WINDOW_SEC` and `ALPACA_TRUTH_EXECUTION_WINDOW_SEC` default **7200** seconds (exit ↔ signal context, exit ↔ order/fill proximity).
- **Slippage / signal-snapshot gates:** `ALPACA_TRUTH_THRESHOLD_SLIPPAGE`, `ALPACA_TRUTH_THRESHOLD_SIGNAL_SNAP`. If unset: **90%** when **`ALPACA_BASE_URL`** is **paper**, else **95%** (stricter live-shaped runs).
- **Broker fetch:** `ALPACA_TRUTH_FETCH_BROKER_ORDERS=0` disables REST order pull (debug only).

### External data paths the mission relies on

- **Corporate actions:** `https://data.alpaca.markets/v1/corporate-actions` (not deprecated broker URLs that 404).
- **Broker orders:** Alpaca REST `list_orders` with safe pagination (dict-shaped rows tolerated); timestamps from **`filled_at` / `submitted_at` / `created_at`**; paper fills treat **explicit $0** commission as fee-computable.

### Interpretation — what DATA_READY does *not* mean

- **`DATA_READY: YES` is not the same as `LEARNING_STATUS: READY`.** `telemetry/alpaca_strict_completeness_gate.py` (`evaluate_completeness`) can still return **`BLOCKED`** (e.g. `incomplete_trade_chain`, `live_entry_decision_made_missing_or_blocked`) while the warehouse is green. Run both when the question is “promotion / strict panel” vs “PnL packet join coverage.” **Vacuous strict window:** zero terminal closes in the evaluated window does **not** set `BLOCKED` or `NO_POST_DEPLOY_PROOF_YET`; `LEARNING_STATUS` stays **`ARMED`** (optional `learning_inform_note` + `STRICT_WINDOW_ZERO_CLOSES` in gate JSON).
- **Execution join at 100% on paper** can be achieved in part via documented fallbacks (e.g. **economic closure** when order stream alignment is weak). That supports **attribution math**, not a claim that every exit row matched a broker **`order_id`** in logs. Board and CSA language must stay precise.
- **Baseline for improvement:** Record the **timestamped** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` and `replay/alpaca_truth_warehouse_*` dirs from the run you treat as baseline; compare future runs to those filenames and %s.

### Outputs (timestamped tags)

- `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md`, `ALPACA_TRUTH_WAREHOUSE_BLOCKERS_*.md` (when NO), `ALPACA_PNL_AUDIT_PACKET_*.md`, `ALPACA_BOARD_DECISION_PACKET_*.md`
- `replay/alpaca_truth_warehouse_<TS>/`, `replay/alpaca_execution_truth_<TS>/`, manifest under `replay/`

**Other scripts** (`scripts/run_alpaca_data_ready_on_droplet.py`, `.sh`, etc.) may exist for legacy or auxiliary checks; **warehouse pass/fail for PnL truth** is defined by the **mission** above and the runbook.

## 1.3 Canonical PnL audit lineage (field → emitter → persistence → join)

**Purpose:** Massive PnL reviews require a **stable contract** for where each audit field is emitted, stored, and joined. This is separate from **DATA_READY** (warehouse mission) but must stay **consistent** with it.

### Canonical docs (committed)

| Path | Role |
|------|------|
| `docs/pnl_audit/REQUIRED_FIELDS.md` | Human canonical list of required fields by entity (A–G). |
| `docs/pnl_audit/LINEAGE_MATRIX.json` | **Machine contract:** one row per field with emitter path, persistence, join keys, failure notes. |
| `docs/pnl_audit/LINEAGE_MATRIX.md` | Human table + per-field detail (generated from JSON). |
| `docs/pnl_audit/FIELD_ADDITION_PLAYBOOK.md` | How to add/fix a field without strategy changes. |
| `docs/pnl_audit/ADVERSARIAL_FINDINGS.md` | Standing red-team traps (dual sources, join fragility, fees). |

### Governance rules

- **`LINEAGE_MATRIX.json` is the contract.** Any telemetry or persistence change that affects PnL audit fields **must** update the matrix (and regenerate `LINEAGE_MATRIX.md` if the table changes).
- **Broker vs local sources are explicit** in each matrix row (`source_of_truth`, `persistence_location`). **Broker `order.id`** is authoritative for execution joins when local `logs/orders.jsonl` omits `order_id`.
- **Map integrity check (no penalties):**  
  `python3 scripts/audit/alpaca_pnl_lineage_map_check.py`  
  With evidence:  
  `python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence`
- **Full evidence pack (context + SRE verification + copies):**  
  `python3 scripts/audit/alpaca_pnl_lineage_evidence_bundle.py`  
  Writes under `reports/daily/<ET-date>/evidence/` (see `ALPACA_PNL_LINEAGE_*` filenames).

---

# 2. PROJECT ARCHITECTURE OVERVIEW

## 2.1 ENTRY POINTS (PRIMARY)
- `deploy_supervisor.py` — orchestrates all services  
- `main.py` — core trading engine  
- `uw_flow_daemon.py` — UW API ingestion  
- `dashboard.py` — monitoring dashboard  
- `heartbeat_keeper.py` — health monitor  

## 2.2 SECONDARY MODULES
- `startup_contract_check.py`  
- `position_reconciliation_loop.py`  
- `risk_management.py`  
- `momentum_ignition_filter.py`  
- `comprehensive_learning_scheduler.py`  
- `v2_nightly_orchestration_with_auto_promotion.py`  

## 2.2.1 STRATEGY ARCHITECTURE (UPDATED - 2026-04-08)
- **equity (Alpaca V2 Harvester primary)** — UW-driven equity strategy. `strategies/equity_strategy.py`. Live/paper telemetry uses `strategy_id=equity` where recorded.
- **wheel (optional, in repo)** — Options wheel path: `strategies/wheel_strategy.py`, universe YAML under `config/universe_wheel*.yaml`, toggles in `config/strategies.yaml`. **Harvester milestone and strict-era narratives default to equity paper**; wheel may be disabled or idle on a given host — confirm `strategies.yaml` and open positions, not this doc alone.
- Single droplet, single Alpaca account class per deploy, single UW ingestion, single EOD review where applicable.
- Config: `config/strategies.yaml` (primary). **Operational truth** = files in repo + **`config/registry.py`** + section **1.2** warehouse baseline.

## 2.2.2 STRUCTURAL UPGRADE MODULES (ADDITIVE - 2026-01-20)
- `structural_intelligence/market_context_v2.py` — market context snapshot (premarket/overnight + vol term proxy)
- `structural_intelligence/symbol_risk_features.py` — realized vol + beta feature store (per-symbol)
- `structural_intelligence/regime_posture_v2.py` — regime label + posture (log-only context layer)
- (REMOVED) Shadow A/B modules — shadow trading is not supported in v2-only mode.

## 2.3 CONFIG FILES
- `config/registry.py` — **single source of truth**  
- `config/theme_risk.json`  
- `config/execution_router.json`  
- `config/startup_safety_suite_v2.json`  
- `config/uw_signal_contracts.py`  

## 2.4 RUNTIME DIRECTORIES
- `logs/`  
- `state/`  
- `data/`  
- `signals/`  
- `structural_intelligence/`  
- `learning/`  
- `telemetry/`  
- `xai/`  
- `self_healing/`  

## 2.5 CANONICAL PATHS AND REPO CLEANUP (ADDITIVE - 2026-02-27)
- Repo canonical layout and report paths: see **`reports/repo_audit/CANONICAL_REPO_STRUCTURE.md`** and **`reports/repo_audit/CANONICAL_PATHS.json`**.
- Dashboard endpoint → data map: **`reports/DASHBOARD_ENDPOINT_MAP.md`**.
- Governance, replay, and effectiveness paths: **`reports/repo_audit/CANONICAL_GOVERNANCE_PATHS.md`**, **`reports/repo_audit/CANONICAL_REPLAY_PATHS.md`**.
- Legacy one-off scripts: **`README_DEPRECATED_SCRIPTS.md`** (production entry points listed there and in section 2.1).

---

# 3. GLOBAL RULES (MUST / MUST NOT)

## 3.1 ROOT CAUSE RULE
Cursor MUST:
- fix underlying issues  
- investigate missing data  
- validate assumptions  
- ensure real signals flow end‑to‑end  

Cursor MUST NOT:
- mask errors  
- clear data to hide failures  
- create empty structures to fake health  
- bypass validation  

---

## 3.2 DATA SOURCE RULE (UPDATED)
**Reports MUST always use production data from the droplet.**

Cursor MUST:
- use `ReportDataFetcher`  
- validate data source  
- reject reports with invalid or empty data  
- include data source metadata  

Cursor MUST NOT:
- read local logs  
- read local state files  
- assume local data is production data  

---

## 3.3 SAFETY RULES
Cursor MUST:
- enforce trading arm checks  
- enforce LIVE mode acknowledgment  
- validate notional, price, and buying power  
- prevent division by zero  
- clamp invalid ranges  

Cursor MUST NOT:
- bypass safety checks  
- modify safety logic without explicit instruction  

---

## 3.4 TRUTH GATE (ALPACA / DROPLET DATA)
Cursor and all Alpaca actions MUST treat droplet execution and canonical data as the Truth Gate:
- All reports and conclusions require droplet execution and canonical logs/state; no local-only conclusions.
- Missing required data (e.g. exit_attribution, master_trade_log) = HARD FAILURE; do not proceed.
- Join coverage below threshold (e.g. direction_readiness, exit-join health) = HARD FAILURE when asserted as readiness.
- Schema mismatch or unversioned required fields = HARD FAILURE.
- Only frozen artifacts (e.g. EOD bundle, frozen trade sets) may be used for learning or tuning.

<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->
## Alpaca attribution truth contract (canonical)

**Governance (CSA):** This subsection is canonical Alpaca attribution material. **Drift** between live emitters, sinks, and this contract is a **governance incident** and must be triaged like a production data-integrity breach.

### Canonical artifact paths (board / audit)
- `reports/ALPACA_BLOCKER_CLOSURE_PROOF_20260325_0112.md` — blocker closure checklist and compile/git evidence.
- `reports/ALPACA_OFFLINE_FULL_DATA_AUDIT_20260325_0112.md` — CSA offline full data-path audit (**verdict A required** before profit-contributor / promotion claims that depend on attribution readiness).
- `reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2310.md` — Alpaca REST + FILL payload wiring proof.

Promote newer dated filenames when they supersede the above; keep the same report family names.

### Invariants (non-negotiable)
1. **Deterministic join keys** on decision and execution records: `decision_event_id`, `canonical_trade_id`, `symbol_normalized`, `time_bucket_id` (rule: `300s|<utc_epoch_floor>` — `telemetry/attribution_emit_keys.py`).
2. **Entry/exit snapshot parity:** `telemetry/attribution_feature_snapshot.py` — `build_shared_feature_snapshot` (entry/blocked) and `build_exit_snapshot_from_metadata` (exit); persisted `entry_market_context` and `entry_regime_posture` on `StateFiles.POSITION_METADATA` via `main.py` / `AlpacaExecutor._persist_position_metadata`.
3. **UW decomposition + provenance:** `apply_uw_decomposition_fields` adds component proxies plus `uw_asof_ts`, `uw_ingest_ts`, `uw_staleness_seconds`, `uw_missing_reason`; `uw_composite_score_derived` is **derived only** (no composite-only logging as the sole signal).
4. **Economics explicit:** `main.py` `log_order` → `telemetry/attribution_emit_keys.attach_paper_economics_defaults` — `fee_excluded_reason` and/or `fee_amount`; `slippage_bps` + `slippage_ref_price_type` vs `slippage_excluded_reason`; decision reference mid stored as `decision_slippage_ref_mid`. **No silent zero fees** — exclusions must be explicit.
5. **Append-only sinks:** `main.py` `jsonl_write`, `telemetry/signal_context_logger.py`; retention/rotation — `docs/DATA_RETENTION_POLICY.md`.
6. **CSA offline audit:** run `scripts/alpaca_offline_full_data_audit.py` (Linux/droplet); **verdict A** before offline profit-contributor narratives that depend on attribution readiness.
7. **Operational rule:** After changes to `main.py` or `telemetry/*` emitters, **restart `stock-bot.service`** so the process loads new code (no hot reload assumption).

### TRUE data path map (Alpaca; module/file names)
| Stage | Emitter / module | Sink path |
|-------|------------------|-----------|
| Trade intent (entered/blocked) | `main.py` `_emit_trade_intent`, `_emit_trade_intent_blocked` | `logs/run.jsonl` (`event_type=trade_intent`) |
| Exit intent | `main.py` `_emit_exit_intent` | `logs/run.jsonl` (`event_type=exit_intent`) |
| Signal context (enter/blocked/exit) | `telemetry/signal_context_logger.py` `log_signal_context` | **`logs/signal_context.jsonl` — DEPRECATED / dead-pipe for ML** (may be empty on production hosts; do **not** depend on it for Harvester or XGBoost features) |
| Orders / execution | `main.py` `log_order` | `logs/orders.jsonl` |
| **Entry ML snapshot (submit-time)** | `main.py` `AlpacaExecutor._submit_order_guarded` → `telemetry/entry_snapshot_logger.try_append_entry_snapshot` | **`logs/entry_snapshots.jsonl`** (`msg=entry_snapshot`; join `order_id` ↔ `exit_attribution.entry_order_id`) |
| Blocked would-have | `main.py` `log_blocked_trade` | `state/blocked_trades.jsonl` |
| UW ingestion | `uw_flow_daemon.py` | `data/uw_flow_cache.json`, `data/uw_flow_cache.log.jsonl`; optional mirror `logs/uw_daemon.jsonl` |
| UW → decision snapshot | Scoring in `main.py` + `telemetry/attribution_feature_snapshot.py` | Join: `symbol_normalized` + `time_bucket_id` (same bucket rule as attribution keys) |
| Position state | `main.py` `AlpacaExecutor.mark_open`, `_persist_position_metadata` | `state/position_metadata.json` (`config.registry.StateFiles.POSITION_METADATA`) |
| Exit attribution v2 | `main.py` `log_exit_attribution` → `src/exit/exit_attribution.py` `append_exit_attribution` | `logs/exit_attribution.jsonl` |
| Truth / warehouse (read-only extractors) | e.g. `scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py` | `reports/ALPACA_TRUTH_*`, `ALPACA_EXECUTION_*`, etc. |

### Machine learning telemetry — denormalized canonical (Harvester)

**Adopted architecture (2026-04-08):** Alpaca ML training and offline analytics use **denormalized payloads**, not a monolithic per-trade log and **not** `signal_context.jsonl`.

1. **Primary sink — `logs/exit_attribution.jsonl`:** Each closed-trade row carries rich JSON suitable for flattening: e.g. **`entry_uw`**, **`exit_uw`**, **`v2_exit_components`**, **`direction_intel_embed`** (entry/exit intel snapshots and deltas), **`entry_regime`**, **`composite_version`**, **`variant_id`**, quality metrics, and join keys (`trade_id`, `trade_key`, `canonical_trade_id`, **`entry_order_id`**). This is the **canonical source of ML-ready trade facts** for the Harvester era when relational `signal_context` is absent.

2. **Entry composite at submit — `logs/entry_snapshots.jsonl` (PRIMARY for entry-time UW components):** On each successful broker submit from the entry path, the bot appends **`msg=entry_snapshot`** with **`timestamp_utc`**, **`symbol`**, **`order_id`**, **`client_order_id`**, **`composite_score`**, and the full **`components`** dict (same shape as `composite_meta.components`: flow, dark_pool, iv_skew, etc.). **`scripts/telemetry/alpaca_ml_flattener.py`** joins **`order_id`** ↔ **`exit_attribution.entry_order_id`** first; populated rows set **`mlf_ml_feature_source=entry_snapshot`** and **`mlf_scoreflow_join_tier=entry_snapshot`**, and fill **`mlf_scoreflow_total_score`** / **`mlf_scoreflow_components_*`** from the snapshot so existing CSV consumers keep stable column names.

3. **Fallback sink — `logs/scoring_flow.jsonl`:** Time-series **`composite_calculated`** lines (per symbol) hold **UW/composite component breakdown**. Used only when **no** matching row exists in **`entry_snapshots.jsonl`** for that trade’s **`entry_order_id`**.

4. **Wide join policy (scoring_flow → training CSV, fallback only):** When no entry snapshot matches, ML feature extraction uses a **4-hour “Last Known Score” lookback** as the **preferred** match: the **most recent** `composite_calculated` for the trade symbol with **`ts <= entry_anchor`** and **`entry_anchor - ts <= 14400` seconds** (override via `--scoreflow-lookback-sec`). If **no** row falls in that window but an **older** composite exists with **`ts <= entry_anchor`**, the flattener **falls back** to it by default (disable with `--no-scoreflow-unbounded-fallback`); **`mlf_scoreflow_join_tier`** is **`4h_window`**, **`unbounded_fallback`**, or **`none`**. **Entry anchor** resolves in order: `entry_ts` on the exit row → `entry_timestamp` → open instant parsed from `trade_id` (`open_<SYM>_<ISO>`). Join key prefers **`symbol_normalized`** then **`symbol`**. Duplicate timestamps in `scoring_flow` for the same symbol are **coalesced** (last line wins). Exported fields include **`mlf_scoreflow_total_score`**, **`mlf_scoreflow_components_*`**, **`mlf_scoreflow_snapshot_ts_epoch`**, **`mlf_scoreflow_snapshot_age_sec`**, **`mlf_scoreflow_lookback_sec_applied`**.

5. **Harvester phase:** **ACTIVE.** Cohort filtering for strict-era learning uses **`STRICT_EPOCH_START`** in `telemetry/alpaca_strict_completeness_gate.py` (open time from `trade_id` / entry instant). **100-trade milestone data** and subsequent closes in that era remain **intact inside these payloads**; emptiness of `signal_context.jsonl` does **not** imply loss of ML features for that cohort. **Truth-warehouse / Telegram DATA_READY (2026-04-13):** **`DATA_READY: YES`** after fixing the **blocked-boundary classifier** in `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` (score_snapshot `gates.*` booleans and `uw_deferred` were previously mis-read, yielding **0%** blocked-boundary coverage); droplet audit achieved **96.57%** blocked/near-miss bucket coverage with execution/fees/slippage joins still at **100%**. Score snapshots now emit **`time_bucket_id`** for deterministic 5m joins (`score_snapshot_writer.py`).

6. **Training export:** **`scripts/telemetry/alpaca_ml_flattener.py`** writes **`reports/Gemini/alpaca_ml_cohort_flat.csv`** — flattened `mlf_*` feature columns plus base trade fields for XGBoost and similar tools. The script prints **`entry_snapshot_join_pct`**, **`scoreflow_snapshot_coverage_pct`**, and **`scoreflow_total_score_populated_pct`** after each run for SRE verification. **`--no-entry-snapshots`** forces legacy scoring_flow-only behavior.

7. **Invariant (ML):** Do not assert “missing `signal_context`” as a missing-feature incident for Harvester without checking **`exit_attribution`** embeds, **`entry_snapshots`** join coverage, and **`scoring_flow`** fallback coverage separately.
<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->


---

# 4. SIGNAL INTEGRITY CONTRACT

## 4.1 NORMALIZATION RULES
Cursor MUST:
- extract all metadata fields  
- validate structure before processing  
- ensure no missing keys  

Required fields:
- `flow_conv`  
- `flow_magnitude`  
- `signal_type`  
- `direction`  
- `flow_type`  

---

## 4.2 CLUSTERING RULES
Cursor MUST:
- preserve `signal_type`  
- preserve metadata  
- ensure clusters contain real data  

Cursor MUST NOT:
- drop metadata  
- create empty clusters  

---

## 4.3 GATE EVENT RULES
Cursor MUST:
- include `gate_type`  
- include `signal_type`  
- include full context  

Cursor MUST NOT:
- log "unknown" unless truly unknown  

---

## 4.4 COMPOSITE SCORING RULES

See Section 7 (Scoring Pipeline Contract) for detailed scoring rules.

---

# 7. SCORING PIPELINE CONTRACT (SYSTEM HARDENING - 2026-01-10)

## 7.1 SCORING PIPELINE FIXES (PRIORITY 1-4)

### Priority 1: Freshness Decay Configuration
- **Location:** `uw_enrichment_v2.py:234`
- **Constant:** `DECAY_MINUTES = 180` (changed from 45)
- **Rationale:** Reduces score decay from 50% after 45min to 50% after 180min
- **Impact:** Prevents aggressive score reduction for stale data
- **Reference:** See `SIGNAL_SCORE_PIPELINE_AUDIT.md` for full analysis

### Priority 2: Flow Conviction Default
- **Location:** `uw_composite_v2.py:552`
- **Change:** Default `flow_conv` from `0.0` to `0.5` (neutral)
- **Rationale:** Ensures primary component (weight 2.4) contributes 1.2 instead of 0.0 when conviction is missing
- **Impact:** Prevents loss of primary scoring component

### Priority 3: Core Features Always Computed
- **Location:** `main.py:7390-7434`
- **Requirement:** `iv_term_skew`, `smile_slope`, `event_alignment` must always exist
- **Fallback:** If computation fails, default to `0.0` (neutral)
- **Telemetry:** Logs missing core features for monitoring
- **Impact:** Prevents 3 components from contributing 0.0 (potential 1.35 points lost)

### Priority 4: Expanded Intel Neutral Defaults
- **Location:** `uw_composite_v2.py` component functions
- **Requirement:** All V3 expanded components return neutral default (0.2x weight) instead of 0.0 when data missing
- **Components:** congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, oi_change, etf_flow, squeeze_score
- **Impact:** Prevents 11 components from contributing 0.0 (potential 4.0 points lost)

## 7.2 SCORE CALCULATION FORMULA

```
composite_raw = (
    flow_component +           # 2.4 * flow_conv (defaults to 0.5 if missing)
    dp_component +             # 1.3 * dp_strength
    insider_component +        # 0.5 * (0.25-0.75)
    iv_component +             # 0.6 * abs(iv_skew) (defaults to 0.0 if missing)
    smile_component +          # 0.35 * abs(smile_slope) (defaults to 0.0 if missing)
    whale_score +              # 0.7 * avg_conv (if detected)
    event_component +          # 0.4 * event_align (defaults to 0.0 if missing)
    motif_bonus +              # 0.6 * motif_strength
    toxicity_component +       # -0.9 * (toxicity - 0.5) (if > 0.5)
    regime_component +         # 0.3 * (regime_factor - 1.0) * 2.0
    # V3 expanded (11 components, neutral default 0.2x weight if missing)
    congress_component +       # 0.9 * strength (or 0.18 if missing)
    shorts_component +         # 0.7 * strength (or 0.14 if missing)
    inst_component +          # 0.5 * strength (or 0.10 if missing)
    tide_component +           # 0.4 * strength (or 0.08 if missing)
    calendar_component +       # 0.45 * strength (or 0.09 if missing)
    greeks_gamma_component +   # 0.4 * strength (or 0.08 if missing)
    ftd_pressure_component +   # 0.3 * strength (or 0.06 if missing)
    iv_rank_component +        # 0.2 * strength (or 0.04 if missing)
    oi_change_component +      # 0.35 * strength (or 0.07 if missing)
    etf_flow_component +       # 0.3 * strength (or 0.06 if missing)
    squeeze_score_component    # 0.2 * strength (or 0.04 if missing)
)

composite_score = composite_raw * freshness  # freshness decays over 180min (not 45min)
composite_score += whale_conviction_boost   # +0.5 if whale detected
composite_score = max(0.0, min(8.0, composite_score))  # Clamp to 0-8
```

## 7.3 SCORE TELEMETRY REQUIREMENTS

- **Module:** `telemetry/score_telemetry.py`
- **State File:** `state/score_telemetry.json`
- **Recording:** After each composite score calculation in `main.py:7565`
- **Tracks:**
  - Score distribution (min, max, mean, median, percentiles, histogram)
  - Component contributions (avg, zero percentage)
  - Missing intel counts (per component)
  - Defaulted conviction count
  - Decay factor distribution
  - Neutral defaults count (per component)
  - Core features missing count

## 7.4 SCORE MONITORING DASHBOARD

- **Endpoints:**
  - `/api/scores/distribution` - Score distribution statistics
  - `/api/scores/components` - Component health statistics
  - `/api/scores/telemetry` - Complete telemetry summary
- **Panel:** "Score Health" (to be added to dashboard UI)
- **Displays:**
  - Histogram of scores
  - Component contribution breakdown
  - Missing intel counts
  - Decay factor distribution
  - % of trades using default conviction
  - % of trades using neutral-expanded-intel defaults

## 7.5 ADAPTIVE WEIGHTS & STAGNATION ALERTS (2026-01-10)

### Current Protection Status

**✅ Protected Component:**
- `options_flow` - Hardcoded to always return default weight (2.4) in `uw_composite_v2.py:83-85`
- **Reason:** Adaptive system previously learned bad weight (0.612 instead of 2.4), killing all scores

**⚠️ Unprotected Components:**
- All other 21 components can have adaptive multipliers applied (0.25x to 2.5x)
- If multiple components are reduced to 0.25x, this can cause significant score reduction

### Stagnation Alert Causes

**Common Causes:**
1. **Adaptive weights reducing multiple components** - If 5+ components reduced to 0.25x → 3-4 point score reduction
2. **Zero score threshold** - 20+ consecutive signals with score=0.00 triggers alert
3. **Funnel stagnation** - >50 alerts but 0 trades in 30min during RISK_ON regimes

### Diagnostic Steps

**When stagnation alerts occur:**
1. Check adaptive weight state: `state/signal_weights.json`
2. Verify component multipliers: Run `comprehensive_score_diagnostic.py`
3. Review weight reductions: Components with multiplier < 1.0
4. Calculate impact: `effective_weight = base_weight * multiplier`

### Recommended Actions

**Immediate:**
- Review `SCORE_STAGNATION_ANALYSIS.md` for full analysis
- Run diagnostics to check current weight state
- Verify if weights need reset or protection

**Long-term:**
- Consider adding safety floors for critical components (similar to `options_flow`)
- Review adaptive learning data to ensure weights learned from correct behavior
- Add component contribution monitoring to track weight impacts

---

## 7.6 STRUCTURAL UPGRADE: COMPOSITE V2 + SHADOW A/B (2026-01-20) — DEPRECATED for Alpaca V2 Harvester

**Operational note (2026-04-08):** Composite/shadow weight experiments below are **not** on the Harvester critical path. Alpaca paper collection uses **V5.0 Passive Hunter** + strict-era telemetry (§1.0, §1.1). Keep this section for historical scoring/structural context only.

### Composite versioning (contract)
- **v2 is the only composite**:
  - The system exposes a single composite scorer in `uw_composite_v2.py` (v2-only).
  - v1 composite functions and version flags are removed and MUST NOT be reintroduced.

### Feature inputs added (log-only until promotion)
- Per-symbol risk features attached in enrichment:
  - `realized_vol_5d`, `realized_vol_20d`, `beta_vs_spy`
- Market context snapshot:
  - `state/market_context_v2.json`
- Regime/posture snapshot:
  - `state/regime_posture_state.json`

### Trading mode (contract)
- Trading is **paper-only** for now.
- The engine MUST refuse entries if `ALPACA_BASE_URL` is not the Alpaca paper endpoint.

### Daily review
- Daily review artifacts are derived from **v2 live paper logs/state only** (no shadow comparisons).

---

## 7.7 COMPOSITE V2 WEIGHT TUNING (SHADOW-ONLY) (2026-01-20)

### Contract (do not break)
- **v2-only**: weights affect the only engine.
- **Paper-only**: tuning is validated in paper trading; no live deployment without explicit approval.
- **Logging preserved**: tuning never bypasses safety/guards; observability remains append-only.

### Config-driven weights
- **Location**: `config/registry.py` → `COMPOSITE_WEIGHTS_V2`
- **Versioning**: `COMPOSITE_WEIGHTS_V2["version"]` (e.g., `2026-01-20_wt1`)
- **New knobs (v2-only adjustment layer)**:
  - vol/beta: `vol_*`, `beta_*`, `*_bonus_max`, `low_vol_penalty_*`
  - UW strength: `uw_*`, `uw_bonus_max` (uses conviction + trade_count; no reward when trade_count==0)
  - premarket alignment: `premarket_align_bonus`, `premarket_misalign_penalty` (SPY/QQQ overnight proxy)
  - regime/posture: `regime_align_bonus`, `regime_misalign_penalty`, `posture_conf_strong`
  - alignment dampening: `misalign_dampen`, `neutral_dampen`

### Score-shaping (optional, OFF by default)
- **Gate**: only applied when explicitly enabled (env/config), and MUST be regression-covered.
- **Params**: `shape_*` keys in `COMPOSITE_WEIGHTS_V2`
- **Purpose**: nonlinear volatility reward, extra regime-aligned boost, and weak-UW penalties under heavy print counts.

### Observability additions (additive)
- `logs/system_events.jsonl`:
  - `subsystem="scoring" event_type="composite_version_used"` includes `v2_weights_version`

### Diagnostics + reports (droplet-source-of-truth)
- **Weight impact**:
  - generator: `diagnostics/weight_impact_report.py` (runs on droplet)
  - runner: `reports/_daily_review_tools/run_droplet_weight_impact.py`
  - output: `reports/WEIGHT_IMPACT_YYYY-MM-DD.md`
- **Weight tuning summary**:
  - generator: `reports/_daily_review_tools/droplet_weight_tuning_summary_payload.py` (runs on droplet)
  - runner: `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py`
  - output: `reports/WEIGHT_TUNING_SUMMARY_YYYY-MM-DD.md`
- **Fetch helper** (for exporting droplet-generated files):
  - `reports/_daily_review_tools/fetch_from_droplet.py`

### Operational note: refreshing vol/beta when market is closed
- Worker may skip the vol/beta refresh when `market_open=false`.
- Use the droplet-native refresh tool to repopulate `state/symbol_risk_features.json` on-demand:
  - `reports/_daily_review_tools/run_droplet_refresh_symbol_risk_features.py`

## 7.8 UW INTELLIGENCE LAYER (CENTRAL CLIENT + UNIVERSE + INTEL PASSES) (2026-01-20)

### Invariants (non-negotiable)
- **All UW HTTP calls must route through** `src/uw/uw_client.py` (rate-limited, cached, logged).
- **All UW endpoints must be validated** against the official OpenAPI spec at `unusual_whales_api/api_spec.yaml`.
- **Invalid UW endpoints must be blocked at runtime** by `uw_client` before any caching/rate limiting/network, and must log `uw_invalid_endpoint_attempt`.
- **UW daily usage must be persisted** to `state/uw_usage_state.json` (self-healing; never crashes engine).
- **UW response cache (v2 intelligence) lives under** `state/uw_cache/` (TTL enforced per endpoint policy).
- **Symbol-level UW calls are allowed only for** `daily_universe ∪ core_universe`.
- **Universe build must happen before market open** (or the intel passes fall back and log).
- **Pre/post intel must be generated daily**:
  - `state/premarket_intel.json`
  - `state/postmarket_intel.json`
- **Composite scoring is v2-only**; there is no composite version flag.

### UW endpoint validation (anti-404 contract) (2026-01-20)
- **Official spec location**: `unusual_whales_api/api_spec.yaml` (downloaded from UW and committed).
- **Spec loader**: `src/uw/uw_spec_loader.py` (extracts OpenAPI `paths` without YAML dependencies).
- **Static auditing**: `scripts/audit_uw_endpoints.py` (used by regression; fails if any UW endpoint used in code is not in spec).
- **Runtime blocking**: `src/uw/uw_client.py` rejects invalid endpoints and logs `uw_invalid_endpoint_attempt`.

### Components
- **Endpoint policies**: `config/uw_endpoint_policies.py`
- **Central UW client**: `src/uw/uw_client.py`
- **Universe builder**: `scripts/build_daily_universe.py` → `state/daily_universe.json`, `state/core_universe.json`
- **Pre-market pass**: `scripts/run_premarket_intel.py` → `state/premarket_intel.json`
- **Post-market pass**: `scripts/run_postmarket_intel.py` → `state/postmarket_intel.json`
- **Regression runner**: `scripts/run_regression_checks.py`

### Droplet execution + state sync (operational phase) (2026-01-20)

#### Invariants (non-negotiable)
- **Droplet execution must be runnable end-to-end**:
  - `scripts/build_daily_universe.py`
  - `scripts/run_premarket_intel.py`
  - `scripts/run_postmarket_intel.py`
  - `scripts/run_regression_checks.py`
- **Order of operations is binding**:
  - Universe build → premarket intel → postmarket intel → regression
- **State is synced locally for review**:
  - All synced artifacts MUST be written under: `droplet_sync/YYYY-MM-DD/`
  - Each sync MUST append to: `droplet_sync/YYYY-MM-DD/sync_log.jsonl`
- **Safety on failure**:
  - If droplet regression fails, sync MUST abort (no partial “success”).
  - Sync failures MUST be logged and MUST NOT break trading.
- **Shadow-only enforcement**:
  - v2 composite MUST consume UW intel only from `state/premarket_intel.json` / `state/postmarket_intel.json` (no live UW calls in scoring).
- **UW polling must be single-instance (quota safety)**:
  - `uw_flow_daemon.py` MUST NOT run more than once on the droplet.
  - Systemd service `uw-flow-daemon.service` is the canonical runner.
  - The daemon enforces a file lock at `state/uw_flow_daemon.lock` to prevent duplicates.

#### Operator scripts
- **Full run + sync**: `scripts/run_uw_intel_on_droplet.py`
  - Fetches: `state/daily_universe.json`, `state/core_universe.json`, `state/premarket_intel.json`, `state/postmarket_intel.json`, `state/uw_usage_state.json`
  - Fetches tails: `logs/system_events.jsonl` (last 500 lines), `logs/master_trade_log.jsonl` (tail), `logs/exit_attribution.jsonl` (tail)
- **Premarket trigger**: `scripts/run_premarket_on_droplet.py`
- **Postmarket trigger**: `scripts/run_postmarket_on_droplet.py`

### Observability
- `logs/system_events.jsonl` (subsystem=`uw`):
  - `uw_call`
  - `uw_rate_limit_block`
  - `daily_universe_built`
  - `premarket_intel_ready`
  - `postmarket_intel_ready`

## 7.9 INTELLIGENCE & PROFITABILITY LAYER (ATTRIBUTION + P&L + SECTOR/REGIME + UNIVERSE v2 + DASHBOARD + HEALTH) (2026-01-20)

### Invariants (non-negotiable)
- **v2-only engine**: v1 code paths are removed and MUST NOT be reintroduced.
- **No shadow trading**: shadow A/B artifacts are not produced in v2-only mode.
- **Attribution/P&L/dashboard are sourced from v2 live paper logs + state only**.
- **Attribution is append-only and non-blocking**:
  - Writer: `src/uw/uw_attribution.py`
  - Output: `logs/uw_attribution.jsonl`
  - Attribution MUST NEVER raise inside scoring.
- **Sector profiles are config-driven**:
  - Config: `config/sector_profiles.json`
  - Resolver: `src/intel/sector_intel.py` (safe defaults to `UNKNOWN`)
- **Regime state is a stable snapshot**:
  - Engine: `src/intel/regime_detector.py`
  - Output: `state/regime_state.json`
- **Universe scoring v2 is active (v2-only)**:
  - Config: `DAILY_UNIVERSE_SCORING_V2` in `config/registry.py`
  - Output: `state/daily_universe_v2.json`
- **Daily Intel P&L is best-effort and additive**:
  - Script: `scripts/run_daily_intel_pnl.py`
  - Outputs: `reports/UW_INTEL_PNL_YYYY-MM-DD.md`, `state/uw_intel_pnl_summary.json`
- **Intel dashboard is generated from state + logs**:
  - Generator: `reports/_dashboard/intel_dashboard_generator.py`
  - Output: `reports/INTEL_DASHBOARD_YYYY-MM-DD.md`
- **Intel health checks are required for visibility (self-heal optional)**:
  - Script: `scripts/run_intel_health_checks.py`
  - Output: `state/intel_health_state.json`
  - Self-heal attempts MUST be logged in the health state under `self_heal` and MUST NOT impact trading.

## 7.10 UW FLOW DAEMON HEALTH SENTINEL (WATCHDOG) (2026-01-20)

### Invariants (non-negotiable)
- **Daemon must be single-instance** (systemd + file lock): `uw-flow-daemon.service` + `state/uw_flow_daemon.lock`.
- **PID must be valid**:
  - systemd `ExecMainPID` must exist and must be present in `/proc` on the droplet.
- **Lock must be consistent**:
  - `state/uw_flow_daemon.lock` must exist
  - lock must be held (advisory lock)
  - lock file `pid=` should match `ExecMainPID` (best-effort verification)
- **Polling output must be fresh**:
  - Canonical output is `data/uw_flow_cache.json`
  - If stale beyond threshold, sentinel logs a warning/critical health event.
- **Crash loops must be detected**:
  - Crash loop is considered **current instability** (failed/auto-restart/non-active), not historical `NRestarts` alone.
- **Endpoint error spikes must be detected**:
  - Sentinel scans `logs/system_events.jsonl` for `uw_rate_limit_block` and `uw_invalid_endpoint_attempt`.
- **Sentinel must write a health state file**:
  - `state/uw_daemon_health_state.json`
- **Restart-storm detection (observability-only)**:
  - Sentinel may surface `restart_storm_detected` when journal shows repeated “Another instance is already running” patterns.
- **Dashboard must display daemon health**:
  - Intel dashboard includes “UW Flow Daemon Health” section sourced from `state/uw_daemon_health_state.json`.
- **Self-healing is optional and conservative**:
  - Script may attempt `systemctl restart uw-flow-daemon.service` only when enabled (`--heal`)
  - All attempts/results must be logged as system events.

### Operator script
- `scripts/run_daemon_health_check.py`

## 7.11 v2 SHADOW TRADING READINESS + TUNING PIPELINE (2026-01-21)

### Invariants (non-negotiable)
- (UPDATED) v2 LIVE READINESS (paper-only):
  - v2 MUST consume intel from state files only (no live UW calls in scoring).
  - v2 MUST enforce paper endpoint configuration (misconfig => block entries).
  - v2 MUST log all trade lifecycle events for audit/telemetry (master trade log + attribution).
  - Pre-open readiness MUST pass before session:
    - Script: `scripts/run_preopen_readiness_check.py`
    - Must validate freshness of universe + premarket intel + regime + daemon health.
    - Must fail if daemon health is `critical`.
  - Tuning suggestions are advisory only:
    - Helper: `src/intel/v2_tuning_helper.py` → `reports/V2_TUNING_SUGGESTIONS_YYYY-MM-DD.md`
    - No auto-application of weight changes.
  - Dashboard must expose v2 activity via v2 live logs/state (no shadow).

## 7.12 v2 EXIT INTELLIGENCE LAYER (PAPER LIVE) (2026-01-21)

### Invariants (non-negotiable)
- **v2 exit intelligence is live (paper)**:
  - MUST submit paper exit orders when required.
  - MUST log every v2 exit decision and attribution.
- **Exit attribution must be logged for every v2 exit**:
  - Engine: `src/exit/exit_attribution.py`
  - Output: `logs/exit_attribution.jsonl`
- **Exit score must be intel-driven (multi-factor)**:
  - Engine: `src/exit/exit_score_v2.py`
  - Includes UW/sector/regime + score deterioration + thesis flags.
- **Exit attribution naming contract**: All exit attribution components (the list written to `attribution_components` in exit_attribution records) MUST have `signal_id` values beginning with the **`exit_`** prefix (e.g. `exit_flow_deterioration`, `exit_score_deterioration`, `exit_regime_shift`). This is the canonical schema for effectiveness and board review.
- **Dynamic targets and stops are required** (best-effort when prices are available):
  - Targets: `src/exit/profit_targets_v2.py`
  - Stops: `src/exit/stops_v2.py`
- **Replacement logic is conservative and logged**:
  - Engine: `src/exit/replacement_logic_v2.py`
- **Pre/post-market exit intel must be generated**:
  - `scripts/run_premarket_exit_intel.py` → `state/premarket_exit_intel.json`
  - `scripts/run_postmarket_exit_intel.py` → `state/postmarket_exit_intel.json`
- **Exit analytics must be produced daily**:
  - `scripts/run_exit_intel_pnl.py` → `state/exit_intel_pnl_summary.json`, `reports/EXIT_INTEL_PNL_YYYY-MM-DD.md`
  - `scripts/run_exit_day_summary.py` → `reports/EXIT_DAY_SUMMARY_YYYY-MM-DD.md`
- **Dashboard must expose exit intel**:
  - Intel dashboard includes “Exit Intelligence Snapshot (v2)”.

## 7.13 POST-CLOSE ANALYSIS PACK (DAILY REVIEW BUNDLE) (2026-01-21)

### Invariants (non-negotiable)
- **Additive (no orders)**: pack generation must never submit orders or affect trading behavior.
- **Canonical location**:
  - `analysis_packs/YYYY-MM-DD/`
- **Pack generator**:
  - `scripts/run_postclose_analysis_pack.py`
  - Produces: `analysis_packs/YYYY-MM-DD/MASTER_SUMMARY_YYYY-MM-DD.md`
  - Includes best-effort copies of key `state/`, key `reports/`, and log tails under `analysis_packs/YYYY-MM-DD/{state, reports, logs}/`
- **Droplet integration**:
  - `scripts/run_uw_intel_on_droplet.py --postclose-pack` runs the pack on droplet and syncs it under `droplet_sync/YYYY-MM-DD/analysis_packs/YYYY-MM-DD/`

# 8. TELEMETRY CONTRACT (SYSTEM HARDENING - 2026-01-10)

## 8.1 SCORE TELEMETRY MODULE

- **File:** `telemetry/score_telemetry.py`
- **Purpose:** Track score distribution, component health, and missing data patterns
- **State File:** `state/score_telemetry.json`
- **Functions:**
  - `record(symbol, score, components, metadata)` - Record a score calculation
  - `get_score_distribution(symbol, lookback_hours)` - Get score statistics
  - `get_component_health(lookback_hours)` - Get component contribution stats
  - `get_missing_intel_stats(lookback_hours)` - Get missing data statistics
  - `get_telemetry_summary()` - Get complete telemetry summary

## 8.2 TELEMETRY INTEGRATION

- **Location:** `main.py:7565` (after all boosts applied)
- **Metadata Captured:**
  - `freshness`: Freshness factor applied
  - `conviction_defaulted`: Whether conviction was defaulted to 0.5
  - `missing_intel`: List of missing expanded intel components
  - `neutral_defaults`: List of components using neutral defaults
  - `core_features_missing`: List of missing core features

## 8.3 DASHBOARD TELEMETRY ENDPOINTS

- **Endpoint:** `/api/scores/distribution`
  - Returns: Score min, max, mean, median, percentiles, histogram
  - Parameters: `symbol` (optional), `lookback_hours` (default: 24)
  
- **Endpoint:** `/api/scores/components`
  - Returns: Per-component stats (avg contribution, zero percentage, total count)
  - Parameters: `lookback_hours` (default: 24)
  
- **Endpoint:** `/api/scores/telemetry`
  - Returns: Complete telemetry summary (all statistics)
  - Parameters: None

## 8.4 STRUCTURAL UPGRADE DASHBOARD ENDPOINTS (2026-01-20)
- **Endpoint:** `/api/regime-and-posture`
  - Returns:
    - `state/market_context_v2.json` snapshot
    - `state/regime_posture_state.json` snapshot
    - `composite_version: "v2"` (static)

---

## 8.5 [TELEMETRY_EQUALIZER_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Produce **equalizer-ready** telemetry that maps **per-feature contributions → realized PnL**, without modifying any trading logic.

Invariants (non-negotiable):
- **Read-only**: telemetry builders MUST read from logs/state only and MUST NOT write anywhere except `telemetry/YYYY-MM-DD/`.
- **Trading-safe**: MUST NOT affect trading/scoring/exit behavior (observability only).
- **Idempotent**: running multiple times for the same date must produce the same files given the same inputs.
- **Best-effort**: missing logs/fields are recorded as missing; bundle still generates.

Canonical outputs (generated by `scripts/run_full_telemetry_extract.py`):
- Folder: `telemetry/YYYY-MM-DD/`
- Equalizer artifacts under: `telemetry/YYYY-MM-DD/computed/`
  - `feature_equalizer_builder.json`
  - `feature_value_curves.json`
  - `regime_sector_feature_matrix.json`

### Daily Required Artifacts List (computed/)
The following computed artifacts are considered **daily-required** for a full telemetry bundle:
- `feature_equalizer_builder.json`
- `long_short_analysis.json`
- `exit_intel_completeness.json`
- `feature_value_curves.json`
- `regime_sector_feature_matrix.json`
- `score_distribution_curves.json`
- `regime_timeline.json`
- `replacement_telemetry_expanded.json`
- `pnl_windows.json`
- `signal_performance.json`
- `signal_weight_recommendations.json`

### Master Trade Log (append-only)
Path:
- `logs/master_trade_log.jsonl`

Purpose:
- A single, append-only stream of v2 live (paper) trade lifecycle records for long-term learning and auditing.

Rules:
- Append-only (never rewrite history).
- MUST NOT change trading/scoring/exit behavior; this is a passive “tap” off existing live logging.

### Feature Families (definition)
“Feature families” are **telemetry-only groupings** used to summarize score behavior and parity deltas without changing any trading logic.
- Families are used in:
  - `score_distribution_curves.json`
- (Optional) future dashboards/analysis pack summaries
- Canonical family set (coarse, stable): `flow`, `darkpool`, `sentiment`, `earnings`, `alignment`, `greeks`, `volatility`, `regime`, `event`, `short_interest`, `etf_flow`, `calendar`, `toxicity`, plus `other/unknown` fallbacks.

### Equalizer Knob Families (definition)
“Equalizer knob families” are the **operator-facing** counterparts of feature families:
- They define the buckets you would tune in a future equalizer UI (analysis-only).
- They MUST be derived only from telemetry artifacts (no live weight changes).

Required contents (minimum):
- **Per-feature PnL mapping**: total/avg PnL, win-rate, count (overall + by long/short).
- **Per-feature exit impact** (best-effort): exit score distributions + deterioration/RS/vol-expansion summaries for trades where the feature is active.
- **Equalizer-ready structures**: value curves (binned/quantiles) suitable for converting feature strength into a suggested weight/curve without touching live logic.

---

## 8.6 [LONG_SHORT_ASYMMETRY_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Track long vs short asymmetry using v2 live (paper) realized exits.

Required metrics (minimum):
- **Win rate**, **avg PnL**, **avg win**, **avg loss**, **expectancy** for:
  - overall
  - long-only
  - short-only

Output:
- `telemetry/YYYY-MM-DD/computed/long_short_analysis.json`

---

## 8.7 [EXIT_INTEL_COMPLETENESS_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Ensure exit-intel telemetry contains the full set of **required deterioration components** for debugging and promotion decisions.

Required exit-intel components (minimum keys in `exit_attribution.v2_exit_components`):
- `vol_expansion`
- `regime_shift`
- `sector_shift`
- `relative_strength_deterioration` (top-level in attribution record)
- `score_deterioration` (top-level + component-level where applicable)
- `flow_deterioration`
- `darkpool_deterioration`
- `sentiment_deterioration`

Output:
- `telemetry/YYYY-MM-DD/computed/exit_intel_completeness.json`

Rule:
- If keys are missing, bundle MUST still be produced and must report missing-key counts.

---

## 8.8 [FEATURE_VALUE_CURVES_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Produce per-feature “value curves” suitable for a future **feature equalizer** (shadow-only analysis).

Requirements:
- Curves MUST be derived from realized v2 shadow exits only.
- Curves MUST be computed separately for long/short when side is known.
- Curves MUST include counts per bin and average realized PnL per bin.

Output:
- `telemetry/YYYY-MM-DD/computed/feature_value_curves.json`

---

## 8.9 [REGIME_SECTOR_MATRIX_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Provide diagnostics for regime-aware and sector-aware feature weighting.

Requirements:
- For each (regime, sector) cell, compute per-feature counts and realized PnL summaries (best-effort).
- Must include a top-level summary for sparse cells (low sample sizes).

Output:
- `telemetry/YYYY-MM-DD/computed/regime_sector_feature_matrix.json`

---

## 8.10 [REPLACEMENT_LOGIC_TELEMETRY_CONTRACT] (v2-only, additive) (2026-01-22)

Requirements:
- Telemetry MUST count replacement exits and include replacement metadata when present:
  - `replacement_candidate`
  - `replacement_reasoning` (best-effort)
- Output MUST include:
  - count of replacement exits
  - realized PnL summary for replacement vs non-replacement exits (when PnL exists)

Where captured:
- `logs/master_trade_log.jsonl` (replacement fields when present)
- `logs/exit_attribution.jsonl` (`replacement_candidate`, `replacement_reasoning`)
- summarized into `telemetry/YYYY-MM-DD/FULL_TELEMETRY_YYYY-MM-DD.md` and `telemetry_manifest.json`.

---

# 9. CURSOR BEHAVIOR CONTRACT (ENHANCED - 2026-01-10)

## 9.1 MEMORY BANK LOADING RULE

Cursor MUST:
- **ALWAYS** load `MEMORY_BANK_ALPACA.md` at the start of every session
- **ALWAYS** read Section 0 (Cursor Behavior Contract) first
- **ALWAYS** reference `MEMORY_BANK_ALPACA.md` before making ANY code changes
- **ALWAYS** update `MEMORY_BANK_ALPACA.md` when adding new system behavior

Cursor MUST NOT:
- Skip loading `MEMORY_BANK_ALPACA.md`
- Overwrite `MEMORY_BANK_ALPACA.md` unless explicitly instructed
- Make changes without checking `MEMORY_BANK_ALPACA.md` first

## 9.2 MEMORY BANK UPDATE RULES

Cursor MUST update `MEMORY_BANK_ALPACA.md` when:
- New modules are added
- New telemetry is added
- New scoring logic is added
- New dashboard panels are added
- New operational rules are added
- New contracts are established

## 9.3 MEMORY BANK AS SINGLE SOURCE OF TRUTH

`MEMORY_BANK_ALPACA.md` is the authoritative source for:
- Architecture (Section 2)
- Signal integrity (Section 4)
- Scoring pipeline (Section 7)
- Telemetry (Section 8)
- Cursor behavior (Section 0, 9)
- Deployment workflow (Section 6)
- Report generation (Section 5)

## 9.4 SACRED LOGIC PROTECTION

Cursor MUST NOT modify without explicit permission:
- Core strategy logic (signal generation, model logic)
- Wallet/P&L/risk math (unless explicitly required)
- `.env` secrets or their loading path
- Systemd service configuration
- Fundamental process structure (`deploy_supervisor.py` + children)

All changes MUST be:
- Additive (not replacing existing logic)
- Defensive (fail-safe, not fail-dangerous)
- Reversible (can be undone if needed)
- Documented (in `MEMORY_BANK_ALPACA.md`)

---

## 4.4 COMPOSITE SCORING RULES
Cursor MUST:
- count only symbol keys (exclude metadata keys)  
- validate cache contents  
- ensure scoring only runs with real data  

---

# 5. REPORT GENERATION CONTRACT

## 5.1 REQUIRED STEPS
Cursor MUST:
1. Use `ReportDataFetcher(date="YYYY-MM-DD")`  
2. Fetch trades, blocked trades, signals, orders, gates  
3. Validate with `validate_report_data()`  
4. Validate data source  
5. Include data source metadata  
6. Reject invalid reports  

## 5.4 END-OF-DAY TRADE REVIEW (EOD)
- **Droplet-native generator**:
  - Payload: `reports/_daily_review_tools/droplet_end_of_day_review_payload.py`
  - Runner: `reports/_daily_review_tools/run_droplet_end_of_day_review.py`
- **Output**:
  - `reports/END_OF_DAY_REVIEW_YYYY-MM-DD.md`
- **Contract**:
  - MUST use droplet logs/state as source-of-truth
  - MUST be brutally honest (explicit YES/NO verdicts)
  - MUST review v2 live paper trades (no shadow comparison) and include buy-and-hold benchmark (best-effort)

---

## 5.5 EOD Data Pipeline (Canonical)

Canonical 8-file bundle paths (relative to repo root; **do not move/rename**):
- `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/master_trade_log.jsonl`
- `state/blocked_trades.jsonl`, `state/daily_start_equity.json`, `state/peak_equity.json`, `state/signal_weights.json`, `state/daily_universe_v2.json`

**Retention — do not truncate or rotate (why past data can disappear):** These files are append-only. If any process **truncates** or **rotates** them (e.g. keeps only last N lines or last N MB), past dates are lost and backfill/forensic will report `no_data_for_date` for those dates. **deploy_supervisor.py** runs `startup_cleanup()` and `rotate_logs()` to prevent disk fill; those routines **MUST** skip the retention-protected paths: `logs/exit_attribution.jsonl`, `logs/attribution.jsonl`, `logs/master_trade_log.jsonl`, `state/blocked_trades.jsonl`, `reports/state/exit_decision_trace.jsonl`. See **`docs/DATA_RETENTION_POLICY.md`**. Any new cleanup or rotation logic MUST NOT touch these paths so today's (and past days') data remain available for scenario and multi-day runs.

**Runner:** `board/eod/run_stock_quant_officer_eod.py` — uses `REPO_ROOT` + canonical paths with `(REPO_ROOT / rel).resolve()`; defensive checks (missing → log.error, data[name]=None; empty → log.warning, [] or None); EOD board JSON generated locally from bundle (no external agent).

**Contract:** `board/quant_officer_contract.md` (fallback: `board/stock_quant_officer_contract.md`).

**Outputs:** `board/eod/out/quant_officer_eod_<DATE>.json`, `board/eod/out/quant_officer_eod_<DATE>.md`. On parse failure: `board/eod/out/<DATE>_raw_response.txt`, exit 1.

**Cron:** EOD at 21:30 UTC weekdays; installed via `board/eod/install_eod_cron_on_droplet.py`. Audit+sync: `scripts/run_droplet_audit_and_sync.sh` (21:32 UTC weekdays) — runs `run_stockbot_daily_reports.py` for the date, then audit, then commits EOD + droplet_audit + stockbot pack and pushes. Local fetch (repeatable): `scripts/pull_eod_to_local.ps1` (Windows) or `scripts/pull_eod_to_local.sh` (Git Bash/Linux) — run weekdays after 21:35 UTC to get latest EOD without conflicts. Direct: `scripts/local_sync_from_droplet.sh`, `scripts/fetch_eod_to_local.py` → `board/eod/out/` and `EOD--OUT/`.

**Docs:** `docs/EOD_DATA_PIPELINE.md`, `docs/CRON_STRATEGIC_REVIEW.md`; summary: `reports/EOD_TARGETED_REPAIR_SUMMARY.md`.

**Extended canonical (vNext):** `state/symbol_risk_snapshot.json` — optional daily per-symbol risk snapshot; produced by `scripts/generate_symbol_risk_snapshot.py`; EOD runner loads defensively and includes "Symbol risk intelligence" subsection in memo when present; copies to `board/eod/out/symbol_risk_snapshot_<DATE>.json` and `.md`. See docs/EOD_DATA_PIPELINE.md.

**EOD data hardening (observability):** `scripts/eod_bundle_manifest.py` — validates canonical 8-file bundle (exists, non-empty, sha256); outputs `reports/eod_manifests/EOD_MANIFEST_<DATE>.json|.md`; exits non-zero if any required file missing/empty. `scripts/generate_signal_weight_exit_inventory.py` — signal/weight/exit inventory (COMPOSITE_WEIGHTS_V2, adaptive state/signal_weights.json, exit usage); output `reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_<DATE>.md`. Droplet runner: `scripts/run_stock_eod_integrity_on_droplet.sh` (path-agnostic: REPO_DIR defaults to script's parent directory); manifest → EOD quant officer → inventory → commit + push. §3.2 (reports use droplet production data).

**Unified daily intelligence pack:** `scripts/run_stockbot_daily_reports.py` — creates `reports/stockbot/YYYY-MM-DD/` with 9 files: STOCK_EOD_SUMMARY.md/.json, STOCK_EQUITY_ATTRIBUTION.jsonl, STOCK_WHEEL_ATTRIBUTION.jsonl, STOCK_BLOCKED_TRADES.jsonl, STOCK_PROFITABILITY_DIAGNOSTICS.md/.json, STOCK_REGIME_AND_UNIVERSE.json, MEMORY_BANK_SNAPSHOT.md. Canonical wheel fields: strategy_id, phase, option_type, strike, expiry, dte, delta_at_entry, premium, assigned, called_away. Intelligence expansion: `scripts/run_molt_intelligence_expansion.py` loads pack via load_equity_attribution(), load_wheel_attribution(), load_profitability_diagnostics(), load_blocked_trades(), load_regime_universe(). Pack integrated into EOD flow via run_stock_eod_integrity_on_droplet.sh.

**Cron + Git diagnostic:** `scripts/diagnose_cron_and_git.py` — full Cron + Git + execution diagnostic and repair (path-agnostic). Auto-detects stock-bot root (/root/stock-bot-current, /root/stock-bot); diagnoses cron, verifies scripts, EOD dry-run, git push; repairs cron if needed; updates Memory Bank; outputs `reports/STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_<DATE>.md`. Usage: `python3 scripts/diagnose_cron_and_git.py` on droplet; `--local` for Windows; `--remote` to run via DropletClient; `--dry-run` for report only. **Remote runner:** `python scripts/run_diagnose_on_droplet_via_ssh.py` — pulls latest on droplet, runs diagnostic, from local machine. **Verified 2026-02-01:** EOD 21:30 UTC, sync 21:32 UTC Mon–Fri; droplet push OK.

### Signal Snapshot Mapping Layer (observability-only)
- **Log:** `logs/signal_snapshots.jsonl` — append-only, one JSON record per lifecycle moment.
- **Schema:** timestamp_utc, symbol, lifecycle_event (ENTRY_DECISION | ENTRY_FILL | EXIT_DECISION | EXIT_FILL), mode (LIVE | PAPER | SHADOW), trade_id, regime_label, composite_score_v2, freshness_factor, components (present/defaulted/contrib), uw_artifacts_used, notes.
- **Writer:** `telemetry/signal_snapshot_writer.py` — write_snapshot_safe(); never raises.
- **Hooks:** main.py at entry decision (pre-submit), entry fill (log_attribution), exit decision (pre-close), exit fill (log_exit_attribution). SHADOW mode: counterfactual components; non-mutating.
- **Report:** `reports/SIGNAL_MAP_<DATE>.md` — daily per-symbol snapshot summary; generator `scripts/generate_daily_signal_map_report.py`; droplet runner `scripts/run_daily_signal_map_on_droplet.py`.
- **Snapshot harness verification (pre-market required):**
  - **Runner:** `scripts/run_snapshot_harness_on_droplet.py` (DropletClient); shell `scripts/run_snapshot_harness_on_droplet.sh`.
  - **Success criteria:** logs/signal_snapshots_harness_<DATE>.jsonl exists with >0 lines; reports/SNAPSHOT_HARNESS_VERIFICATION_<DATE>.md passes schema checks; reports/SIGNAL_MAP_<DATE>.md non-empty and labeled HARNESS.
  - **NO ORDERS PLACED:** Harness produces snapshots from master_trade_log; never places orders.

### Snapshot→Outcome Attribution
- **Join keys contract:** `telemetry/snapshot_join_keys.py` — canonical join_key and join_key_fields for snapshots↔master_trade_log↔exit_attribution↔blocked_trades. Prefer trade_id; surrogate: symbol|rounded_ts_bucket|side|lifecycle_event.
- **Report:** `reports/SNAPSHOT_OUTCOME_ATTRIBUTION_<DATE>.md` — join quality, outcome buckets (WIN/LOSS/FLAT/blocked), signal separability, marginal value (informative/neutral/misleading), shadow comparisons.
- **Shadow snapshot profiles (NO-APPLY):** `config/shadow_snapshot_profiles.yaml` — baseline, emphasize_dark_pool, emphasize_congress, emphasize_regime, disable_toxicity, etc. `telemetry/snapshot_builder.py` recomputes composite with profile multipliers; writes to `logs/signal_snapshots_shadow_<DATE>.jsonl`.
- **Shadow snapshots do NOT change decisions.** They are counterfactual analysis only.
- **Runner:** `scripts/run_snapshot_outcome_attribution_on_droplet.py` — harness → shadow snapshots → attribution report → commit + push.

### Exit Join Canonicalization
- **Join key precedence (deterministic exit joins):** `telemetry/snapshot_join_keys.py` — a) position_id (preferred); b) trade_id (live:SYMBOL:entry_ts); c) surrogate: symbol + side + entry_ts_bucket + intent_id.
- **Exit join fields:** EXIT_DECISION and EXIT_FILL snapshots emit `exit_join_key`, `exit_join_key_fields`, `entry_timestamp_utc` for auditability.
- **Reconciliation:** `telemetry/exit_join_reconciler.py` — resolves delayed exits, partial fills, regime-driven exits by time-window tolerance (default 5 min).
- **Report:** `reports/EXIT_JOIN_HEALTH_<DATE>.md` — snapshot→exit match rate, unmatched reasons, sources.

### Blocked-Trade Intelligence Attribution
- **Linkage:** `telemetry/blocked_snapshot_linker.py` — links state/blocked_trades.jsonl to nearest ENTRY_DECISION snapshot by symbol + time window (10 min).
- **Output:** `logs/blocked_trade_snapshots.jsonl` — append-only; each record: blocked_reason, snapshot components present/defaulted/missing, regime_label, notes.
- **Report:** `reports/BLOCKED_TRADE_INTEL_<DATE>.md` — blocked counts by reason, intelligence at block time, shadow profile deltas (hypothetical; NO-APPLY).
- **Runner:** `scripts/run_exit_join_and_blocked_attribution_on_droplet.py` — intel producers → UW audit → harness (if needed) → exit join health → blocked intel report → commit + push.

#### Daily AI Review Checklist
After EOD and learning workflow runs, Cursor should consider:
- `reports/LEARNING_STATUS_<today>.md`
- `reports/ENGINEERING_HEALTH_<today>.md`
- `reports/PROMOTION_PROPOSAL_<today>.md` or `reports/REJECTION_WITH_REASON_<today>.md`
- `reports/MEMORY_BANK_CHANGE_PROPOSAL_<today>.md`

If the user asks:
- "what should I do next?"
- "status"
- "AI summary"

Cursor should summarize these artifacts and suggest:
- reviews to perform
- experiments to consider
- proposals that may be applied manually

Cursor MUST NOT apply changes unless explicitly instructed.

### Learning & Engineering Governor (in-repo workflow)
- **Role:** In-repo Python code that produces reports. Rule-based (no LLM). Cursor implements all code; this workflow produces artifacts ONLY; never applies changes.
- **NO-APPLY guarantee:** This workflow MUST NEVER change weights, gates, or decisions. Artifact-only consumption. No live UW calls. No orders.
- **Workflows:**
  - **Learning Orchestrator** (`moltbot/orchestrator.py`): Verifies Memory Bank version, learning pipeline artifacts, NO-APPLY compliance. Output: `reports/LEARNING_STATUS_<DATE>.md`
  - **Engineering Sentinel** (`moltbot/sentinel.py`): Reads cron logs, EXIT_JOIN_HEALTH, BLOCKED_TRADE_INTEL, SNAPSHOT_OUTCOME_ATTRIBUTION. Output: `reports/ENGINEERING_HEALTH_<DATE>.md`. No code changes.
  - **Multi-Agent Learning Board** (`moltbot/board.py`): signal_advocate, risk_auditor, counterfactual_analyst, governance_chair. Output: `reports/PROMOTION_PROPOSAL_<DATE>.md` or `reports/REJECTION_WITH_REASON_<DATE>.md`
  - **Promotion Discipline** (`moltbot/promotion_discipline.py`): Multi-day stability, regime consistency, blocked-trade impact, shadow persistence. No automatic promotion. Output: `reports/PROMOTION_DISCIPLINE_<DATE>.md`
  - **Memory Bank Evolution** (`moltbot/memory_evolution.py`): Detects patterns, proposes Memory Bank updates. Output: `reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md`. Never writes MEMORY_BANK directly.
- **Automation:** `scripts/run_molt_workflow.py` — runs full learning workflow. `scripts/run_molt_on_droplet.sh` — droplet runner. Cron: 21:35 UTC weekdays (post-market) via `scripts/install_molt_cron_on_droplet.py`
- **Promotion:** Human approval required. The workflow proposes; Cursor/human approves and applies.

### Cursor Automations (pre-merge/pre-deploy governance layer)
- **Role:** Cursor Cloud automations run as the **front line** of governance: PR risk classification, PR bug review, security review on push to main, governance integrity (every 10 min), weekly governance summary. They do **not** modify droplet code or runtime; they produce artifacts and GitHub comments/issues.
- **Architecture:** Cursor Automations → Cursor → GitHub → Droplet → CSA/SRE → Deploy Gates → Artifacts. Automations are first-class evidence; CSA is the strategic layer; SRE is the behavioral layer.
- **CSA consumption:** CSA ingests `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` and optional weekly summaries via `scripts/audit/csa_automation_evidence.py`. CSA findings and verdict JSON include an **Automation Evidence** section; CSA does not depend on automations to run.
- **SRE consumption:** SRE reads `GOVERNANCE_AUTOMATION_STATUS.json`; when status is anomalies, SRE writes `reports/audit/SRE_AUTOMATION_ANOMALY_<date>.md` and records `automation_anomalies_present` in SRE_STATUS.json. SRE still operates on runtime signals alone if automations are unavailable.
- **Specs and activation:** `.cursor/automations/` (README, YAML/TS per automation); activation guide: `reports/audit/CURSOR_AUTOMATIONS_ACTIVATION.md`. Slack is disabled unless explicitly enabled later.

### UW canonical rules
- **Docs:** `docs/uw/README.md`, `docs/uw/ENDPOINT_POLICY.md` — canonical reference.
- **No hallucinated endpoints:** all must exist in `unusual_whales_api/api_spec.yaml`; static audit `scripts/audit_uw_endpoints.py` fails CI if unknown endpoints referenced.
- **Single-instance ingestion:** uw_flow_daemon only; file lock + systemd; scoring reads only from cached artifacts (uw_flow_cache, premarket_intel, postmarket_intel, uw_expanded_intel).

### Alpaca quantified governance (experiment pipeline)
- **Governance principles:** Quantified governance framework for the Alpaca stock bot: hypothesis-led experiments, review-only CSA + SRE, no execution gating from governance artifacts. All governance outputs are analysis-only; they do not gate live execution, scale risk, or use deploy authorization.
- **Experiment lifecycle:** (1) Hypothesis documented and tagged in the hypothesis ledger; (2) Validation window defined (trade-count and/or session-based); (3) CSA + SRE review artifacts produced; (4) Completion/break alerts via Telegram when appropriate; (5) No automatic promotion or deploy blocking.
- **CSA + SRE personas (Alpaca, review-only):** Canonical definitions: `docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` §8. **CSA** — Chief Strategy Auditor, Economic Truth Guardian: session-based/low-frequency learning truth (durable edges vs sparse wins); certifies from live entry/exit intent + realized outcome; narrative learning verdicts include `CSA_LEARNING_UNBLOCKED_LIVE_TRUTH_CONFIRMED`, `CSA_LEARNING_BLOCKED`, `CSA_PASS_WEAK`; no portfolio, allocation, or execution timing. **SRE** — Operational Integrity Sentinel: session-aware telemetry, open/close boundaries, overnight state; narrative pipeline verdicts include `SRE_LEARNING_PIPELINE_HEALTHY`, `SRE_PIPELINE_DEGRADED`, `SRE_PIPELINE_UNHEALTHY`. **Unchanged:** `enforce_csa_gate.py` still keys off **PROCEED | HOLD | ESCALATE | ROLLBACK** in `CSA_VERDICT_*.json`; `SRE_STATUS.json` / events semantics unchanged. Both produce reports and verdicts only; they do not modify trading config, place orders, or block deploys via new persona text alone.
- **Analysis-only constraints:** Governance scripts and ledger are append-only and safe when missing or empty. No code path in the trading engine or deploy pipeline reads the hypothesis ledger for gating. `state/deploy_authorization.json` is not used; deploy authorization is out of scope for this pipeline.
- **Alpaca-specific context:** Market type: US equities (session-based). Validation windows: trade-count and session-based. Metrics: expectancy, PnL/day, capital efficiency, slippage, drawdown. Ledger path: `state/governance_experiment_1_hypothesis_ledger_alpaca.json`.
- **Alpaca Data Sources (canonical — live bot writes here):** Closed-trade count and PnL MUST use the same paths the live bot writes to. **canonical_closed_trade_log_path:** `logs/exit_attribution.jsonl` (v2 equity exits; one line per closed trade). **Secondary:** `logs/attribution.jsonl` (closed trades with PnL/close_reason; filter out `trade_id` starting with `open_`). **Fallback:** `logs/master_trade_log.jsonl` (records with `exit_ts` set = closed trade). Paths are relative to repo root (e.g. `/root/stock-bot` on droplet). Config registry: `config.registry.LogFiles.EXIT_ATTRIBUTION`, `LogFiles.ATTRIBUTION`, `LogFiles.MASTER_TRADE_LOG`. If these paths change, update `scripts/experiment_1_status_check_alpaca.py` and this section.

#### Alpaca droplet — live operational canon (last material infra update: 2026-04-13 — **4 AMD vCPUs / 8GB RAM**; re-verify after future changes)
- **Goals:** Single source of operational truth for the **live Alpaca equity droplet**; align scripts and operators on paths, units, and secrets **without** implying trading or deploy authorization from this text.
- **Constraints:** This canon is descriptive. It does not replace CSA/SRE review artifacts, hypothesis ledger rules, or SPI non-prescriptive outputs. When host configuration changes, re-run a read-only audit and update this subsection + evidence under `reports/daily/<ET-date>/evidence/`.
- **SSH (canonical):** Prefer `Host alpaca` in `~/.ssh/config` resolving to **`104.236.102.57`**; **`droplet_config.json`** is the repo anchor (`use_ssh_config: true`, `username: root`, **`project_dir: /root/stock-bot`**). Scripted path: **`droplet_client.py`** (Paramiko). **Never** use **`147.182.255.165`** for stock-bot.
- **Compute (production — verified 2026-04-13):** **4 AMD vCPUs / 8GB RAM** (institutional-grade resize). **Hostname (legacy DigitalOcean slug, unchanged):** `ubuntu-s-1vcpu-2gb-nyc3-01-alpaca` — do not infer vCPU/RAM from the name alone.
- **Canonical repo root on this droplet:** **`/root/stock-bot` only** — present and active. **`/root/stock-bot-current`** and **`/root/trading-bot-current`** were **not present** at verify; tools such as `scripts/diagnose_cron_and_git.py` may still probe those paths first — do not assume they exist on every host.
- **Python:** Trading stack **`/root/stock-bot/venv`** (Python **3.12.3**). **`stock-bot-dashboard.service`** runs **`/usr/bin/python3 /root/stock-bot/dashboard.py`** (not the venv interpreter).
- **systemd — core active units (verified):**
  - **`stock-bot.service`:** `WorkingDirectory=/root/stock-bot`, `EnvironmentFile=/root/stock-bot/.env`, **`ExecStart=/root/stock-bot/systemd_start.sh`** → activates venv and runs **`venv/bin/python deploy_supervisor.py`**. Drop-ins observed: logging flags, **`MIN_EXEC_SCORE=2.7`**, truth router mirror, **`STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth`**.
  - **`stock-bot-dashboard.service`:** Flask dashboard, **`PORT=5000`**, `EnvironmentFile=-/root/stock-bot/.env`.
  - **`uw-flow-daemon.service`:** **`venv/bin/python uw_flow_daemon.py`**, `EnvironmentFile=-/root/stock-bot/.env`.
- **Port 5000 (verified):** Bound by the **`python3`** process started as **`/usr/bin/python3 .../dashboard.py`** (dashboard unit). **`deploy_supervisor.py`** may also spawn a **venv** `dashboard.py` child; at verify only the **systemd dashboard** process held the port — treat duplicate dashboard processes as an operational risk to inspect (`ss -tlnp`, `ps aux`) after deploys.
- **systemd — `trading-bot.service`:** **not-found** on this host (do not use that unit name here).
- **systemd — units in `failed` state (observed 2026-03-28, non-exhaustive):** `alpaca-forward-truth-contract.service` (timer still triggers; journal showed **exit 2 INCIDENT**), `alpaca-postclose-deepdive.service`, `stock-bot-dashboard-audit.service`, `trading-bot-doctor.service`. These are **SRE signals**, not automatic instructions to restart or reconfigure during audits.
- **Timers (observed):** `alpaca-forward-truth-contract.timer`, `alpaca-postclose-deepdive.timer`, `stock-bot-dashboard-audit.timer`.
- **Telegram / secrets:** **`/root/.alpaca_env`** (mode `600`) — sourced by **cron** jobs (e.g. trade milestones). **`/root/stock-bot/.env`** — API keys, dashboard Basic Auth, **`EnvironmentFile`** for systemd units above. Sync path when needed: **`scripts/sync_telegram_to_dotenv.py`**.
- **Milestone + integrity cadence (root):** `alpaca-telegram-integrity.timer` + `scripts/run_alpaca_telegram_integrity_cycle.py` (see **Alpaca Telegram + data integrity cycle** below). **Harvester trade-count Telegram (10 / 100 / 250):** `scripts/telemetry_milestone_watcher.py` (cron hourly is typical). Legacy `notify_alpaca_trade_milestones` crontab lines must be absent. **Fast-lane 15m / 4h** is **not** part of V2 Harvester ops — confirm with `crontab -l` only if debugging that experiment.
- **Logs / evidence:** Runtime under **`logs/`** relative to repo; governance JSON under **`state/`** (e.g. `state/alpaca_*.json`, `state/fast_lane_experiment/`). Packaged evidence: **`reports/daily/<ET-date>/evidence/`** (see repo visibility rules).
- **Offline PnL + SPI:** `scripts/audit/alpaca_pnl_massive_final_review.py` with **`--root /root/stock-bot`**; strict cohort from `telemetry/alpaca_strict_completeness_gate.py` and session truth runners (**SPI does not authorize behavior change** — see below).

#### Alpaca Signal Path Intelligence (SPI)
- **Purpose:** Post-trade, read-only path analytics on **executed Alpaca trades** already selected by the strict / session PnL cohort (`complete_trade_ids` joined to `logs/exit_attribution.jsonl`). Describes distributions (time-to-threshold, MAE/MFE-style path stats, volatility ratio vs a pre-entry window of comparable length, descriptive path-shape buckets). **Not** price targets, forecasts, or recommendations.
- **Constraints:** No strategy, execution, exit/stop, or signal changes. No mutation of canonical logs or broker state. Default bar load is **cache-only** (`fetch_if_missing=False`); optional `ALPACA_SPI_FETCH_BARS=true` may populate `data/bars/` via existing `data/bars_loader.py` (operator opt-in only).
- **Metrics (definitions):**
  - **Time-to-outcome (minutes):** First bar in the hold window where favorable excursion reaches configurable fractional moves (default +0.5%, +1%, +2% vs entry); `null` if the threshold is never hit before exit. **Time to exit** = hold duration (entry timestamp → exit timestamp).
  - **MAE/MFE (% of entry):** From session 1m OHLC over the hold window (long: MAE from lows, MFE from highs; short inverted). **MAE before first +1%** = max adverse from entry until the first +1% favorable touch or exit, whichever comes first. When bars are missing, optional fallbacks use `snapshot.mae_pct` / `mfe_pct` on the exit row when present; otherwise path fields are `null` and archetype `no_intraday_path_data`.
  - **Volatility:** Sample standard deviation of log(close) returns on hold-window bars vs the same statistic on pre-entry bars (same symbol, same session day, window length ≈ hold length). **Ratio** = path vol / baseline vol when baseline > 0.
  - **Path archetypes:** Descriptive labels only (`grind_flat`, `dip_then_recover`, `spike_then_chop`, `immediate_rejection`, `trend_hold`, `other_mixed`, `no_intraday_path_data`) — rule-based, non-prescriptive.
- **Signal dimension:** Per-trade bucket = dominant key from `exit_contributions` or `v2_exit_components` when present; else `attribution_unknown`. Aggregations are **counts and percentiles**, not tuning directives.
- **Invariant:** **SPI does not authorize behavior change.** No runtime component may gate entries, exits, sizing, or risk on SPI output. CSA/SRE may review SPI artifacts as governance evidence only.
- **Implementation map:** Core logic `src/analytics/alpaca_signal_path_intelligence.py`. PnL packet integration and artifact filenames `ALPACA_SPI_SECTION_<TS>.{md,json}`, `ALPACA_PNL_SIGNAL_PATH_INTELLIGENCE_<TS>.{md,json}` — `scripts/audit/alpaca_pnl_massive_final_review.py` (same `--ts` / `--output-dir` as the rest of the Alpaca PnL review bundle). Bar IO: `data/bars_loader.py`. Strict cohort semantics: §1.1 (strict era), `telemetry/alpaca_strict_completeness_gate.py`, and session truth JSON from `scripts/audit/alpaca_forward_truth_contract_runner.py` / `alpaca_pnl_market_session_unblock_pipeline.py`.
- **Governance activation:** Framework doc: `docs/QUANTIFIED_GOVERNANCE_EXPERIMENT_FRAMEWORK_ALPACA.md`. Ledger: `state/governance_experiment_1_hypothesis_ledger_alpaca.json`. Tag: `scripts/tag_profit_hypothesis_alpaca.py [YES|NO]`. Validate: `scripts/validate_hypothesis_ledger_alpaca.py` (exit 0 = valid). Health: run validate; break alert when invalid/stale: `scripts/notify_governance_experiment_alpaca_break.py`; completion alert when validation window satisfied and ledger healthy: `scripts/notify_governance_experiment_alpaca_complete.py` (uses TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID; at most one completion message per phase). CSA + SRE oversight: review-only; reports support CSA_REVIEW and SRE_REVIEW sections per framework doc. Parallel analysis workers (safe to scale): historical expectancy recomputation, slippage distribution analysis, session-based PnL attribution, counterfactual would-have-traded analysis—all read-only, no orders, no API writes.
- **Status:** Alpaca system is governance-ready; **V2 Harvester** paper data collection is active; governance and ledger tooling remain analysis-only unless explicitly tagged.

### Governance Experiments
- **Experiment #1 — ALPACA_BASELINE_VALIDATION_AND_METRICS_TRUTH**
  - **Mode:** Analysis-only.
  - **Purpose:** Prove data integrity and metric truth-chain for Alpaca; establish baseline expectancy and PnL per session/day; validate that slippage and drawdown metrics are computable and stable.
  - **Validation window:** 7 trading sessions OR 500 closed trades (whichever comes first).
  - **Success criteria:** Metrics computed without gaps for the full window; ledger health PASS (validator exit 0); no silent failures (break alerts = 0).
  - **Default action on expiry:** ITERATE if any metric gaps or integrity issues; READY if all success criteria met.
- **Tagging discipline (Alpaca experiments):** change_id = Git commit SHA (canonical). Tag every relevant change with `python scripts/tag_profit_hypothesis_alpaca.py YES|NO`. For Experiment #1, default to NO unless a profit hypothesis is explicitly stated. Do not gate execution on ledger or tags.
- **Daily health command:** `python scripts/run_alpaca_experiment_1_daily_checks.py` (runs validate + break alert; exits non-zero if break sent). No cron installation unless explicitly authorized.
- **Daily Telegram contract (Alpaca governance):** Every trading day, after market close, run: `python scripts/run_alpaca_daily_governance.py`. This MUST send a Telegram message even if PnL is negative or no candidate changes exist. Message must clearly state either **"NO CHANGE CANDIDATE TODAY"** or **"CHANGE CANDIDATE PRESENT — REVIEW REQUIRED"**. Ensures no silent losing day with no governance signal. Cron is NOT installed automatically; opt-in only (see comment block in script).

### Scenario Lab (Parallel Analysis)
- **Concept:** Scenario experiments (#2–N) are parallel, analysis-only runs that replay and explore alternative strategies using historical or shadow trade data. They do **not** replace or write to Experiment #1.
- **Rules:** Scenario experiments are NOT truth experiments. They do NOT gate execution. They do NOT write to canonical ledgers (e.g. `state/governance_experiment_1_hypothesis_ledger_alpaca.json`). They exist to generate ranked hypotheses for future experiment selection.
- **Registry:** `docs/SCENARIO_EXPERIMENT_REGISTRY_ALPACA.md` — scenario_id, description, parameters varied, data source, output path, status.
- **Runner:** `scripts/scenario_lab/run_scenario_batch.py` — load historical/shadow logs; apply alternative entry/exit/sizing/session logic; run in parallel (--workers N); write only to `reports/scenario_lab/<scenario_id>_<DATE>.json`. No broker writes; no execution hooks; no ledger writes.
- **CPU utilization (droplet — 2026-04-13):** Production Alpaca host is **4 AMD vCPUs / 8GB RAM**. Scenario lab is **SAFE TO SCALE** and remains **read-only**. With four vCPUs it is now reasonable to run parallel analysis **on the droplet** with up to **`--workers 3`** while leaving headroom for **`stock-bot`**, **`uw-flow-daemon`**, and the OS. The generic cap **(cpu_count − 1)** workers still applies (**3** on this host when fully utilizing spare cores — prefer **`--workers 3`** over saturating all four).
- **Summary reports:** `reports/scenario_lab/SCENARIO_SUMMARY_<DATE>.md` — scenario ranking, CSA_REVIEW (why misleading, fragile assumptions), SRE_REVIEW (data completeness, replay fidelity, failure modes). Scenario outputs feed future experiment selection; Experiment #1 remains the single canonical truth source.

### Alpaca Fast-Lane (25-trade shadow) — DEPRECATED for V2 Harvester operations

**Not** the active milestone or data-collection path. Historical shadow lane only: 25-trade cycles, ledger under `state/fast_lane_experiment/`, `logs/fast_lane_shadow.log`, optional cron via `scripts/install_fast_lane_cron_on_droplet.py`. **2026-03-17 CSA: NO PROMOTION** (governance-closed batch). **Primary Harvester cadence:** `scripts/telemetry_milestone_watcher.py` (10 / 100 / 250 vs `STRICT_EPOCH_START`) + integrity cycle (§ below). Detail when needed: `docs/ALPACA_FAST_LANE_LIVE_ACTIVATION_VERIFICATION.md`, `docs/SHADOW_25_TRADE_PROMOTION_EXPERIMENT_DESIGN.md`, `scripts/run_fast_lane_shadow_cycle.py`, `scripts/notify_fast_lane_summary.py`. **2000-trade edge pipeline** (`scripts/alpaca_edge_2000_pipeline.py`) remains an optional offline study — same isolation rules; no execution authority.

### Alpaca Rolling Reviews & Shadow Experiments — INVENTORIED
- **Inventory doc:** `docs/ALPACA_ROLLING_REVIEWS_AND_SHADOW_EXPERIMENTS.md` — code-level inventory of (1) rolling reviews of trades (EOD 1/3/5/7 day windows, 5d rolling PnL, 30d/last-N comprehensive review, trade visibility, fast-lane 25-trade, daily pack, weekly ledger), (2) shadow experiments and shadow policies (telemetry shadow variants, state/shadow A1–C2, shadow comparison last387, fast-lane, snapshot profiles, intraday/exit-lag shadow, ShadowTradeLogger, droplet shadow confirmation), and (3) their wiring to CSA, SRE, tuning, and daily/weekly reviews. Descriptive only; no behavior changes, no new cron, no new promotion logic.
- This inventory is Alpaca US-equities only; no cross-venue execution paths.

### Alpaca Tiered Board Review — DESIGN PROPOSED
- **Design doc:** `docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` — governance design that (1) tiers Alpaca rolling reviews into Tier 1 (short: 1d/3d/5d, 25-trade fast-lane), Tier 2 (medium: 7d/30d, last-N), Tier 3 (long: last387, weekly ledger, stability), (2) maps shadow experiments into governance inputs (state/shadow A1–C2 + shadow comparison), diagnostic-only (telemetry shadow, exit-lag, ShadowTradeLogger, daily confirmation), and excluded from promotion (fast-lane, snapshot profiles), (3) proposes Alpaca-native tiered board review model: convergence rules, Board Review Packet structure, CSA/SRE roles, promotion gate and heartbeat (design only). Synthesis and design only; no implementation, no code/cron/promotion changes.
- Design stays Alpaca-native; no shared code or state with non-Alpaca venues.

### Alpaca Tier 3 Board Review — IMPLEMENTED
- **Script:** `scripts/run_alpaca_board_review_tier3.py` — Alpaca Tier 3 (long-horizon) Board Review packet generation. Args: --base-dir, --date, --force, --dry-run. Reads last387/last750/30d comprehensive review, SHADOW_COMPARISON_LAST387, weekly ledger (optional), CSA_VERDICT_LATEST, SRE_STATUS, etc.; writes `reports/ALPACA_BOARD_REVIEW_<YYYYMMDD>_<HHMM>/BOARD_REVIEW.md` and `BOARD_REVIEW.json`; updates `state/alpaca_board_review_state.json`. No cron, no promotion logic, no heartbeat, no convergence logic.
- **Packet directory:** `reports/ALPACA_BOARD_REVIEW_<timestamp>/` (timestamp UTC YYYYMMDD_HHMM).
- **CSA/SRE approval:** Plan reviewed in `reports/audit/ALPACA_TIER3_PLAN_CSA_REVIEW.md` (ACCEPT) and `ALPACA_TIER3_PLAN_SRE_REVIEW.md` (OK); packet reviewed in `ALPACA_TIER3_PACKET_CSA_REVIEW.md` (ACCEPT) and `ALPACA_TIER3_PACKET_SRE_REVIEW.md` (OK).

### Alpaca Tier 1 + Tier 2 Board Reviews — IMPLEMENTED
- **Scripts:** `scripts/run_alpaca_board_review_tier1.py` (Tier 1 short-horizon), `scripts/run_alpaca_board_review_tier2.py` (Tier 2 medium-horizon). Tier 1: 1d/3d/5d rolling windows, 5d rolling PnL state, trade visibility (since-hours), fast-lane ledger, daily pack; writes `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/TIER1_REVIEW.md` and `.json`. Tier 2: 7d/30d/last100 comprehensive review (read-only), CSA_BOARD_REVIEW (latest); writes `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/TIER2_REVIEW.md` and `.json`. Both merge-update `state/alpaca_board_review_state.json` (tier1_last_run_ts, tier1_last_packet_dir, tier2_last_run_ts, tier2_last_packet_dir); existing Tier 3 keys preserved.
- **Packet directories:** `reports/ALPACA_TIER1_REVIEW_<timestamp>/`, `reports/ALPACA_TIER2_REVIEW_<timestamp>/`.
- **CSA/SRE approval:** Plan: `reports/audit/ALPACA_TIER1_TIER2_PLAN_CSA_REVIEW.md` (ACCEPT), `ALPACA_TIER1_TIER2_PLAN_SRE_REVIEW.md` (OK). Packets: `ALPACA_TIER1_TIER2_PACKET_CSA_REVIEW.md` (ACCEPT), `ALPACA_TIER1_TIER2_PACKET_SRE_REVIEW.md` (OK).
### Alpaca Telegram Governance — IMPLEMENTED
- **Helper:** `scripts/alpaca_telegram.py` — `send_governance_telegram(text, log_path=None, script_name=...)`. Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID; on failure appends to `TELEGRAM_NOTIFICATION_LOG.md` (repo root); never raises. **Integration:** Tier 1/2/3, convergence, promotion gate, heartbeat scripts accept `--telegram`; after successful run they send a one-line summary; failures do not block (exit 0). Plan: `docs/ALPACA_PHASE6_TELEGRAM_PLAN.md`. CSA/SRE: ACCEPT/OK.
- **Quiet hours (default on):** Governance sends (including `telegram_failure_detector` pager, integrity cycle, post-close helper, tier summaries) **do not call the Telegram API** on **Saturday/Sunday America/New_York** or on **weekdays before 07:00 ET or from 21:00 ET onward** — no message and **no** new line in `TELEGRAM_NOTIFICATION_LOG.md` for that attempt. **Disable** for 24/7 sends (e.g. E2E): `TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS=0` in `.env` or unit `Environment`. **Optional window:** `TELEGRAM_GOVERNANCE_ET_SEND_START_HOUR` (default 7), `TELEGRAM_GOVERNANCE_ET_SEND_END_HOUR` (default 21, end exclusive). **SRE note:** `TELEGRAM_NOTIFICATION_LOG.md` lines showing **HTTP 404** from `api.telegram.org` almost always mean an **invalid or revoked `TELEGRAM_BOT_TOKEN`** (confirm with @BotFather); fix credentials on the droplet, then `scripts/sync_telegram_to_dotenv.py` if systemd loads `.env` only.
- **Telegram & cross-environment sync (April 2026):** **Dual locations** are normal on the droplet: **`/root/stock-bot/.env`** ( **`EnvironmentFile`** for **`stock-bot.service`** and dashboard units) and **`/root/.alpaca_env`** ( **cron**, **milestones**, and many **manual** one-shots). **Alpaca trading keys** and **Telegram** vars often exist in **both**; drifting copies cause “works in cron but not systemd” (or vice versa).
- **Sync tool:** Whenever **`/root/.alpaca_env`** is updated (or Telegram vars are fixed there first), **always** run **`scripts/sync_telegram_to_dotenv.py`** so **`systemd`** inherits the correct **`TELEGRAM_BOT_TOKEN`** / **`TELEGRAM_CHAT_ID`** (and related copies into **`.env`** per script behavior). Typical pattern: `cd /root/stock-bot && set -a && source /root/.alpaca_env && set +a && venv/bin/python3 scripts/sync_telegram_to_dotenv.py` (adjust venv path if needed).
- **Telegram on droplet:** Vars live in `/root/.alpaca_env` or after sourcing `.env`; E2E runner sources both and runs `scripts/sync_telegram_to_dotenv.py` to write into `.env` for systemd. See ARCHITECTURE_AND_OPERATIONS § Telegram.
- **Where TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set on droplet (do not hunt again):** (1) **`/root/.alpaca_env`** — used by cron and manual runs; always `source /root/.alpaca_env` (or `source /root/stock-bot/.env`) before running any script that sends Telegram (e.g. DATA_READY pipeline, E2E audit, fast-lane). (2) **`/root/stock-bot/.env`** — loaded by systemd for `stock-bot.service`; if you add vars to **`.alpaca_env` only**, run **`source /root/.alpaca_env` then `python3 scripts/sync_telegram_to_dotenv.py`** so systemd’s **`.env`** stays authoritative. (3) Venv does not store them; they are in the **environment** after you source `.alpaca_env` or `.env`. For DATA_READY on droplet: `cd /root/stock-bot && ./scripts/run_alpaca_data_ready_on_droplet.sh` (script sources `/root/.alpaca_env` when present) or `source /root/.alpaca_env && PYTHONPATH=. python scripts/run_alpaca_data_ready_on_droplet.py`.

### Telegram Notification Authority (production)
- **Canonical Alpaca production sender package:** `telemetry/alpaca_telegram_integrity/` — invoked by `scripts/run_alpaca_telegram_integrity_cycle.py` (systemd timer). This is the **intended** sole source of **automated** milestone + data-integrity Telegram for Alpaca.
- **Allowed message kinds (integrity cycle):** (1) **100-trade checkpoint** (informational, gated) and deferred integrity variant; (2) **250-trade milestone**; (3) **data integrity / drift / strict regression** alerts (`alpaca_data_integrity`); (4) **manual test sends** (`--send-test-*`, `[TEST]` prefix in text). Pager evaluation inside the cycle may trigger integrity alerts when post-close / direction-readiness windows fail.
- **Transport:** `scripts/alpaca_telegram.py` — `send_governance_telegram(..., script_name=...)`.
- **Enforcement (droplet):** Set **`TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`** in `/root/stock-bot/.env` so **only** the allowlisted `script_name` values used by the integrity runner can open the Telegram HTTP API; all other callers (board `--telegram`, post-close, promotion gate, heartbeat, fast-lane, edge pipeline, one-off scripts) are **blocked** at the helper and logged to `TELEGRAM_NOTIFICATION_LOG.md`. Leave unset on dev machines when running E2E or manual board Telegram.
- **Canonical closed-trade count (dashboard + audit alignment):** `src/governance/canonical_trade_count.py` — `compute_canonical_trade_count` (unique `trade_key` from `logs/exit_attribution.jsonl`, era-cut excluded; optional time floor for session/milestone mode). Dashboard situation strip uses **no floor** (full post-era cumulative); Telegram milestones use the same function **with** the configured floor.

### Alpaca Telegram + data integrity cycle (2026-03-30) — PRIMARY (droplet)
- **Purpose:** Single coherent Alpaca-only pipeline for (1) **250-trade milestone** Telegram (once per US regular-session anchor day, counting unique canonical `trade_key` closes from a configured **count floor**), (2) **data integrity / drift** Telegram when warehouse coverage, staleness, exit_attribution tail probes, strict completeness regression (ARMED→BLOCKED), or post-close / direction-readiness pager windows fail, (3) **safe self-heal** (mkdir log dirs; `systemctl try-restart` **alpaca-postclose-deepdive.service** only if failed — never `stock-bot`). **Default count floor (`milestone_counting_basis: integrity_armed`):** first integrity cycle in the ET session anchor where the **same pre-checks as the 100-trade checkpoint** pass; until then milestone trade count stays **0** even if exits exist since 09:30 ET. Legacy: set `milestone_counting_basis` to **`session_open`** to count since 09:30 ET open only.
- **Entry:** `scripts/run_alpaca_telegram_integrity_cycle.py` — flags: `--dry-run`, `--skip-warehouse`, `--no-self-heal`, `--send-test-milestone`, `--send-test-integrity`, **`--send-test-100trade`** (all `[TEST]`-prefixed where applicable). **systemd:** `deploy/systemd/alpaca-telegram-integrity.service` + `alpaca-telegram-integrity.timer` (every **10 minutes**). **Install:** `bash scripts/install_alpaca_telegram_integrity_on_droplet.sh` (copies units, `daemon-reload`, enable/start timer). Units load `EnvironmentFile` **both** `/root/stock-bot/.env` and `/root/.alpaca_env` (optional `-` prefix).
- **Config:** `config/alpaca_telegram_integrity.json` — `enabled`, **`milestone_counting_basis`** (`integrity_armed` default, or `session_open`), `milestone_trade_count` (default 250), `checkpoint_100_*`, `warehouse_days_when_run`, `warehouse_run_every_n_cycles` (throttle full truth warehouse mission), `warehouse_coverage_file_max_age_hours`, `coverage_thresholds_pct`, `exit_attribution_tail_lines`, `integrity_alert_cooldown_sec`, `strict_regression_alert_cooldown_sec`, `self_heal` toggles. Full warehouse mission runs only during **US RTH ET** (throttled); milestone and strict probe run every invocation.
- **State:** `state/alpaca_milestone_250_state.json` (per-session-anchor idempotent milestone), **`state/alpaca_milestone_integrity_arm.json`** (per anchor: `arm_epoch_utc` when integrity pre-check first passes), `state/alpaca_telegram_integrity_cycle.json` (cycle counter, cooldowns, last_good snapshot). **Log:** `logs/alpaca_telegram_integrity.log` (append-only line per run; `telegram_failure_detector` milestone window prefers this file, then legacy `notify_milestones.log`).
- **Direction readiness vs `ALPACA DATA INTEGRITY ALERT`:** Pager text `direction_readiness_pager:RUNNER_NOT_RUN:direction_readiness_missing` means **`state/direction_readiness.json` was absent** during the Mon–Fri **09:00–21:59 UTC** check window (same rule as `scripts/governance/telegram_failure_detector.py`). **Fix:** `cd /root/stock-bot && ./venv/bin/python scripts/governance/check_direction_readiness_and_run.py` (writes/refreshes the JSON from `logs/exit_attribution.jsonl`). **Prevention:** `python3 scripts/governance/install_direction_readiness_cron_on_droplet.py` installs `*/5 9-21 * * 1-5` → `logs/direction_readiness_cron.log`. The integrity cycle **reuses `run_auto_heal(..., direction_readiness)`** and re-evaluates the pager **before** building integrity-alert reasons, so a transient missing file is usually repaired in the same 10-minute cycle. **`Last known good: not recorded yet`** on the alert template only means a full clean snapshot was never written to `alpaca_telegram_integrity_cycle.json` (`last_good`); run a green warehouse + probes cycle once to populate it (see **§1.2**).
- **Legacy removed:** `scripts/notify_alpaca_trade_milestones.py` is a **no-op stub** (deprecated). **Crontab** lines calling it must be removed (`python3 scripts/install_cron_alpaca_notifier.py` strips them). `scripts/install_alpaca_notifier_cron.sh` refuses to reinstall old cron. **Optional:** `systemctl disable --now telegram-failure-detector.timer` when the new timer is primary, to avoid duplicate paging; rollback by re-enabling that timer and disabling `alpaca-telegram-integrity.timer`.
- **100-trade checkpoint (informational):** After the same `trade_key` count (same **count floor** as the 250 milestone — see `milestone_counting_basis`) reaches **`checkpoint_100_trade_count`** (default **100**, `config/alpaca_telegram_integrity.json`), the cycle sends **`[ALPACA] 100-TRADE CHECKPOINT`** once per session anchor **only if** pre-checks pass: latest warehouse coverage artifact present and fresh, **`DATA_READY: YES`**, coverage %s ≥ configured thresholds, **`LEARNING_STATUS == ARMED`**, and exit_attribution tail probe clean. If degraded at 100+, sends **one** deferred drift-style Telegram (`ALPACA DATA INTEGRITY ALERT (100-trade checkpoint deferred)`); when integrity recovers, sends the informational checkpoint. **Guard file:** `state/alpaca_100trade_sent.json` (`checkpoint_100_info_sent`, `checkpoint_100_deferred_sent`, `last_count`, `session_anchor_et`). **`--send-test-100trade`** sends `[TEST] …` and updates `last_test_100trade_utc` in the guard file (does not set `checkpoint_100_info_sent`). **Does not** gate or replace the **250-trade** milestone (separate state file).
- **Code layout:** `telemetry/alpaca_telegram_integrity/` (session open clock, milestone counting, `checkpoint_100.py` guard I/O, warehouse summary parse, strict/exit probes, templates including 100-trade formats, self-heal). **Tests:** `tests/test_alpaca_telegram_integrity.py`. **No trading logic, signals, or Kraken paths.**

### Alpaca End-to-End Governance Audit — VERIFIED
- **Timestamp:** 2026-03-16 (droplet run with real data).
- **Runner:** `scripts/run_alpaca_e2e_audit_on_droplet.py` — git pull, sync Telegram from venv/.alpaca_env to .env, verify env, run full chain (Tier 1→2→3→convergence→promotion gate→heartbeat) with --telegram, direct Telegram send test; fetch artifacts; write CSA/SRE reviews.
- **Scripts executed on droplet:** Tier 1/2/3, convergence, promotion gate, heartbeat (all with --force --telegram); packet dirs in state/alpaca_board_review_state.json.
- **Telegram:** Transport verified (direct send returned True). **Operator confirmed message received** (2026-03-16).
- **CSA/SRE:** reports/audit/ALPACA_E2E_CSA_REVIEW.md (PASS), ALPACA_E2E_SRE_REVIEW.md (OK).

### Alpaca Heartbeat — IMPLEMENTED
- **Script:** `scripts/run_alpaca_board_review_heartbeat.py` — Records last heartbeat and Tier 1/2/3 timestamps; optional staleness (--stale-hours, default 24). Reads alpaca_board_review_state.json and alpaca_convergence_state.json; writes `state/alpaca_heartbeat_state.json`. No decisions, no tuning, no promotion. Plan: `docs/ALPACA_PHASE5_HEARTBEAT_PLAN.md`. CSA/SRE: ACCEPT/OK.

### Alpaca Promotion Gate — IMPLEMENTED
- **Script:** `scripts/run_alpaca_promotion_gate.py` — Advisory promotion gate status. Reads convergence state, Tier 2/3 packets (or board fallbacks), SHADOW_COMPARISON_LAST387.json, SRE_STATUS; writes `state/alpaca_promotion_gate_state.json` (gate_ready, blockers, one_liner). No auto-promotion; human approval required. Plan: `docs/ALPACA_PHASE4_PROMOTION_GATE_PLAN.md`. CSA: `reports/audit/CSA_FINDINGS_ALPACA_PHASE4_PROMOTION_GATE_PLAN.md` (ACCEPT). SRE: `reports/audit/SRE_VERDICT_ALPACA_PHASE4_PROMOTION_GATE_PLAN.md` (OK).

### Alpaca Convergence — IMPLEMENTED
- **Script:** `scripts/run_alpaca_convergence_check.py` — Convergence check across Tier 1, Tier 2, Tier 3 (PnL sign consistency + SRE anomaly). Args: --base-dir, --force, --dry-run. Reads `state/alpaca_board_review_state.json` for packet dirs; Tier 1/2/3 packet JSON or fallbacks (rolling_pnl_5d.jsonl, board 7d/30d/last387); `reports/audit/SRE_STATUS.json`. Writes `state/alpaca_convergence_state.json` (convergence_status green/yellow/red, divergence_class none/mild/moderate/severe, one_liner). Advisory only; no auto-block, no promotion logic. Plan: `docs/ALPACA_PHASE3_CONVERGENCE_PLAN.md`. CSA: `reports/audit/CSA_FINDINGS_ALPACA_PHASE3_CONVERGENCE_PLAN.md` (ACCEPT). SRE: `reports/audit/SRE_VERDICT_ALPACA_PHASE3_CONVERGENCE_PLAN.md` (OK).

### Alpaca full engine & data repair (2026-03-30) — OPERATOR CANON
- **When to run:** Hollow `position_metadata` (e.g. `entry_score==0` for all), false `max_drawdown_exceeded` from stale `peak_equity.json` (e.g. 100k vs ~47k live paper equity), and 32/32 capacity with no rotation. **Controlled liquidation** is allowed as a one-shot reset when metadata and risk state are untrustworthy — documented in daily evidence.
- **Orchestrator (droplet):** `git pull` then `python3 scripts/repair/alpaca_full_repair_orchestrator.py --full-repair` (optional `--skip-liquidation`, `--skip-systemd-restart`). Produces evidence under `reports/daily/<ET>/evidence/` (`ALPACA_FULL_REPAIR_*`, `ALPACA_FULL_LIQUIDATION_*`, etc.).
- **Liquidation script (`alpaca_controlled_liquidation.py`):** For a **true** full book reset, **`systemctl stop stock-bot`** (or equivalent) before `--execute` so the loop cannot re-open symbols while you flatten. Then calls `cancel_all_orders()` first, then `close_position(symbol)` with `cancel_orders=True` when the installed `alpaca_trade_api` supports it; on `TypeError` (older SDK), falls back to `close_position(symbol)` only — the first repair droplet run failed all closes with `unexpected keyword argument 'cancel_orders'`. After the first close wave it polls `list_positions` up to ~120s; if anything remains, it runs a **second** close wave on the residual list and polls again (covers partial fills / races). Clears `state/position_metadata.json` **only** when the book is flat; exit code **3** if positions remain (or final position list fails).
- **Peak equity policy:** (1) `scripts/reset_peak_equity_to_broker.py --apply` sets peak to live broker equity. (2) Each `run_risk_checks` calls `sanitize_peak_equity_vs_broker()` so peak cannot stay far above live equity (`PEAK_EQUITY_SANITY_MAX_RATIO`, default 1.28; set `PEAK_EQUITY_SANITY_DISABLE=1` to turn off). (3) Normal ratchet still via `update_peak_equity`.
- **Governor freezes:** `freeze_trading()` writes dict entries with `active: true`. `check_freeze_state()` must treat those as active (fixed 2026-03-30). Clear drawdown-only flags with `scripts/clear_drawdown_governor_freeze.py --apply` or manual edit.
- **Metadata repair:** `scripts/repair/repair_position_metadata_from_logs.py` backfills open positions from last `composite_calculated` per symbol in `logs/scoring_flow.jsonl`. Runtime dashboard/recovery also uses `utils.entry_score_recovery` (attribution.jsonl + scoring_flow). New fills should still go through `mark_open` / `_persist_position_metadata` for full `v2` blocks.
- **Exit tuning (conservative):** Env-only knobs — `V2_EXIT_SCORE_THRESHOLD` (default 0.80), `STALE_TRADE_EXIT_MINUTES`, `TRAILING_STOP_PCT`, optional `EXIT_PRESSURE_*`. Sample: `deploy/alpaca_post_repair.env.sample`.
- **Dashboard:** Open positions API exposes `metadata_instrumented`, `metadata_reconciled_repair_only`, `metadata_gap_flags` for UI truth.
- **Rollback:** Evidence file `ALPACA_FULL_REPAIR_ROLLBACK_<TS>.md` + git revert of the repair commit; restore `position_metadata` / `peak_equity` from backups if taken.

---

## 5.2 PROHIBITED PRACTICES
Cursor MUST NOT:
- read local logs  
- generate reports with 0 trades (unless market closed)  
- skip validation  
- commit incorrect reports  

---

## 5.3 REPORT CHECKLIST
Cursor MUST verify:
- Data source = "Droplet"  
- Trade count > 0 (or documented reason)  
- Timestamp < 1 hour old  
- Validation passed  

---

# 6. DEPLOYMENT WORKFLOW (FULL SOP)

## 6.1 REQUIRED STEPS
Cursor MUST:
1. Commit + push to GitHub  
2. SSH into droplet using `droplet_client.py` (via `deploy_dashboard_via_ssh.py` or similar)  
3. Pull latest code: `git pull origin main`  
4. Restart services (dashboard, trading bot, etc.)  
5. Wait for verification (check health endpoints)  
6. Verify deployment success  
7. Report to user

**VERIFIED WORKFLOW (2026-01-12):**
- ✅ SSH connection via `droplet_client.py` works (paramiko installed)
- ✅ Deployment script `deploy_dashboard_via_ssh.py` successfully deploys
- ✅ Dashboard can be started with: `nohup python3 dashboard.py > logs/dashboard.log 2>&1 &`
- ✅ Health check endpoint responds (Basic Auth required):
  - `set -a && source /root/stock-bot/.env && set +a && curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health`  

---

## 6.2 PROHIBITED ACTIONS
Cursor MUST NOT:
- skip GitHub push  
- skip droplet deployment  
- ask user to run commands  
- assume droplet is updated  
- report early  

---

## 6.3 SSH CONFIG
**DEPLOY_TARGET: 104.236.102.57 (stock-bot)**

**VERIFIED (2026-01-12):** SSH deployment works via `droplet_client.py` with paramiko.

**Preferred (use SSH config alias):** Cursor and scripts should prefer the **alpaca** SSH alias. It uses your `~/.ssh/config` for host, port, and key — one place to manage, and user-confirmed working.

Droplet config (`droplet_config.json`) — **preferred**:
```json
{
  "host": "alpaca",
  "port": 22,
  "username": "root",
  "use_ssh_config": true,
  "project_dir": "/root/stock-bot",
  "connect_timeout": 30,
  "connect_retries": 5
}
```
Ensure `~/.ssh/config` has a `Host alpaca` block that resolves to `104.236.102.57` (and IdentityFile, etc.).

**Alternative (direct IP):** If you don't use an SSH config alias, specify the IP and key explicitly:
```json
{
  "host": "104.236.102.57",
  "port": 22,
  "username": "root",
  "use_ssh_config": false,
  "key_file": "C:/Users/markl/.ssh/id_ed25519",
  "project_dir": "/root/stock-bot",
  "connect_timeout": 30,
  "connect_retries": 5
}
```

**CRITICAL:** 
- All deployments MUST target `104.236.102.57` (stock-bot) — use `droplet_config.json` or DropletClient. Prefer **host "alpaca"** with **use_ssh_config: true** when available.
- **NEVER use `147.182.255.165`** — that IP is for a different droplet/bot. This repo uses `104.236.102.57` only.
- SSH alias **alpaca** resolves to this IP (configure in `~/.ssh/config`).
- **REQUIRED:** `paramiko` library must be installed: `python -m pip install paramiko`
- SSH key must be authorized on droplet (user fixed key mismatch on 2026-01-12)

### STOCK-BOT ISOLATION
- **Repository identity:** stock-bot (equities only). Do not conflate with other bots’ IPs or repos.
- **Droplet binding:** `droplet_config.json` is the single source for host/key; DropletClient MUST use it.
- **Forbidden IP:** `147.182.255.165` — never use for stock-bot. That IP is for a different bot.
- **Canonical droplet (live verify 2026-03-28):** Prefer SSH alias **alpaca** (use_ssh_config true); else **`104.236.102.57`**. **Active clone:** **`/root/stock-bot`** only on that host. Alternate path names (`/root/stock-bot-current`, `/root/trading-bot-current`) appear in **diagnostic scripts** for portability — they were **absent** on the verified Alpaca droplet; see **§ Alpaca droplet — live operational canon** under Alpaca quantified governance.

---

## 6.4 CREDENTIALS & ENVIRONMENT

### Strict format (systemd / `EnvironmentFile`)
**CRITICAL:** `systemd` **`EnvironmentFile`** entries must look exactly like **`KEY=VALUE`** lines in **`/root/stock-bot/.env`**:
- **MUST NOT** use `export ` prefixes on lines systemd reads from the file.
- **MUST NOT** add **trailing spaces** after the value or around `=`.
- **MUST NOT** wrap values in **surrounding quotes** in the file (unless your tooling explicitly requires otherwise — the droplet canon is unquoted `KEY=value`).

Malformed or partial files cause **supervisor exit** and a **`stock-bot.service` restart / crash loop** (`journalctl` will show missing required keys).

### Required variables (partial `.env` = crash loop)
**CRITICAL:** **`/root/stock-bot/.env`** must be **complete** for supervisor boot, dashboard auth, and governance — not Alpaca-only.

| Variable | Requirement |
|----------|-------------|
| **`ALPACA_KEY`** | Alpaca API key ID — **exactly 20 characters** (e.g. `PK…`). |
| **`ALPACA_SECRET`** | Alpaca secret — **exactly 40 characters**. |
| **`ALPACA_BASE_URL`** | Trading **REST** base URL only — e.g. **`https://paper-api.alpaca.markets`** or live equivalent. **No** **`/v2`** suffix on this variable. |
| **`UW_API_KEY`** | Unusual Whales API key — **required for supervisor boot** (`deploy_supervisor.py` / `systemd_start.sh` fail-closed if missing or empty). |
| **`DASHBOARD_USER`** / **`DASHBOARD_PASS`** | Dashboard **HTTP Basic Auth** — **required** for the live dashboard and for **`scripts/dashboard_verify_all_tabs.py`** (source `.env` before running). |
| **`TELEGRAM_BOT_TOKEN`** / **`TELEGRAM_CHAT_ID`** | **Required for governance** Telegram sends (integrity cycle, milestones, notifier paths that use the helper). |

### Credentials location (canonical file)
**CRITICAL:** Production secrets for **`stock-bot.service`** live in:
- **`/root/stock-bot/.env`**

See **Telegram & cross-environment sync** under **Alpaca Telegram Governance** for **`/root/.alpaca_env`** and cron/manual runs — both locations must stay consistent when Telegram or Alpaca vars change.

### Credential Loading
- The systemd service (`stock-bot.service`) automatically loads credentials via `EnvironmentFile=/root/stock-bot/.env`
- `deploy_supervisor.py` uses `load_dotenv()` to load `.env` file
- All services inherit environment variables from the supervisor

### Important Notes
- **DO NOT** commit `.env` file to git (it's in `.gitignore`)
- **DO NOT** truncate or overwrite `.env` with templates or empty placeholders — see **SRE recovery playbook** below if keys must be recovered.
- Credentials are loaded automatically by systemd service

### SRE recovery playbook — memory scraping (April 2026)
**When:** **`/root/stock-bot/.env`** was accidentally **truncated** or overwritten but long-lived daemons may still hold the old environment in RAM.

**Principle:** **Do not assume secrets are gone** until you have checked **live process environments** on the droplet.

**Discovery command (high-signal; redact output in chat logs):**
```bash
grep -z -a 'UW_API_KEY' /proc/*/environ 2>/dev/null | tr '\0' '\n'
```
Repeat with **`DASHBOARD_USER`**, **`DASHBOARD_PASS`**, or other key names. Prefer identifying the owning PID first (e.g. **`uw_flow_daemon.py`** often still has **`UW_API_KEY`** and dashboard vars), then merge **only** the missing lines into **`/root/stock-bot/.env`** with **`chmod 600`**. **Operational helper (optional, repo):** `scripts/_sre_recover_env_from_uw_flow.py` — reads **`uw_flow_daemon`** environ and appends missing keys.

**After recovery:** `sudo systemctl restart stock-bot`, then run **`scripts/dashboard_verify_all_tabs.py`** with `.env` sourced.

---

## 6.5 SYSTEMD SERVICE MANAGEMENT

### Service Details
**NOTE (2026-03-28 live verify):** On the Alpaca droplet, **`trading-bot.service` is not installed** (`not-found`). Use **`stock-bot.service`**.

**stock-bot.service (live configuration):**
- **SERVICE_NAME:** `stock-bot.service`
- **Service file location:** `/etc/systemd/system/stock-bot.service` (+ drop-ins under `stock-bot.service.d/`)
- **Service configuration:**
  - **WorkingDirectory:** `/root/stock-bot`
  - **EnvironmentFile:** `/root/stock-bot/.env`
  - **ExecStart:** **`/root/stock-bot/systemd_start.sh`** (sources venv, runs **`venv/bin/python deploy_supervisor.py`**)
  - **Restart:** `always` (`RestartSec=10` observed)
  - **User:** `root`
  - **Start on boot:** `enabled`

**Manual Dashboard Start (VERIFIED WORKING):**
```bash
cd /root/stock-bot
nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
```

**Dashboard Health Check:**
```bash
set -a && source /root/stock-bot/.env && set +a
curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health
# Should return: {"status":"degraded"|"healthy",...}
```

### Service Management Commands
```bash
# Start/Stop/Restart
sudo systemctl start stock-bot
sudo systemctl stop stock-bot
sudo systemctl restart stock-bot

# Check status
sudo systemctl status stock-bot

# View logs
journalctl -u stock-bot -f          # Follow logs
journalctl -u stock-bot -n 100      # Last 100 lines
journalctl -u stock-bot -b          # Since boot
```

### Service Architecture
- **Entry Point:** `deploy_supervisor.py` (started from `systemd_start.sh` under `stock-bot.service`)
- **Supervisor typically manages child processes:** `dashboard.py`, `uw_flow_daemon.py` (UW API ingestion), `main.py` (core trading engine).
- **Live droplet nuance (2026-03-28):** **`uw-flow-daemon.service`** also runs a dedicated venv `uw_flow_daemon.py`. **`stock-bot-dashboard.service`** runs **`dashboard.py`** with **system** Python and **owns TCP :5000**; the supervisor may still spawn a **second** `dashboard.py` under venv — see **Alpaca droplet — live operational canon** before assuming one dashboard process or one UW daemon instance.

### Migration Notes
The bot was migrated from manual supervisor execution to systemd management:
- ✅ Preserved all trading logic
- ✅ Preserved supervisor architecture (`deploy_supervisor.py`)
- ✅ Added automatic restart on failure
- ✅ Added automatic start on boot
- ✅ Centralized logging via journalctl
- ❌ Did NOT modify trading logic
- ❌ Did NOT modify `deploy_supervisor.py` logic
- ❌ Did NOT modify `.env` file contents

### Troubleshooting
If service won't start:
1. Verify `.env` file exists: `ls -la /root/stock-bot/.env`
2. Check service status: `sudo systemctl status stock-bot`
3. Check logs: `journalctl -u stock-bot -n 50`
4. Verify credentials format in `.env` file (no spaces around `=`)

---

## Alpaca Dashboard — Canonical verification and recovery

### Purpose
Ensure the Alpaca dashboard remains a truthful trust surface and cannot silently regress after deploys or resets.

### Canonical service
- **systemd unit:** `stock-bot-dashboard.service`
- **Runtime:** Flask on **:5000**; **`ExecStart=/usr/bin/python3 /root/stock-bot/dashboard.py`** with `EnvironmentFile=-/root/stock-bot/.env` and `PORT=5000` (live verify 2026-03-28). **`ss -tlnp`** showed **only** this process bound to `:5000`; `deploy_supervisor.py` may still spawn an additional venv `dashboard.py` child — see **Alpaca droplet — live operational canon**.
- **Authoritative source:** origin/main (no SCP hotfixes permitted)

### Canonical endpoints
- **Operational activity:** /api/alpaca_operational_activity?hours=72
  - Must return HTTP 200
  - Must include exact CSA disclaimer:
    “Trades are executing on Alpaca. Data is NOT certified for learning or attribution.”
- **Integrity computed:** /api/telemetry/latest/computed?name=data_integrity
  - Must return HTTP 200
  - ok:false is valid and must render PARTIAL (amber), not error

### Canonical verifier (hard gate)
- **Script:** scripts/dashboard_verify_all_tabs.py
- **Command:**
  ```bash
  python3 -u scripts/dashboard_verify_all_tabs.py --json-out <path>.json
  ```
- **Pass condition:** exit code 0 and all tabs HTTP 200 (currently 25/25)

### Canonical proof location
- Droplet proof bundle: reports/audit/ALPACA_DASHBOARD_DROPLET_PROOF_<TS>.md
- Verifier JSON: reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<TS>.json
- Proof must be marked executed:true for CSA clearance.

### Recovery procedure (if dashboard regresses)
1. `git fetch origin main && git reset --hard origin/main`
2. `systemctl restart stock-bot-dashboard.service`
3. Run the canonical verifier (above).
4. If verifier fails:
   - Inspect failing endpoint/status in the JSON output
   - Fix in repo (never SCP)
   - Re-run verifier until exit 0
5. Update droplet proof + closeout only after verifier passes

### Governance status
- Dashboard truth: RESTORED and PERMANENTIZED
- CSA status: PERMANENTIZED_OK
- Permanentizing commit: 1bab716d51aca0373878612b1f66d20ccb53639f

### Authoritative artifacts (do not copy contents; reference only)
- reports/audit/ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1815Z.md
- reports/audit/ALPACA_DASHBOARD_UI_CLOSEOUT_20260326_1815Z.md
- reports/audit/ALPACA_DASHBOARD_PERMANENTIZE_CLOSEOUT_20260326_2015Z.md

---

## 6.6 DASHBOARD DEPLOYMENT (VERIFIED 2026-01-12, UPDATED 2026-03-28)

### Dashboard URL and How It Runs
- **Live URL:** http://104.236.102.57:5000/
- **Primary service for :5000 (live verify 2026-03-28):** **`stock-bot-dashboard.service`** — **`/usr/bin/python3 /root/stock-bot/dashboard.py`**, `PORT=5000`. **`ss -tlnp`** showed this PID as the listener.
- **Supervisor stack:** `stock-bot.service` → **`systemd_start.sh`** → **`deploy_supervisor.py`** → child processes including **`venv` `dashboard.py`**, **`main.py`**, and often **`uw_flow_daemon.py`** (while **`uw-flow-daemon.service`** may also run UW ingestion separately — see **Alpaca droplet — live operational canon**).
- **Stale-PID warning still applies:** Any **extra** `dashboard.py` not under the intended unit can hold or confuse port binding; **`pkill -f 'dashboard\.py'`** before restarts remains the safe deploy hygiene when changing dashboard code.
- **CRITICAL — Stale dashboard PIDs:** When you run `sudo systemctl restart stock-bot`, systemd kills only the **supervisor** process. The supervisor’s **child** (e.g. `dashboard.py`) may **survive as an orphan** and keep holding port 5000. A **new** supervisor then starts a **new** dashboard, which may bind to another port (e.g. 5001). Users hitting :5000 then see **old code** (e.g. no Strategy column, no Wheel open positions). So **every deploy must kill all dashboard processes** before or when restarting, so the **new** supervisor’s dashboard is the only one and binds 5000.

### Deploy Steps (Use This Every Time)
1. **Push:** Commit and push to GitHub.
2. **Deploy via DropletClient:** `DropletClient().deploy()` (or equivalent SSH).
3. **Deploy sequence on droplet (automated in `droplet_client.deploy()`):**
   - `git pull origin main`
   - **`pkill -f 'dashboard\.py'`** — kill ALL dashboard processes (stale orphans).
   - `sudo systemctl restart stock-bot` — supervisor and fresh children (one dashboard) start.
4. **User after deploy:** **Hard-refresh** the browser (Ctrl+Shift+R or Ctrl+F5) so cached HTML/JS are dropped and the new dashboard (Strategy column, Wheel tab open positions) loads.
5. **Verify:** Open http://104.236.102.57:5000/ → Positions tab: first column must be "Strategy" (Wheel/Equity). Wheel Strategy tab: "Current wheel positions" section must show if state/wheel_state.json has open CSPs/CCs.

### Deployment Process (Scripts)
**VERIFIED WORKING:** SSH deployment via `droplet_client.py` works correctly. `deploy()` now runs `pkill -f 'dashboard\.py'` before restarting stock-bot.

**Deployment Script:** `deploy_dashboard_via_ssh.py` (alternative). Prefer `DropletClient().deploy()` so stale-dashboard kill is included.

**Required Dependencies:**
- `paramiko` library: `python -m pip install paramiko`
- `droplet_config.json` configured with correct SSH key path
- SSH key authorized on droplet (user fixed key mismatch on 2026-01-12)

### Deployment Steps (VERIFIED)
1. **Code Push:** Commit and push to GitHub
2. **SSH Connection:** Use `DropletClient()` from `droplet_client.py`
3. **Pull Code:** `git pull origin main` on droplet
4. **Kill stale dashboard then restart:** 
   - `pkill -f 'dashboard\.py'`  (or `pkill -f 'python.*dashboard.py'`) so no orphan holds port 5000
   - `sudo systemctl restart stock-bot`
5. **Verify (Basic Auth required):** `set -a && source /root/stock-bot/.env && set +a && curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health`

### Dashboard Startup
**VERIFIED METHOD (2026-01-12):**
```bash
cd /root/stock-bot
nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
```

**Health Check:**
```bash
set -a && source /root/stock-bot/.env && set +a
curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health
# Expected: {"status":"degraded"|"healthy","alpaca_connected":true,...}
```

### Dashboard Endpoints
- **Main:** http://104.236.102.57:5000/
- **Health:** http://104.236.102.57:5000/health
- **Positions:** http://104.236.102.57:5000/api/positions
- **Health Status:** http://104.236.102.57:5000/api/health_status

### Recent Fixes (2026-01-12)
- ✅ Fixed blocking file read operations (`readlines()` → chunk-based reading)
- ✅ Optimized large file processing (10,000 line limit, efficient reading)
- ✅ All endpoints return valid JSON even on errors
- ✅ Memory-efficient file operations

### Top Strip (Health, P&L today, 7d, Last signal)
- **Data source:** `loadTopStrip()` fetches `/api/sre/health`, `/api/executive_summary?timeframe=24h`, `/api/executive_summary?timeframe=7d`. "Last signal" comes from `/api/health_status` (or health payload) `last_signal_timestamp`; if that API or `signal_history_storage.get_last_signal_timestamp()` fails, the UI shows "Last signal: Error".
- If Health / P&L today / P&L 7d show "—", the SRE or executive summary endpoints may be failing, unreachable, or the engine may be down. "Last signal: Error" usually means the health/signal-history path failed (e.g. import error or missing file).

### Troubleshooting Dashboard
If dashboard not responding:
1. Check if running: `ps aux | grep dashboard.py | grep -v grep`
2. **If multiple dashboard PIDs:** run `pkill -f 'dashboard\.py'` then `sudo systemctl restart stock-bot` so only one dashboard runs on 5000.
3. Check logs: `tail -50 /root/stock-bot/logs/dashboard.log`
4. Start manually (only if not using supervisor): `cd /root/stock-bot && nohup python3 dashboard.py > logs/dashboard.log 2>&1 &`
5. Verify port: `netstat -tlnp | grep 5000` or `ss -tlnp | grep 5000`
6. **After code deploy:** always hard-refresh browser (Ctrl+Shift+R) so new HTML/JS load.

---

## 6.7 FAILURE POINT MONITORING + SELF-HEALING SYSTEM (UPDATED 2026-01-14)

### System Overview
The failure point monitoring system tracks all critical system components and provides self-healing for recoverable issues. It answers "Why am I not trading?" with explicit, accurate explanations.

### Failure Point Categories

**FP-1.x: Data & Signal Generation**
- **FP-1.1:** UW Daemon Running - Checks if `uw_flow_daemon.py` process is active
- **FP-1.2:** Cache File Exists - Verifies `data/uw_flow_cache.json` exists and has data
- **FP-1.3:** Cache Fresh - Checks cache file age (< 10 min = OK, < 30 min = WARN, > 30 min = ERROR)
- **FP-1.4:** Cache Has Symbols - Verifies cache contains symbol data
- **FP-1.5:** UW API Authentication - Checks for recent 401/403 errors in daemon logs

**FP-2.x: Scoring & Evaluation**
- **FP-2.1:** Adaptive Weights Initialized - Verifies `state/signal_weights.json` has 21 components

**FP-3.x: Gates & Filters**
- **FP-3.1:** Freeze State - Checks `check_performance_freeze()` and `state/governor_freezes.json`
  - **Single Source of Truth:** Matches `monitoring_guards.py:check_freeze_state()` exactly
  - **Files Checked:** `state/governor_freezes.json` (active freezes where value == True)
  - **Performance Freeze:** Automatically set by `check_performance_freeze()` in LIVE mode only
- **FP-3.2:** Max Positions Reached - Checks Alpaca positions vs `MAX_CONCURRENT_POSITIONS` (16)
- **FP-3.3:** Concentration Gate - Calculates `net_delta_pct` and checks if > 70% (blocking bullish entries)
  - **Matches:** `main.py:5794` - Blocks when `net_delta_pct > 70.0` and `direction == "bullish"`

**FP-4.x: Execution & Broker**
- **FP-4.1:** Alpaca Connection - Tests `api.get_account()` connectivity
- **FP-4.2:** Alpaca API Authentication - Checks for 401/403 errors
- **FP-4.3:** Insufficient Buying Power - Warns if buying power < $100

**FP-6.x: System & Infrastructure**
- **FP-6.1:** Bot Running - Checks if `main.py` process is active (multiple pattern matching + port 8081 check)

### Freeze State Contract

**Single Source of Truth:** `monitoring_guards.py:check_freeze_state()`

**Logic:**
1. First checks `check_performance_freeze()` (only in LIVE mode, freezes on extreme losses)
2. Then checks `state/governor_freezes.json` for any active freezes (value == True)

**Files:**
- ✅ `state/governor_freezes.json` - ACTIVE (single source of truth)
- ❌ `state/pre_market_freeze.flag` - REMOVED (stale mechanism, cleaned up 2026-01-14)

**How Bot Uses It:**
- `main.py:7430` - Early exit if frozen: `if not check_freeze_state(): return {"clusters": 0, "orders": 0}`
- `main.py:6050` - Passed to expectancy gate: `freeze_active = check_freeze_state() == False`

**How Panel Reads It:**
- `failure_point_monitor.py:check_fp_3_1_freeze_state()` - Matches main.py logic exactly

**Self-Healing:**
- ❌ **NO self-healing for freezes** - Must be manually cleared (correct behavior)

### Trading Blockers Function

**Function:** `get_trading_blockers()` in `failure_point_monitor.py`

**Purpose:** Provides explicit answer to "Why am I not trading?"

**Returns:**
```python
{
    "blocked": bool,
    "blockers": [
        {
            "type": "freeze_state" | "max_positions" | "concentration_gate" | "system_error",
            "active": bool,
            "reason": str,
            "source": str,
            "can_self_heal": bool,
            "requires_manual_action": bool,
            "fp_id": str
        }
    ],
    "summary": str
}
```

**Usage:**
- Dashboard `/api/failure_points` endpoint includes blockers
- Dashboard UI shows "Why am I not trading?" panel when blocked
- `get_trading_readiness()` includes blockers in response

### Self-Healing System

**Routines:**
1. **`_heal_uw_daemon()`** - Restarts UW daemon (kills process, supervisor restarts; fallback: systemd)
2. **`_heal_weights_init()`** - Initializes weights file via `fix_adaptive_weights_init.py`
3. **`_heal_bot_restart()`** - Restarts bot service via systemd

**Logging:**
- ✅ All self-healing actions logged to `logs/self_healing.jsonl` (structured JSONL)
- ✅ Includes: timestamp, FP ID, action, message, success status
- ✅ Also prints to console for immediate visibility

**Safety:**
- ✅ All routines are safe operational repairs
- ✅ No modifications to sacred logic
- ✅ No deletion of important state
- ✅ No masking of real problems

### Dashboard Integration

**Endpoint:** `/api/failure_points`
- Returns trading readiness status
- Includes all failure point details
- Includes blockers explanation

**UI Tab:** "⚠️ Trading Readiness"
- Shows overall readiness (READY/DEGRADED/BLOCKED)
- Lists all failure points with status
- Shows "Why am I not trading?" panel when blocked
- Auto-refreshes every 30 seconds

### Usage

**Check Trading Readiness:**
```bash
python3 -c "from failure_point_monitor import get_failure_point_monitor; m = get_failure_point_monitor(); r = m.get_trading_readiness(); print(r['readiness'])"
```

**Get Trading Blockers:**
```bash
python3 -c "from failure_point_monitor import get_failure_point_monitor; m = get_failure_point_monitor(); b = m.get_trading_blockers(); print(b['summary'])"
```

**View Self-Healing Logs:**
```bash
tail -20 logs/self_healing.jsonl | jq '.'
```

---

## 6.8 TRADING BLOCKERS EXPLANATION (NEW 2026-01-14)

### Common Blockers

1. **Freeze State (FP-3.1)**
   - **Reason:** Trading frozen by operator or performance freeze
   - **Source:** `state/governor_freezes.json` or `check_performance_freeze()`
   - **Action Required:** Manual - Clear freeze flags in `governor_freezes.json`

2. **Max Positions (FP-3.2)**
   - **Reason:** At capacity (16/16 positions)
   - **Source:** Alpaca API position count
   - **Action Required:** None - Wait for natural exits or manually close positions

3. **Concentration Gate (FP-3.3)**
   - **Reason:** Portfolio >70% long-delta, blocking bullish entries
   - **Source:** Portfolio calculation (net_delta / account_equity)
   - **Action Required:** None - Wait for exits, bearish signals, or manually close positions

4. **System Errors (FP-1.x, FP-4.x, FP-6.x)**
   - **Reason:** Critical system component failed
   - **Source:** Various (daemon, cache, API, bot process)
   - **Action Required:** Check self-healing status, may require manual intervention

---

## 6.9 ALPHA UPGRADE (Displacement Policy, Shorts, EOD) — 2026-01-26

### New Config Keys (env)

- **`DISPLACEMENT_ENABLED`** (default `true`): Master switch for displacement policy.
- **`DISPLACEMENT_MIN_HOLD_SECONDS`** (default `1200`, 20 min): Min hold before displacement unless emergency (score &lt; 3 or pnl &lt; -0.5%).
- **`DISPLACEMENT_MIN_DELTA_SCORE`** (default `0.75`): Challenger must beat current by at least this.
- **`DISPLACEMENT_REQUIRE_THESIS_DOMINANCE`** (default `true`): Require at least one of flow/regime/dark_pool win.
- **`DISPLACEMENT_THESIS_DOMINANCE_MODE`** (default `flow_or_regime`): Mode for thesis dominance.
- **`DISPLACEMENT_LOG_EVERY_DECISION`** (default `true`): Log every displacement evaluate to system_events.

### New Logs / Events

- **`logs/system_events.jsonl`**: `subsystem=displacement`, `event_type=displacement_evaluated`, `severity=INFO`, `details={allowed, reason, ...}`.
- **`close_reason`** for displacement exits: `displaced_by_<SYMBOL>|delta=<x>|age_s=<y>|thesis=<reason>` (when policy diagnostics present).

### Toggle-Back (Revert Displacement Tuning)

Do **not** remove code; revert by config:

- `DISPLACEMENT_MIN_HOLD_SECONDS=0`
- `DISPLACEMENT_MIN_DELTA_SCORE=0`
- `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE=false`

### Verification

```bash
python scripts/verify_alpha_upgrade.py
```

Exits non-zero on any FAIL. Checks: displacement policy present, displacement logging, shorts sanity, feature snapshot, shadow experiments (if enabled), EOD report.

### EOD Alpha Diagnostic

```bash
python reports/_daily_review_tools/generate_eod_alpha_diagnostic.py --date YYYY-MM-DD
```

Output: `reports/EOD_ALPHA_DIAGNOSTIC_<DATE>.md`. Headline PnL, win rate, top/bottom symbols, displacement summary, data availability.

### Displacement Logs / Variant Scoreboard

- **Displacement:** Filter `logs/system_events.jsonl` for `subsystem=displacement`, `event_type=displacement_evaluated`. Use `details.allowed`, `details.reason`, `details.delta_score`, `details.age_seconds` for audit.
- **Shadows / variants:** When shadow experiments enabled, see `logs/shadow.jsonl` for `event_type=shadow_variant_decision` and `shadow_variant_summary`.

---

## 6.10 ALPHA DISCOVERY (Thesis Tags, Directional Gate, Shadow Matrix) — 2026-01-27

### Thesis Tags

- **Module:** `telemetry/thesis_tags.py` — `derive_thesis_tags(snapshot) -> dict`
- **Tags:** `thesis_flow_continuation`, `thesis_flow_reversal`, `thesis_dark_pool_accumulation`, `thesis_dark_pool_distribution`, `thesis_premarket_gap_continuation`, `thesis_event_earnings_drift`, `thesis_congress_tailwind`, `thesis_insider_tailwind`, `thesis_regime_alignment_score` (0–1), `thesis_vol_expansion`, `thesis_vol_compression`
- **Contract:** Missing data => `None` (never silently `False`).

### Directional Gate (HIGH_VOL)

- **HIGH_VOL:** Top quartile `realized_vol_20d`. For HIGH_VOL only:
  - **Longs:** Require at least one of `thesis_flow_continuation`, `thesis_dark_pool_accumulation`, `thesis_regime_alignment_score >= 0.6`.
  - **Shorts:** Require at least one of `thesis_flow_reversal`, `thesis_dark_pool_distribution`, `thesis_regime_alignment_score <= 0.4`.
- **Logging:** `subsystem=directional_gate`, `event_type=blocked_high_vol_no_alignment`, `feature_snapshot`, `thesis_tags` in `logs/system_events.jsonl`. Does **not** reduce vol exposure; prevents directional guessing in volatile names.

### Shadow Experiment Matrix

- **Config:** `SHADOW_EXPERIMENTS_ENABLED`, `SHADOW_EXPERIMENTS` (list of variants), `SHADOW_MAX_VARIANTS_PER_CYCLE` (default 4).
- **Module:** `telemetry/shadow_experiments.py` — `run_shadow_variants(live_context, candidates, positions)`. Writes **only** to `logs/shadow.jsonl`; **no** live orders.
- **Events:** `shadow_variant_decision` (per symbol/variant), `shadow_variant_summary` (per variant/cycle).

### Trade / Exit Intent (Run Log)

- **`logs/run.jsonl`:** `event_type=trade_intent` (feature_snapshot, thesis_tags, displacement_context) at entry; `event_type=exit_intent` (feature_snapshot_at_exit, thesis_tags_at_exit, thesis_break_reason) at exit. Additive only.

### How to Interpret EOD Alpha Tables

- **Headline:** Total PnL, win rate, top/bottom symbols — same as before.
- **Winners vs Losers:** Counts; use for feature effect-size (mean winners vs mean losers) when you have trade-level snapshots.
- **Telemetry:** `trade_intent` / `exit_intent` counts and `directional_gate` blocks — confirm live decisions are explained.
- **Shadow scoreboard:** Per-variant `would_enter` / `would_exit` / blocked — use to see **what to turn up** (variants that would have traded more) and **what to turn down** (variants that block more).
- **Data availability:** PASS/FAIL per dataset; use substitutes when documented.

---

## 6.11 Phase-2 Activation (Log Sinks, Heartbeat, Verification) — 2026-01-27

### Config (env)

- **`PHASE2_TELEMETRY_ENABLED`** (default `true`): Gate trade_intent/exit_intent emission.
- **`PHASE2_HEARTBEAT_ENABLED`** (default `true`): Emit phase2_heartbeat once per cycle.
- **`PHASE2_REQUIRE_SYMBOL_RISK_FEATURES`** (default `true`): If symbol_risk missing, emit CRITICAL and set high_vol_count=0.

### Canonical Log Sinks

- **Startup:** `_phase2_confirm_log_sinks()` runs when bot starts (`__main__`). Ensures `logs/run.jsonl`, `logs/system_events.jsonl`, `logs/shadow.jsonl`, `logs/orders.jsonl` are writable.
- **Event:** `subsystem=phase2`, `event_type=log_sink_confirmed`, `details={resolved_paths, writable}`. If any not writable → CRITICAL + fail fast (exit 1).

### Phase-2 Heartbeat

- **Once per cycle** (after run_once + evaluate_exits): `subsystem=phase2`, `event_type=phase2_heartbeat`, `details={ts, cycle_id, telemetry_enabled, shadow_enabled, wrote_trade_intent_count_this_cycle, wrote_exit_intent_count_this_cycle, wrote_shadow_decision_count_this_cycle, symbol_risk_feature_count, high_vol_threshold, high_vol_symbol_count}`.
- If **`PHASE2_REQUIRE_SYMBOL_RISK_FEATURES`** and symbol_risk empty → `event_type=symbol_risk_missing_required`, `severity=CRITICAL` before heartbeat.

### Trade / Exit Intent (Extended)

- **trade_intent:** Emitted for **every** entry attempt (blocked or entered). Includes `decision_outcome` (`entered`|`blocked`), `blocked_reason` when blocked.
- **exit_intent:** `thesis_break_reason` required; use `unknown` + `thesis_break_unknown_reason` when indeterminable.

### Shadow

- After `run_shadow_variants`: `subsystem=phase2`, `event_type=shadow_variants_rotated`, `details={variants_run_this_cycle}`.
- Shadow **never** places orders; only writes to `logs/shadow.jsonl`.

### EOD Diagnostic

- **Sections:** Winners vs Losers, High-Volatility Alpha, Shadow Scoreboard, Data availability, **Section presence and FAIL reasons**.
- If a section cannot be populated (e.g. symbol_risk missing), report **explicit FAIL** reasons; do not silently omit.

### Verification (run on droplet)

1. **Restart** service safely; **wait 5 minutes** of runtime.
2. **Runtime identity:** `python3 scripts/phase2_runtime_identity.py` → `reports/PHASE2_RUNTIME_IDENTITY.md` (systemd units, WorkingDirectory, git rev, python path).
3. **Activation proof:** `python3 scripts/phase2_activation_proof.py --date YYYY-MM-DD` → `reports/PHASE2_ACTIVATION_PROOF_<DATE>.md` (heartbeats, trade_intent, shadow, symbol_risk, EOD, PASS/FAIL).
4. **Audit:** `python3 scripts/phase2_forensic_audit.py --date YYYY-MM-DD --local` → `reports/PHASE2_VERIFICATION_SUMMARY_<DATE>.md` + `exports/VERIFY_*.csv`.

**From local (fetch from droplet):**

```bash
python scripts/run_phase2_audit_on_droplet.py --date YYYY-MM-DD
```

Uploads audit/proof/runtime-identity scripts, runs them on droplet, fetches reports and CSVs.

**Success criteria:** phase2_heartbeat present; trade_intent present; shadow_variant_decision present (when enabled); symbol_risk_features.json exists and >0 symbols; EOD has all required sections.

---

# 10. DECISION INTELLIGENCE TRACE CONTRACT (2026-01)

Every trade or block decision MUST be explained by a **multi-layer intelligence trace**. There must never be a single opaque reason. Every decision must show: which signals fired, which opposed, how they combined, and why the final decision was made.

## 10.1 Schema: DecisionIntelligenceTrace

```text
DecisionIntelligenceTrace {
  intent_id          : str (UUID)
  symbol             : str
  side_intended      : str ("buy" | "sell")
  ts                 : str (ISO)
  cycle_id           : int | null

  signal_layers: {
    alpha_signals    : [{ name, value, score, direction, confidence }]
    flow_signals     : [{ name, value, score, direction, confidence }]
    regime_signals   : [{ name, value, score, direction, confidence }]
    volatility_signals : [{ name, value, score, direction, confidence }]
    dark_pool_signals  : [{ name, value, score, direction, confidence }]
  }

  opposing_signals   : [{ name, layer, reason, magnitude }]

  aggregation: {
    raw_score, normalized_score, direction_confidence, score_components
  }

  gates: {
    directional_gate : { passed, reason }
    risk_gate        : { passed, reason }
    capacity_gate    : { passed, reason }
    displacement_gate: { evaluated, passed, incumbent_symbol, challenger_delta, min_hold_remaining }
  }

  final_decision: {
    outcome          : "entered" | "blocked"
    primary_reason    : str
    secondary_reasons : [str]
  }
}
```

Object MUST be serializable and logged verbatim with every trade_intent.

## 10.2 Invariants

- **All trade_intent emits MUST include intelligence_trace.** Every emit (entered or blocked) must carry a populated trace; there are no exceptions once this contract is in force.
- **Coverage rule:** No block site may emit without a trace. Every call to `_emit_trade_intent` / `_emit_trade_intent_blocked` must pass `intelligence_trace`.
- **At least 2 signal layers** must contribute; otherwise the decision is INVALID.
- **Incremental build only:** use `build_initial_trace`, then `append_gate_result` per gate, then `set_final_decision` before emit. Gates and `final_decision` must always be present before emit.
- **Size cap:** serialized trace MUST be &lt; 500KB per trace.
- If **blocked**, `primary_reason` MUST map to a gate OR opposing signal.
- **No module overwrites another** when appending to the trace; each gate/signal appends only its own slice.

### 10.2.1 Missing-trace behavior

If a trade_intent is emitted with `decision_outcome` in `{entered, blocked}` and `intelligence_trace` is missing, the runtime MUST emit a **CRITICAL** system_event: `subsystem="telemetry"`, `event_type="missing_intelligence_trace"`, with `symbol`, `decision_outcome`, `blocked_reason` (if any). The trade_intent is still written (no crash); the CRITICAL event makes omissions impossible to ignore in production.

## 10.3 Blocked reason codes (enum)

Replace opaque `blocked_reason` strings with:

- `blocked_reason_code` — one of: `capacity_full`, `displacement_min_hold`, `displacement_no_dominance`, `displacement_blocked`, `displacement_failed`, `directional_conflict`, `blocked_high_vol_no_alignment`, `risk_exceeded`, `symbol_exposure_limit`, `sector_exposure_limit`, `opposing_signal_override`, `score_below_min`, `max_positions_reached`, `symbol_on_cooldown`, `momentum_ignition_filter`, `market_closed`, `long_only_blocked_short_entry`, `regime_blocked`, `concentration_gate`, `theme_exposure_blocked`, `other`.
- `blocked_reason_details` — structured: `{ primary_reason, gates }`. Each MUST reference the trace.

## 10.4 trade_intent extensions (additive only)

- `intent_id`
- `intelligence_trace` (full object)
- `active_signal_names[]`
- `opposing_signal_names[]`
- `gate_summary`
- `final_decision_primary_reason`
- When blocked: `blocked_reason_code`, `blocked_reason_details`

**DO NOT** remove existing fields (`blocked_reason` retained for backward compat).

## 10.5 Rules for future contributors

1. Every call to `_emit_trade_intent` / `_emit_trade_intent_blocked` MUST pass a populated `intelligence_trace` when telemetry is enabled.
2. Build the trace incrementally: `build_initial_trace` at decision start, `append_gate_result` at each gate, `set_final_decision` before emit.
3. Validate with `validate_trace()` before emit; if invalid, log and do not treat the decision as explained.
4. Dry-run validation: `python3 scripts/validate_intelligence_trace_dryrun.py` MUST pass (trace exists, ≥2 layers, gates populated, final_decision coherent, size &lt; 500KB).## WHEEL STRATEGY DASHBOARD INTEGRATION (2026-02-02)
- **strategy_id and wheel-specific fields** surfaced in stock-bot dashboard and API; no trade engine changes.
- **Dashboard:** Closed Trades tab shows strategy_id (Equity/Wheel), filter (All / Equity only / Wheel only), and wheel columns when strategy_id = wheel: wheel_phase, option_type, strike, expiry, dte, premium, assigned, called_away.
- **API:** `GET /api/stockbot/closed_trades` returns `closed_trades` (list) and `count`; each record has `strategy_id`, `wheel_phase`, `option_type`, `strike`, `expiry`, `dte`, `delta_at_entry`, `premium`, `assigned`, `called_away` (nullable for equity). `GET /api/stockbot/wheel_analytics` returns wheel-only metrics: premium_collected, assignment_rate_pct, call_away_rate_pct, expectancy_per_trade_usd, realized_pnl_sum.
- **Loader:** `dashboard._load_stock_closed_trades()` reads attribution.jsonl (closed trades with strategy_id from context) and telemetry.jsonl (strategy_id=wheel events); combines and sorts by timestamp.
- **Wheel Strategy tab:** Dedicated analytics panel (premium, assignment, call-away, expectancy); read-only.
- **Diagnostics:** `scripts/audit_stock_bot_readiness.py` check `stockbot_closed_trades_wheel_fields` verifies strategy_id and wheel phase/option metadata; `scripts/verify_dashboard_contracts.py` includes `/api/stockbot/closed_trades` and `/api/stockbot/wheel_analytics`. Full-integration dashboard check validates both endpoints.
- **Canonical field names:** Per wheel_strategy and MEMORY_BANK §2.2.1: strategy_id, phase (exposed as wheel_phase in API/UI), option_type, strike, expiry, dte, delta_at_entry, premium, assigned, called_away.
- **Deployment (live):** Pushed to GitHub; deployed to droplet via `deploy_dashboard_via_ssh.py` (git pull + dashboard restart only; no trade engine restart). Droplet at 104.236.102.57; dashboard at http://104.236.102.57:5000/. Post-deploy verification: `/api/stockbot/closed_trades` and `/api/stockbot/wheel_analytics` return 200 (verified 2026-02-02). To re-verify: `python scripts/verify_wheel_endpoints_on_droplet.py`.- **Dashboard endpoint map:** `reports/DASHBOARD_ENDPOINT_MAP.md` — canonical mapping of all API routes to data locations. All paths resolved against `_DASHBOARD_ROOT` (cwd-independent). Perf: XAI auditor max 3k lines; system_events tail-only read (~200KB); no engine data modified.

### Dashboard Data Mapping Audit (2026-02-05)
- **Closed trades:** `_load_stock_closed_trades` now reads `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` (v2 equity exits), `logs/telemetry.jsonl`. Deduped by (symbol, timestamp). Paths resolved via `(_DASHBOARD_ROOT / LogFiles.*).resolve()`.
- **Wheel analytics:** Primary from closed_trades (strategy_id=wheel); fallback `reports/*_stock-bot_wheel.json`, `state/wheel_state.json` when logs empty.
- **Wheel universe health:** Primary `state/wheel_universe_health.json`; when missing, derives from `config/universe_wheel.yaml` and `state/daily_universe_v2.json` (no external script required).
- **Strategy comparison:** `reports/{date}_stock-bot_combined.json` from `scripts/generate_daily_strategy_reports.py`.
- **Regime/posture:** `state/market_context_v2.json`, `state/regime_posture_state.json`; paths resolved via _DASHBOARD_ROOT.
- **Rule:** Dashboard connects to logs/state/config only; NEVER modifies trading engine. See `reports/DASHBOARD_ENDPOINT_MAP.md`.
- **Profitability & Learning tab:** `/api/profitability_learning` serves live CSA verdict + trade state and pre-rendered `reports/board/PROFITABILITY_COCKPIT.md`. Cockpit is regenerated automatically after each CSA 100-trade run (`run_csa_every_100_trades.py`), on day reset (`reset_csa_trade_count_for_today.py`), and optionally via cron; see `reports/audit/DROPLET_CSA_AND_COCKPIT.md`.

### Dashboard Rationalization Pass (2026-02-09)
- **Canonical layout:** See `docs/TRADING_DASHBOARD.md` for tab layout, data sources, and where to find Health, P&L, Wheel, and scoring.
- **Core cockpit (top-level):** Positions, Closed Trades, Executive Summary, SRE Monitoring. Health and P&L remain always visible via Top Strip and Executive Summary.
- **Strategy:** Wheel Strategy (includes Wheel Universe Health as sub-panel), Strategy Comparison.
- **Advanced (under “More” dropdown):** Signal Review, Natural Language Auditor, Trading Readiness, Telemetry.
- **Merged/removed from main bar:** Wheel Universe Health merged into Wheel Strategy tab (no data source removed).
- **Scoring labels:** UI shows “Entry Signal Strength” and “Current Signal Strength” (backend still `entry_score` / `current_score` from position metadata and live composite). Real values from engine; no legacy placeholders.
- **Top Strip:** Health (SRE), P&L today, P&L 7d, Last signal, Last update. Populated by `loadTopStrip()` (SRE health + executive summary 24h/7d).
- **Executive Summary:** Now includes Health & Wheel at a glance (from `/api/sre/health`, `/api/stockbot/wheel_analytics`).
- **Where to look:** Health → Executive Summary + SRE tab + Top Strip. P&L → Executive Summary + Positions + Closed Trades + Top Strip. Wheel → Wheel Strategy tab + Executive Summary + Closed Trades (filter). Scoring → Positions table columns (Entry/Current Signal Strength).

### Wheel Strategy Execution & Dashboard Data Activation (2026-02-09)
- **What was addressed:** Wheel had no explicit lifecycle logging; premium was not recorded on fill; dashboard could show zeros when wheel had not yet executed or when telemetry lacked premium.
- **Fixes:** (1) Explicit wheel lifecycle events in `logs/system_events.jsonl` (subsystem=wheel): wheel_run_started, wheel_csp_skipped (with reason), wheel_order_submitted, wheel_order_filled (with premium). (2) After each CSP order submit, wheel strategy polls Alpaca for fill (up to 5×2s); when filled, records **premium** (filled_avg_price × 100) in the same telemetry record. (3) Fallback DTE window: if no contracts in config DTE range, try up to 21 DTE once to allow one trade. (4) Regime is modifier-only; wheel is not gated by regime (comment in main.py and docs/REGIME_DETECTION.md).
- **How to validate:** (1) Run bot during market hours; check `logs/system_events.jsonl` for subsystem=wheel. (2) If a wheel order fills, check `logs/telemetry.jsonl` for strategy_id=wheel and non-null premium. (3) Dashboard Wheel Strategy tab and `/api/stockbot/wheel_analytics` show total_trades and premium_collected from telemetry + attribution. (4) Run `python scripts/generate_daily_strategy_reports.py`; confirm `reports/*_stock-bot_wheel.json` and combined report. (5) Scoring: Positions table uses entry_score from metadata and current_score from live composite (no static placeholders).

### Wheel root cause & verification playbook (2026-02-09)
- **Definitive outcome (ran on droplet 2026-02-09):** **A — Wheel NOT RUNNING.** Evidence: wheel_run_started = 0 in logs/system_events.jsonl; config had wheel.enabled = True. Root cause: **trading bot process had been running since Feb 07 and was never restarted after wheel-enabled code was deployed**; in-memory code never reached the wheel block. Full report: `reports/WHEEL_ROOT_CAUSE_REPORT_2026-02-09.md`.
- **Fix applied on droplet:** `sudo systemctl restart stock-bot` (new process 20:23 UTC 2026-02-09). **Deployment rule:** After pushing wheel or main-loop changes, restart stock-bot on droplet so the process loads new code.
- **Outcomes (for future runs):** Run `python3 scripts/wheel_root_cause_report.py --days 5` on droplet to get A/B/C/D.
- **Outcomes:** A = Wheel NOT RUNNING (scheduling/config/dispatch); B = RUNNING but ALWAYS SKIPPING (eligibility/universe/contracts); C = SUBMITTING but NOT FILLING (broker/liquidity/pricing); D = Pipeline/counting bug (dashboard or strategy_id/filter).
- **Fixes applied (minimum safe):** (1) Wheel now runs whenever `wheel.enabled` is true even if `strategy_context` fails to import (main.py: run wheel with or without context manager so dispatch is not blocked). (2) Wheel analytics contract test: `python3 scripts/test_wheel_analytics_contract.py` — given fixture with strategy_id=wheel and premium, analytics aggregation must report total_trades ≥ 1 and premium_collected ≥ 0 (for CI/regression). (3) Regime remains modifier-only; no gating.
- **Verification (next cycle):** (1) On droplet, run `wheel_root_cause_report.py --days 5` and open the generated report. (2) If A: confirm strategies.yaml wheel.enabled and that no exception prevents wheel invocation. (3) If B: use report’s skip-reason table; address top reasons (universe/DTE/limits) without relaxing risk limits broadly. (4) If C: inspect last submitted orders; improve order type/price within policy; add “not filled because …” logs. (5) If D: ensure _load_stock_closed_trades and wheel_analytics filter include strategy_id=wheel; run contract test. (6) Truth checks: wheel_run_started each cycle; skip reasons logged if skipping; order_submitted/order_filled with order_id/premium when applicable; telemetry and dashboard analytics consistent.
- **Docs:** `docs/TRADING_DASHBOARD.md` §8 — Wheel troubleshooting (where to look: system_events, telemetry, state, endpoint; how to interpret A/B/C/D; diagnostic script; regime = modifier-only).

### Droplet wheel check (2026-02-10)
- **Ran via SSH:** `python scripts/run_wheel_check_on_droplet.py` (uses DropletClient; full output in `reports/droplet_wheel_check_YYYY-MM-DD.txt`).
- **Result:** **Outcome B — Wheel RUNNING but ALWAYS SKIPPING.** wheel_run_started = 30 (last 7 days), wheel_order_submitted = 0, wheel_order_filled = 0. **Blocking reason: no_spot (840 skips).** Every candidate is skipped because `api.get_quote(symbol)` returns no valid bid/ask (spot <= 0 or exception) in `strategies/wheel_strategy.py` _run_csp_phase().
- **Root cause:** Alpaca quote API (paper) shape mismatch — quote object may use different attribute names or return None/partial; narrow spot extraction (ap/ask_price only) failed for all symbols.

### Wheel spot resolution — Alpaca contract and verification (2026-02-10)
- **Alpaca quote contract (definitive):** `normalize_alpaca_quote(raw_quote)` in `strategies/wheel_strategy.py` — accepts raw `api.get_quote()` return; never raises; returns None only if raw_quote is None. Normalized dict: `ask`, `bid`, `last_trade` (float | None), `source_fields_present` (list of field names found). Handles object and dict; extracts ap/ask_price/askprice, bp/bid_price/bidprice, last_trade.price|p.
- **Single spot resolution:** `resolve_spot_from_market_data(normalized_quote, bar_close)` — only place spot is resolved. Order: ask > bid > last_trade > bar_close; returns (spot_price, spot_source) or (None, None). CSP and CC both use `_resolve_spot(api, symbol)` which gets quote → normalize → get bar close → resolve_spot_from_market_data → emit telemetry.
- **Telemetry (mandatory):** Every attempt emits either **wheel_spot_resolved** (symbol, spot_price, spot_source, quote_fields_present, bar_used) or **wheel_spot_unavailable** (symbol, quote_fields_present, bar_attempted). no_spot skip occurs only when wheel_spot_unavailable was emitted.
- **Verification report:** `python3 scripts/wheel_spot_resolution_verification.py --days 7` → `reports/wheel_spot_resolution_verification_<date>.md` (counts resolved vs unavailable, spot_source distribution, first option-chain reach, wheel_order_submitted/filled, next blocker with evidence).
- **Droplet check assertion:** `scripts/run_wheel_check_on_droplet.py` runs the verification script and **fails with exit 1** if wheel_spot_resolved == 0 and wheel_spot_unavailable > 0 (no spot resolved during market hours).
- **Verification commands:** After deploy + restart: `python3 scripts/run_wheel_check_on_droplet.py`; inspect `reports/wheel_spot_resolution_verification_*.md` and `grep '"event_type": "wheel_spot_resolved"' logs/system_events.jsonl | tail -5`.

---
## Fixed Strategy Capital Allocation (25% Wheel / 75% Equity) (2026-02-10)
- **Policy:** Wheel always controls 25% of total account equity; equity 75%. No borrowing across strategies. Alpaca is execution-only; capital intent enforced internally.
- **Config (authoritative):** `config/strategies.yaml` → `capital_allocation.mode: fixed`, `strategies.wheel.allocation_pct: 25`, `strategies.equity.allocation_pct: 75`.
- **Single source of truth:** `capital/strategy_allocator.py` — `can_allocate(strategy_id, required_notional, total_equity, wheel_state)` returns (allowed, details). Wheel used = sum(open_csps notional) from `state/wheel_state.json`. Wheel budget = total_equity × 0.25; wheel_available = budget − used.
- **Enforcement:** In `strategies/wheel_strategy.py` _run_csp_phase, before each CSP: call `can_allocate("wheel", notional, account_equity, state)`. If blocked: emit **wheel_capital_blocked**, continue to next candidate (do not break). Removed direct account-level buying_power and max_capital_fraction checks.
- **Telemetry (mandatory):** Every wheel capital decision: **wheel_capital_check** (wheel_budget, wheel_used, wheel_available, required_notional, decision, reason). When blocked: **wheel_capital_blocked** (symbol, wheel_budget, wheel_used, wheel_available, required_notional, reason).
- **Verification:** `scripts/run_wheel_check_on_droplet.py` prints last 5 wheel_capital_check/wheel_capital_blocked; asserts wheel_capital_check appears when wheel runs. See `docs/TRADING_DASHBOARD.md` § Strategy Capital Allocation.
- **Wheel per-position limits (aligned to wheel budget, paper trading):** Per-position limits are a **fraction of the wheel budget** (25% of account), not of total account equity. Rationale: enable CSP placement for learning and observability on paper. Config: `strategies.wheel.per_position_fraction_of_wheel_budget` (e.g. 0.5 = 50% of wheel budget per CSP), `max_concurrent_positions` (e.g. 1). Logic: `per_position_limit = wheel_budget * per_position_fraction_of_wheel_budget`; allow CSP only if `required_notional <= per_position_limit`. Telemetry: **wheel_position_limit_check** (wheel_budget, per_position_limit, required_notional, decision, reason); **wheel_position_limit_blocked** when blocked. On block: emit telemetry and continue to next candidate. For live trading, tighten by lowering `per_position_fraction_of_wheel_budget` or `max_concurrent_positions` as needed.
- **Idempotent wheel submission + schema versioning + action closure:** (1) **Schema:** All wheel system_events include `event_schema_version: 1` (WHEEL_EVENT_SCHEMA_VERSION). (2) **Idempotency:** `build_wheel_client_order_id(cycle_id, symbol, side, expiry, strike, qty)` produces stable id format `WHEEL|<cycle8>|<SYM>|<SIDE>|<YYYYMMDD>|<STRIKE>|<QTY>`. Before submit, if `state.recent_orders[client_order_id]` has status `submitted` or `filled`, emit **wheel_order_idempotency_hit** and do not submit (no duplicate orders on restart/retry). After submit: record in `state.recent_orders`; after fill update status to `filled`. Prune to last 200 orders on save. **wheel_order_idempotency_hit** means restart protection worked. Resolving stuck `submitted`: check broker for order status; if filled, update state; if canceled/rejected, remove or mark in recent_orders. (3) **Daily review gates:** `scripts/generate_wheel_daily_review.py` enforces mandatory governance chain per cycle; on regression exits 1 and writes "Governance regressions" section. (4) **Board action closure:** `reports/wheel_actions_<date>.json` holds actions with action_id (hash of title+owner+reference_section), status (proposed/done/blocked/deferred). EOD runner loads prior actions and requires closure (status + note) for each; missing closure fails the run.
- **Signal propagation contract:** Every open position is re-evaluated by the signal engine each cycle (in evaluate_exits). `evaluate_signal_for_symbol(symbol, context)` (signal_open_position.py) always returns (strength, evaluated, skip_reason); never silently skips. When evaluated: emit **signal_strength_evaluated** (subsystem=signals; symbol, position_side, signal_strength, evaluation_context=open_position_refresh); persist to `state/signal_strength_cache.json`. When skipped: emit **signal_strength_skipped** (symbol, reason). **Difference:** signal = 0 means evaluated and neutral; “signal not evaluated” means no recent signal_strength_evaluated (dashboard shows N/A). **Audit:** `python3 scripts/audit_signal_propagation.py [--minutes 15]` asserts every open position has at least one signal_strength_evaluated in the window; exits non-zero if any MISSING. Droplet check runs this audit and fails loudly if any position lacks evaluation.
- **Signal trend deltas (instrumentation only):** signal_strength_cache per-symbol includes prev_signal_strength, prev_evaluated_at, signal_delta, signal_delta_abs, signal_trend (strengthening|weakening|flat|unknown), signal_trend_window (last_eval). Flat when abs(delta) < 0.05. We emit signal_trend_evaluated on each evaluated refresh. Not used for entry/exit.
- **Correlation snapshot (analytics only):** state/signal_correlation_cache.json: as_of, window_minutes, method=pearson, pairs (top K), top_symbols (max_corr, most_correlated_with, avg_corr_topk). Script: compute_signal_correlation_snapshot.py --minutes 60 --topk 20. Not used for trading; daily review and Board use for concentration review.
- **Board watchlists from signal analytics (review-only, zero trading impact):** EOD Board run builds two mandatory watchlists from caches: (1) **Weakening Signal Watchlist** — open positions with signal_trend=weakening and signal_delta ≤ -0.50 (SIGNAL_WEAKENING_THRESHOLD); (2) **Correlation Concentration Watchlist** — symbols with max_corr ≥ 0.80 (CORRELATION_CONCENTRATION_THRESHOLD). Thresholds live in board/eod/run_stock_quant_officer_eod.py only; **must NOT be imported or referenced by trading code.** Board prompt requires a response for every watchlist symbol (why still held / exit trigger, or concentration acceptable / mitigation). Output schema requires wheel_watchlists.weakening_signals and .correlation_concentration with board_rationale and exit_review_condition / mitigation_considered. Artifact: reports/wheel_watchlists_<date>.json (date, thresholds, merged input + Board responses). Missing required entries fails the Board run. Droplet check asserts artifact exists and rationales present when watchlists non-empty. Daily review references the artifact and counts. **Guarantee:** No trading logic may reference these outputs; read-only governance.
- **Wheel governance badge:** Single daily PASS/FAIL derived from real artifacts. Written to `reports/wheel_governance_badge_<YYYY-MM-DD>.json` and embedded at the top of `reports/wheel_daily_review_<date>.md`. Fields: overall_status, event_chain_coverage_pct, cycles_with_full_chain, cycles_total, idempotency_hits, board_action_closure, dominant_blocker, generated_at. **Rules:** overall_status = FAIL if daily review exits non-zero, or event_chain_coverage_pct < 100% for cycles that reached ranking, or board_action_closure = FAIL; otherwise PASS. **Where it appears:** droplet check output (compact summary), wheel daily review markdown (top), Board daily bundle (near top); prompt tells Board "Wheel governance badge status is <PASS/FAIL>. If FAIL, address blockers before proposing new actions." **Meaning:** PASS = event chain complete, prior actions closed, no gate failure; FAIL = fix governance regressions or run EOD board to close prior wheel actions, then re-run daily review.

---
## Profitability Push (2026-02-09)
- **LIVE (deployed):** (1) **Exit logic:** No "unknown" exit reasons; every exit maps to concrete reason (signal_decay, stop, regime_shift, risk, etc.). Fallback is "risk". Regime-aware exit timing (BEAR: cut losers faster -0.8% stop, let winners run longer 1.0% target; modifiers only, no gating). Telemetry: exit_reason_recorded per close in system_events (subsystem=exit). (2) **Displacement:** BEAR + high-confidence (score >= 7): relaxed score advantage and PnL band for displacement. Log when displacement blocks: displacement_blocked_no_candidate (symbol, new_signal_score, regime) in system_events. (3) **Wheel:** Runs every cycle when enabled; lifecycle events (wheel_run_started, wheel_csp_skipped, wheel_order_submitted, wheel_order_filled). Restart stock-bot after deploy so wheel runs.
- **Board:** Customer Advocate, Innovation Officer, SRE roles in config/ai_board_roles.json. Board output must include: top_3_root_causes_pnl_degradation, top_3_concrete_actions_next, expected_impact_per_action, success_failure_measured_in_3_5_days. Contract: board/stock_quant_officer_contract.md — prescription mandatory; Customer Advocate must disagree when results poor.
- **Wheel as profit engine:** Role: income stabilizer and drawdown reducer. Track: premium collected per day, expectancy per wheel trade (dashboard /api/stockbot/wheel_analytics: expectancy_per_trade_usd, premium_collected), correlation with equity P&L. Compare wheel vs equity contribution weekly (reports, dashboard).
- **Multi-day expectancy:** Board must answer "Is expectancy improving?" over 3, 5, 7 days. If not after 5–7 days: change strategy, reduce frequency, re-evaluate edge.
- **Regime:** Modifier-only; never gates trading.

---
## Wheel Strategy Audit — PATH B (2026-02-09)
- **Decision:** PATH B. Wheel was **not** using UW intelligence: selector used only Alpaca volume/OI/spread and stub IV; no UW cache or composite score.
- **Evidence:** `strategies/wheel_universe_selector.py` had no reads of `uw_flow_cache` or `uw_composite_v2`; ranking was by `wheel_suitability_score` (liquidity*0.4 + iv*0.3 + spread*0.3). Hard filters (spot, contracts) ran per-ticker in order of that list.
- **Fix applied:** (1) **UW-first ranking:** In `wheel_universe_selector`, added `_rank_by_uw_intelligence()` — reads `CacheFiles.UW_FLOW_CACHE`, gets regime from state, calls `uw_composite_v2.compute_composite_score_v2(symbol, enriched, regime)` per symbol; sorts by UW score descending; top N become the candidate list. (2) **Order of operations:** Sector/earnings/count filter → UW rank → take top `universe_max_candidates` → hard filters (spot, contracts) only in `_run_csp_phase` per-ticker. (3) **Explainability:** Every cycle emits `wheel_candidate_ranked` (subsystem=wheel) with top_5_symbols, top_5_uw_scores, chosen or reason_none.
- **Wheel intelligence contract:** Primary driver = UW composite score from `data/uw_flow_cache.json` + `uw_composite_v2.compute_composite_score_v2`. Secondary = liquidity/OI/spread (for telemetry). Spot and contract availability are hard filters applied only to the UW-ranked list. Regime is modifier-only (used in composite call).
- **Verification:** On droplet, `grep wheel_candidate_ranked logs/system_events.jsonl` and `wheel_root_cause_report.py --days 1`; expect wheel_run_started, wheel_candidate_ranked, and wheel_csp_skipped with reasons. See `docs/TRADING_DASHBOARD.md` §6.1.

---
## Wheel Dry-Run Validation (Market-Closed) (2026-02-09)
- **Purpose:** Prove UW-first ranking and `wheel_candidate_ranked` emission without live quotes, options chains, or market hours. No broker calls; deterministic test.
- **Command (run from repo root, e.g. on droplet):**  
  `python3 scripts/wheel_dry_run_rank.py`
- **Expected stdout:** Ranked candidates (symbol, uw_score) then final line: `wheel_candidate_ranked emitted successfully`.
- **Verify event:**  
  `grep '"event_type": "wheel_candidate_ranked"' logs/system_events.jsonl | tail -1`  
  Expect: non-empty `top_5_symbols`, UW scores present, `chosen` = null, `reason_none` = `"dry_run_rank_only"`.
- **Interpretation:** If dry-run emits correctly → ranking path is wired; zero count during market-closed hours is expected; live wheel will emit during market hours. If dry-run does NOT emit → systemic wiring issue; fix before market open.
- **Docs:** See `docs/TRADING_DASHBOARD.md` §6.1 (validate wheel intelligence without market hours).

---
## CRON + GIT DIAGNOSTIC (2026-02-04)
- **Detected path:** /root/stock-bot
- **Cron:** crontab has EOD entry with correct path (21:30 UTC); audit+sync 21:32 UTC via run_droplet_audit_and_sync.sh
- **Git push:** push OK (if transient ref-lock on remote, retry or push from local)
- **Report generation:** EOD dry-run OK
- **Operational readiness audit (droplet):** All CRITICAL checks passed (2026-02-04). MEDIUM unified_daily_intelligence_pack: **addressed** — run_droplet_audit_and_sync.sh now runs run_stockbot_daily_reports.py for $DATE before the audit and adds reports/stockbot/$DATE to the sync commit.
- **Repairs applied:** (parity: config/strategies, universe_wheel, universe_wheel_expanded, strategies/, main.py duplicate composite_meta removed; audit+sync generates daily pack before audit)

---
## Strategy Sovereignty (2026-02-05)
- Wheel and Equity are independent institutions.
- No cross-strategy displacement.
- Separate capital, exits, promotion metrics.
- Dashboard and AI board are strategy-aware.
- **Config:** `config/strategy_governance.json` — position caps, capital fractions, displacement rules, exit policies, promotion metrics per strategy.
- **Exit policies:** `src/exit/wheel_exit_v1.py` (wheel: time + premium decay); equity uses equity_exit_v2.
- **Analytics:** `scripts/aggregate_strategy_pnl.py` → `artifacts/strategy_pnl.json` (EQUITY/WHEEL segmented PnL).
- **AI Board:** `config/ai_board_roles.json` — adversarial review roles (Equity Skeptic, Wheel Advocate, Risk Officer, Promotion Judge); require_disagreement and require_synthesis.

---
## Mode divergence contract (2026-02-05)
- LIVE, PAPER, SHADOW must not be symmetric.
- LIVE changes are small and controlled; PAPER changes are meaningful; SHADOW changes are aggressive.
- Mode governance lives in `config/mode_governance.json` and must be resolved per-trade to avoid bleed.
- Analytics must include mode+strategy rollups (`artifacts/mode_strategy_pnl.json`) for promotion decisions.
- **Script:** `scripts/aggregate_mode_strategy_pnl.py` — produces mode:strategy buckets (LIVE:EQUITY, PAPER:WHEEL, etc.).
- **Contract:** non_interference (mode settings resolved at decision-time per trade); promotion only from PAPER/SHADOW into LIVE after evidence.

---
## Exit timing + scenario replay initiative (2026-02-07)
- Added config/exit_timing_scenarios.json to explore multi-hour to multi-day hold floors and reduced decay/displacement sensitivity.
- Implemented src/governance/governance_loader.py to load/resolve (strategy_governance, mode_governance, exit_timing_scenarios) into a per-decision policy blob.
- Added scripts/replay_week_multi_scenario.py to generate a scenario replay report from droplet-captured artifacts; defaults to diagnostics-only unless a canonical counterfactual replay engine is present.
- Added config/ai_board_exit_research_addendum.json requiring hold-time expectancy analysis, exit-reason expectancy, and explicit data demands for unbiased counterfactual replays.

## Exit timing enforcement shim (2026-02-07)
- Added src/governance/apply_exit_timing_policy.py as a non-breaking enforcement shim.
- Runtime must call apply_exit_timing_to_exit_config(...) during exit evaluation to enforce scenario params.
- If not called, behavior remains unchanged (safe by default).

## Alpaca market data capture + counterfactual exit replay (2026-02-07)
- Added src/exit/exit_attribution_enrich.py and patched src/exit/exit_attribution.py to enrich exit rows with mode, strategy, regime_label, and entry/exit fields when available.
- Added scripts/fetch_alpaca_bars.py to pull historical bars from Alpaca Market Data API for recent traded symbols.
- Added scripts/replay_exit_timing_counterfactuals.py to run exit-only counterfactual replays for hold-floor scenarios (no forward-looking entry optimization).
- Governance requirement: exit_attribution rows must include mode+strategy (and ideally entry_ts/entry_price/qty) to enable mode:strategy bucketing and unbiased exit timing research.

## Pre-Monday instrumentation and Cursor governance (2026-02-07)
- Added replay-readiness sanity check to ensure exits are replayable.
- Locked AI Board mandate to exit timing and hold-duration analysis.
- Wrote explicit promotion and rollback criteria before results.
- Introduced .cursorrules to encode governance invariants and prevent drift.

## Board output packaging and AI Board workflow upgrade (2026-02-07)
- Added `scripts/board_daily_packager.py` to create dated folders under `board/eod/out/YYYY-MM-DD/` with:
  - `daily_board_review.md` (combined markdown artifacts).
  - `daily_board_review.json` (combined JSON artifacts).
- Updated `.cursorrules` with:
  - AI Board Charter and Invocation Protocol.
  - Automatic (cron) and manual Board Review triggers.
  - Multi-model, multi-agent execution guidance.
  - Conflict handling and multi-idea requirements.
  - Innovation Officer "What else?" mandate.
  - Customer Profit Advocate escalation.
- Added `docs/BOARD_REVIEW.md` documenting the daily Board Review workflow and how to test it.

## Board Upgrade V2 (2026-02-07)
- Strengthened all agents with adversarial, multi-option, and evidence-based mandates.
- Added yesterday's commitments tracking.
- Added multi-model execution requirement.
- Added deeper Innovation Officer and SRE Officer mandates.
- Updated .cursorrules with V2 governance rules.

## Board Upgrade V3 — Multi-Day Intelligence (2026-02-08)
- **Multi-Day Analysis Module:** `scripts/run_multi_day_analysis.py` — runs automatically after daily EOD pipeline; computes rolling 3-day, 5-day, 7-day windows; outputs `board/eod/out/YYYY-MM-DD/multi_day_analysis.json` and `.md`. Metrics: regime persistence/transition, volatility trend, sector rotation, attribution vs exit, churn, hold-time, exit-reason distribution, blocked trades (displacement/max positions/capacity), displacement sensitivity, capacity utilization, expectancy, MAE/MFE.
- **Regime Review Officer:** New agent (`.cursor/agents/regime_review_officer.json`) — analyzes 3/5/7-day regime behavior, detects transitions, identifies misalignment, produces 2–3 regime-aware options. Must participate in every Board Review.
- **Updated Agents:** All agents now read multi-day analysis, incorporate multi-day trends, produce multi-day options, track multi-day commitments (1/3/5-day).
- **Multi-Day Board Review Sections:** Daily Board Review includes multi-day regime summary, multi-day P&L & risk, multi-day exit & churn, multi-day blocked trades, multi-day innovation opportunities, multi-day promotion review.
- **Multi-Day Commitments:** Extended from yesterday's commitments to 1-day, 3-day, 5-day commitments. Board reports: Completed, Not completed, Blocked, Needs escalation. Customer Profit Advocate challenges incomplete commitments.
- **Board Packager:** `scripts/board_daily_packager.py` now includes `multi_day_analysis.json` and `.md` in combined outputs.
- **Cron Integration:** After EOD pipeline: run multi-day analysis → run V3 Board Review → package → commit → push → deploy.
- **Governance:** `.cursorrules` updated with V3 mandates: multi-day analysis required, Regime Review Officer participation, multi-day evidence required for LIVE/PAPER changes, multi-day scenario replay for exit timing.
- **Documentation:** `docs/BOARD_REVIEW.md` updated, `docs/BOARD_UPGRADE_V2.md` references V3, `docs/BOARD_UPGRADE_V3.md` created.

## Remediation Pass: Regime, Exit Timing, Displacement, Attribution (2026-02-08)
- **Regime detection fix:** Stockbot daily pack was reading regime from top level of `daily_universe_v2.json`; regime is under `_meta`. Fixed in `scripts/run_stockbot_daily_reports.py` to read `(v2.get("_meta") or {}).get("regime_label")` with fallback `"NEUTRAL"` so multi-day analysis no longer shows UNKNOWN for all days.
- **Regime never a gate:** `ENABLE_REGIME_GATING` default changed from `true` to `false` in `main.py`. Regime is a modifier only (sizing, filters, preferences); it must never fully block trading. See `docs/REGIME_DETECTION.md`.
- **Exit timing shim wired:** `apply_exit_timing_to_exit_config` is now called at the start of `evaluate_exits()`; policy is applied from `config/exit_timing_scenarios.json` (mode/strategy/regime/scenario). Min-hold floor is enforced before adding a position to the close list; skips logged as `hold_floor_skipped`. Scenario set via `EXIT_TIMING_SCENARIO` (default `baseline_current`).
- **Diagnostics added:** `scripts/regime_detection_diagnostic.py`, `scripts/exit_timing_diagnostic.py`, `scripts/displacement_capacity_diagnostic.py`, `scripts/attribution_exit_reconciliation.py` for regime, exit timing by reason/mode:strategy, displacement/capacity blocked counts, and attribution vs exit PnL reconciliation.
- **Displacement/capacity:** Documented in `docs/CAPACITY_AND_DISPLACEMENT.md`. Regime can influence policy but never set capacity to zero or fully block. Displacement decisions already logged to `logs/system_events.jsonl` (subsystem=displacement).
- **Board reasoning:** Board agents should treat regime as modifier-only; ask explicitly about regime health, exit timing health, displacement/capacity health, and attribution vs exit alignment. See `docs/BOARD_REVIEW.md` interpretation notes.
---

## Roadmap to Institutional Alpha (>1% Weekly)

- **Pillar 1: Microstructure (OFI).** Capture Order Flow Imbalance and Volume Adjusted Mid-Price (VAMP) to predict 1-minute lead times.
- **Pillar 2: Mathematical Stationarity.** Implementation of Fractional Differentiation in the ML pipeline to preserve trend memory.
- **Pillar 3: Adaptive Risk (HMM).** Transition from static stop-losses to Hidden Markov Model regime-aware position sizing.

---

## Implementation History

- **2026-04-13 (SRE — droplet + truth warehouse):** Alpaca production droplet resized to **4 AMD vCPUs / 8GB RAM** (`MEMORY_BANK_ALPACA.md` canon updated). **Telegram / ML harvester integrity:** full-truth warehouse mission reports **`DATA_READY: YES`** with **96.57%** blocked-boundary coverage (was fail-closed at **0%** due to mission-side misclassification of `score_snapshot` gate rows — fixed in `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py`; `score_snapshot_writer.py` stamps **`time_bucket_id`**). **`repair_failed_defer`** structural fix for UW pre-filter shipped earlier same window (`board/eod/live_entry_adjustments.py`, `board/eod/root_cause.py`).
- **2026-04-08 (Alpaca V2 Harvester — SRE / telemetry):** **100-trade milestone** reached in the Harvester era with **100% execution-join / data-integrity** on the audited strict cohort; ops tracking **250** for ML scale-up. **Telemetry hardening:** `STRICT_EPOCH_START` reset to **2026-04-07T17:01:00Z** (new ML telemetry era; prior cohort excluded from strict counts — `telemetry/alpaca_strict_completeness_gate.py`). **Milestone latching:** `scripts/telemetry_milestone_watcher.py` clamps CSV cutoffs to the strict epoch (no pre-epoch milestone spam), resets OOS sent-flags on floor change so **250 cannot skip 100**, and `scripts/extract_gemini_telemetry.py` enforces the same floor for `entries_and_exits.csv`. **Live data:** Alpaca **SIP WebSocket** stream with REST fallback (`src/alpaca/stream_manager.py`), singleton `AlpacaStreamManager`, **`websockets` pinned <11** for `alpaca-trade-api`. **Paper promos:** env-gated **PASSIVE_THEN_CROSS** pending queue + workers (non-blocking vs baseline). **Governance / audits:** strict quant edge report, paper capital caps missions, integrity-closure and profit-discovery campaign scripts under `scripts/audit/`; post-deploy manual proof requirement relaxed where it caused **ARMED→BLOCKED** downtime; Telegram **integrity-only** mode exit 0 when post-close sends are blocked. **Canonical trade count** alignment: dashboard strip + milestone parity + droplet diagnosis scripts (`compute_canonical_trade_count`, `scripts/telemetry_sync_milestone_state.py` for `.milestone_state.json` sync when needed).
- **2026-04-03:** Migrated Alpaca execution to V5.0 Passive Hunter. Implemented midpoint pegging (NBBO, 1¢ inside spread capped at mid), 2026 decimal enforcement (2 dp if price ≥ $1, 4 dp if < $1), 20 bps spread guard with `spread_too_wide_abort`, and 24/5 overnight routing (`extended_hours` when outside US RTH and `asset.overnight_tradable`). See `main.py` (`v5_compute_limit_price`, `AlpacaExecutor.compute_entry_price`, `submit_entry`).

---

## Maintenance Log (Infrastructure History)

- **2026-04-23 (Vanguard — double-barrel ML, offense/defense, observability):** **(1) Double-barrel ML:** **V2 Profit Agent** is the **LIVE** entry hard gate via `telemetry.vanguard_ml_runtime.evaluate_v2_live_gate` (probability vs `models/vanguard_v2_profit_agent_threshold.json`, code default **0.3876** when JSON missing). **V3 Alpha Hunter** runs in **SHADOW** only on `trade_intent` (`telemetry.shadow_evaluator` / `enrich_shadow_v2_v3_fields`): threshold from `models/vanguard_v3_hunter_threshold.json` (**holdout_probability_threshold ≈ 0.354**), model targets **>1.5% MFE** cohort semantics per Vanguard training manifest — **does not** gate live orders. **(2) Structural offense / defense:** **`src/offense/entry_momentum_gate.py`** — relative strength vs SPY (5m) when available else **price > session VWAP** (REST bars). **`src/offense/streak_breaker.py`** — **two consecutive losing closes → block new entries 30 minutes** (`state/offense_streak_state.json`). Exit stack continues to carry **ATR-based dynamic stops** (`main.py` ATR envs), **time / signal decay** components in exit scoring (`time_decay` / `signal_decay` paths in `evaluate_exits`), and **trailing / chop** discipline consistent with deployed `exit_score_v2` / `stops_v2` — operator shorthand: **60m underwater decay pressure**, **1.5× ATR trail**, **RS/VWAP entry gate**, **2-loss / 30m entry breaker** (see cited modules). **(3) Observability overhaul (Command Center):** Dashboard **dual-barrel cumulative realized PnL** is **decoupled from epoch-truncated JSONL**: **`state/continuous_pnl_ledger.jsonl`** append-only rows written from **`src/exit/exit_attribution.append_exit_attribution`** after each successful `exit_attribution.jsonl` line (`telemetry.continuous_pnl_ledger`). API **`GET /api/dashboard/dual_barrel_cumulative_pnl`** prefers the ledger, falls back to tail reconstruction (`telemetry.command_center_dashboard`). **Daily UTC trade volume** uses immutable **`state/daily_trade_ledger.json`** for past UTC days + live scan for today (`telemetry.command_center_dashboard.daily_trade_volume_utc_with_ledger`). UI: **`static/index.html`**, **`static/app.js`**. **Retroactive seed:** `scripts/telemetry/seed_continuous_pnl_ledger.py` (optional `--force`). **Epoch SRE:** log truncation (`logs/*.jsonl`) must **never** delete `state/continuous_pnl_ledger.jsonl` or `state/daily_trade_ledger.json` — they are **not** in the epoch JSONL tarball scope.
- **2026-04-13:** Production Alpaca droplet upgraded to **4 AMD vCPUs / 8GB RAM**; `MEMORY_BANK_ALPACA.md` operational canon + Scenario Lab CPU guidance updated. Truth-warehouse **`DATA_READY: YES`** at **96.57%** blocked-boundary coverage logged (classifier/join fix + `time_bucket_id` on score snapshots).
- **2026-04-08:** `MEMORY_BANK_ALPACA.md` updated for **Alpaca V2 Harvester** phase, milestone/epoch telemetry truth, and pruned Fast-Lane as non-primary ops (doc sync; pull on droplet after `git push`).
- **2026-04-03:** Successfully applied Linux Kernel security patches to Alpaca droplet (v6.8.0-100 -> v6.8.0-107). System rebooted and verified bot auto-restart.

---

