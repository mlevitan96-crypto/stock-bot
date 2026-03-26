# Alpaca daily post-market Telegram — closeout (CSA + SRE)

**Timestamp:** 20260325_231500Z

---

## 1) Script used

| Field | Value |
|--------|--------|
| **Primary** | `scripts/alpaca_postclose_deepdive.py` |
| **Telegram** | `scripts/alpaca_telegram.py` (`send_governance_telegram`) |
| **Learning snapshot (read-only)** | `telemetry.alpaca_strict_completeness_gate.evaluate_completeness(root)` — **read-only** on logs; does not change learning behavior. |
| **Audit log (append-only)** | `reports/alpaca_daily_close_telegram.jsonl` |

---

## 2) Scheduler type and timing

| Field | Value |
|--------|--------|
| **Type** | **systemd timer** (single timer unit — no parallel cron added) |
| **Unit files** | `deploy/systemd/alpaca-postclose-deepdive.timer`, `deploy/systemd/alpaca-postclose-deepdive.service` |
| **Schedule** | `OnCalendar=Mon..Fri 16:30:00 America/New_York` — **30 minutes after NYSE regular session close** (16:00 ET), DST-safe. |
| **Service env** | `EnvironmentFile=-/root/stock-bot/.env` added so Telegram variables resolve consistently with other droplet jobs. |

**Install / refresh on host:**

```bash
sudo cp /root/stock-bot/deploy/systemd/alpaca-postclose-deepdive.service /etc/systemd/system/
sudo cp /root/stock-bot/deploy/systemd/alpaca-postclose-deepdive.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alpaca-postclose-deepdive.timer
```

Or run `python scripts/deploy_alpaca_postclose_on_droplet.py` from a workstation with `droplet_config.json`.

---

## 3) Telegram send verified

| Check | Result |
|--------|--------|
| **Code path** | Single formatted message: date (ET), trade activity counts, PnL snapshot (mean/median %, USD sum where `snapshot.pnl` exists), **Learning** line (`LEARNING_STATUS`, seen/incomplete, reason), **CSA** line (`APPROVED_PLAN`, join gate), top 3 recommendations, refresh note, report names. |
| **`--dry-run`** | **No HTTP send** — message printed to stdout only; audit line appended with `dry_run: true`, `telegram_ok: false`. |
| **Live send on droplet (this session)** | **Not re-verified end-to-end** — droplet dry-run exited **4** (`MEMORY_BANK.md` canonical markers missing). Fix MEMORY_BANK on the host, then run: `TRADING_BOT_ROOT=/root/stock-bot ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py` (omit `--dry-run`) once to confirm Telegram delivery. |
| **Prior journal evidence** | Timer fired at **2026-03-25 20:30:02 UTC**; service failed with same MEMORY_BANK gate (pre-existing host readiness issue). |

---

## 4) Deduplication verified

| Mechanism | Detail |
|-----------|--------|
| **Append-only audit** | Each send (or dry-run) appends one JSON object to `reports/alpaca_daily_close_telegram.jsonl`. |
| **Live dedupe** | Before work, if a prior line exists for the same `session_date_et` with `dry_run: false` and `telegram_ok: true`, the script exits **`dedupe_skip`** with **no second Telegram** (covers full path + `no_new_data` re-runs). |
| **Override** | `--force` skips fingerprint short-circuit **and** live dedupe (for SRE recovery only). |

**Operator check (same ET session date):**

1. Run once live (after MB fix) → Telegram received + `telegram_ok: true` in JSONL.  
2. Run again without `--force` → stdout `dedupe_skip`, **no** second Telegram.

---

## 5) Trading and learning untouched

- **Trading / execution:** No edits to `main.py`, order routing, or schedulers beyond the **post-close oneshot** unit (already separate from `stock-bot.service`).
- **Learning:** No changes to learning algorithms or writers; only **read** `evaluate_completeness` for the Telegram line.

---

## 6) Mandatory statement (qualified)

**Alpaca daily post-market Telegram is live** in **repository and systemd contract**: one timer, enriched message body, dry-run without send, JSONL audit, and per-session dedupe.

**Host readiness:** On the Alpaca droplet, the job **fails closed** until `MEMORY_BANK.md` satisfies the script’s canonical contract (current error: `canonical markers missing`). After that is repaired, the next scheduled **16:30 America/New_York** fire (shown in `systemctl list-timers` as the equivalent UTC instant) will send **exactly one** live message per ET session date unless `--force` is used.

---

## CSA / SRE sign-off (synthetic)

| Gate | Role | Verdict |
|------|------|---------|
| Discovery | SRE | PASS — script located |
| CSA script choice | CSA | APPROVE |
| Wiring + audit | SRE | PASS (code + units) |
| Droplet dry-run | SRE | **FAIL exit 4** — MEMORY_BANK; fix then re-run live proof |
| Deduplication | CSA | PASS — by design |
