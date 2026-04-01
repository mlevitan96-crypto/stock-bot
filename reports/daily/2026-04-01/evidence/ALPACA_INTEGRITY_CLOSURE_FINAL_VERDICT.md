# Final verdict — Alpaca integrity closure mission (evidence-only)

**Evidence root:** `reports/daily/2026-04-01/evidence/`  
**Droplet repo HEAD (after pull + systemd copy):** `e813350493ed235261d2092f2c9b7ecb8e66dc53`  
**ET session anchor:** `2026-04-01`

| Question | Answer | Proof pointer |
|----------|--------|----------------|
| **Strict (integrity precheck / session open_ts)** | **ARMED** | `ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json` → `strict.LEARNING_STATUS` |
| **Strict (era export / default `STRICT_EPOCH_START`)** | **BLOCKED** | `ALPACA_STRICT_BASELINE.json` — different `open_ts_epoch` scope (see `ALPACA_ARM_BLOCKER_DIAGNOSIS.md`) |
| **Coverage DATA_READY deterministic + YES?** | **YES** | `ALPACA_COVERAGE_PARSE_BASELINE.json` (`parse_ok`, `data_ready_yes: true`); `ALPACA_COVERAGE_BASELINE.md` header |
| **Integrity session armed (`arm_epoch_utc` for anchor)?** | **YES** | `ALPACA_ARM_STATE_PROOF.md` + dry-run JSON |
| **250 milestone floored to 0 under integrity_armed?** | **NO** | `unique_closed_trades: 16` in dry-run JSON |
| **250 eligible to fire now?** | **NO** | `16 < 250`; `fired_milestone: false` |
| **Telegram prod senders (systemd paths) integrity-only?** | **YES** (for post-close + failure-detector units deployed) | `ALPACA_TELEGRAM_PROD_ENABLEMENT_PROOF.md` |

## Commits / artifacts

- **Coverage + systemd:** `e8133504` (`fix(integrity): load_latest_coverage scans reports/daily; systemd Telegram lockdown…`) + optional comment follow-up on `telegram-failure-detector.service`.
- **Collector:** `scripts/audit/collect_alpaca_integrity_closure_evidence.py` (rerun helper).

## Rollback (summary)

1. Revert `warehouse_summary.py` / systemd unit files to pre-change revision; `git checkout <rev> -- <paths>`; push; droplet `git pull`.
2. `cp` units to `/etc/systemd/system/`, `systemctl daemon-reload`.

## Rerun commands (droplet)

```bash
# Pull (resolve untracked conflicts first if any)
find /root/stock-bot/reports/daily -name 'ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_*.json' -exec mv -t /tmp {} + 2>/dev/null; true
cd /root/stock-bot && git pull origin main

# Systemd
sudo cp deploy/systemd/alpaca-postclose-deepdive.service /etc/systemd/system/
sudo cp deploy/systemd/telegram-failure-detector.service /etc/systemd/system/
sudo systemctl daemon-reload

# Baseline strict export (era cohort)
PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py --root /root/stock-bot \
  --out-json reports/daily/$(TZ=America/New_York date +%Y-%m-%d)/evidence/ALPACA_STRICT_BASELINE.json

# Coverage parse
PYTHONPATH=. python3 scripts/audit/parse_coverage_smoke_check.py --root /root/stock-bot \
  --out-json reports/daily/$(TZ=America/New_York date +%Y-%m-%d)/evidence/ALPACA_COVERAGE_PARSE_BASELINE.json

# Integrity dry-run (no Telegram HTTP; updates arm state when cp_ok)
PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py --dry-run --skip-warehouse --no-self-heal

# Optional: full collector from dev machine
python3 scripts/audit/collect_alpaca_integrity_closure_evidence.py
```

## PASS / FAIL

**PASS** for mission goals on droplet evidence date **2026-04-01**, with explicit **dual strict** disclosure and **250 not eligible** due to count &lt; target (not due to missing arm).
