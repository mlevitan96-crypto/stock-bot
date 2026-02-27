# Getting Trading Operational — Signals Fix Summary

**Date:** 2026-02-23 (post droplet upgrade: 4 AMD vCPUs, 8 GB RAM, 160 GB disk)

---

## 1. Done

- **Services restarted** on the upgraded droplet:
  - `stock-bot.service` → main loop, deploy_supervisor, dashboard, heartbeat_keeper
  - `uw-flow-daemon.service` → populates `data/uw_flow_cache.json`
- **Intel producers run** on droplet:
  - `build_daily_universe.py` → `state/daily_universe.json`
  - `run_premarket_intel.py` → `state/premarket_intel.json`
  - `run_postmarket_intel.py` → `state/postmarket_intel.json`
  - `build_expanded_intel.py` → **55 symbols** written to `data/uw_expanded_intel.json`
- **Cache status:** `uw_flow_cache.json` and `uw_expanded_intel.json` exist and are recent (~17:01–17:03 UTC). UW daemon is running and growing the cache.

---

## 2. Current blocker: scores below MIN_EXEC_SCORE (2.5)

- **Audit result:** 100% of candidates blocked at **5_expectancy_gate** (score_floor_breach).
- **Score distribution:** median = 0.172; max in sample ≈ 1.055 (SPY, CAT). **0%** of candidates above 2.5.
- **Verdict:** Pipeline is correct; **composite scores are too low**, not a gate bug.

---

## 3. Why scores are low

- **Composite** = sum of component contributions × freshness (clamp 0–8). Key components: options_flow (2.4), dark_pool (1.3), congress (0.9), shorts_squeeze (0.7), etc.
- Many components are **0** when data is missing (we removed placeholder defaults). Per earlier audits: **congress, shorts_squeeze, institutional, calendar, whale, motif_bonus** were 100% zero for many symbols because no producer was writing them into the cache.
- **UW daemon** is the main writer for conviction, sentiment, dark_pool, insider, congress, institutional, calendar, greeks, etc. If the UW API returns sparse data or the daemon only polls a subset of symbols, those components stay 0 and the composite stays low.

---

## 4. What to do next (fix signals)

1. **Keep daemon and intel producers running**
   - Daemon: already started via `uw-flow-daemon.service`.
   - Intel producers: run daily or after market open/close (e.g. cron or manual):
     ```bash
     cd /root/stock-bot && python3 scripts/build_daily_universe.py && python3 scripts/run_premarket_intel.py && python3 scripts/run_postmarket_intel.py && python3 scripts/build_expanded_intel.py
     ```
   - Or from local: `python scripts/run_intel_producers_on_droplet.py`

2. **Verify cache has conviction/sentiment**
   - On droplet:  
     `python3 -c "import json; c=json.load(open('data/uw_flow_cache.json')); syms=[k for k in c if isinstance(c.get(k),dict)]; print(len(syms)); [print(k, c[k].get('conviction'), c[k].get('sentiment')) for k in syms[:10]]"`
   - If conviction/sentiment are mostly None/empty, the UW API or daemon config (symbols, rate limits) may need adjustment.

3. **Optional: sync `signal_audit_diagnostic.py` to droplet**
   - The script is not on the droplet (older repo). Push to GitHub, pull on droplet, then re-run:
     `python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7`
   - That will produce per-component breakdown (which signals are dead/muted) in the audit report.

4. **Optional: temporary MIN_EXEC_SCORE for testing**
   - To get a few trades while improving data: on the droplet set env for `stock-bot.service`, e.g. `MIN_EXEC_SCORE=1.1`, then restart. **Revert to 2.5** once signals are fixed.

---

## 5. References

- **Checklist:** `docs/SIGNAL_DATA_SOURCES_AND_CHECKLIST.md`
- **Audit:** `reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md`
- **Start services after reboot:** `python scripts/start_droplet_services.py`
