# Resilience Validation Suite

## Overview

This validation suite adversarially tests the self-healing architecture under controlled failure conditions. It validates the system's ability to **DETECT → CLASSIFY → RESPOND → RECOVER OR HALT SAFELY** across all risk areas.

## Safety

- **NEVER runs automatically** - All tests are opt-in
- **NEVER modifies .env or secrets**
- **NEVER modifies production logic**
- **NEVER modifies wallet/P&L/risk math**
- All validation code is isolated under `/root/stock-bot/validation/`
- Chaos hooks only activate when explicitly triggered

## Usage

### Run All Scenarios
```bash
cd /root/stock-bot
python3 validation/validation_runner.py --scenario all
```

### Run Specific Scenarios
```bash
# Single scenario
python3 validation/validation_runner.py --scenario state_persistence

# Multiple scenarios
python3 validation/validation_runner.py --scenario state_persistence,partial_failure
```

### Available Scenarios

1. **state_persistence** - Tests state persistence and reconciliation (Risk #6)
2. **partial_failure** - Tests partial service failure detection (Risk #9)
3. **api_drift** - Tests API contract validation (Risk #11)
4. **chaos_modes** - Tests chaos testing hooks (Risk #12)
5. **trade_guard** - Tests trade sanity checks (Risk #15)
6. **scoring_pipeline_fixes** - Tests scoring pipeline fixes (Priority 1-4 from audit)

## Test Scenarios

### State Persistence (Risk #6)
- **Corrupted state file recovery**: Tests self-healing when state file is corrupted
- **State reconciliation**: Tests reconciliation with Alpaca on startup
- **Atomic write integrity**: Tests that state writes are atomic

### Partial Service Failure (Risk #9)
- **Kill trading-bot detection**: Tests that killing trading-bot is detected
- **Health registry tracking**: Tests that all services are tracked
- **Health aggregation**: Tests that overall health is correctly computed

### API Drift (Risk #11)
- **Missing required field detection**: Tests that missing fields are detected
- **Extra fields tolerance**: Tests that extra fields don't cause failures
- **Type mismatch detection**: Tests that type mismatches are detected
- **Compatibility check**: Tests that compatibility checks run on startup

### Chaos Modes (Risk #12)
- **Chaos mode environment variable**: Tests that chaos mode is controlled by env var
- **State corruption chaos mode**: Tests state corruption simulation
- **Invalid credentials chaos mode**: Tests invalid credentials simulation

### Trade Guard (Risk #15)
- **Oversized position rejection**: Tests that oversized positions are rejected
- **Cooldown enforcement**: Tests that cooldown is enforced
- **Price sanity check**: Tests that unrealistic prices are rejected
- **Direction flip protection**: Tests that direction flips are blocked
- **Excessive notional rejection**: Tests that excessive notional is rejected

### Scoring Pipeline Fixes (System Hardening)
- **Freshness decay configuration**: Tests that decay_min = 180 (not 45)
- **Flow conviction default**: Tests that conviction defaults to 0.5 (not 0.0)
- **Core features computed**: Tests that iv_skew, smile_slope, event_align are always present
- **Expanded intel defaults**: Tests that missing intel provides neutral defaults (not 0.0)
- **Telemetry recording**: Tests that telemetry records scores correctly
- **Dashboard endpoints**: Tests that dashboard endpoints return valid JSON

## Reports

Reports are generated in `validation/report/validation_report_TIMESTAMP.md`

Each report includes:
- Summary with pass/fail counts
- Per-scenario results
- State snapshots (health.json, trading_state.json)
- Log excerpts
- Recommendations for fixes

## Example Report Structure

```markdown
# Resilience Test Report

**Generated:** 2026-01-10T12:00:00Z
**Duration:** 45.2 seconds
**Total Tests:** 15
**Passed:** 14
**Failed:** 1

## Summary
- **Total Scenarios:** 5
- **Pass Rate:** 93.3%

## Scenario Results

### ✅ state_persistence
**Status:** PASS
**Test Results:**
- ✅ Corrupted state file recovery: PASS
- ✅ State reconciliation: PASS
- ✅ Atomic write integrity: PASS

### ❌ partial_failure
**Status:** FAIL
**Test Results:**
- ✅ Kill trading-bot detection: PASS
- ✅ Health registry tracking: PASS
- ❌ Health aggregation: FAIL
  - Overall status should be FAILED when critical service is FAILED

## State Snapshots
[Health and state snapshots at key points]

## Log Excerpts
[Relevant log excerpts]

## Recommendations
- **partial_failure/Health aggregation**: Fix aggregation logic
```

## Requirements

- Python 3.7+
- Access to `/root/stock-bot/` directory
- Read access to `state/` and `logs/` directories
- Ability to read journalctl logs (may require sudo)

## Notes

- Some tests may be skipped if required services are not running
- Tests that require Alpaca API credentials may be skipped if credentials are not available
- Tests are designed to be non-destructive, but some may temporarily affect system state
- All tests restore system state after completion where possible

## Troubleshooting

### "Scenario file not found"
- Ensure you're running from `/root/stock-bot/`
- Check that `validation/scenarios/` directory exists

### "Permission denied"
- Some tests require read access to system logs
- May need to run with appropriate permissions

### "Module not found"
- Ensure you're running from the correct directory
- Check that required modules (state_manager, trade_guard, etc.) are available
