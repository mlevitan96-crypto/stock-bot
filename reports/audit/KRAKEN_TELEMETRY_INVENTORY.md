# Kraken telemetry inventory — droplet vs contract

**Method:** SSH to configured droplet (`DropletClient`); commands recorded in probe run 2026-03-18. Raw capture: `reports/audit/KRAKEN_DROPLET_PROBE_RAW.txt` (if present).

## 1. Unified events

| Check | Result |
|-------|--------|
| `unified_events.jsonl` under `/root` (depth ≤5) | **MISSING** — `find` returned no files |
| Venue-specific unified log for Kraken | **MISSING** |

**Status:** **MISSING**

## 2. Entry attribution (Kraken)

| Check | Result |
|-------|--------|
| Dedicated `kraken_*entry*` jsonl on droplet | **MISSING** (no Kraken live tree) |

**Status:** **MISSING** (Kraken-scoped)

## 3. Exit attribution (Kraken)

| Check | Result |
|-------|--------|
| Kraken venue exits | **MISSING** — live `/root/stock-bot/logs/exit_attribution.jsonl` contains **US equities** (e.g. PLTR), Alpaca-style lifecycle, **not** Kraken pairs |

**Status:** **MISSING** for Kraken; **OK/ACTIVE** for **Alpaca/stock-bot only** (do not relabel)

## 4. Execution logs

| Stream | Exists | Non-empty | Notes |
|--------|--------|-----------|-------|
| `submit_entry.jsonl` (stock-bot) | Yes | Yes (~9349 lines) | Alpaca path, not Kraken venue |

**Kraken execution trail:** **MISSING**

## 5. Blocked / counterfactual

| Check | Result |
|-------|--------|
| `state/blocked_trades.jsonl` (registry path) | Not probed line-by-line; **Kraken-specific** blocked log | **MISSING** as Kraken artifact |

## 6. Research-only Kraken data (non-trade)

| Path | Status |
|------|--------|
| `/root/stock-bot/data/raw/kraken` | **OK** — OHLC cache / download pipeline |
| `reports/massive_reviews/kraken_*` | **OK** — historical review outputs, not live telemetry |

## Summary table (Kraken live contract)

| Stream | Exists | Non-empty | Append-only verified | Last write | Schema version |
|--------|--------|-----------|----------------------|------------|----------------|
| unified_events (Kraken) | NO | — | — | — | — |
| Entry attribution (Kraken) | NO | — | — | — | — |
| Exit attribution (Kraken) | NO | — | — | — | — |
| Execution (Kraken) | NO | — | — | — | — |
| Blocked (Kraken) | NO | — | — | — | — |

**Verdict:** Kraken **live** telemetry inventory = **all MISSING**. Droplet runs **stock-bot (Alpaca)**; Kraken is **research/cache only** in this deployment.
