# ALPACA — Telegram pipeline ground truth (Phase 1)

**ET date:** `2026-03-27`

## A) Bot + routing health

### getMe (same stack as production: `scripts/alpaca_telegram_env_detect.apply_detected_telegram_env` + `urllib` to Telegram API)

**Command (droplet):** `TRADING_BOT_ROOT=/root/stock-bot venv/bin/python3` with env detect + `getMe` (see mission collector).

**Output (redacted — no token):**

```text
detect_ok True src systemd:/etc/systemd/system/stock-bot.service+/root/stock-bot/.env
{"ok":true,"result":{"id":8756383108,"is_bot":true,"first_name":"Stock Governance Daily","username":"Alpacadailybot",...}}
```

### Token + chat routing

- **Source:** `scripts/alpaca_telegram_env_detect.py` resolved to **`systemd:/etc/systemd/system/stock-bot.service+/root/stock-bot/.env`**
- **Routing:** `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` loaded from that stack (values not logged).

## B) Runner / scheduler proof

**Canonical entrypoint:** `scripts/alpaca_postclose_deepdive.py`  
**systemd:** `deploy/systemd/alpaca-postclose-deepdive.service` → `ExecStart=.../venv/bin/python3 .../scripts/alpaca_postclose_deepdive.py`  
**Timer:** `alpaca-postclose-deepdive.timer` — `OnCalendar=Mon..Fri 16:30:00 America/New_York`

**Droplet proof:**

```text
systemctl is-enabled alpaca-postclose-deepdive.timer
systemctl is-active alpaca-postclose-deepdive.timer
systemctl list-timers --all | grep alpaca-postclose
```

**Output:**

```text
enabled
active
Mon 2026-03-30 20:30:00 UTC   2 days Fri 2026-03-27 20:30:06 UTC  2h 6min ago alpaca-postclose-deepdive.timer ...
```

**Journal (same calendar day, service):**

```text
journalctl -u alpaca-postclose-deepdive.service --since today --no-pager
```

**Output (verbatim):**

```text
Mar 27 20:30:06 ... systemd[1]: Starting alpaca-postclose-deepdive.service ...
Mar 27 20:30:06 ... python3[1625840]: STOP — Memory Bank: canonical markers missing
Mar 27 20:30:06 ... systemd[1]: alpaca-postclose-deepdive.service: Main process exited, code=exited, status=4/NOPERMISSION
Mar 27 20:30:06 ... systemd[1]: Failed to start alpaca-postclose-deepdive.service ...
```

**Conclusion:** The runner **did execute today** at **20:30 UTC** (16:30 America/New_York). It **did not reach Telegram** because the process **exited 4** before send path.

**Cron:** `crontab -l | grep postclose` — **empty** (no duplicate cron path).

## C) Dedupe / sent-state

**Sent-state store:** `reports/alpaca_daily_close_telegram.jsonl` (append-only audit).

**Tail (droplet):** Last live success lines refer to **`session_date_et": "2035-01-02"`** (synthetic session from prior testing) and **`2026-03-25`** dry-run entries — **no entry for `2026-03-27`.**

**Watermark:** `state/postclose_watermark.json` still points at fingerprint session **`2035-01-02`** from **2026-03-25** — post-close did not advance state on **2026-03-27** due to early abort.

**Artifact:** `TELEGRAM_NOTIFICATION_LOG.md` exists untracked on droplet; **not** the primary driver of today’s silence (failure was pre-Telegram).
