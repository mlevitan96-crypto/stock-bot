# Data Integrity Fixes — 2026-02-27

Summary of changes implemented for giveback, Phase 1 audit, entry attribution, pytest spine, and dashboard governance visibility.

---

## 1. Giveback so stopping condition can be satisfied

**File:** `main.py` (log_exit_attribution)

- **Change:** When `high_water` is missing or equals entry price, set `high_water = max(entry_price, exit_price)` for long (or `min` for short) before calling `compute_exit_quality_metrics`. This yields a defined MFE (and thus `profit_giveback`, possibly 0) whenever the trade had any profit, so effectiveness_aggregates can populate `avg_profit_giveback` and `stopping_checks.giveback_le_baseline_plus_005` can be evaluated.
- **Note:** `run_effectiveness_reports.py` already had a fallback (lines 393–399) to compute giveback from joined rows when exit_reason-level giveback was missing; the main fix is ensuring exit_attribution records get non-null `exit_quality_metrics.profit_giveback` when the position had upside.

---

## 2. Run droplet Phase 1 checks and record Alpaca alignment

**New/updated:**

- **`scripts/run_phase1_audit_on_droplet.py`** — Runs Phase 1 audit via DropletClient (or prints commands when no droplet config): service status (stock-bot, uw-flow-daemon), masked env keys, log tail, Alpaca alignment. Writes `reports/audit/PHASE1_DROPLET_RESULTS.md` and `PHASE1_DROPLET_RESULTS.json`, and `PHASE1_ALPACA_ALIGNMENT.json` when alignment is captured.
- **`scripts/alpaca_alignment_snapshot.py`** — Prints one JSON object with `positions_count`, `cash`, `equity`, `status` (no secrets). Used by Phase 1 script on droplet.

**Usage:**  
`python scripts/run_phase1_audit_on_droplet.py [--out-dir PATH] [--skip-alpaca]`  
With `DROPLET_HOST` or `droplet_config.json`, runs remotely and records results.

---

## 3. Fix entry attribution so signal_effectiveness.json is real

**File:** `main.py` (entry attribution context before log_attribution)

- **Change:** When building `context` for entry attribution, set `context["attribution_components"]` from (in order):  
  1. `_composite_meta.get("attribution_components")`,  
  2. else `composite_result.get("attribution_components")` when composite_result is the full composite dict,  
  3. else build a list from `comps` dict: `[{"signal_id": k, "name": k, "contribution_to_score": round(float(v), 4)} for k, v in comps.items() if isinstance(v, (int, float))]`.  
- **Effect:** Joined closed trades get `entry_attribution_components` so `build_signal_effectiveness(joined)` in `run_effectiveness_reports.py` can populate `signal_effectiveness.json`.

---

## 4. Minimal pytest spine and wire into deploy

- **`requirements.txt`:** Added `pytest>=7.0.0`.
- **`droplet_client.py` (deploy):** After `git_pull`, added step **pytest_spine** that runs:
  - `validation/scenarios/test_exit_attribution_phase4.py`
  - `validation/scenarios/test_effectiveness_reports.py`
  - `validation/scenarios/test_attribution_loader_join.py`  
  with `-v --tb=short`, captures last 50 lines of output, and appends to `results["steps"]`. Deploy does **not** fail if pytest fails; the step result records success/failure and output for review.

---

## 5. Expose giveback + stopping_condition on dashboard

**File:** `dashboard.py`

- **New endpoint:** `GET /api/governance/status`
- **Returns:** JSON with `avg_profit_giveback`, `stopping_condition_met`, `stopping_checks`, `decision`, `joined_count`, `win_rate`, `expectancy_per_trade`, and `source_decision` / `source_aggregates` (paths to the files used). Reads latest `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` and falls back to latest `reports/effectiveness_*/effectiveness_aggregates.json` when needed.
- **`reports/DASHBOARD_ENDPOINT_MAP.md`:** Updated to include `/api/governance/status`.

---

## Verification

- **Giveback:** After deploy, run a few closes with profitable trades and confirm `logs/exit_attribution.jsonl` has `exit_quality_metrics.profit_giveback` non-null where MFE > 0; then run `run_effectiveness_reports.py` and check `effectiveness_aggregates.avg_profit_giveback`.
- **Phase 1:** Run `python scripts/run_phase1_audit_on_droplet.py` with droplet config and inspect `reports/audit/PHASE1_DROPLET_RESULTS.md` and `PHASE1_ALPACA_ALIGNMENT.json`.
- **Entry attribution:** After new entries, confirm `logs/attribution.jsonl` has `context.attribution_components` on open_* records; re-run effectiveness and confirm `signal_effectiveness.json` has per-signal_id stats.
- **Pytest:** On droplet after pull, deploy step "pytest_spine" runs; check `results["steps"]` for `pytest_spine` and its output.
- **Dashboard:** Open `/api/governance/status` and confirm `avg_profit_giveback`, `stopping_condition_met`, and `stopping_checks` are present.
