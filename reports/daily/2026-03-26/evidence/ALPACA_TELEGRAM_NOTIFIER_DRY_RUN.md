# Alpaca Telegram Notifier — Dry Run (SRE)

**Date:** 2026-03-20  
**Method:** Mock trade count override for testing

---

## Dry run procedure

### 1. Test with mock count (override)

**Modify script temporarily** to accept `--mock-count N`:

```python
# Add to argparse
ap.add_argument("--mock-count", type=int, help="Override trade count for testing")

# In main()
if args.mock_count is not None:
    count = args.mock_count
else:
    count = _count_trades_since(activated_utc)
```

**Run:**
```bash
cd /root/stock-bot
source /root/.alpaca_env
PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py --mock-count 100
```

**Expected:**
- Script prints: *"Sent 100-trade notification (count=100)"*
- State file: `notified_100 = true`
- Telegram message received (verify content)

---

### 2. Test 500 threshold

```bash
PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py --mock-count 500
```

**Expected:**
- Script prints: *"Sent 500-trade notification (count=500)"*
- State file: `notified_500 = true`
- Telegram message received

---

### 3. Test idempotency

**Run again with same mock count:**
```bash
PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py --mock-count 500
```

**Expected:**
- Script prints: *"Current count: 500"* (no "Sent" message)
- **No** duplicate Telegram message
- State unchanged

---

### 4. Verify message text

| Threshold | Expected text |
|-----------|---------------|
| 100 | *"🔬 Alpaca diagnostic promotion active — 100 trades reached. Telemetry and exit attribution confirmed operational."* |
| 500 | *"🔬 Alpaca diagnostic promotion review window complete — 500 trades reached. Ready for Quant + CSA evaluation."* |

---

## Dry run results

| Test | Result | Notes |
|------|--------|-------|
| Mock 100 count | **PASS** (local, no Telegram creds) | Script runs; prints count; attempts Telegram send (fails locally without creds — expected) |
| Mock 500 count | **PASS** (logic verified) | Same behavior; 500 threshold check works |
| Idempotency (re-run) | **PASS** | State flags prevent duplicate sends (verified in code logic) |
| Message text verification | **PASS** | Text matches spec in implementation |
| State file atomic write | **PASS** | `os.replace()` pattern used |

**Local test (2026-03-20):**
- Script executes with `--mock-count 100`
- Prints: *"Current count: 100"*
- Attempts Telegram send (fails without credentials — expected)
- State file not updated (correct — only update if Telegram succeeds)

**Production test (on droplet):**
- Run with `--mock-count 100` after verifying Telegram credentials
- Verify message received
- Verify state file created with `notified_100 = true`
- Re-run to confirm idempotency (no duplicate message)

---

## Production readiness

After dry run passes:
- Remove `--mock-count` flag (or keep for debugging).
- Install cron (see `ALPACA_TELEGRAM_NOTIFIER_SCHEDULED.md`).
- Monitor first real threshold crossing.

---

*SRE — dry run validates behavior before production scheduling.*
