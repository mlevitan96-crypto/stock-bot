# Live trading regression check (post-change)

## stock-bot systemd

From `ALPACA_INTEGRITY_CLOSURE_CONTEXT.md` — **`stock-bot.service` active (running)**; `deploy_supervisor.py`, `main.py`, `dashboard.py`, `heartbeat_keeper.py` in cgroup. No restart performed for this mission.

## Journal (last ~30 minutes)

File: `ALPACA_JOURNAL_STOCKBOT_30M_TAIL.txt` (400 lines from `journalctl -u stock-bot --since '30 minutes ago'`).

- **Grep `ERROR`:** no matches in captured tail.

## system_events.jsonl

Phase 0 capture attempted `rg ERROR` on tail — **`rg` not installed** on droplet; message `no_ERROR_in_tail` / stderr noted in `ALPACA_INTEGRITY_CLOSURE_CONTEXT.md`. **Not a proof of zero ERROR**; use journal tail above for regression signal.

## Strict (integrity precheck scope)

`ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json`: `strict.LEARNING_STATUS` = **ARMED** (session-open cohort).

## Verdict

No evidence of **stock-bot** instability or ERROR burst in the captured **30-minute** journal window after systemd copy / `daemon-reload` (which did not touch `stock-bot`).
