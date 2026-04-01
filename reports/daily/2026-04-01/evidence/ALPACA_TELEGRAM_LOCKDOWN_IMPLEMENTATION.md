# Telegram authority lockdown — implementation (approach B + systemd)

## Chosen approach

**B)** Gate non-integrity sends using existing `scripts/alpaca_telegram.py` behavior: when `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`, only `_INTEGRITY_ONLY_SCRIPT_NAMES` may hit the Telegram API.

## Repo / droplet changes

1. **`alpaca-postclose-deepdive.service`**  
   - After `EnvironmentFile=-/root/stock-bot/.env`, add:  
     `Environment=TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`  
   - **Effect:** post-close still writes Markdown reports; `send_governance_telegram(..., script_name="postclose_deepdive")` is **blocked** (not on allowlist).

2. **`telegram-failure-detector.service`**  
   - Same `Environment=` line.  
   - **Effect:** pager path `script_name="telegram_failure_detector"` blocked.

3. **`alpaca-telegram-integrity.service`**  
   - **Does not** set `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`.  
   - Integrity cycle uses allowlisted names (`alpaca_milestone_250`, `alpaca_data_integrity`, etc.).

## Rollback

1. Remove the `Environment=TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` lines from both unit files (or check out prior `deploy/systemd` revision).
2. `cp` units to `/etc/systemd/system/`, `systemctl daemon-reload`.
3. Optional: re-enable Telegram failure pager sends.

## Belt-and-suspenders (optional)

Set `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` in `/root/stock-bot/.env` to block **manual** CLI sends (tier reviews, promotion gate, etc.) that are not allowlisted. Not required for systemd timers covered above if operators only use units.

## Deep-dive capability preserved

`alpaca_postclose_deepdive.py` unchanged; reports and watermarks still produced; only HTTP send is blocked under this env.
