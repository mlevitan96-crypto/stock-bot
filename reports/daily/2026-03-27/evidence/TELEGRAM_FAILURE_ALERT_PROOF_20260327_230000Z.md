# Telegram failure alert — proof (Phase 3–5)

**TS:** `20260327_230000Z`

## Detector

- **Script:** `scripts/governance/telegram_failure_detector.py`
- **State:** `state/telegram_failure_pager_state.json` (dedupe + last window states)

## systemd (droplet)

**Unit files (repo):**

- `deploy/systemd/telegram-failure-detector.service`
- `deploy/systemd/telegram-failure-detector.timer` — **every 5 minutes** (`OnUnitActiveSec=5min`)

**Install:** `python scripts/governance/install_telegram_failure_detector_on_droplet.py`

**Captured output (install run):**

```text
systemctl is-active telegram-failure-detector.timer
active

systemctl list-timers --all | grep telegram-failure
Fri 2026-03-27 22:51:51 UTC ... telegram-failure-detector.timer     telegram-failure-detector.service
```

## Dry-run paging (droplet)

Command:

```bash
cd /root/stock-bot && venv/bin/python3 scripts/governance/telegram_failure_detector.py --dry-run
```

**Excerpt (stdout):** Alpaca **post_close** evaluated **`SEND_FAILED`** / `memory_bank_or_nonzero_exit` with **auto_heal** `alpaca_strict_audit_ran`; **dry-run** printed **`TELEGRAM FAILURE PAGER — ALERT`** (no live HTTP when `--dry-run`).

## Auto-heal (Phase 4)

| Venue | Hook |
|-------|------|
| **alpaca** | `telemetry/alpaca_strict_completeness_gate.py --root <root> --audit` (read-only evaluation; **does not** weaken gates) |
| **kraken** | `scripts/governance/check_direction_readiness_and_run.py` (existing idempotent refresh) |
| **alpaca milestone** | **No auto-heal** (`milestone_no_auto_heal`) to avoid spurious notifier invocations |

After heal, **post_close** and **kraken** windows are **re-evaluated** once.

## REMEDIATED path

When a window transitions from a failing state to **`SENT`** / **`PASS`**, the detector emits **`TELEGRAM FAILURE PAGER — REMEDIATED`** (covered in `tests/test_telegram_failure_detector.py`).
