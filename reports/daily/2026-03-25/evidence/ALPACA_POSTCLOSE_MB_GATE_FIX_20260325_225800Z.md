# Alpaca post-close — MEMORY_BANK gate repair (SRE)

**Timestamp:** 20260325_225800Z

---

## Required markers (from `scripts/alpaca_postclose_deepdive.py`)

| Check | Expected |
|--------|-----------|
| Start / end | `<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->` … `<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->` |
| Title line | `## Alpaca attribution truth contract (canonical)` |
| Phrases | `decision_event_id`, `canonical_trade_id`, `symbol_normalized`, `time_bucket_id` |

---

## Before (droplet `/root/stock-bot/MEMORY_BANK.md`)

The first ~25 lines **did not** contain `ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START` or the canonical title block. The post-close job failed with:

```text
STOP — Memory Bank: canonical markers missing
```

(exit code **4**, observed in prior runs and reproduced before upload.)

---

## After (repair)

1. **Repo + droplet:** Inserted the canonical block (read-only documentation of join keys) immediately after the “DO NOT OVERWRITE” header in `MEMORY_BANK.md`.
2. **Verification on droplet:**

```bash
grep -q 'ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START' /root/stock-bot/MEMORY_BANK.md && echo MB_MARKERS_OK
```

**Result:** `MB_MARKERS_OK`

3. **Gate command (must be exit 0):**

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot \
  ./venv/bin/python3 scripts/alpaca_postclose_deepdive.py --dry-run --force
```

**Result:** **PYEXIT:0** (run `20260325T22:54Z` UTC, session inferred from logs as `2026-03-25`).

---

## STOP-GATE

**PASS** — MEMORY_BANK gate no longer blocks the post-close job on the Alpaca droplet.
