# Signal Data Sources and Droplet Checklist

**Purpose:** One place to see where each scoring signal gets its data and how to ensure it is collected. No placeholders — real scores require real data.

See also: `reports/SIGNAL_INTEGRITY_REAL_SCORES_PATH.md`, `SIGNAL_SCORE_PIPELINE_AUDIT.md`.

---

## 1. Data sources (who collects what)

| Component | Data source | Collected by | Cache key / file |
|-----------|-------------|--------------|-------------------|
| **conviction, sentiment** | UW flow API | `uw_flow_daemon.py` | Per-symbol in `data/uw_flow_cache.json` |
| **dark_pool** | UW dark_pool_levels | `uw_flow_daemon.py` | `cache[symbol]["dark_pool"]` |
| **insider** | UW insider API | `uw_flow_daemon.py` | `cache[symbol]["insider"]` |
| **congress** | UW congress_recent_trades (aggregated) | `uw_flow_daemon.py` | `cache[symbol]["congress"]` |
| **institutional** | UW institutional endpoint | `uw_flow_daemon.py` | `cache[symbol]["institutional"]` |
| **calendar** | UW calendar | `uw_flow_daemon.py` | `cache[symbol]["calendar"]` |
| **greeks** | UW greeks endpoint | `uw_flow_daemon.py` | `cache[symbol]["greeks"]` |
| **oi_change** | UW OI change | `uw_flow_daemon.py` | `cache[symbol]["oi_change"]` |
| **etf_flow** | UW ETF flow | `uw_flow_daemon.py` | `cache[symbol]["etf_flow"]` |
| **iv_rank** | UW IV rank | `uw_flow_daemon.py` | `cache[symbol]["iv_rank"]` |
| **ftd_pressure / shorts** | UW FTD/shorts | `uw_flow_daemon.py` | `cache[symbol]["ftd_pressure"]` / `shorts_ftds` |
| **market_tide** | UW market-wide sentiment | `uw_flow_daemon.py` | Per-ticker or market-wide in cache |
| **iv_term_skew, smile_slope, event_alignment, toxicity, freshness** | Derived in enricher | `uw_enrichment_v2.enrich_signal()` | From cache (conviction, sentiment, dark_pool, _last_update) |
| **whale, motif_*** | TemporalMotifDetector | `uw_enrichment_v2` (motif_detector) | History of cache updates (state/uw_motifs.json) |
| **expanded_intel** | Merge of caches | `scripts/build_expanded_intel.py` | `data/uw_expanded_intel.json` (premarket + postmarket + uw_flow_cache) |

**Pipeline:** `main.py` loads `uw_flow_cache.json` → `enrich_signal(symbol, cache, regime)` → `compute_composite_score_v2(symbol, enriched, regime)` → clusters → decide_and_execute → expectancy gate → submit_entry.

---

## 2. Droplet checklist (signals working)

Run these on the droplet (or via SSH) to ensure data is collected and signals can produce real scores.

### 2.1 Daemon and cache

```bash
cd /root/stock-bot

# 1. uw_flow_cache present and recent (< 15 min)
ls -la data/uw_flow_cache.json
stat -c %Y data/uw_flow_cache.json   # compare to date +%s

# 2. Daemon running (if using systemd)
systemctl status uw_flow_daemon   # or whatever the service name is

# 3. Cache has symbols and key fields
python3 -c "
import json
from pathlib import Path
p = Path('data/uw_flow_cache.json')
if not p.exists():
    print('MISSING: data/uw_flow_cache.json')
    exit(1)
c = json.load(p)
syms = [k for k in c if isinstance(c.get(k), dict) and not k.startswith('_')]
print(f'Symbols: {len(syms)}')
for s in syms[:5]:
    d = c[s]
    print(f'  {s}: conviction={d.get(\"conviction\")}, sentiment={d.get(\"sentiment\")}, dark_pool={bool(d.get(\"dark_pool\"))}')
"
```

### 2.2 Intel producers

```bash
# Run intel producers so expanded_intel is merged from cache
python3 scripts/build_daily_universe.py || true
python3 scripts/run_premarket_intel.py || true
python3 scripts/run_postmarket_intel.py || true
python3 scripts/build_expanded_intel.py || true

# Expanded intel exists
ls -la data/uw_expanded_intel.json
```

### 2.3 Signal health (after a run)

```bash
# After main.py has run (paper or live), signal health log should exist
wc -l logs/signal_health.jsonl
tail -1 logs/signal_health.jsonl | python3 -m json.tool | head -40
```

Use `logs/signal_health.jsonl` to see which components have `has_data: true` vs `false` per symbol.

### 2.4 Score telemetry

```bash
# Optional: check state/score_telemetry.json for defaulted_conviction, missing_intel
cat state/score_telemetry.json | python3 -m json.tool | head -50
```

---

## 3. No placeholders (contract)

- **Conviction missing:** Composite uses `0.0`; note `conviction_missing` in composite notes; telemetry can record.
- **Greeks missing:** Composite uses `0.0`; note `greeks_missing` in composite notes.
- **Other components:** When data is missing, component returns `0.0` (no neutral fake default). Score is only raised when real data is present.

---

## 4. Plugins and tooling

- **Schema / config:** Use `config/tuning` and attribution docs (e.g. compound-engineering-context or repo docs) when adding or changing signal fields so names stay consistent.
- **Multi-model:** Prosecutor/defender/board can read `logs/signal_health.jsonl` and `state/score_telemetry.json` for evidence on whether signals are working.

---

## 5. Quick reference: key files

| File | Purpose |
|------|--------|
| `data/uw_flow_cache.json` | Primary cache written by uw_flow_daemon |
| `data/uw_expanded_intel.json` | Merge of premarket + postmarket + cache (build_expanded_intel) |
| `logs/signal_health.jsonl` | Per-symbol per-component has_data and contribution (append each score) |
| `state/score_telemetry.json` | Aggregated score telemetry (defaulted_conviction, missing_intel, etc.) |
| `uw_flow_daemon.py` | Only component that should call UW API; writes cache |
| `uw_enrichment_v2.py` | enrich_signal(): derives iv_skew, smile, toxicity, freshness, motifs from cache |
| `uw_composite_v2.py` | compute_composite_score_v2(): all components, no fake defaults |
