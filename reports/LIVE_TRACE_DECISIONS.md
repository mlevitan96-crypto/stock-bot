# Live Trace — Decision Intelligence (Live Samples)

**Generated:** 2026-01-28T15:25:44.087510+00:00
**Window:** last 10 minutes

**trade_intent count:** 166 (entered: 0, blocked: 166)
**Missing intelligence_trace:** 0 (FAIL if > 0)

## 2 ENTERED samples

## 2 BLOCKED samples

### Blocked sample 1
- **intent_id:** ae70e68a-c88b-4f9f-874d-1f44fc6d7bad
- **symbol:** COP
- **decision_outcome:** blocked
- **signal_layers (names):** ['alpha_signals', 'flow_signals', 'regime_signals', 'dark_pool_signals']
- **gates summary:** {"capacity_gate": {"passed": true, "reason": "ok"}, "displacement_gate": {"passed": false, "reason": "displacement_no_thesis_dominance"}}
- **final_decision:** {"outcome": "blocked", "primary_reason": "displacement_blocked", "secondary_reasons": []}
- **blocked_reason_code:** displacement_blocked

Raw (redacted):
```json
{
  "ts": "2026-01-28T15:25:41.649897+00:00",
  "event_type": "trade_intent",
  "symbol": "COP",
  "side": "buy",
  "score": 5.273999999999999,
  "displacement_context": null,
  "decision_outcome": "blocked",
  "blocked_reason": "displacement_blocked",
  "intent_id": "ae70e68a-c88b-4f9f-874d-1f44fc6d7bad",
  "intelligence_trace": "(present, see above)",
  "active_signal_names": [
    "insider",
    "iv_skew",
    "smile",
    "event",
    "motif_bonus",
    "toxicity_penalty",
    "congress",
    "shorts_squeeze",
    "institutional",
    "market_tide",
    "calendar",
    "greeks_gamma",
    "ftd_pressure",
    "iv_rank",
    "oi_change",
    "squeeze_score",
    "freshness_factor",
    "flow",
    "whale",
    "etf_flow",
    "regime",
    "dark_pool"
  ],
  "opposing_signal_names": [
    "toxicity_penalty"
  ],
  "gate_summary": {
    "capacity_gate": {
      "passed": true,
      "reason": "ok"
    },
    "displacement_gate": {
      "passed": false,
      "reason": "displacement_no_thesis_dominance"
    }
  },
  "final_decision_primary_reason": "displacement_blocked",
  "blocked_reason_code": "displacement_blocked",
  "blocked_reason_details": {
    "primary_reason": "displacement_blocked",
    "gates": {
      "capacity_gate": {
        "passed": true,
        "reason": "ok"
      },
      "displacement_gate": {
        "passed": false,
        "reason": "displacement_no_thesis_dominance"
      }
    }
  }
}
```
### Blocked sample 2
- **intent_id:** 09167808-6e09-40ab-a0f1-4168bb773c67
- **symbol:** WMT
- **decision_outcome:** blocked
- **signal_layers (names):** ['alpha_signals', 'flow_signals', 'regime_signals', 'dark_pool_signals']
- **gates summary:** {"capacity_gate": {"passed": true, "reason": "ok"}, "displacement_gate": {"passed": false, "reason": "displacement_no_thesis_dominance"}}
- **final_decision:** {"outcome": "blocked", "primary_reason": "displacement_blocked", "secondary_reasons": []}
- **blocked_reason_code:** displacement_blocked

Raw (redacted):
```json
{
  "ts": "2026-01-28T15:25:44.155476+00:00",
  "event_type": "trade_intent",
  "symbol": "WMT",
  "side": "buy",
  "score": 5.262,
  "displacement_context": null,
  "decision_outcome": "blocked",
  "blocked_reason": "displacement_blocked",
  "intent_id": "09167808-6e09-40ab-a0f1-4168bb773c67",
  "intelligence_trace": "(present, see above)",
  "active_signal_names": [
    "insider",
    "iv_skew",
    "smile",
    "event",
    "motif_bonus",
    "toxicity_penalty",
    "congress",
    "shorts_squeeze",
    "institutional",
    "market_tide",
    "calendar",
    "greeks_gamma",
    "ftd_pressure",
    "iv_rank",
    "oi_change",
    "squeeze_score",
    "freshness_factor",
    "flow",
    "whale",
    "etf_flow",
    "regime",
    "dark_pool"
  ],
  "opposing_signal_names": [
    "toxicity_penalty"
  ],
  "gate_summary": {
    "capacity_gate": {
      "passed": true,
      "reason": "ok"
    },
    "displacement_gate": {
      "passed": false,
      "reason": "displacement_no_thesis_dominance"
    }
  },
  "final_decision_primary_reason": "displacement_blocked",
  "blocked_reason_code": "displacement_blocked",
  "blocked_reason_details": {
    "primary_reason": "displacement_blocked",
    "gates": {
      "capacity_gate": {
        "passed": true,
        "reason": "ok"
      },
      "displacement_gate": {
        "passed": false,
        "reason": "displacement_no_thesis_dominance"
      }
    }
  }
}
```