# Alpaca Repo ↔ Droplet Parity — Confirmed (SRE)

**UTC:** 2026-03-20  
**Local repo:** `c:\Dev\stock-bot`  
**Droplet:** `/root/stock-bot`

---

## Changes to commit locally

| File | Change type | Status |
|------|-------------|--------|
| `src/exit/exit_score_v2.py` | **Code change** — wiring `get_merged_exit_weights` | **Modified** (not committed) |
| `config/tuning/active.json` | **Config change** — diagnostic promotion overlay | **New file** (not tracked) |
| `state/alpaca_diagnostic_promotion.json` | **State marker** — promotion metadata | **New file** (not tracked) |
| `scripts/notify_alpaca_trade_milestones.py` | **New script** — trade milestone notifications | **New file** (not tracked) |
| `scripts/verify_telegram_env_alpaca.py` | **New helper** — credential verification | **New file** (not tracked) |
| `scripts/reset_notification_state.py` | **New helper** — state reset | **New file** (not tracked) |
| `scripts/install_alpaca_notifier_cron.sh` | **New helper** — cron installation | **New file** (not tracked) |
| `reports/audit/ALPACA_*.md` | **Documentation** — audit reports | **New files** (not tracked) |

---

## Droplet runtime state

| Item | Status |
|------|--------|
| **Files uploaded via SFTP** | **Yes** — `exit_score_v2.py`, `active.json`, promotion state, notifier script, helpers |
| **Service restarted** | **Yes** — `sudo systemctl restart stock-bot` (2026-03-20T00:22:45Z) |
| **Cron installed** | **Yes** — via `install_alpaca_notifier_cron.sh` |
| **Git HEAD on droplet** | `28abc2a33e365caa58736b99a175ae360f9d1447` (may be stale if local commits not pushed) |

---

## Parity restoration steps

1. **Commit locally:**
   ```bash
   git add src/exit/exit_score_v2.py
   git add config/tuning/active.json
   git add state/alpaca_diagnostic_promotion.json
   git add scripts/notify_alpaca_trade_milestones.py
   git add scripts/verify_telegram_env_alpaca.py
   git add scripts/reset_notification_state.py
   git add scripts/install_alpaca_notifier_cron.sh
   git add reports/audit/ALPACA_*.md
   git commit -m "Alpaca diagnostic promotion: SCORE_DETERIORATION_EMPHASIS + trade milestone notifications"
   ```

2. **Push to repo:**
   ```bash
   git push origin main
   ```

3. **Pull on droplet:**
   ```bash
   cd /root/stock-bot
   git pull origin main
   ```

4. **Verify:**
   - Git HEAD matches runtime
   - No untracked runtime diffs (config/tuning/active.json should match)
   - Service still active

---

## Current state

- **Runtime files on droplet:** Uploaded via SFTP; **active** and **operational**.
- **Git parity:** **Pending** — local commits not yet pushed; droplet git HEAD may be behind.

**Action required:** Commit and push from local machine to restore git parity.

---

*SRE — parity restoration pending local commit + push; runtime is operational.*
