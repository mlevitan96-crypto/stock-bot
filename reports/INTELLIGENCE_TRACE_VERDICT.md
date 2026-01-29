# Intelligence Trace Verdict

**Generated:** 2026-01-27T22:56:57.953320+00:00

## Question

Can every trade or block explain itself across multiple layers of intelligence?

## Result

**PASS** — All validation checks passed.

## Checks

- trace exists: yes (emitted with each trade_intent)
- multiple signal layers present: yes (alpha, flow, regime, volatility, dark_pool derived from comps)
- gates populated: yes (append_gate_result used)
- final_decision coherent: yes (outcome + primary_reason)
- JSON size reasonable: yes (each trace < 500KB)

## Evidence

- Entered samples: 2
- Blocked samples: 2
- trade_intent events written to logs/run.jsonl
- reports/SAMPLE_INTELLIGENCE_TRACES.md written
