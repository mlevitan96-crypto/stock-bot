# ALPACA EXIT INTEGRITY AUDIT

Exit path taxonomy: **stop** (fixed % loss), **trail** (trailing stop hit), **profit** (target hit), **decay** (signal decay ratio), **stale** (time/stale rules), **structural** (`structural_intelligence`), **v2** (exit score v2 >= threshold + hold floor).

Suppression per mission: hold-time floor, score decay gating, P&L thresholds — mapped from `notes`, `v2_blocked_hold_floor`, decay flags, and rule fields below.

## AAPL

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0005,
  "hold_notes": [],
  "v2_exit_score": 0.054,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6319,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## AMD

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0091,
  "hold_notes": [],
  "v2_exit_score": 0.1547,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6698,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## BAC

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0043,
  "hold_notes": [],
  "v2_exit_score": 0.0502,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6464,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## C

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.007,
  "hold_notes": [],
  "v2_exit_score": 0.0471,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6823,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## COIN

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0077,
  "hold_notes": [],
  "v2_exit_score": 0.075,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.7006,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## COP

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0051,
  "hold_notes": [],
  "v2_exit_score": 0.0552,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.668,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## CVX

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0007,
  "hold_notes": [],
  "v2_exit_score": 0.0522,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.644,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## F

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0054,
  "hold_notes": [],
  "v2_exit_score": 0.0493,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6686,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## GM

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0026,
  "hold_notes": [],
  "v2_exit_score": 0.0884,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6987,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## GOOGL

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0016,
  "hold_notes": [],
  "v2_exit_score": 0.0512,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6349,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## HOOD

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0222,
  "hold_notes": [],
  "v2_exit_score": 0.11,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.681,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## INTC

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0081,
  "hold_notes": [],
  "v2_exit_score": 0.1491,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6761,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## JPM

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.002,
  "hold_notes": [],
  "v2_exit_score": 0.0497,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6512,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## MRNA

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0184,
  "hold_notes": [],
  "v2_exit_score": 0.2484,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6832,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## MS

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0046,
  "hold_notes": [],
  "v2_exit_score": 0.0477,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6808,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## MSFT

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0049,
  "hold_notes": [],
  "v2_exit_score": 0.0826,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6575,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## NIO

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0073,
  "hold_notes": [],
  "v2_exit_score": 0.0653,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6847,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## NVDA

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0026,
  "hold_notes": [],
  "v2_exit_score": 0.0532,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.658,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## PFE

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0047,
  "hold_notes": [],
  "v2_exit_score": 0.0229,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.8088,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## PLTR

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0026,
  "hold_notes": [],
  "v2_exit_score": 0.1389,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6703,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## RIVN

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0147,
  "hold_notes": [],
  "v2_exit_score": 0.0464,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6781,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## SLB

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0042,
  "hold_notes": [],
  "v2_exit_score": 0.0471,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6856,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## SOFI

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.01,
  "hold_notes": [],
  "v2_exit_score": 0.0515,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.662,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## TGT

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0044,
  "hold_notes": [],
  "v2_exit_score": 0.0527,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6625,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## TSLA

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.005,
  "hold_notes": [],
  "v2_exit_score": 0.061,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6614,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## UNH

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0022,
  "hold_notes": [],
  "v2_exit_score": 0.142,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.7041,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## WFC

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.003,
  "hold_notes": [],
  "v2_exit_score": 0.0484,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6608,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## WMT

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0022,
  "hold_notes": [],
  "v2_exit_score": 0.0486,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6639,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## XLE

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0,
  "hold_notes": [],
  "v2_exit_score": 0.0521,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6307,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## XLF

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0027,
  "hold_notes": [],
  "v2_exit_score": 0.1879,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": null,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## XLI

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": -0.0012,
  "hold_notes": [],
  "v2_exit_score": 0.0515,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6316,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## XLP

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0029,
  "hold_notes": [],
  "v2_exit_score": 0.0515,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6316,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## XOM

- **stop:** not_triggered
- **trail:** not_triggered
- **profit:** not_triggered
- **decay:** not_triggered
- **stale:** not_triggered
- **structural:** not_triggered or hold (see structural dict)
- **v2:** not_triggered (score below promotion threshold or components)

**Diagnostics (selected):**

```json
{
  "pnl_pct": 0.0013,
  "hold_notes": [],
  "v2_exit_score": 0.048,
  "rule_based_would_close": false,
  "adaptive_would_close": false,
  "decay_ratio": 0.6638,
  "decay_threshold_effective": 0.2,
  "structural": {
    "should_exit": false,
    "reason": "",
    "scale_out_pct": 0.0,
    "recommended_action": "HOLD"
  }
}
```

## Structural broken?

If any symbol shows `structural` import/runtime error above → **FAIL** for structural path.
