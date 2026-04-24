# Alpaca DATA_READY — governance pack (2026-03-30)

Structured plan, role sign-offs, adversarial review, and CSA decision. **Execution on the droplet** requires: `git pull` this commit, **`APCA_*` in `/root/.alpaca_env`**, `systemctl restart` the trading unit, then `bash scripts/droplet_truth_warehouse_and_gates.sh`.

---

## 1. Objective

Raise **honest telemetry** toward **`DATA_READY: YES`** and **strict learning chain completeness** without weakening gates: execution join, fees/slippage inputs, corporate actions API, signal context at exit, and CSA strict cohort.

---

## 2. Plan (engineering)

| Step | Owner | Action |
|------|--------|--------|
| P1 | SRE | Ensure `/root/.alpaca_env` (or systemd `EnvironmentFile`) exports **`APCA_API_KEY_ID`** / **`APCA_API_SECRET_KEY`** (same as bot). Source before SSH audits: `. /root/.alpaca_env`. |
| P2 | Engineering | Persist **`entry_order_id`** on immediate fill → `state/position_metadata.json`; pass **`exit_order_id`**, **`entry_order_id`**, **`exit_ts`**, and **`order_id`** (duplicate of exit) on **`logs/exit_attribution.jsonl`** rows. |
| P3 | Engineering | Log **`close_position`** to **`orders.jsonl`** with **`order_id`**, **`filled_avg_price`**, **`filled_qty`**, **`ts`**, **`canonical_trade_id`** (via existing `log_order` merge). |
| P4 | SRE | Deploy repo to droplet; **restart bot** so new closes populate **`logs/exit_event.jsonl`** / **`exit_signal_snapshot.jsonl`** (`append_exit_*` already in code). |
| P5 | Quant | Run `scripts/droplet_truth_warehouse_and_gates.sh` (or runbook commands); track **`execution_join_coverage`**, **`fee_coverage`**, **`signal_snapshot_exits`**, **`corporate_actions`**. |
| P6 | CSA | Run `telemetry.alpaca_strict_completeness_gate.evaluate_completeness`; triage **`reason_histogram`** (legacy cohort may stay incomplete; forward era must tighten). |

---

## 3. SRE — confirmation

- **Confirmed:** Mission default root now prefers **`/root/stock-bot`** then **`/root/trading-bot-current`** when `TRADING_BOT_ROOT` is unset.  
- **Confirmed:** `scripts/droplet_truth_warehouse_and_gates.sh` sources `.alpaca_env` before Python.  
- **Risk called out:** If `.alpaca_env` remains Telegram-only, **`NO_API_KEYS`** and zero fee enrichment from REST will persist — **not a code bug**.  
- **Deploy:** After pull, restart the process that runs `main.py` so new telemetry fields appear on **new** exits only; historical rows stay unchanged.

---

## 4. Quant officer — confirmation

- **Confirmed:** `compute_join_coverage` treats an exit as joined if **`order_id`** or **`exit_order_id`** is present — populating both on new rows directly targets the gate.  
- **Confirmed:** Richer **`orders.jsonl`** close rows improve symbol/time proximity fallback and broker-side fee rows when keys exist.  
- **Measure success (3–5 sessions):** `execution_join_coverage` trending **up** on **new** window; fees/slippage move only after **keys + fills** in logs.  
- **Not claimed:** Instant **98%** on full **90d** history until enough **new** post-deploy exits exist.

---

## 5. CSA (contract / strict cohort) — confirmation

- **Confirmed:** Strict gate requires **unified entry/exit**, **orders with canonical_trade_id**, **exit_intent**, **entry_decision_made** (forward era) — **not** solved by order_id alone.  
- **Confirmed:** Adding **`entry_order_id`** to metadata and execution fields is **contract-aligned** (additive, join-friendly).  
- **Explicit non-action:** Do **not** lower **`STRICT_EPOCH_START`** or skip **`terminal_close`** checks to fake green.

---

## 6. Adversarial review

| Challenge | Response |
|-----------|----------|
| *You are gaming join % by duplicating `order_id`.* | Duplicate is **explicit documentation** for the mission reader; the **same** Alpaca UUID is stored once semantically as `exit_order_id`. |
| *98% join will still fail on old logs.* | True. **Forward-looking** proof is required; board narratives must segment **pre/post** deploy. |
| *`.alpaca_env` duplication leaks keys.* | File is already root-only; **same** pattern as systemd. No secrets in git. |
| *metadata `entry_order_id` missing for reconciled-only entries.* | Acknowledged gap; primary path is **immediate fill**. Reconciliation backfill can be a follow-up. |

---

## 7. CSA — decision (best path forward)

1. **Merge and deploy** this repository revision to the droplet.  
2. **Fix production env**: add **`APCA_*`** to `/root/.alpaca_env` **or** ensure audit cron uses the **same EnvironmentFile** as the bot.  
3. **Restart** the trading service.  
4. **Run** `bash scripts/droplet_truth_warehouse_and_gates.sh` and archive outputs under `replay/` and `reports/`.  
5. **Re-evaluate strict cohort** on **forward** closes only if needed (`forward_since_epoch` / postfix windows per existing audit scripts).  
6. **Strategy / PnL narratives** remain **blocked** until Quant + CSA agree gates are green or **documented waivers** exist.

---

## 8. Artifacts touched (this change set)

- `main.py` — `entry_order_id` persistence; `exit_attribution` execution fields; `close_position` `log_order` enrichment.  
- `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` — droplet root resolution.  
- `scripts/droplet_truth_warehouse_and_gates.sh` — one-shot audit + strict gate.  
- `docs/DATA_READY_RUNBOOK.md` — source `.alpaca_env` in example command.

---

*End of governance pack.*
