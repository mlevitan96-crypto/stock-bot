# ALPACA LIQUIDATION WAVE 3

- Orchestrator UTC: `2026-03-30T21:10:13.366038+00:00`
- Subprocess exit code: **3**
- Controlled liquidation evidence: `ALPACA_FULL_LIQUIDATION_ORCH_WAVE3_20260330_205502Z.md`

## Subprocess stdout (full)

```text
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
{
  "evidence_md": "/root/stock-bot/reports/daily/2026-03-30/evidence/ALPACA_FULL_LIQUIDATION_ORCH_WAVE3_20260330_205502Z.md",
  "positions_before": 33,
  "executed": true,
  "positions_after": 33,
  "flat": false
}
```

## Subprocess stderr (full)

```text
(empty)
```

- positions_before: **33**
- positions_after: **33**
- open_orders_after: **33**

## Symbols still open after wave

```json
[
  "AAPL",
  "AMD",
  "BAC",
  "C",
  "COIN",
  "COP",
  "CVX",
  "F",
  "GM",
  "GOOGL",
  "HOOD",
  "INTC",
  "JPM",
  "MRNA",
  "MS",
  "MSFT",
  "NIO",
  "NVDA",
  "PFE",
  "PLTR",
  "RIVN",
  "SLB",
  "SOFI",
  "TGT",
  "TSLA",
  "UNH",
  "WFC",
  "WMT",
  "XLE",
  "XLF",
  "XLI",
  "XLP",
  "XOM"
]
```

## close_position results (excerpt from liquidation evidence)

```json
[
  {
    "symbol": "AAPL",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "AMD",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "BAC",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "C",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "COIN",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "COP",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "CVX",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "F",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "GM",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "GOOGL",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "HOOD",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "INTC",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "JPM",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "MRNA",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "MS",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "MSFT",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "NIO",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "NVDA",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "PFE",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "PLTR",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "RIVN",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "SLB",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "SOFI",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "TGT",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "TSLA",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "UNH",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "WFC",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "WMT",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "XLE",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "XLF",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "XLI",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "XLP",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "XOM",
    "wave": "wave1",
    "ok": true,
    "error": null
  },
  {
    "symbol": "AAPL",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "AMD",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "BAC",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 4, available: 0)"
  },
  {
    "symbol": "C",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "COIN",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "COP",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "CVX",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "F",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 35, available: 0)"
  },
  {
    "symbol": "GM",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "GOOGL",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "HOOD",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 6, available: 0)"
  },
  {
    "symbol": "INTC",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 4, available: 0)"
  },
  {
    "symbol": "JPM",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "MRNA",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 8, available: 0)"
  },
  {
    "symbol": "MS",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "MSFT",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "NIO",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 72, available: 0)"
  },
  {
    "symbol": "NVDA",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "PFE",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 12, available: 0)"
  },
  {
    "symbol": "PLTR",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "RIVN",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 27, available: 0)"
  },
  {
    "symbol": "SLB",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 4, available: 0)"
  },
  {
    "symbol": "SOFI",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 26, available: 0)"
  },
  {
    "symbol": "TGT",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 3, available: 0)"
  },
  {
    "symbol": "TSLA",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "UNH",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "WFC",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 2, available: 0)"
  },
  {
    "symbol": "WMT",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "XLE",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 6, available: 0)"
  },
  {
    "symbol": "XLF",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 12, available: 0)"
  },
  {
    "symbol": "XLI",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  },
  {
    "symbol": "XLP",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 3, available: 0)"
  },
  {
    "symbol": "XOM",
    "wave": "wave2",
    "ok": false,
    "error": "insufficient qty available for order (requested: 1, available: 0)"
  }
]
```

