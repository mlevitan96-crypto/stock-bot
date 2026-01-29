# Sample Intelligence Traces

**Generated:** 2026-01-27T22:56:57.947606+00:00

## 2 Entered

### Entered sample 1 — SYM1

```json
{
  "intent_id": "67557976-8f27-4d4d-a2ba-8425fe14bb8d",
  "symbol": "SYM1",
  "side_intended": "buy",
  "ts": "2026-01-27T22:56:57.941894+00:00",
  "cycle_id": 1,
  "signal_layers": {
    "alpha_signals": [
      {
        "name": "composite",
        "value": 3.5,
        "score": 3.5,
        "direction": "bullish",
        "confidence": 0.85
      }
    ],
    "flow_signals": [
      {
        "name": "flow_strength",
        "value": 1.2,
        "score": 1.2,
        "direction": "bullish",
        "confidence": 0.62
      }
    ],
    "regime_signals": [],
    "volatility_signals": [
      {
        "name": "rv_20d",
        "value": 0.25,
        "score": 0.25,
        "direction": "bullish",
        "confidence": 0.5
      }
    ],
    "dark_pool_signals": [
      {
        "name": "dark_pool_bias",
        "value": 0.3,
        "score": 0.3,
        "direction": "bullish",
        "confidence": 0.5
      }
    ]
  },
  "opposing_signals": [],
  "aggregation": {
    "raw_score": 3.5,
    "normalized_score": 3.5,
    "direction_confidence": 0.8500000000000001,
    "score_components": {
      "flow_strength": 1.2,
      "dark_pool_bias": 0.3,
      "rv_20d": 0.25,
      "composite": 3.5
    }
  },
  "gates": {
    "score_gate": {
      "passed": true,
      "reason": "ok"
    },
    "capacity_gate": {
      "passed": true,
      "reason": "ok"
    },
    "risk_gate": {
      "passed": true,
      "reason": "ok"
    },
    "directional_gate": {
      "passed": true,
      "reason": "ok"
    }
  },
  "final_decision": {
    "outcome": "entered",
    "primary_reason": "all_gates_passed",
    "secondary_reasons": []
  }
}
```

### Entered sample 2 — SYM2

```json
{
  "intent_id": "fe0595d0-c646-4e37-b4f0-6b4410771a94",
  "symbol": "SYM2",
  "side_intended": "buy",
  "ts": "2026-01-27T22:56:57.943736+00:00",
  "cycle_id": 2,
  "signal_layers": {
    "alpha_signals": [
      {
        "name": "composite",
        "value": 2.8,
        "score": 2.8,
        "direction": "bullish",
        "confidence": 0.78
      }
    ],
    "flow_signals": [
      {
        "name": "flow_strength",
        "value": -0.1,
        "score": -0.1,
        "direction": "bullish",
        "confidence": 0.5
      }
    ],
    "regime_signals": [
      {
        "name": "regime_mult",
        "value": 1.0,
        "score": 1.0,
        "direction": "bullish",
        "confidence": 0.6
      }
    ],
    "volatility_signals": [],
    "dark_pool_signals": []
  },
  "opposing_signals": [
    {
      "name": "flow_strength",
      "layer": "flow_signals",
      "reason": "negative_contribution",
      "magnitude": -0.1
    }
  ],
  "aggregation": {
    "raw_score": 4.1,
    "normalized_score": 4.1,
    "direction_confidence": 0.9099999999999999,
    "score_components": {
      "flow_strength": -0.1,
      "regime_mult": 1.0,
      "composite": 2.8
    }
  },
  "gates": {
    "score_gate": {
      "passed": true,
      "reason": "ok"
    },
    "capacity_gate": {
      "passed": true,
      "reason": "ok"
    },
    "risk_gate": {
      "passed": true,
      "reason": "ok"
    },
    "directional_gate": {
      "passed": true,
      "reason": "ok"
    }
  },
  "final_decision": {
    "outcome": "entered",
    "primary_reason": "all_gates_passed",
    "secondary_reasons": []
  }
}
```

## 2 Blocked

### Blocked sample 1 — SYM3 (score_below_min)

```json
{
  "intent_id": "1721ce06-3639-43a6-8a99-8cca77ada3c8",
  "symbol": "SYM3",
  "side_intended": "buy",
  "ts": "2026-01-27T22:56:57.945458+00:00",
  "cycle_id": 3,
  "signal_layers": {
    "alpha_signals": [
      {
        "name": "composite",
        "value": 3.5,
        "score": 3.5,
        "direction": "bullish",
        "confidence": 0.85
      }
    ],
    "flow_signals": [
      {
        "name": "flow_strength",
        "value": 1.2,
        "score": 1.2,
        "direction": "bullish",
        "confidence": 0.62
      }
    ],
    "regime_signals": [],
    "volatility_signals": [
      {
        "name": "rv_20d",
        "value": 0.25,
        "score": 0.25,
        "direction": "bullish",
        "confidence": 0.5
      }
    ],
    "dark_pool_signals": [
      {
        "name": "dark_pool_bias",
        "value": 0.3,
        "score": 0.3,
        "direction": "bullish",
        "confidence": 0.5
      }
    ]
  },
  "opposing_signals": [],
  "aggregation": {
    "raw_score": 2.1,
    "normalized_score": 2.1,
    "direction_confidence": 0.71,
    "score_components": {
      "flow_strength": 1.2,
      "dark_pool_bias": 0.3,
      "rv_20d": 0.25,
      "composite": 3.5
    }
  },
  "gates": {
    "score_gate": {
      "passed": false,
      "reason": "score_below_min"
    }
  },
  "final_decision": {
    "outcome": "blocked",
    "primary_reason": "score_below_min",
    "secondary_reasons": []
  }
}
```

### Blocked sample 2 — SYM4 (displacement_blocked)

```json
{
  "intent_id": "aa50dd10-222e-4115-982d-24cbec5ac2eb",
  "symbol": "SYM4",
  "side_intended": "buy",
  "ts": "2026-01-27T22:56:57.945931+00:00",
  "cycle_id": 4,
  "signal_layers": {
    "alpha_signals": [
      {
        "name": "composite",
        "value": 2.8,
        "score": 2.8,
        "direction": "bullish",
        "confidence": 0.78
      }
    ],
    "flow_signals": [
      {
        "name": "flow_strength",
        "value": -0.1,
        "score": -0.1,
        "direction": "bullish",
        "confidence": 0.5
      }
    ],
    "regime_signals": [
      {
        "name": "regime_mult",
        "value": 1.0,
        "score": 1.0,
        "direction": "bullish",
        "confidence": 0.6
      }
    ],
    "volatility_signals": [],
    "dark_pool_signals": []
  },
  "opposing_signals": [
    {
      "name": "flow_strength",
      "layer": "flow_signals",
      "reason": "negative_contribution",
      "magnitude": -0.1
    }
  ],
  "aggregation": {
    "raw_score": 3.8,
    "normalized_score": 3.8,
    "direction_confidence": 0.88,
    "score_components": {
      "flow_strength": -0.1,
      "regime_mult": 1.0,
      "composite": 2.8
    }
  },
  "gates": {
    "score_gate": {
      "passed": true,
      "reason": "ok"
    },
    "capacity_gate": {
      "passed": true,
      "reason": "ok"
    },
    "displacement_gate": {
      "evaluated": true,
      "passed": false,
      "reason": "displacement_blocked",
      "incumbent_symbol": "OTHER",
      "challenger_delta": 0.5,
      "min_hold_remaining": null
    }
  },
  "final_decision": {
    "outcome": "blocked",
    "primary_reason": "displacement_blocked",
    "secondary_reasons": []
  }
}
```
