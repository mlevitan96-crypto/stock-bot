# Alpaca Telegram — Message Format (Phase 2)

**Mission:** Governance-grade alert content and tone.  
**Authority:** CSA, SRE. READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Required Fields (Every Alert)

| Field | Description | Example |
|-------|-------------|---------|
| **Bot** | Identifier | ALPACA |
| **Dataset** | Source of count | TRADES_FROZEN |
| **Trade count reached** | Integer | 500 |
| **Coverage vs MEMORY_BANK bar** | Meets / below bar; join % and override note if applicable | Coverage: below bar (join 0%, override used) |
| **Next unlocked action** | One line | Minimum viable dataset reached; loss causality and profit discovery viable. |
| **Timestamp (UTC)** | ISO 8601 | 2026-03-18T14:30:00Z |

---

## 2. Trade-Count Milestone Message Template

```
[ALPACA] TRADES_FROZEN milestone

Dataset: TRADES_FROZEN
Trade count reached: {N}

Coverage: {meets bar | below bar ({entry_pct}% entry, {exit_pct}% exit){; override used if applicable}}

Next: {next_unlocked_action}

{timestamp_utc}
```

**Tone:** Informational, governance-grade, no spam. No emoji or casual language.

---

## 3. Analysis Completion Message Template

For phase-completion alerts (see ALPACA_TELEGRAM_ANALYSIS_ALERTS.md):

```
[ALPACA] Analysis phase complete

Phase: {phase_name}
Artifacts: {artifact_paths}
Readiness: {readiness_status}

{timestamp_utc}
```

---

## 4. Constraints

- **No spam:** One message per milestone per threshold; one per analysis phase completion (e.g. per pipeline run or explicit “phase done” trigger).
- **Length:** Keep to a few lines; use newlines for readability; avoid truncation of critical fields (count, coverage, paths).
- **Secrets:** Never include tokens, chat ids, or credentials in message body.
