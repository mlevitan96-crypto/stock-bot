# Droplet Full System Audit Proof

**Generated:** 2026-01-27T03:25:32.602577+00:00
**Date:** 2026-01-26
**Git Commit:** 6447fd67e481d17eeadf8a4ea8dc7aabb9da1d19

## Service Status
```
WorkingDirectory: /root/stock-bot
```

## PASS/FAIL Table (12 sections)
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

## §2 Evidence (Data & Features)
- **Symbol risk features count:** 53
- **File exists:** Yes

## §5 Evidence (Entry & Routing)
- **Audit dry-run orders count:** 0
0
- **Sample entries (redacted):**

## Confidence Score
91%

## Final Answer

**Can STOCK-BOT execute, manage, exit, observe, and learn from trades correctly?**

**MOSTLY YES (11/12)** — 1 subsystem(s) failed: §5