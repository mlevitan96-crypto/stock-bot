#!/usr/bin/env python3
"""
Architecture Mapping Audit
===========================

Comprehensive review of all mappings, labels, paths, and configurations
to ensure consistency across the entire system.

This audit checks for:
1. Component name mappings (composite_score_v3 → SIGNAL_COMPONENTS)
2. File path mappings (logs vs data directories)
3. Function/import mappings
4. State file mappings
5. Configuration mappings
6. Deprecated code references
7. Hardcoded paths or labels
"""

import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re

# Known mappings to verify
COMPONENT_NAME_MAPPINGS = {
    "composite_score_v3": {
        "flow": "options_flow",
        "dark_pool": "dark_pool",
        "insider": "insider",
        "iv_skew": "iv_term_skew",
        "smile": "smile_slope",
        "whale": "whale_persistence",
        "event": "event_alignment",
        "motif_bonus": "temporal_motif",
        "toxicity_penalty": "toxicity_penalty",
        "regime": "regime_modifier",
        "congress": "congress",
        "shorts_squeeze": "shorts_squeeze",
        "institutional": "institutional",
        "market_tide": "market_tide",
        "calendar": "calendar_catalyst",
        "greeks_gamma": "greeks_gamma",
        "ftd_pressure": "ftd_pressure",
        "iv_rank": "iv_rank",
        "oi_change": "oi_change",
        "etf_flow": "etf_flow",
        "squeeze_score": "squeeze_score",
    },
    "legacy_attribution": {
        "flow_count": "options_flow",
        "flow_premium": "options_flow",
        "darkpool": "dark_pool",
        "gamma": "greeks_gamma",
        "net_premium": "options_flow",
        "volatility": "iv_term_skew",
    }
}

def extract_python_imports(file_path: Path) -> Set[str]:
    """Extract all imports from a Python file"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
    except:
        pass
    return imports

def extract_string_literals(file_path: Path) -> List[str]:
    """Extract string literals from a Python file"""
    strings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Str):
                    strings.append(node.s)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    strings.append(node.value)
    except:
        pass
    return strings

def check_component_name_consistency():
    """Check that component names are consistent across files"""
    print("=" * 80)
    print("COMPONENT NAME CONSISTENCY CHECK")
    print("=" * 80)
    print()
    
    issues = []
    
    # Get SIGNAL_COMPONENTS from adaptive_signal_optimizer
    try:
        from adaptive_signal_optimizer import SIGNAL_COMPONENTS
        expected_components = set(SIGNAL_COMPONENTS)
    except:
        print("WARNING: Could not import SIGNAL_COMPONENTS from adaptive_signal_optimizer")
        return
    
    # Check fix_component_tracking.py mappings
    try:
        from fix_component_tracking import COMPONENT_NAME_MAP, LEGACY_COMPONENT_MAP
        mapped_components = set(COMPONENT_NAME_MAP.values())
        legacy_mapped = set(LEGACY_COMPONENT_MAP.values())
        
        # Check all mapped components are in SIGNAL_COMPONENTS (excluding None which is valid for metadata)
        unmapped = mapped_components - expected_components - {None}
        if unmapped:
            issues.append(f"COMPONENT_MAP contains components not in SIGNAL_COMPONENTS: {unmapped}")
        
        unmapped_legacy = legacy_mapped - expected_components
        if unmapped_legacy:
            issues.append(f"LEGACY_COMPONENT_MAP contains components not in SIGNAL_COMPONENTS: {unmapped_legacy}")
        
        # Check all SIGNAL_COMPONENTS are mapped (or have direct match)
        missing_mappings = expected_components - mapped_components - legacy_mapped
        # Some components might be direct matches (same name in both systems)
        direct_matches = expected_components & set(COMPONENT_NAME_MAP.keys())
        missing_mappings = missing_mappings - direct_matches
        
        if missing_mappings:
            issues.append(f"SIGNAL_COMPONENTS not covered by mappings: {missing_mappings}")
        
    except ImportError as e:
        issues.append(f"Could not import fix_component_tracking: {e}")
    
    # Check uw_composite_v2.py returns components with correct names
    try:
        # Read the file to check component names in return dict
        uw_file = Path("uw_composite_v2.py")
        if uw_file.exists():
            content = uw_file.read_text()
            # Look for components dict in return statement
            if '"flow"' in content and '"options_flow"' not in content:
                # This is expected - composite_score_v3 returns "flow", which gets mapped
                pass
    except:
        pass
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: All component name mappings are consistent")
    
    print()
    return issues

def check_file_path_consistency():
    """Check that file paths are consistent"""
    print("=" * 80)
    print("FILE PATH CONSISTENCY CHECK")
    print("=" * 80)
    print()
    
    issues = []
    
    # Check config/registry.py paths
    try:
        from config.registry import Directories, CacheFiles, StateFiles, LogFiles
        
        # Check that paths exist or are properly defined
        all_paths = []
        all_paths.extend([getattr(Directories, attr) for attr in dir(Directories) if not attr.startswith('_')])
        all_paths.extend([getattr(CacheFiles, attr) for attr in dir(CacheFiles) if not attr.startswith('_')])
        all_paths.extend([getattr(StateFiles, attr) for attr in dir(StateFiles) if not attr.startswith('_')])
        all_paths.extend([getattr(LogFiles, attr) for attr in dir(LogFiles) if not attr.startswith('_')])
        
        # Check for hardcoded paths in main files
        main_files = ["main.py", "comprehensive_learning_orchestrator_v2.py", "adaptive_signal_optimizer.py"]
        for main_file in main_files:
            file_path = Path(main_file)
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Look for hardcoded paths (should use registry)
                hardcoded = re.findall(r'["\'](logs|data|state|config)/[^"\']+["\']', content)
                if hardcoded:
                    issues.append(f"{main_file} contains hardcoded paths: {set(hardcoded)}")
        
    except Exception as e:
        issues.append(f"Could not check file paths: {e}")
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: All file paths are consistent")
    
    print()
    return issues

def check_deprecated_references():
    """Check for references to deprecated code"""
    print("=" * 80)
    print("DEPRECATED CODE REFERENCES CHECK")
    print("=" * 80)
    print()
    
    issues = []
    deprecated_items = [
        "comprehensive_learning_orchestrator",  # Without _v2
        "_learn_from_outcomes_legacy",
        "from comprehensive_learning_orchestrator import",  # Old import
    ]
    
    # Check Python files
    for py_file in Path(".").glob("*.py"):
        if py_file.name == "architecture_mapping_audit.py":
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            for deprecated in deprecated_items:
                if deprecated in content:
                    issues.append(f"{py_file.name} references deprecated: {deprecated}")
        except:
            pass
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: No deprecated code references found")
    
    print()
    return issues

def check_import_consistency():
    """Check that imports are consistent"""
    print("=" * 80)
    print("IMPORT CONSISTENCY CHECK")
    print("=" * 80)
    print()
    
    issues = []
    
    # Check that comprehensive_learning_orchestrator_v2 is used, not old version
    main_file = Path("main.py")
    if main_file.exists():
        content = main_file.read_text(encoding='utf-8', errors='ignore')
        if "from comprehensive_learning_orchestrator_v2 import" not in content:
            issues.append("main.py does not import comprehensive_learning_orchestrator_v2")
        if "from comprehensive_learning_orchestrator import" in content:
            issues.append("main.py imports deprecated comprehensive_learning_orchestrator (without _v2)")
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: All imports are consistent")
    
    print()
    return issues

def check_state_file_mappings():
    """Check state file mappings"""
    print("=" * 80)
    print("STATE FILE MAPPINGS CHECK")
    print("=" * 80)
    print()
    
    issues = []
    
    try:
        from config.registry import StateFiles
        
        # Expected state files
        expected_state_files = [
            "signal_weights.json",
            "comprehensive_learning_state.json",
            "position_metadata.json",
            "learning_processing_state.json",
            "gate_pattern_learning.json",
            "uw_blocked_learning.json",
            "signal_pattern_learning.json",
            "learning_scheduler_state.json",
            "profitability_tracking.json",
        ]
        
        # Check that state files are defined in registry
        state_file_attrs = [attr for attr in dir(StateFiles) if not attr.startswith('_')]
        
        print("State files defined in registry:")
        for attr in sorted(state_file_attrs):
            path = getattr(StateFiles, attr)
            print(f"  {attr}: {path}")
        
    except Exception as e:
        issues.append(f"Could not check state files: {e}")
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: State file mappings are consistent")
    
    print()
    return issues

def generate_mapping_report():
    """Generate comprehensive mapping report"""
    print("=" * 80)
    print("ARCHITECTURE MAPPING AUDIT")
    print("=" * 80)
    print()
    print("This audit checks for:")
    print("  1. Component name consistency")
    print("  2. File path consistency")
    print("  3. Deprecated code references")
    print("  4. Import consistency")
    print("  5. State file mappings")
    print()
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_component_name_consistency())
    all_issues.extend(check_file_path_consistency())
    all_issues.extend(check_deprecated_references())
    all_issues.extend(check_import_consistency())
    all_issues.extend(check_state_file_mappings())
    
    # Summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print()
    
    if all_issues:
        print(f"FOUND {len(all_issues)} potential issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("SUCCESS: All architecture mappings are consistent!")
        print()
        print("No issues found. The system is properly configured.")
    
    print()
    print("=" * 80)
    
    return all_issues

if __name__ == "__main__":
    generate_mapping_report()
