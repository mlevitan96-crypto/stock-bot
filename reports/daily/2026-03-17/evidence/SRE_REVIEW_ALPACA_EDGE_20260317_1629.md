# SRE review: Alpaca 2000-trade edge discovery

- **Reproducibility:** INPUT_FREEZE.md documents TRADES_FROZEN.csv, ENTRY_ATTRIBUTION_FROZEN.jsonl, EXIT_ATTRIBUTION_FROZEN.jsonl hashes.
- **Caching integrity:** Bars cache under data/bars_cache (symbol/date_resolution.json); pipeline uses --bars-rate-limit-safe by default.
- **Rate-limit safety:** --bars-rate-limit-safe and --bars-batch-size control Alpaca Data API load; --skip-bars avoids API.
- **Dataset hashes:** Recorded in INPUT_FREEZE.md in report dir. No live or paper impact.
