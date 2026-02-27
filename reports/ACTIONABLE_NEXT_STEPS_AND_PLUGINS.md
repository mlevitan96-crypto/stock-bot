# Actionable, Profitable Next Steps — Safe Implementation & Plugin Use

**Goal:** Next steps that are **actionable**, **profitable** (move toward making money), **safe** (reversible, testable, small), and **plugin-aware** (use MCP/docs where they speed or harden work).

---

## 1. Priority Order (What to Do Next)

| Order | Step | Why profitable / actionable | Safe how |
|-------|------|-----------------------------|----------|
| **1** | **Live pipeline audit (pre-Monday)** | Ensures Monday we have data to measure; without it we can’t run effectiveness or score-vs-profitability on live. | Read-only audit + doc; no config/trade logic changes. |
| **2** | **Multi-model reads effectiveness + customer advocate** | Board and prosecutor/defender cite “what the numbers say” and “what would help the customer”; fewer heuristic verdicts, better decisions. | Add file reads and append to prompts; no change to verdict logic until you choose. |
| **3** | **Lock min_exec_score 1.8 for Monday** | Backtest profitable band is (1.5, 2.0]; 1.8 is already validated. Prevents last-minute gate changes that blur live vs backtest. | Config-only; revert by changing one number. |
| **4** | **First live week: define success + run effectiveness** | “Success” = data flowing, effectiveness runnable by Friday; then run effectiveness on the week. | No trading changes; define criteria and run existing script. |
| **5** | **One small tuning cycle (after first live week)** | Use effectiveness/blame → one overlay → backtest compare → paper → lock or revert. | Governed workflow: change proposal, overlay, compare, revert path. |
| **6** | **Blocked-trades report on droplet (weekly)** | Answers “what we could have made”; informs whether gate is too tight. | Existing script; schedule or run post-EOD. |

---

## 2. How to Implement Safely

### 2.1 Live pipeline audit (Step 1)

- **What:** Trace order flow → position open/close → where `attribution` and `exit_attribution` are written (logs/state). Check schema: `entry_score`, `context.attribution_components` (if available), `exit_reason`, `exit_quality_metrics`.
- **Safe:** Audit only. Produce a short doc (e.g. `reports/LIVE_PIPELINE_AUDIT_YYYY-MM-DD.md`) with: (a) where each artifact is written, (b) schema vs backtest, (c) gaps and fix list. No code change until you decide.
- **Plugin use:** Use **compound-engineering-context** (or repo docs) to look up logging/telemetry patterns or schema contracts so the audit checks the right fields.

### 2.2 Multi-model sees effectiveness + customer advocate (Step 2)

- **What:** In `multi_model_runner.py`, after loading baseline_metrics/summary: (a) if `backtest_dir/effectiveness/` exists, read `EFFECTIVENESS_SUMMARY.md` or key JSONs (e.g. `entry_vs_exit_blame.json`, `exit_effectiveness.json`) and append a short “Evidence” block to prosecutor and defender prompts; (b) if `backtest_dir/customer_advocate.md` exists, append a “Customer advocate” block to the board prompt and to the synthesis section of `board_verdict.md`.
- **Safe:** Additive only. New content is “if present, include”; no change to verdict logic except that prompts are richer. You can later make the board verdict conditional on that evidence.
- **Plugin use:** When editing `multi_model_runner.py`, use the plugin to pull **config/tuning/schema** or attribution docs so the evidence block uses the same field names as effectiveness (e.g. `entry_vs_exit_blame`, `profit_giveback`).

### 2.3 Lock min_exec_score 1.8 (Step 3)

- **What:** Ensure orchestration and any live/paper config use `min_exec_score: 1.8` for Monday. Document in run_meta or a one-line “Monday gate: 1.8” in NEXT_STEPS or preflight.
- **Safe:** Single config value; revert by changing it back. No code logic change.

### 2.4 First live week success + effectiveness (Step 4)

- **What:** (a) Define “success” for the first live week (e.g. “Trades execute; attribution and exit_attribution written; no crashes; effectiveness runnable on the week by Friday”). (b) On Friday (or when you have a week of data), run `run_effectiveness_reports.py --start ... --end ... --out-dir reports/effectiveness_live_YYYY-MM-DD`.
- **Safe:** Definition is doc-only; effectiveness run is read-only from live logs. No trading or gate changes.

### 2.5 One small tuning cycle (Step 5)

- **What:** Follow PATH_TO_PROFITABILITY + GOVERNED_TUNING_WORKFLOW: (1) From effectiveness/blame, pick one lever (e.g. one exit weight or one signal weight). (2) Write a change proposal (`reports/change_proposals/...`). (3) Add one overlay (`config/tuning/examples/...`). (4) Run `compare_backtest_runs.py` baseline vs proposed. (5) Run `regression_guards.py`. (6) If pass, enable overlay on paper for a week; if falsification criteria hit, revert.
- **Safe:** Config-only overlay; backtest compare and guards before paper; explicit revert path.
- **Plugin use:** Use **config/tuning/schema.json** (or plugin to fetch it) when writing the overlay so fields and types are correct; use plugin to look up `regression_guards` or compare script usage if needed.

### 2.6 Blocked-trades report on droplet (Step 6)

- **What:** Run `run_blocked_trade_analysis.py` (or the full counter-intelligence path) on droplet after EOD or weekly; write `reports/blocked_opportunity_cost_YYYY-MM-DD.md` and push or sync.
- **Safe:** Report only; no trading or gate change. Uses existing scripts.

---

## 3. Leveraging Plugins to Speed or Harden

Use plugins (e.g. **compound-engineering-context** MCP) in these ways:

| When | How | Benefit |
|------|-----|---------|
| **Implementing multi-model evidence** | Fetch `config/tuning/schema.json` or attribution/effectiveness schema so prompts use correct field names. | Fewer mismatches; prosecutor/defender cite real metrics. |
| **Writing a tuning overlay** | Look up schema and examples (e.g. `exit_weights`, `entry_weights_v3`) before writing JSON. | Valid overlay first time; fewer invalid-config runs. |
| **Adding regression guards** | Look up existing guard patterns or compare_backtest_runs usage. | Consistent checks; reuse of existing patterns. |
| **Live pipeline audit** | Look up logging/telemetry or contract docs for attribution and exit_attribution. | Audit checks the right fields and sinks. |
| **Any new script that touches config or attribution** | Pull schema or contract docs before coding. | Code stays aligned with schema; safer refactors. |

**Safety in code:** When you add or change logic (e.g. multi-model evidence, new guards), keep changes **small**, **behind “if present”** where possible, and **revertible** (one PR or one file). Use the plugin to confirm types and field names so we don’t introduce schema drift.

---

## 4. Concrete Implementation Checklist

- [x] **1. Live pipeline audit** — `reports/LIVE_PIPELINE_AUDIT.md` documents write path and schema to verify on droplet.
- [x] **2. Multi-model evidence** — `multi_model_runner.py` loads effectiveness + customer_advocate when present.
- [x] **3. Lock gate** — backtest_config and orchestration use min_exec_score 1.8; ensure live engine reads 1.8 (see audit).
- [ ] **4. First live week** — Define success criteria; run effectiveness on the week’s data when available.
- [ ] **5. One tuning cycle** — One change proposal → one overlay → backtest compare → guards → paper → lock or revert.
- [ ] **6. Blocked report** — Schedule or run blocked-trade analysis on droplet; publish opportunity-cost report.

---

## 5. Summary

- **Actionable and profitable:** Live audit and multi-model evidence set you up to measure and decide; min_exec_score lock and first-week effectiveness give a clean read; one tuning cycle and blocked report directly support P&L and gate decisions.
- **Safe:** Audit is read-only; multi-model is additive; gate is one config; tuning is governed (proposal → overlay → compare → revert); blocked report is report-only.
- **Plugins:** Use the documentation/schema plugin whenever you touch config, attribution, or effectiveness so implementations stay correct and consistent—faster and safer.

*Aligned with NEXT_STEPS_PROFITABILITY.md, ACTIONABLE_BACKTEST_FRAMEWORK_AND_IDEAS.md, PATH_TO_PROFITABILITY.md, and GOVERNED_TUNING_WORKFLOW.md.*
