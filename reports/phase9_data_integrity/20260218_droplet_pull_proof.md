# Droplet pull proof (2026-02-18)

## git pull
```
From https://github.com/mlevitan96-crypto/stock-bot
 * branch            main       -> FETCH_HEAD
   1b1a218..9b6c638  main       -> origin/main
Updating 1b1a218..9b6c638
Fast-forward
 main.py                                            |  73 ++++++++++-
 .../phase9_data_integrity/20260218_blame_trace.md  |  26 ++++
 .../20260218_exit_quality_trace.md                 |  30 +++++
 reports/phase9_data_integrity/20260218_precheck.md |  14 ++
 scripts/run_data_integrity_trace_on_droplet.py     | 144 +++++++++++++++++++++
 5 files changed, 280 insertions(+), 7 deletions(-)
 create mode 100644 reports/phase9_data_integrity/20260218_blame_trace.md
 create mode 100644 reports/phase9_data_integrity/20260218_exit_quality_trace.md
 create mode 100644 reports/phase9_data_integrity/20260218_precheck.md
 create mode 100644 scripts/run_data_integrity_trace_on_droplet.py
```

## Commit hash after pull
9b6c638229200ebcd4fc1cc55ec73aa393b4b2a0

## grep high_water main.py (first 50)
```
2178:            high_water = (info.get("high_water") or entry_price) if entry_price else None
2179:            # Guard: when high_water unavailable or equal to entry, giveback cannot be computed
2180:            if high_water is None or (entry_price and abs(float(high_water) - float(entry_price)) < 1e-9):
2181:                log_event("data_integrity", "exit_quality_high_water_unavailable", symbol=symbol,
2182:                          high_water=high_water, entry_price=entry_price, note="giveback will be null")
2188:                high_water_price=float(high_water) if high_water else None,
3728:        self.high_water = {}
3980:                    "high_water": current_price,
3990:                self.high_water[symbol] = current_price
5549:                # Data integrity: ensure high_water available for exit_quality_metrics (giveback)
5550:                info["high_water"] = self.high_water.get(symbol, info.get("high_water") or entry_price)
5572:            if symbol in self.high_water:
5573:                del self.high_water[symbol]
5643:            "high_water": entry_price,
5661:        self.high_water[symbol] = entry_price
5905:                        "high_water": current_price,
5914:                    self.high_water[symbol] = current_price
5921:                    self.high_water.pop(symbol, None)
5983:                                    self.high_water.pop("V", None)
6205:                            "high_water": meta.get("high_water", float(getattr(pos, "current_price", 0)))
6219:                                "high_water": float(getattr(pos, "current_price", 0))
6264:            high_water_price = info.get("high_water", current_price) or current_price  # BULLETPROOF: Ensure non-zero
6295:            high_water_pct = ((high_water_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
6299:            high_water_pct = max(-1000.0, min(1000.0, high_water_pct))
6486:                "high_water_pct": high_water_pct,
6538:                        exit_signals["drawdown"] = high_water_pct - pnl_pct
6683:                info["high_water"] = max(info.get("high_water", current_price), current_price)
6684:                trail_stop = info["high_water"] - info["trail_dist"]
6686:                self.high_water[symbol] = max(self.high_water.get(symbol, current_price), current_price)
6687:                trail_stop = self.high_water[symbol] * (1 - trailing_stop_pct)
7232:                    # Data integrity: ensure high_water available for exit_quality_metrics (giveback)
7233:                    info["high_water"] = self.high_water.get(symbol, info.get("high_water") or entry_price)
7299:                self.high_water.pop(symbol, None)
8097:                        if symbol in self.executor.high_water:
8098:                            del self.executor.high_water[symbol]
```

## grep exit_quality_high_water_unavailable
```
2181:                log_event("data_integrity", "exit_quality_high_water_unavailable", symbol=symbol,
```

## import run_effectiveness_reports
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'scripts.analysis.run_effectiveness_reports'
```
