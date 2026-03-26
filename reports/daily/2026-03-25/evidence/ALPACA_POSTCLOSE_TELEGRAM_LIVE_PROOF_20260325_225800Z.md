# Alpaca post-close Telegram — live synthetic proof (CSA + SRE)

**Timestamp:** 20260325_225800Z  
**Host:** Alpaca droplet (`/root/stock-bot`)

---

## Phase 0 — DONE contract (CSA)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `alpaca-postclose-deepdive.timer` **enabled** and **active** | **PASS** (`systemctl is-enabled` → `enabled`, `is-active` → `active`) |
| 2 | `alpaca-postclose-deepdive.service` runs **exit 0** for proof commands | **PASS** (all steps reported `PYEXIT:0`) |
| 3 | Telegram message **received** | **PASS (operational)** — live step (B) returned 0 and `send_governance_telegram` path has no HTTP error in output; **confirm on handset** if required for human CSA. |
| 4 | `reports/alpaca_daily_close_telegram.jsonl` appended with **`success: true`** for live send | **PASS** (see JSONL excerpt below, middle line) |
| 5 | Second run same `session_date_et` → **dedupe**, no second live send | **PASS** — third JSONL line has `dedupe_skip: true`; stdout `dedupe_skip: live Telegram already recorded` |

**CSA final verdict:** **LIVE_PROVEN** (synthetic session date; handset visual optional).

---

## Systemd timer

```text
systemctl is-enabled alpaca-postclose-deepdive.timer  → enabled
systemctl is-active alpaca-postclose-deepdive.timer   → active
```

`systemctl list-timers` (excerpt):

```text
NEXT                        LEFT LAST                              PASSED UNIT
Thu 2026-03-26 20:30:00 UTC  …    Wed 2026-03-25 20:30:02 UTC      …      alpaca-postclose-deepdive.timer
```

*(20:30 UTC during EDT equals **16:30 America/New_York**, i.e. 30 minutes after NYSE close.)*

Units refreshed from repo: `deploy/systemd/alpaca-postclose-deepdive.{service,timer}` → `/etc/systemd/system/`, `daemon-reload`, timer enabled/started.

---

## Synthetic proof protocol (no real trades required)

Pinned ET calendar date **`2035-01-02`** — no log rows fall in that session window → **0 trades** path, deterministic message body and stable `message_hash` across dry-run and live for the same artifact paths.

### A) Format only (no Telegram HTTP)

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot \
  ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py \
  --session-date-et 2035-01-02 --dry-run --force
```

- **Exit:** 0  
- **Expected:** stdout `DRY-RUN (no Telegram HTTP)`; JSONL line with `"dry_run": true`, `"success": false`, `"message_hash": "<sha256>"`.

### B) Live send once

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot \
  ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py \
  --session-date-et 2035-01-02 --force
```

- **Exit:** 0  
- **Expected:** JSONL line with `"dry_run": false`, **`"success": true`**, same `message_hash` as A (same body).

### C) Dedupe (no duplicate send)

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot \
  ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py \
  --session-date-et 2035-01-02
```

- **Exit:** 0  
- **Expected:** stdout `dedupe_skip:`; JSONL line with **`"dedupe_skip": true`**, `"success": false`.

---

## `alpaca_daily_close_telegram.jsonl` tail (proof date `2035-01-02`)

```jsonl
{"session_date_et": "2035-01-02", "dry_run": true, "dedupe_skip": false, "success": false, "telegram_ok": false, "message_hash": "fcfbf0b962076c7e3b6ae990faf1dcc20a2a35eb6279e04ecc73580312f04630", "message_kind": "full_deepdive", "no_new_data": false, "report_deep": "/root/stock-bot/reports/ALPACA_POSTCLOSE_DEEPDIVE_20350102_2254.md", "report_summary": "/root/stock-bot/reports/ALPACA_POSTCLOSE_SUMMARY_20350102_2254.md", "logged_at_utc": "2026-03-25T22:54:47.545509+00:00"}
{"session_date_et": "2035-01-02", "dry_run": false, "dedupe_skip": false, "success": true, "telegram_ok": true, "message_hash": "fcfbf0b962076c7e3b6ae990faf1dcc20a2a35eb6279e04ecc73580312f04630", "message_kind": "full_deepdive", "no_new_data": false, "report_deep": "/root/stock-bot/reports/ALPACA_POSTCLOSE_DEEPDIVE_20350102_2254.md", "report_summary": "/root/stock-bot/reports/ALPACA_POSTCLOSE_SUMMARY_20350102_2254.md", "logged_at_utc": "2026-03-25T22:54:55.279426+00:00"}
{"session_date_et": "2035-01-02", "dry_run": false, "dedupe_skip": true, "success": false, "telegram_ok": false, "message_hash": null, "message_kind": "dedupe_skip", "logged_at_utc": "2026-03-25T22:55:01.598728+00:00"}
```

---

## Trading / learning

- **No changes** to trading, execution, or learning **logic**.  
- **Read-only** `evaluate_completeness` continues to supply the learning line in the Telegram body.

---

## Mandatory closing statement

**No further trading days will be lost to unproven activation claims** for this pipeline: completion now requires **droplet exit 0**, **JSONL `success: true`** for a live send, and a **dedupe** audit line on immediate re-run for the same `session_date_et`. Synthetic proof above demonstrates the full path without real trades.

---

## SRE notes

- Upload used workspace `MEMORY_BANK.md` and `scripts/alpaca_postclose_deepdive.py` plus systemd units; re-run `deploy_alpaca_postclose_on_droplet.py` or equivalent after every change.  
- Windows runners: set `PYTHONIOENCODING=utf-8` when printing droplet file heads that contain Unicode.
