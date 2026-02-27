# UW missing-input penalty experiment summary

## Config
- UW_MISSING_INPUT_MODE=penalize (paper-only)
- UW_MISSING_INPUT_PENALTY=0.75

## Counts
- Penalty events (missing_inputs_penalized): **0**
- Reached expectancy gate (score passed to gate): **0**
- Expectancy gate pass (score_after >= 2.5): **0**
- Candidates previously rejected (no UW score_after) that now reach gate: **0**

## Post-adjustment score distribution (penalty events only)
- No penalty events (no post-adjustment scores).

## Paper trades
- From score_snapshot (expectancy_gate_pass=True): **0**
- From attribution (closed/executed): **2022**

## Comparison to historical executed trades
- No historical executed scores in attribution.

## Verdict

No penalty events were recorded. Either UW_MISSING_INPUT_MODE was not 'penalize', or no candidates had missing UW inputs (use_quality was None). On droplet, rejections may be due to low quality (e.g. 0.0) rather than missing data; those are unchanged.
