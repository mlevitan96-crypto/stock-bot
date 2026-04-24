# Alpaca MEMORY_BANK — gap analysis (`20260328_213500Z`)

**Baseline:** `MEMORY_BANK.md` Alpaca-adjacent sections before Phase 3.  
**Truth:** `ALPACA_DROPLET_REALITY_20260328_213500Z.md` (SSH read-only).

| ID | Location / topic | Issue | Action |
|----|------------------|-------|--------|
| G1 | §6.5 ExecStart | Documented direct `venv/bin/python deploy_supervisor.py` | **UPDATE** → `systemd_start.sh` wrapper (verified) |
| G2 | §6.5 trading-bot.service | Ambiguous “may not exist” | **UPDATE** → `trading-bot.service` **not-found** on live host |
| G3 | §6.6 dashboard architecture | States dashboard is **only** supervisor child | **UPDATE** → separate `stock-bot-dashboard.service` owns `:5000`; supervisor also runs venv dashboard child |
| G4 | §6.3 isolation | “Do NOT reference trading-bot paths” vs multi-root scripts | **UPDATE** → live droplet has **`/root/stock-bot` only**; other paths are script fallbacks, not guaranteed |
| G5 | Alpaca quantified governance | No single “live droplet canon” block | **ADD** → `#### Alpaca droplet — live operational canon` |
| G6 | Tier 3 board review | “Not yet implemented Tier 1/2…” contradicts next heading | **DELETE** stale bullet |
| G7 | Fast-lane cron | MEMORY claims 15m/4h cron install | **UPDATE** → root crontab at verify had **no** fast-lane lines; treat install as **conditional** / verify on host |
| G8 | SPI / PnL | Already aligned with `--root` | **KEEP** (cross-ref canon path `/root/stock-bot`) |
| G9 | Alpaca Dashboard § Canonical service | Missing live runtime detail | **UPDATE** → `/usr/bin/python3`, port owner, dual-process note |

**Not changed (still valid on live host):**

- `droplet_config.json` `project_dir` `/root/stock-bot`
- Forbidden IP `147.182.255.165`
- `.env` + `.alpaca_env` split for systemd vs cron
- Strict epoch §1.1 (code-sourced, not SSH)

**End.**
