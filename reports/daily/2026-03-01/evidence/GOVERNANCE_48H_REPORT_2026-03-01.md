# Governance Loop — Last 48 Hours Report

**Generated:** 2026-03-01 22:57:40 UTC
**Window:** 2026-02-27 22:57 UTC → 2026-03-01 22:57 UTC

---

## 1. Process status

- **Governance loop process:** Running

## 2. Loop state (current)

```json
{
  "last_lever": "",
  "last_candidate_expectancy": null,
  "prev_candidate_expectancy": null,
  "last_decision": "",
  "expectancy_history": [],
  "last_replay_jump_cycle": 0,
  "tried_entry_thresholds": [],
  "tried_exit_strengths": []
}
```

## 3. Cycles in last 48 hours

| Cycle (dir) | Time (UTC) | Decision | Lever | Baseline exp | Candidate exp |
| --- | --- | --- | --- | --- | --- |
| equity_governance_20260228T002149Z | 2026-02-28 00:21 |  | entry(min_exec_score=2.7) | None | None |
| equity_governance_20260228T001746Z | 2026-02-28 00:17 |  | entry(min_exec_score=2.7) | None | None |

### equity_governance_20260228T002149Z

**Decision:**
```json
{}
```

### equity_governance_20260228T001746Z

**Decision:**
```json
{}
```

## 4. Log activity (last 48h)

Total log lines in window: **2837**

<details>
<summary>Log excerpt (first 100 lines)</summary>

```
[2026-02-28T00:17:45Z] === GOVERNANCE CYCLE 1 ===
[2026-02-28T00:17:45Z] === GOVERNANCE CYCLE 1 ===
[2026-02-28T00:17:46Z] Lever variety: cycle=1 ENTRY_THRESHOLD=2.7 EXIT_STRENGTH=0.02
[2026-02-28T00:17:46Z] Lever variety: cycle=1 ENTRY_THRESHOLD=2.7 EXIT_STRENGTH=0.02
[2026-02-28T00:17:46Z] === EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ===
[2026-02-28T00:17:46Z] === EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ===
[2026-02-28T00:17:46Z] OUT_DIR=reports/equity_governance/equity_governance_20260228T001746Z BASELINE_DIR=reports/effectiveness_baseline_blame
[2026-02-28T00:17:46Z] OUT_DIR=reports/equity_governance/equity_governance_20260228T001746Z BASELINE_DIR=reports/effectiveness_baseline_blame
[2026-02-28T00:17:46Z] MIN_CLOSED_TRADES=100
[2026-02-28T00:17:46Z] MIN_CLOSED_TRADES=100
[2026-02-28T00:17:46Z] A1 Baseline effectiveness (equity from logs) -> reports/effectiveness_baseline_blame
[2026-02-28T00:17:46Z] A1 Baseline effectiveness (equity from logs) -> reports/effectiveness_baseline_blame
[2026-02-28T00:17:46Z] Baseline joined_count=2320 total_losing_trades=1431
[2026-02-28T00:17:46Z] Baseline joined_count=2320 total_losing_trades=1431
[2026-02-28T00:17:46Z] A2 Generating recommendation (entry vs exit)
[2026-02-28T00:17:46Z] A2 Generating recommendation (entry vs exit)
[2026-02-28T00:17:46Z] A2 Replay-driven lever selection (live vs top replay candidate)
[2026-02-28T00:17:46Z] A2 Replay-driven lever selection (live vs top replay candidate)
[2026-02-28T00:17:46Z] Lever=entry
[2026-02-28T00:17:46Z] Lever=entry
[2026-02-28T00:17:47Z] Autopilot script failed. Exiting loop.
[2026-02-28T00:21:49Z] === GOVERNANCE CYCLE 1 ===
[2026-02-28T00:21:49Z] === GOVERNANCE CYCLE 1 ===
[2026-02-28T00:21:49Z] Lever variety: cycle=1 ENTRY_THRESHOLD=2.7 EXIT_STRENGTH=0.02
[2026-02-28T00:21:49Z] Lever variety: cycle=1 ENTRY_THRESHOLD=2.7 EXIT_STRENGTH=0.02
[2026-02-28T00:21:49Z] === EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ===
[2026-02-28T00:21:49Z] === EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ===
[2026-02-28T00:21:49Z] OUT_DIR=reports/equity_governance/equity_governance_20260228T002149Z BASELINE_DIR=reports/effectiveness_baseline_blame
[2026-02-28T00:21:49Z] OUT_DIR=reports/equity_governance/equity_governance_20260228T002149Z BASELINE_DIR=reports/effectiveness_baseline_blame
[2026-02-28T00:21:49Z] MIN_CLOSED_TRADES=100
[2026-02-28T00:21:49Z] MIN_CLOSED_TRADES=100
[2026-02-28T00:21:49Z] A1 Baseline effectiveness (equity from logs) -> reports/effectiveness_baseline_blame
[2026-02-28T00:21:49Z] A1 Baseline effectiveness (equity from logs) -> reports/effectiveness_baseline_blame
[2026-02-28T00:21:49Z] Baseline joined_count=2320 total_losing_trades=1431
[2026-02-28T00:21:49Z] Baseline joined_count=2320 total_losing_trades=1431
[2026-02-28T00:21:50Z] A2 Generating recommendation (entry vs exit)
[2026-02-28T00:21:50Z] A2 Generating recommendation (entry vs exit)
[2026-02-28T00:21:50Z] A2 Replay-driven lever selection (live vs top replay candidate)
[2026-02-28T00:21:50Z] A2 Replay-driven lever selection (live vs top replay candidate)
[2026-02-28T00:21:50Z] Lever=entry
[2026-02-28T00:21:50Z] Lever=entry
[2026-02-28T00:21:50Z] A3 Using overlay from replay-driven lever selection -> lever=entry
[2026-02-28T00:21:50Z] A3 Using overlay from replay-driven lever selection -> lever=entry
[2026-02-28T00:21:52Z] A3 Restarted stock-bot with overlay active
[2026-02-28T00:21:52Z] A3 Restarted stock-bot with overlay active
[2026-02-28T00:21:52Z] A4 Waiting for >=100 closed trades (since 2026-02-28)
[2026-02-28T00:21:52Z] A4 Waiting for >=100 closed trades (since 2026-02-28)
[2026-02-28T00:21:53Z] Overlay joined_count=0
[2026-02-28T00:21:53Z] Overlay joined_count=0
[2026-02-28T00:23:53Z] Overlay joined_count=0
[2026-02-28T00:23:53Z] Overlay joined_count=0
[2026-02-28T00:25:53Z] Overlay joined_count=0
[2026-02-28T00:25:53Z] Overlay joined_count=0
[2026-02-28T00:27:54Z] Overlay joined_count=0
[2026-02-28T00:27:54Z] Overlay joined_count=0
[2026-02-28T00:29:54Z] Overlay joined_count=0
[2026-02-28T00:29:54Z] Overlay joined_count=0
[2026-02-28T00:31:54Z] Overlay joined_count=0
[2026-02-28T00:31:54Z] Overlay joined_count=0
[2026-02-28T00:33:54Z] Overlay joined_count=0
[2026-02-28T00:33:54Z] Overlay joined_count=0
[2026-02-28T00:35:55Z] Overlay joined_count=0
[2026-02-28T00:35:55Z] Overlay joined_count=0
[2026-02-28T00:37:55Z] Overlay joined_count=0
[2026-02-28T00:37:55Z] Overlay joined_count=0
[2026-02-28T00:39:55Z] Overlay joined_count=0
[2026-02-28T00:39:55Z] Overlay joined_count=0
[2026-02-28T00:41:56Z] Overlay joined_count=0
[2026-02-28T00:41:56Z] Overlay joined_count=0
[2026-02-28T00:43:56Z] Overlay joined_count=0
[2026-02-28T00:43:56Z] Overlay joined_count=0
[2026-02-28T00:45:56Z] Overlay joined_count=0
[2026-02-28T00:45:56Z] Overlay joined_count=0
[2026-02-28T00:47:57Z] Overlay joined_count=0
[2026-02-28T00:47:57Z] Overlay joined_count=0
[2026-02-28T00:49:57Z] Overlay joined_count=0
[2026-02-28T00:49:57Z] Overlay joined_count=0
[2026-02-28T00:51:57Z] Overlay joined_count=0
[2026-02-28T00:51:57Z] Overlay joined_count=0
[2026-02-28T00:53:58Z] Overlay joined_count=0
[2026-02-28T00:53:58Z] Overlay joined_count=0
[2026-02-28T00:55:58Z] Overlay joined_count=0
[2026-02-28T00:55:58Z] Overlay joined_count=0
[2026-02-28T00:57:58Z] Overlay joined_count=0
[2026-02-28T00:57:58Z] Overlay joined_count=0
[2026-02-28T00:59:58Z] Overlay joined_count=0
[2026-02-28T00:59:58Z] Overlay joined_count=0
[2026-02-28T01:01:59Z] Overlay joined_count=0
[2026-02-28T01:01:59Z] Overlay joined_count=0
[2026-02-28T01:03:59Z] Overlay joined_count=0
[2026-02-28T01:03:59Z] Overlay joined_count=0
[2026-02-28T01:05:59Z] Overlay joined_count=0
[2026-02-28T01:05:59Z] Overlay joined_count=0
[2026-02-28T01:08:00Z] Overlay joined_count=0
[2026-02-28T01:08:00Z] Overlay joined_count=0
[2026-02-28T01:10:00Z] Overlay joined_count=0
[2026-02-28T01:10:00Z] Overlay joined_count=0
[2026-02-28T01:12:00Z] Overlay joined_count=0
[2026-02-28T01:12:00Z] Overlay joined_count=0
[2026-02-28T01:14:01Z] Overlay joined_count=0
```
</details>

<details>
<summary>Log excerpt (last 100 lines)</summary>

```
[2026-03-01T21:18:33Z] Overlay joined_count=0
[2026-03-01T21:18:33Z] Overlay joined_count=0
[2026-03-01T21:20:34Z] Overlay joined_count=0
[2026-03-01T21:20:34Z] Overlay joined_count=0
[2026-03-01T21:22:34Z] Overlay joined_count=0
[2026-03-01T21:22:34Z] Overlay joined_count=0
[2026-03-01T21:24:34Z] Overlay joined_count=0
[2026-03-01T21:24:34Z] Overlay joined_count=0
[2026-03-01T21:26:35Z] Overlay joined_count=0
[2026-03-01T21:26:35Z] Overlay joined_count=0
[2026-03-01T21:28:35Z] Overlay joined_count=0
[2026-03-01T21:28:35Z] Overlay joined_count=0
[2026-03-01T21:30:35Z] Overlay joined_count=0
[2026-03-01T21:30:35Z] Overlay joined_count=0
[2026-03-01T21:32:36Z] Overlay joined_count=0
[2026-03-01T21:32:36Z] Overlay joined_count=0
[2026-03-01T21:34:36Z] Overlay joined_count=0
[2026-03-01T21:34:36Z] Overlay joined_count=0
[2026-03-01T21:36:36Z] Overlay joined_count=0
[2026-03-01T21:36:36Z] Overlay joined_count=0
[2026-03-01T21:38:36Z] Overlay joined_count=0
[2026-03-01T21:38:36Z] Overlay joined_count=0
[2026-03-01T21:40:37Z] Overlay joined_count=0
[2026-03-01T21:40:37Z] Overlay joined_count=0
[2026-03-01T21:42:37Z] Overlay joined_count=0
[2026-03-01T21:42:37Z] Overlay joined_count=0
[2026-03-01T21:44:37Z] Overlay joined_count=0
[2026-03-01T21:44:37Z] Overlay joined_count=0
[2026-03-01T21:46:38Z] Overlay joined_count=0
[2026-03-01T21:46:38Z] Overlay joined_count=0
[2026-03-01T21:48:38Z] Overlay joined_count=0
[2026-03-01T21:48:38Z] Overlay joined_count=0
[2026-03-01T21:50:38Z] Overlay joined_count=0
[2026-03-01T21:50:38Z] Overlay joined_count=0
[2026-03-01T21:52:38Z] Overlay joined_count=0
[2026-03-01T21:52:38Z] Overlay joined_count=0
[2026-03-01T21:54:39Z] Overlay joined_count=0
[2026-03-01T21:54:39Z] Overlay joined_count=0
[2026-03-01T21:56:39Z] Overlay joined_count=0
[2026-03-01T21:56:39Z] Overlay joined_count=0
[2026-03-01T21:58:39Z] Overlay joined_count=0
[2026-03-01T21:58:39Z] Overlay joined_count=0
[2026-03-01T22:00:40Z] Overlay joined_count=0
[2026-03-01T22:00:40Z] Overlay joined_count=0
[2026-03-01T22:02:40Z] Overlay joined_count=0
[2026-03-01T22:02:40Z] Overlay joined_count=0
[2026-03-01T22:04:40Z] Overlay joined_count=0
[2026-03-01T22:04:40Z] Overlay joined_count=0
[2026-03-01T22:06:40Z] Overlay joined_count=0
[2026-03-01T22:06:40Z] Overlay joined_count=0
[2026-03-01T22:08:41Z] Overlay joined_count=0
[2026-03-01T22:08:41Z] Overlay joined_count=0
[2026-03-01T22:10:41Z] Overlay joined_count=0
[2026-03-01T22:10:41Z] Overlay joined_count=0
[2026-03-01T22:12:41Z] Overlay joined_count=0
[2026-03-01T22:12:41Z] Overlay joined_count=0
[2026-03-01T22:14:42Z] Overlay joined_count=0
[2026-03-01T22:14:42Z] Overlay joined_count=0
[2026-03-01T22:16:42Z] Overlay joined_count=0
[2026-03-01T22:16:42Z] Overlay joined_count=0
[2026-03-01T22:18:42Z] Overlay joined_count=0
[2026-03-01T22:18:42Z] Overlay joined_count=0
[2026-03-01T22:20:43Z] Overlay joined_count=0
[2026-03-01T22:20:43Z] Overlay joined_count=0
[2026-03-01T22:22:43Z] Overlay joined_count=0
[2026-03-01T22:22:43Z] Overlay joined_count=0
[2026-03-01T22:24:43Z] Overlay joined_count=0
[2026-03-01T22:24:43Z] Overlay joined_count=0
[2026-03-01T22:26:43Z] Overlay joined_count=0
[2026-03-01T22:26:43Z] Overlay joined_count=0
[2026-03-01T22:28:44Z] Overlay joined_count=0
[2026-03-01T22:28:44Z] Overlay joined_count=0
[2026-03-01T22:30:44Z] Overlay joined_count=0
[2026-03-01T22:30:44Z] Overlay joined_count=0
[2026-03-01T22:32:44Z] Overlay joined_count=0
[2026-03-01T22:32:44Z] Overlay joined_count=0
[2026-03-01T22:34:45Z] Overlay joined_count=0
[2026-03-01T22:34:45Z] Overlay joined_count=0
[2026-03-01T22:36:45Z] Overlay joined_count=0
[2026-03-01T22:36:45Z] Overlay joined_count=0
[2026-03-01T22:38:45Z] Overlay joined_count=0
[2026-03-01T22:38:45Z] Overlay joined_count=0
[2026-03-01T22:40:45Z] Overlay joined_count=0
[2026-03-01T22:40:45Z] Overlay joined_count=0
[2026-03-01T22:42:46Z] Overlay joined_count=0
[2026-03-01T22:42:46Z] Overlay joined_count=0
[2026-03-01T22:44:46Z] Overlay joined_count=0
[2026-03-01T22:44:46Z] Overlay joined_count=0
[2026-03-01T22:46:46Z] Overlay joined_count=0
[2026-03-01T22:46:46Z] Overlay joined_count=0
[2026-03-01T22:48:47Z] Overlay joined_count=0
[2026-03-01T22:48:47Z] Overlay joined_count=0
[2026-03-01T22:50:47Z] Overlay joined_count=0
[2026-03-01T22:50:47Z] Overlay joined_count=0
[2026-03-01T22:52:47Z] Overlay joined_count=0
[2026-03-01T22:52:47Z] Overlay joined_count=0
[2026-03-01T22:54:47Z] Overlay joined_count=0
[2026-03-01T22:54:47Z] Overlay joined_count=0
[2026-03-01T22:56:48Z] Overlay joined_count=0
[2026-03-01T22:56:48Z] Overlay joined_count=0
```
</details>

---

*Report produced by `scripts/governance/run_governance_48h_report_on_droplet.py`*