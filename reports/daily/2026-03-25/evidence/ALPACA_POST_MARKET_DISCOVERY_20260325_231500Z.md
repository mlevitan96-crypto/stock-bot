# Alpaca post-market Telegram — discovery (SRE)

**Timestamp:** 20260325_231500Z

---

## Search terms used

- Post-close / postmarket / EOD / Telegram / Alpaca

---

## Existing implementation (canonical)

| Item | Detail |
|------|--------|
| **Script** | `scripts/alpaca_postclose_deepdive.py` |
| **Role** | Read-only scan of Alpaca session logs (`run.jsonl`, `orders.jsonl`, `signal_context.jsonl`, `blocked_trades.jsonl`, `exit_attribution.jsonl`), MEMORY_BANK contract check, markdown reports under `reports/`, optional Telegram. **Does not** touch trading or learning engines. |
| **Telegram transport** | `scripts/alpaca_telegram.py` → `send_governance_telegram()` using `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (env). Env resolution: `scripts/alpaca_telegram_env_detect.py`. |
| **Prior scheduler** | `deploy/systemd/alpaca-postclose-deepdive.timer` — was `Mon..Fri *-*-* 20:30:00` UTC (correct only when NY == UTC−4; wrong in standard time). |
| **Service** | `deploy/systemd/alpaca-postclose-deepdive.service` — `Type=oneshot`, `WorkingDirectory=/root/stock-bot`, venv `python3` on the script. |
| **Deploy helper** | `scripts/deploy_alpaca_postclose_on_droplet.py` — SFTP script + units, `daemon-reload`, enable timer, remote `--dry-run --force`. |
| **Other Telegram** | Fast-lane / governance scripts (`send_csa_fastlane_verdict_telegram.py`, etc.) — **out of scope** for this daily post-market contract. |

---

## Invocation before this change

| Mode | Status |
|------|--------|
| **systemd timer** | Present on Alpaca droplet; fires weekdays (see journal in closeout). |
| **Manual** | `cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py [--dry-run] [--force]` |

---

## Telegram behavior before change

- Message body was a short “POST-CLOSE DEEP DIVE COMPLETE” block (session, exits w/ pnl, join gate, CSA APPROVED_PLAN, top 3, report paths).
- **`--dry-run`** still called the Telegram API with a `TEST` prefix and updated behavior was ambiguous vs CSA “no send”.
- **Idempotency gap:** On “no new data” path, a **second** run the same session day could send **another** Telegram (duplicate).
- No append-only JSONL audit dedicated to this job.

---

## Conclusion

A **suitable post-market script exists** (`alpaca_postclose_deepdive.py`). It is Alpaca-log–scoped, read-only for trading/learning, and already integrated with Telegram + systemd.

**STOP-GATE:** **Do not stop** — proceed to wiring and scheduler hardening.

---

## Phase 1 — CSA verdict on discovery

**Verdict:** **APPROVE**

**Rationale:** This job is the governed daily Alpaca post-close / governance summary (deep dive + CSA join gate + board recommendations). Extending it for the daily Telegram contract avoids parallel schedulers and duplicate narrative. Trading and learning code paths remain untouched.
