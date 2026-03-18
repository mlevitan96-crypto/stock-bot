# Kraken event emission trace (Phase 4)

## Required events (from contract)

Entry attribution → execution → exit (and optional unified/blocked).

## Codebase search (repo)

| Area | Finding |
|------|---------|
| `src/` | **No** `kraken` / Kraken venue emission |
| `main.py` | **`venue": "alpaca"`** only for live attribution context |
| `scripts/data/kraken_download_30d_resumable.py` | **Public REST OHLC** → checkpoints / cache files; **not** trade lifecycle events |
| `scripts/run_kraken_on_droplet.sh` flow | Massive **review** pipeline; downloads + reports under `kraken/` report dirs — **not** live order emission |

## Unconditional emission

**N/A for Kraken trades** — no emit path found.

## Ordering / silent failure

No `emit_kraken_entry` / `emit_kraken_exit` analog exists. **Dead branch:** entire live Kraken telemetry pipeline is **absent** in this repository.

## Conclusion

**Kraken live trade telemetry is not implemented in stock-bot repo.** Research/download paths exist; **execution stack is Alpaca-only** on audited droplet.
