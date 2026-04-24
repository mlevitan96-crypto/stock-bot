# ALPACA — Fix + proof (Phase 3)

## Failure class

| Class | Applies? |
|--------|----------|
| Scheduler not running | **No** — timer enabled/active; unit started 2026-03-27 20:30 UTC |
| Secrets/env mismatch | **No** — `apply_detected_telegram_env` OK; `getMe` OK |
| Chat routing wrong | **No evidence** — same env as stock-bot |
| Dedupe incorrect | **No** — no live send attempted for 2026-03-27 |
| Logic / timezone bug | **No** — failure explicit Memory Bank gate |
| Exception swallowed | **No** — exit 4 logged in journal |

**Primary:** Preconditions — **MEMORY_BANK canonical block missing** on droplet.

## Minimal fix (applied on droplet)

1. **Append** canonical block from mission artifact  
   `reports/daily/2026-03-27/evidence/MB_ALPACA_ATTRIBUTION_CONTRACT_APPEND.md`  
   to **`/root/stock-bot/MEMORY_BANK.md`** via SFTP to `/tmp/` + `cat >>` (does not remove prior content).

2. **Verification:**

```text
grep -c ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START /root/stock-bot/MEMORY_BANK.md
```

**Output:** `1`

## Rollback plan

- Remove appended section between  
  `<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->` and  
  `<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->`  
  from droplet `MEMORY_BANK.md` (restore from backup or `git checkout -- MEMORY_BANK.md` if committed).

## DRY-RUN send (explicit CSA policy: no LIVE without approval)

**Command:**

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot \
  ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py --dry-run --session-date-et 2026-03-27 --force
```

**Result:** **exit 0**. Payload excerpt (stdout):

```text
--- DRY-RUN (no Telegram HTTP) ---
 ALPACA DAILY POST-MARKET
Date (ET): 2026-03-27
Trades in session window: trade_intent=957 | exit_attribution_rows=256
...
Learning (strict read-only): ARMED | seen=255 incomplete=0 | reason=—
CSA: APPROVED_PLAN=YES | join_gate=PASS
...
Reports: ALPACA_POSTCLOSE_DEEPDIVE_20260327_2237.md | ALPACA_POSTCLOSE_SUMMARY_20260327_2237.md
```

**LIVE send:** **Not executed** — no explicit CSA approval in this mission thread.

## GATED Telegram when strict BLOCKED?

Post-close **does not** emit a separate “GATED” Telegram when dashboard-era strict is BLOCKED; it **would still send** the daily summary with embedded learning fields. Today’s silence was **not** that policy — it was **Memory Bank hard stop**.
