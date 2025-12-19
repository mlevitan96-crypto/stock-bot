# Composite Close Reason Implementation

## Summary
Fixed missing fields in executive summary and implemented composite close reasons that combine multiple exit signals (similar to how entry uses composite signals).

## Changes Made

### 1. Created `build_composite_close_reason()` Function
- **Location**: `main.py` (after `get_exit_urgency`)
- **Purpose**: Combines multiple exit signals into a single composite reason string
- **Format**: `"signal1(value1)+signal2(value2)+signal3"`
- **Example**: `"time_exit(72h)+signal_decay(0.65)+flow_reversal"`

### 2. Updated `evaluate_exits()` Function
- **Location**: `main.py` (AlpacaExecutor class)
- **Changes**:
  - Fetches current composite score for each symbol being evaluated
  - Detects flow reversal by comparing entry direction to current sentiment
  - Calculates signal decay (current_score / entry_score)
  - Collects all exit signals (time, trail stop, signal decay, flow reversal, drawdown, etc.)
  - Builds composite close reason before closing positions
  - Tracks exit reasons per symbol in `exit_reasons` dict

### 3. Updated All Exit Paths
- **Regime Protection**: Uses composite close reason
- **Adaptive Exit**: Uses composite close reason with contributing factors
- **Stale Position**: Uses composite close reason
- **Profit Target (Scale Out)**: Uses composite close reason
- **Time/Trail Stop**: Uses composite close reason
- **Displacement**: Uses composite close reason

### 4. Field Capture Verification
- **`hold_minutes`**: Already captured in `log_exit_attribution()` (line 1019, 1041)
- **`entry_score`**: Already captured in `log_exit_attribution()` (line 1022, 1029)
- **`close_reason`**: Now uses composite format instead of simple strings

## Exit Signal Components

The composite close reason can include:
- `time_exit(72h)` - Position held for X hours
- `trail_stop(-2.5%)` - Trailing stop triggered at X% loss
- `signal_decay(0.65)` - Entry signal decayed to 65% of original
- `flow_reversal` - Options flow reversed direction
- `profit_target(5%)` - Profit target hit at X%
- `drawdown(3.1%)` - Drawdown from high water mark
- `momentum_reversal` - Momentum reversed direction
- `regime_neg_gamma` - Regime protection triggered
- `displaced_by_SYMBOL` - Position displaced by better opportunity
- `stale_position` - Position stale with low movement

## Example Composite Close Reasons

1. **Simple**: `"time_exit(72h)"` - Just time-based exit
2. **Combined**: `"time_exit(72h)+signal_decay(0.65)"` - Time + signal decay
3. **Complex**: `"trail_stop(-2.5%)+signal_decay(0.70)+flow_reversal"` - Multiple signals
4. **Profit**: `"profit_target(5%)+signal_decay(0.80)"` - Profit target + some decay

## Benefits

1. **Better Learning**: Exit reasons now show which signals contributed to the exit decision
2. **Transparency**: You can see exactly why a position was closed
3. **Pattern Recognition**: Can identify which signal combinations lead to better exits
4. **Consistency**: Exit logic now mirrors entry logic (composite signals)

## Executive Summary

The executive summary generator (`executive_summary_generator.py`) already reads:
- `hold_minutes` from `context.hold_minutes`
- `entry_score` from `context.entry_score`
- `close_reason` from `context.close_reason`

All fields should now be populated correctly for new trades. Old trades may still show 0/unknown if they were logged before these fields were captured.

## Testing

After deployment, verify:
1. New exits show composite close reasons in logs
2. Executive summary shows populated fields for new trades
3. Close reasons show multiple signals when applicable

## Answer to Your Question

**"Is there a way for the close reason to be a combination of items like the open reason? Wouldn't that make for a better way to leave positions?"**

**YES!** This is exactly what we've implemented. Just like entry uses composite signals (flow + dark pool + insider + IV skew + etc.), exits now use composite close reasons that combine:
- Time-based signals
- Signal decay
- Flow reversal
- Trail stops
- Profit targets
- Drawdown
- Momentum reversal
- Regime protection

This makes the exit logic more sophisticated and provides better learning data for the ML system.
