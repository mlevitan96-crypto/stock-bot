# BOARD_SRE_PROFIT_VERDICT

## Evidence anchors

- Ran on droplet `/root/stock-bot`; runtime ~seconds for **432** exits + **2000** snapshots tail + **6k** blocked tail.
- **Minute-level counterfactuals not run:** `artifacts/market_data/alpaca_bars.jsonl` **missing** on droplet.

## Operational

- Campaign is CPU/IO bounded by jsonl tail reads; safe to run off-hours.
- **Adversarial:** Full-file line counts on multi-GB logs will not scale forever — switch to indexed warehouse for production analytics.

## Performance

- Full line counts scan large files O(n); tail read capped by `max_bytes` (40MB default chunk from EOF).

## Monitoring gaps

- No continuous dashboard for `mfe_pct - pnl_pct` distribution; **0** rows had both fields in exit tail — exit quality metrics may be unset in log schema for many closes.
- **Blocked trades** tail shows reason histogram only — no automated forward-PnL without replay pipeline.

