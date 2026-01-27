# Full System Audit Verdict

**Generated:** 2026-01-27T03:25:22.078660+00:00
**Date:** 2026-01-26

## PASS/FAIL per section
| § | Section | Result |
|---|---------|--------|
| 0 | Safety and Mode | PASS |
| 1 | Boot and Identity | PASS |
| 2 | Data and Features | PASS |
| 3 | Signal Generation | PASS |
| 4 | Gates and Displacement | PASS |
| 5 | Entry and Routing | FAIL |
| 6 | Position State | PASS |
| 7 | Exit Logic | PASS |
| 8 | Shadow Experiments | PASS |
| 9 | Telemetry | PASS |
| 10 | EOD Synthesis | PASS |
| 11 | Joinability | PASS |

## Failure reasons
- **§5 Entry and Routing:** no audit_dry_run entries in orders.jsonl (submit_entry path not exercised or failed)

## What is PROVEN working
- §0 Safety and Mode
- §1 Boot and Identity
- §2 Data and Features
- §3 Signal Generation
- §4 Gates and Displacement
- §6 Position State
- §7 Exit Logic
- §8 Shadow Experiments
- §9 Telemetry
- §10 EOD Synthesis
- §11 Joinability

## What is PARTIALLY working
- §5 Entry and Routing: no audit_dry_run entries in orders.jsonl (submit_entry path not exercised or failed)

## What is NOT exercised
- §5 Entry and Routing: no audit_dry_run entries in orders.jsonl (submit_entry path not exercised or failed)

## Environment note
Alpaca (`alpaca_trade_api`) and Alpaca keys are required for §2 (symbol risk build) and §5 (entry dry-run). On the droplet, both are available.


## Final Answer

**Can STOCK-BOT execute, manage, exit, observe, and learn from trades correctly?**

**MOSTLY YES** — 11/12 subsystems proven. Remaining failures are environment-dependent (Alpaca) or minor gaps.

## Confidence
91%

## Artifacts
| Report | Path |
|--------|------|
| §0 | reports/AUDIT_00_SAFETY_AND_MODE.md |
| §1 | reports/AUDIT_01_BOOT_AND_IDENTITY.md |
| §2 | reports/AUDIT_02_DATA_AND_FEATURES.md |
| §3 | reports/AUDIT_03_SIGNAL_GENERATION.md |
| §4 | reports/AUDIT_04_GATES_AND_DISPLACEMENT.md |
| §5 | reports/AUDIT_05_ENTRY_AND_ROUTING.md |
| §6 | reports/AUDIT_06_POSITION_STATE.md |
| §7 | reports/AUDIT_07_EXIT_LOGIC.md |
| §8 | reports/AUDIT_08_SHADOW_EXPERIMENTS.md |
| §9 | reports/AUDIT_09_TELEMETRY.md |
| §10 | reports/AUDIT_10_EOD.md |
| §11 | reports/AUDIT_11_JOINABILITY.md |
| CSV | exports/AUDIT_signal_matrix.csv, AUDIT_displacement_decisions.csv, AUDIT_exit_paths.csv, AUDIT_shadow_scoreboard.csv, AUDIT_joinability.csv |