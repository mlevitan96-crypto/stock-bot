# SRE adversarial memo — integrity closure

## Operational fragility

- **`git pull` on droplet** can fail on **untracked** files under `reports/daily/**` (observed). Use `find … -exec mv /tmp` before pull, or commit evidence to `main`.
- **systemd ordering:** `Environment=` after `EnvironmentFile` must override `.env` for the same key; verify with `systemctl cat` after edits.
- **`rg` missing** on droplet broke one smoke grep; use `grep -E` in remote scripts.

## Restart / dependency risk

- **No stock-bot restart** — low blast radius.
- **`daemon-reload` only** — post-close / failure-detector pick up env on next trigger; integrity timer unchanged.

## Monitoring gaps

- Track **`checkpoint_100_precheck_ok`** and **`milestone_integrity_arm.arm_epoch_utc`** in a daily JSON scrape or log line (already appended in `logs/alpaca_telegram_integrity.log`).
- Alert if **DATA_READY** flips NO while trading continues.

## Recurrence prevention

- Keep **newest** warehouse coverage discoverable (flat + `daily/**`) — implemented in `warehouse_summary.py`.
