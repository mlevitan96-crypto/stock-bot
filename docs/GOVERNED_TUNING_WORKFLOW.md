# Governed Tuning Workflow (Phase 6)

Evidence-based tuning of signals and exits using Phase 5 reports, with **reversible**, **measurable**, and **reproducible** changes.

---

## Principles

- **Config-only:** All signal weights, penalties, and exit parameters are config-driven (no hard-coded tuning).
- **Traceable:** Every change is tied to Phase 5 evidence (effectiveness reports).
- **Reversible:** Revert by restoring the previous overlay or unsetting the overlay.
- **Measurable:** Before/after backtest comparison and regression guards are required.

---

## Workflow Overview

1. **Create a change proposal** from Phase 5 evidence (use `docs/templates/change_proposal.md` and optional `change_proposal.json`).
2. **Add a tuning overlay** (e.g. `config/tuning/active.json` or a named file in `config/tuning/examples/`).
3. **Run backtest comparison** (baseline vs proposed) and **regression guards**.
4. If guards pass, run **paper or canary** with the proposed config; collect attribution and effectiveness metrics.
5. **Revert** if falsification criteria are met (see proposal).

---

## Step 1: Change proposal

- **What** is changing: exact config diff (before/after).
- **Why:** which Phase 5 metrics justify it (signal_effectiveness, exit_effectiveness, entry_vs_exit_blame, counterfactual_exit).
- **Expected impact:** which metrics should improve.
- **Falsification criteria:** what would prove the change failed (so you can revert).
- **Rollback:** how to revert and how to verify.

Templates: `docs/templates/change_proposal.md`, `docs/templates/change_proposal.json`.

---

## Step 2: Tuning overlay

- **Schema:** `config/tuning/schema.json` (entry overlay, entry_weights_v3, entry_thresholds, exit_weights).
- **Active overlay:** `config/tuning/active.json` (optional). If present, merged over built-in defaults at runtime.
- **Named overlay:** set `GOVERNED_TUNING_CONFIG` to the path of a specific overlay (e.g. `config/tuning/examples/exit_flow_weight_plus_0.02.json`).

Example (exit weight only):

```json
{
  "version": "2026-02-17_exit_flow_plus_0.02",
  "exit_weights": {
    "flow_deterioration": 0.22
  }
}
```

See `config/tuning/README.md` for layout and apply/revert.

---

## Step 3: Backtest comparison and regression guards

### Backtest comparison

Compare two runs (effectiveness report dirs or backtest output dirs):

```bash
python scripts/governance/compare_backtest_runs.py --baseline reports/effectiveness_baseline --proposed reports/effectiveness_proposed [--out reports/governance_comparison]
```

If you pass **backtest dirs** (containing `backtest_exits.jsonl`), the script can generate effectiveness reports into a subdir and then compare. Output:

- `reports/governance_comparison/comparison.json` — aggregates (PnL, win rate, profit_giveback, total_trades) and deltas; entry_vs_exit_blame summaries.
- `reports/governance_comparison/comparison.md` — human-readable summary.

### Regression guards

Run guards (attribution invariants; optional effectiveness-dir quality checks):

```bash
python scripts/governance/regression_guards.py [--effectiveness-dir PATH] [--strict]
```

- **Attribution invariants:** composite_score == sum(entry attribution_components); exit_score == sum(exit attribution_components).
- **Optional:** pass `--effectiveness-dir` and baseline metrics to check that exit/entry quality has not materially worsened.

Exit code 0 = all pass; 1 = one or more failed.

---

## Step 4: Paper / canary

- Run paper trading (or limited canary) with the **proposed** config (e.g. `GOVERNED_TUNING_CONFIG=config/tuning/examples/exit_flow_weight_plus_0.02.json`).
- Collect the same attribution and effectiveness metrics as in Phase 5.
- Compare against baseline; revert if falsification criteria are met.

---

## Step 5: Revert

- Remove the overlay or restore the previous `config/tuning/active.json` from version control.
- Or set `GOVERNED_TUNING_CONFIG` to the baseline overlay (or unset it).
- Re-run regression guards and (if available) effectiveness report on the same period to verify.

---

## Example governed change

- **Overlay:** `config/tuning/examples/exit_flow_weight_plus_0.02.json` (flow_deterioration 0.20 → 0.22).
- **Proposal:** See `docs/templates/change_proposal.json` for a filled example; or `reports/change_proposals/example_exit_flow_weight_20260217.md` for a ready-to-adapt MD using `docs/templates/change_proposal.md`.

**Apply:**

```bash
# Option A: copy overlay to active
cp config/tuning/examples/exit_flow_weight_plus_0.02.json config/tuning/active.json

# Option B: use env (no file copy)
set GOVERNED_TUNING_CONFIG=config/tuning/examples/exit_flow_weight_plus_0.02.json
python scripts/governance/compare_backtest_runs.py --baseline backtests/30d_baseline --proposed backtests/30d_proposed
python scripts/governance/regression_guards.py
```

**Revert:**

```bash
# Option A: remove active overlay
del config\tuning\active.json   # or rm on Unix

# Option B: unset env
set GOVERNED_TUNING_CONFIG=
```

---

## Proof standard

Every change must be:

- **Traceable** to Phase 5 evidence.
- **Reversible** (config overlay only).
- **Measurable** (comparison + guards).
- **Reproducible** (versioned config, same scripts).
