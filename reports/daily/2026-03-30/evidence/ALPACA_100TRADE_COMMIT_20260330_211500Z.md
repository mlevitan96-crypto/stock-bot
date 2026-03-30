# ALPACA_100TRADE_COMMIT_20260330_211500Z

- **Subject:** `feat(alpaca): 100-trade checkpoint in Telegram integrity cycle`
- **Verify SHA:** `git log -1 --oneline` on `origin/main` after pull.

## Droplet verification commands

```bash
cd /root/stock-bot && git pull origin main
PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py --skip-warehouse --send-test-100trade
cat state/alpaca_100trade_sent.json
```

Expect Telegram body to contain **`[TEST]`** and **`100-TRADE CHECKPOINT`**; JSON `test_100trade_sent: true`; guard file contains `last_test_100trade_utc`.
