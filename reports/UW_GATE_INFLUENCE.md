# UW Gate Influence (Score → Decision)

**Generated:** 2026-01-28T16:44:56.247012+00:00

Gates (score_gate, risk_gate, capacity_gate, displacement_gate, directional_gate) use composite score and capacity/risk state.
UW data influences **composite score**; gates do not reference UW endpoints by name.
**Causal chain:** UW → score_components → composite score → score_gate (min threshold) and capacity/risk/displacement/directional gates.

- **F** (blocked): gates=['capacity_gate', 'displacement_gate']
- **XOM** (blocked): gates=['capacity_gate', 'displacement_gate']
- **MRNA** (blocked): gates=['capacity_gate', 'displacement_gate']
- **TGT** (blocked): gates=['capacity_gate', 'displacement_gate']
- **HD** (blocked): gates=['capacity_gate', 'displacement_gate']