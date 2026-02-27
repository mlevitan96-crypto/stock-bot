# Top 50 blocked examples

Each section: raw signals, features, component scores + weights, final score vs threshold, gate verdicts (with measured values), order intent (if any).

## Example 1: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 2.942,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.69
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "rea
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 2: META (score_final=1.039)

### Signal raw
```json
{
  "symbol": "META",
  "score": 3.108,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    612.5
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.011,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.724
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 3: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 2.83,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.651
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "rea
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 4: META (score_final=1.039)

### Signal raw
```json
{
  "symbol": "META",
  "score": 3.024,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    612.5
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.011,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.695
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 5: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 2.822,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.648
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "re
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 6: META (score_final=1.039)

### Signal raw
```json
{
  "symbol": "META",
  "score": 2.99,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    612.5
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.011,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.684
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "re
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 7: META (score_final=1.039)

### Signal raw
```json
{
  "symbol": "META",
  "score": 2.888,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    612.5
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.011,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.649
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 8: META (score_final=1.039)

### Signal raw
```json
{
  "symbol": "META",
  "score": 2.904,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    612.5
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.011,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.654
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 9: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 4.071,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    14.0
  ],
  "components": {
    "flow": 1.905,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.027,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.145,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.046,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.121,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.97
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "re
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 10: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 4.083,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    14.0
  ],
  "components": {
    "flow": 1.905,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.027,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.145,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.046,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.121,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.975
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 11: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.411,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.971
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 12: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.404,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.967
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 13: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.331,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.929
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 14: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.321,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.924
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 15: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.249,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.885
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 16: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.24,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.881
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smi
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 17: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.173,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.845
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 18: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.165,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.841
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 19: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.101,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.807
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 20: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.093,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.463,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.01,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.034,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.803
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "sm
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 21: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 3.414,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 1.987,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.03,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.065,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.983
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 22: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 3.282,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 1.987,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.03,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.065,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.043,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.932
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "r
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 23: QQQ (score_final=1.039)

### Signal raw
```json
{
  "symbol": "QQQ",
  "score": 4.003,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.989
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 24: SPY (score_final=1.039)

### Signal raw
```json
{
  "symbol": "SPY",
  "score": 3.941,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.121,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.986
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile":
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 25: GS (score_final=1.039)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 4.132,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.988
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 26: QQQ (score_final=1.039)

### Signal raw
```json
{
  "symbol": "QQQ",
  "score": 3.949,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.971
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 27: SPY (score_final=1.039)

### Signal raw
```json
{
  "symbol": "SPY",
  "score": 3.887,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.121,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.968
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile":
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 28: BLK (score_final=1.039)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 2.953,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.597,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.015,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.045,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.994
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 29: GS (score_final=1.039)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 4.064,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.964
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 30: QQQ (score_final=1.039)

### Signal raw
```json
{
  "symbol": "QQQ",
  "score": 3.883,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.949
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 31: SPY (score_final=1.039)

### Signal raw
```json
{
  "symbol": "SPY",
  "score": 3.817,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.121,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.945
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile":
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 32: BLK (score_final=1.039)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 2.907,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.597,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.015,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.045,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.972
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 33: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.381,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.36,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.006,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.026,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.992
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 34: GS (score_final=1.039)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 4.004,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.944
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 35: QQQ (score_final=1.039)

### Signal raw
```json
{
  "symbol": "QQQ",
  "score": 3.819,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.927
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 36: SPY (score_final=1.039)

### Signal raw
```json
{
  "symbol": "SPY",
  "score": 3.754,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.121,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.924
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile":
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 37: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.341,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.36,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.006,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.026,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.97
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile"
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 38: BLK (score_final=1.039)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 2.869,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.597,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.015,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.045,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.953
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 39: GS (score_final=1.039)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 3.922,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.916
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 40: QQQ (score_final=1.039)

### Signal raw
```json
{
  "symbol": "QQQ",
  "score": 3.743,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.902
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile": 
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 41: SPY (score_final=1.039)

### Signal raw
```json
{
  "symbol": "SPY",
  "score": 3.675,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.038,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.121,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.898
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile":
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 42: COST (score_final=1.039)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 3.54,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 2.077,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.033,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.086,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.983
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 43: LCID (score_final=1.039)

### Signal raw
```json
{
  "symbol": "LCID",
  "score": 3.297,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.36,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.006,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.026,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.946
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 44: BLK (score_final=1.039)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 2.811,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [],
  "components": {
    "flow": 1.597,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.015,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.048,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.045,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.0,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.024,
    "freshness_factor": 0.925
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
    "smile
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 1.039 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 1.039, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 1.039}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 1.039, 'candidate_score': 1.039}

### Order intent
None

## Example 45: GS (score_final=0.567)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 4.218,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    900.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.919
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
  
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None

## Example 46: BLK (score_final=0.567)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 4.036,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    1100.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.945
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None

## Example 47: GS (score_final=0.567)

### Signal raw
```json
{
  "symbol": "GS",
  "score": 4.202,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    900.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.06,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.915
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
  
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None

## Example 48: BLK (score_final=0.567)

### Signal raw
```json
{
  "symbol": "BLK",
  "score": 4.008,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    1100.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.937
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None

## Example 49: COST (score_final=0.567)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 4.066,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.974
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None

## Example 50: COST (score_final=0.567)

### Signal raw
```json
{
  "symbol": "COST",
  "score": 4.026,
  "version": "V2",
  "adaptive_weights_active": true,
  "gamma_resistance_levels": [
    960.0
  ],
  "components": {
    "flow": 2.4,
    "dark_pool": 0.157,
    "insider": 0.076,
    "iv_skew": 0.071,
    "smile": 0.004,
    "whale": 0.0,
    "event": 0.206,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.163,
    "regime": 0.007,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 0.2,
    "calendar": 0.0,
    "greeks_gamma": 0.048,
    "ftd_pressure": 0.036,
    "iv_rank": 0.018,
    "oi_change": 0.042,
    "etf_flow": 0.036,
    "squeeze_score": 0.06,
    "freshness_factor": 0.961
  },
  "component_sources": {
    "flow": "real",
    "dark_pool": "missing",
    "insider": "real",
    "iv_skew": "real",
```

### Features
```json
{}
```

### Score components + weights
```json
{}
```

### Final score vs threshold: 0.567 | thresholds: {'expectancy_floor': 2.5, 'min_exec_score': 2.5}

### Gate verdicts
- **composite_gate**: pass=True, reason=passed, params={'threshold': 2.5}, measured={'score': 0.567, 'composite_pre_norm': None, 'composite_post_norm': None}
- **expectancy_gate**: pass=False, reason=score_floor_breach, params={'expectancy_floor': 2.5}, measured={'composite_score': 0.567}
- **block_reason**: pass=False, reason=expectancy_blocked:score_floor_breach, params={}, measured={'score': 0.567, 'candidate_score': 0.567}

### Order intent
None
