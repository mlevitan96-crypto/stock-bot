# DATA_READY runbook — Alpaca truth warehouse & strict cohort

**Canon (anti-drift):** `MEMORY_BANK.md` section **1.2** — Alpaca truth warehouse / `DATA_READY` baseline, keys, gates, and what YES does *not* imply vs strict learning.

**Premise:** Profitability work needs **honest telemetry**. This runbook ties **CSA** (truth / contracts), **SRE** (droplet execution + keys), and **Quant** (coverage metrics you can trade on) to the same commands.

---

## 1. Quant officer — “Can we explain PnL?”

Run the full-truth warehouse on the **droplet** (authoritative logs):

```bash
cd /root/stock-bot
# Or omit --root: mission defaults to /root/stock-bot then /root/trading-bot-current when TRADING_BOT_ROOT unset.
. /root/.alpaca_env 2>/dev/null || true
PYTHONPATH=. python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --root /root/stock-bot --days 90 --max-compute
```

- **`DATA_READY: YES`** → scripted PnL packet + ledgers are emitted under `replay/` and `reports/`.
- **`DATA_READY: NO`** → read `reports/ALPACA_TRUTH_WAREHOUSE_BLOCKERS_*.md` and `ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` (join %, fees, slippage, snapshots, UW, corp actions).

The mission now:

- Prefers **`exit_ts`** for exit rows (aligns joins/slippage/snapshots with `exit_attribution`).
- Parses **`/root/.alpaca_env`** when API keys are missing from the shell (SSH parity with cron).
- Treats **explicit $0** commissions as fee-computable (paper).
- Broadens **unified** join keys and **UW/decomposition** detection on score snapshots + intents.

---

## 2. SRE — “Will SSH runs lie?”

- Prefer: `cd /root/stock-bot && . /root/.alpaca_env && PYTHONPATH=. python3 scripts/...` so **broker REST** and **corporate-actions** calls always see keys.
- The mission’s auto-load of `.alpaca_env` only helps when that file contains **`APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`** (or aliases the mission already reads). If `.alpaca_env` is **Telegram-only** (common), export Alpaca keys into the shell before running, or add the same `APCA_*` lines you use for the bot/systemd unit.
- The auto-loader is a **safety net**, not a substitute for a proper service environment.

Deploy **`src/exit/exit_attribution.py`** (`append_exit_event` / `append_exit_signal_snapshot`) so **`logs/exit_event.jsonl`** fills on **new** closes after restart.

---

## 3. CSA — “Is the strict cohort decision-grade?”

Strict learning gate (join-complete trades):

```bash
cd /root/stock-bot
PYTHONPATH=. python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from telemetry.alpaca_strict_completeness_gate import evaluate_completeness, STRICT_EPOCH_START; print(evaluate_completeness(Path('.'), open_ts_epoch=STRICT_EPOCH_START, audit=False))"
```

- **`LEARNING_STATUS: READY`** → strict panel metrics are trustworthy for promotion-style review.
- **`BLOCKED` + `incomplete_trade_chain`** → fix **missing joins** (orders, unified events, intents) before treating stats as final.

---

## 4. Order of operations (recommended)

1. Deploy latest `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` + `exit_attribution` appenders; restart bot.
2. Run truth warehouse (**90d** first, then **180d** when green).
3. Run strict gate; triage incomplete trades using `telemetry/alpaca_strict_completeness_gate` precheck output.
4. Only then: massive PnL studies, counterfactuals, and board “profitability” narratives.

---

## 5. Role summary

| Role | Question | Primary artifact |
|------|-----------|------------------|
| **Quant** | Do coverage %s support attribution & scenarios? | `ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md`, `replay/alpaca_truth_warehouse_*` |
| **SRE** | Are droplet env + logs append-only and fresh? | crontab, `.alpaca_env`, log mtimes, bot restart after code deploy |
| **CSA** | Are strict-cohort and schema contracts satisfied? | `evaluate_completeness`, `memory_bank/TELEMETRY_STANDARD.md` |

This is the **only** durable path: **measure → fix data → review → change strategy**, repeat.

### Env tuning (optional)

- `ALPACA_TRUTH_CONTEXT_WINDOW_SEC` — seconds for exit ↔ `signal_context.jsonl` join (default **7200** in mission).
- `ALPACA_TRUTH_EXECUTION_WINDOW_SEC` — seconds for exit ↔ order fill time proximity (default **7200**).
- `ALPACA_TRUTH_THRESHOLD_SLIPPAGE` / `ALPACA_TRUTH_THRESHOLD_SIGNAL_SNAP` — override % gates (defaults **90** when `ALPACA_BASE_URL` is **paper**, else **95** for live-shaped runs).
