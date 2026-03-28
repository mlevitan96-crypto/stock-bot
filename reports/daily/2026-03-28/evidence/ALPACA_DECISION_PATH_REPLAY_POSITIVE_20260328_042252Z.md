# Alpaca dry decision replay (positive)

Production path: `telemetry.decision_intelligence_trace` (build_initial_trace + gates + set_final_decision) then `emit_entry_decision_made` with test `write_run` → `logs/test_run.jsonl` only.

## Emitted row (summary)

```json
{
  "event_type": "entry_decision_made",
  "entry_intent_synthetic": false,
  "entry_intent_source": "live_runtime",
  "entry_intent_status": "OK",
  "entry_score_total": 2.5,
  "signal_trace": {
    "policy_anchor": "alpaca_paper_truth_test",
    "intelligence_trace": {
      "intent_id": "4894f54f-8836-4408-94d3-689c068aca47",
      "symbol": "TESTPATH",
      "side_intended": "buy",
      "ts": "2026-03-28T04:22:52.149195+00:00",
      "cycle_id": null,
      "signal_layers": {
        "alpha_signals": [
          {
            "name": "momentum",
            "value": 1.1,
            "score": 1.1,
            "direction": "bullish",
            "confidence": 0.61
          }
        ],
        "flow_signals": [
          {
            "name": "whale_flow_strength",
            "value": 0.4,
            "score": 0.4,
            "direction": "bullish",
            "confidence": 0.5
          }
        ],
        "regime_signals": [],
        "volatility_signals": [],
        "dark_pool_signals": []
      },
      "opposing_signals": [],
      "aggregation": {
        "raw_score": 2.5,
        "normalized_score": 2.5,
        "direction_confidence": 0.75,
        "score_components": {
          "momentum": 1.1,
          "whale_flow_strength": 0.4
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
        "momentum_gate": {
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
  },
  "entry_score_components": {
    "momentum": 0.7,
    "whale_flow_strength": 0.3
  }
}
```
