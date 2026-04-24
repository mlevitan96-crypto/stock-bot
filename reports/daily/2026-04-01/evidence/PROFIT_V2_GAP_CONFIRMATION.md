# PROFIT_V2_GAP_CONFIRMATION

Sources: droplet Phase 0/1 capture (`_PROFIT_V2_DROPLET_RAW.json`), `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md` (campaign), and post-mission artifact checks.

## 1) UW granularity (`signal_context` or equivalent)

| Sink | Droplet fact | Campaign inventory |
|------|----------------|-------------------|
| `logs/signal_context.jsonl` | **0 bytes**, **0 lines** (`stat` + `wc` in raw `phase1.sig_ctx_stat`) | 0 rows loaded |
| **Equivalent recovery data** | `logs/score_snapshot.jsonl` **2000** lines; sample row includes full **`components`** (`flow`, `dark_pool`, `whale`, …) | 2000 rows; **63** exit↔snapshot matches in uplift run |

**Conclusion:** Canonical **`signal_context` is empty** (no per-trade rows). **UW subfield granularity is recoverable** from `score_snapshot` / UW audit logs / `state/uw_cache/`, not from `signal_context.jsonl`.

## 2) Bars for exit timing replay

| Path | Before V2 fetch | After V2 fetch (evidence) |
|------|-------------------|---------------------------|
| `artifacts/market_data/alpaca_bars.jsonl` | **Missing** (`stat: cannot statx` in raw `phase1.bars_stat`) | **Present:** 49 JSONL lines (one per symbol), **~8.2 MB** total (`wc -l` + `ls -la` on droplet) |

**Conclusion:** Gap **confirmed** pre-mission; **closed** by read-only Data API pull (no engine changes).

## 3) SPI path artifacts

| Check | Result |
|-------|--------|
| Glob `reports/**/ALPACA_SPI*.md` | Hit: `reports/daily/2026-04-01/evidence/ALPACA_SPI_ORTHOGONALITY_ANALYSIS.md` (raw `phase1.spi_glob`) |
| Campaign `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md` “SPI artifacts” table | Empty in file body (no extra SPI paths listed beyond campaign’s own outputs) |

**Conclusion:** **Dedicated SPI markdown exists** in daily evidence. **“SPI path”** as a separate long-running artifact stream is **not** evidenced beyond analysis reports; SPI work remains **report-bound**, not a second JSONL sink.

## Reproduced “known gaps” (pre-fix)

1. Empty `signal_context` while exits and scores exist elsewhere.  
2. Missing unified bars file for `replay_exit_timing_counterfactuals`-style joins.  
3. SPI primarily as **analysis outputs**, not a dense per-trade join file.
