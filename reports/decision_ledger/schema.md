# Decision Ledger — Canonical Event Schema



Single canonical event structure used everywhere. No ambiguity.



## DecisionEvent (minimum fields)



| Field | Type | Description |

|-------|------|-------------|

| `run_id` | string | Unique run/session identifier |

| `ts` | number (Unix) | Event timestamp |

| `ts_iso` | string | ISO8601 timestamp |

| `symbol` | string | Ticker |

| `venue` | string | Trading venue (e.g. alpaca) |

| `timeframe` | string | e.g. 1m, 5m |

| `mode` | string | One of: `live` / `shadow` / `replay` / `observe` |

| `signal_raw` | dict | All raw signal outputs |

| `features` | dict | All feature values used |

| `score_components` | dict | `{ name: { value, weight, contribution } }` |

| `score_final` | float | Final composite score |

| `thresholds` | dict | All thresholds used at runtime (e.g. min_exec_score, entry_ev_floor, composite_threshold) |

| `gates` | list | Each element: `{ gate_name, pass, reason, params, measured }` |

| `candidate_status` | string | One of: `GENERATED` / `BLOCKED` / `ORDERED` / `SKIPPED` |

| `order_intent` | dict \| null | If built: qty, notional, price, tif, etc. |

| `order_result` | dict \| null | If attempted: submitted/accepted/rejected + error |



## Gate verdict (element of `gates`)



| Field | Type | Description |

|-------|------|-------------|

| `gate_name` | string | e.g. regime_gate, concentration_gate, composite_gate, expectancy_gate, score_gate, cooldown_gate |

| `pass` | bool | True if candidate passed this gate |

| `reason` | string | Short reason code or description |

| `params` | dict | Gate parameters (e.g. threshold value, min_required) |

| `measured` | dict | Measured values at evaluation (e.g. score, expectancy, net_delta_pct) |



## Candidate status semantics



- **GENERATED**: Candidate was produced by the pipeline but not yet evaluated through all gates (or ledger emitted before full evaluation).

- **BLOCKED**: Candidate was blocked by at least one gate; see `gates` for the first failing gate and reason.

- **ORDERED**: Order intent was built and submission was attempted (see order_result).

- **SKIPPED**: Candidate was explicitly skipped (e.g. observe-only, or skip reason logged).



## File format



- **decision_ledger.jsonl**: One JSON object per line (JSONL). One line per candidate evaluation. Atomic append; safe under crashes.

