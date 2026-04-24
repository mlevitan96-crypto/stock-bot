# PROFIT_V2_FILESYSTEM_RECOVERY_INVENTORY

Scope: droplet `find` under `logs/`, `reports/`, `artifacts/`, `/tmp` filtered by UW/SPI/bars-related names (`phase1.uw_names` in `_PROFIT_V2_DROPLET_RAW.json`). Below: **path, size/mtime notes, schema sample**.

## High-signal recoverable artifacts

| Path | Evidence | Sample schema (first record shape) |
|------|----------|-------------------------------------|
| `logs/score_snapshot.jsonl` | **2000** lines; mtime per tail capture | JSON: `ts`, `ts_iso`, `symbol`, `composite_score`, `gates`, `signal_group_scores` with nested **`components`** (UW-related floats: `flow`, `dark_pool`, `whale`, …) — see raw `phase1.score_snap_wc` |
| `logs/signal_context.jsonl` | **0 bytes** | N/A (empty) |
| `logs/uw_raw_payloads.jsonl` | Listed in find | Raw UW payloads (recovery for API-shaped data) |
| `logs/uw_attribution.jsonl` | Listed | Attribution stream |
| `logs/uw_cache.jsonl` | Listed | Cache / mirror log |
| `logs/scoring_flow.jsonl` | Listed | Scoring diagnostics |
| `state/uw_cache/` | **~43 MB** total; many shard `*.json` files (`ls` in raw `phase1.uw_cache`) | Per-shard JSON blobs keyed by content hash filenames |
| `reports/ALPACA_SIGNAL_CONTRIBUTION_UW_AUDIT_*.md` | Multiple dated files (see `uw_names` list in raw JSON) | Markdown audit tables |
| `reports/daily/2026-04-01/evidence/ALPACA_SPI_ORTHOGONALITY_ANALYSIS.md` | SPI analysis output | Markdown |

## Bars / OHLC

| Path | Evidence |
|------|----------|
| `artifacts/market_data/alpaca_bars.jsonl` | **Created in V2 mission:** 49 lines, ~8.2 MB; each line `{"data":{"bars":{"SYM":[{t,o,h,l,c,v},...]}}}` |
| `data/bars_cache/` | `find` in `phase1.bars_stat` showed no files in sample head (may be empty on this host pre-fetch) |

## Noise / non-repo paths in find output

- `/tmp/dashproof/node_modules/...` entries matched substring `flow` in **third-party** paths — **excluded** from recovery recommendations.

## Join keys (for Phase 3)

- **score_snapshot:** `symbol`, `ts` / `ts_iso`  
- **exit_attribution:** `symbol`, `entry_ts` / `exit_ts`, `canonical_trade_id` (when present)  
- **Campaign match rate:** **63** paired exits to nearest prior snapshot (`PROFIT_V2_SIGNAL_UW_UPLIFT.json`)
