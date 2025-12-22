# Architecture Mapping Review

## Purpose

Comprehensive review of all mappings, labels, paths, and configurations to ensure consistency across the entire system and prevent future mismatches.

## What This Review Covers

1. **Component Name Mappings**
   - `composite_score_v3` component names → `SIGNAL_COMPONENTS` names
   - Legacy attribution.jsonl component names → `SIGNAL_COMPONENTS` names
   - Ensures all 21 components are properly mapped

2. **File Path Mappings**
   - Log files: `logs/` directory
   - State files: `state/` directory
   - Data files: `data/` directory
   - Config files: `config/` directory
   - All paths should use `config/registry.py` (no hardcoded paths)

3. **Function/Import Mappings**
   - Learning orchestrator: Only `comprehensive_learning_orchestrator_v2.py` should be used
   - All imports should reference `_v2` version
   - No references to deprecated `comprehensive_learning_orchestrator.py` (without _v2)

4. **State File Mappings**
   - All state files defined in `config/registry.py` → `StateFiles` class
   - Learning state: `state/learning_processing_state.json`
   - Signal weights: `state/signal_weights.json`
   - Position metadata: `state/position_metadata.json`

5. **Configuration Mappings**
   - All thresholds in `config/registry.py` → `Thresholds` class
   - All directories in `config/registry.py` → `Directories` class
   - All log files in `config/registry.py` → `LogFiles` class

## Running the Audit

```bash
python3 architecture_mapping_audit.py
```

This will check:
- Component name consistency
- File path consistency
- Deprecated code references
- Import consistency
- State file mappings

## Known Mappings

### Component Name Mappings

**composite_score_v3 → SIGNAL_COMPONENTS:**
- `flow` → `options_flow`
- `iv_skew` → `iv_term_skew`
- `smile` → `smile_slope`
- `whale` → `whale_persistence`
- `event` → `event_alignment`
- `regime` → `regime_modifier`
- `calendar` → `calendar_catalyst`
- All others: direct match (same name)

**Legacy attribution.jsonl → SIGNAL_COMPONENTS:**
- `flow_count` → `options_flow`
- `flow_premium` → `options_flow`
- `darkpool` → `dark_pool`
- `gamma` → `greeks_gamma`
- `net_premium` → `options_flow`
- `volatility` → `iv_term_skew`

### Learning System

**ONLY USE:**
- `comprehensive_learning_orchestrator_v2.py` - The ONLY learning orchestrator

**DEPRECATED (DO NOT USE):**
- `comprehensive_learning_orchestrator.py` (without _v2) - REMOVED
- `_learn_from_outcomes_legacy()` in main.py - REMOVED

## Maintenance

Run the architecture mapping audit:
1. **Before major deployments** - Catch mapping issues early
2. **After adding new components** - Ensure mappings are updated
3. **After refactoring** - Verify no mappings were broken
4. **Periodically** - As part of regular maintenance

## Integration with Memory Bank

The MEMORY_BANK.md has been updated to:
- Document that only `comprehensive_learning_orchestrator_v2.py` should be used
- Note that old orchestrator is DEPRECATED and should NOT be referenced
- Include component name mapping information

## Next Steps

1. Run `architecture_mapping_audit.py` regularly
2. Fix any issues it finds
3. Update mappings when adding new components
4. Keep MEMORY_BANK.md updated with any mapping changes
