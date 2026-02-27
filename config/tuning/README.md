# Governed Tuning (Phase 6)

All signal weights, penalties, and exit parameters must be **config-driven**, **versioned**, and **reversible**.

## Layout

- **schema.json** — Describes tunable parameters (entry, exit, thresholds) and their sources.
- **active.json** — Optional overlay applied at runtime. If missing, code uses defaults from `config/registry.py` and `uw_composite_v2.py` / `src/exit/exit_score_v2.py`.
- **examples/** — Example governed changes (small, safe, reversible).

## How to apply a change

1. Create a **change proposal** (see `docs/GOVERNED_TUNING_WORKFLOW.md`) with evidence from Phase 5 reports.
2. Add or edit **active.json** (or a named overlay, e.g. `proposed_20260217.json`).
3. Run backtest comparison (baseline vs proposed) and regression guards.
4. If guards pass, deploy to paper/canary; collect attribution and effectiveness metrics.
5. To **revert**: remove the overlay or restore previous `active.json` from version control.

## Environment

- `GOVERNED_TUNING_CONFIG` — Optional path to a tuning overlay (e.g. `config/tuning/proposed_20260217.json`). If set, this file is merged over the built-in defaults instead of `active.json`.
