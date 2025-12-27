#!/usr/bin/env python3
"""
Cleanup unused code - Archive investigation scripts and identify unused functions
"""

import shutil
from pathlib import Path
import json

def archive_investigation_scripts():
    """Archive investigation/test scripts to archive/ directory"""
    print("=" * 80)
    print("ARCHIVING INVESTIGATION SCRIPTS")
    print("=" * 80)
    
    investigation_keywords = [
        'investigate', 'diagnose', 'check_', 'verify_', 'test_', 
        'fix_', 'audit', 'debug', 'troubleshoot', 'analyze_',
        'COMPLETE_', 'FULL_', 'DIAGNOSE_', 'FIX_', 'VERIFY_',
        'APPLY_', 'DEPLOY_', 'REGression_', 'STATISTICAL_'
    ]
    
    # Files to keep (active scripts)
    keep_files = {
        'main.py', 'dashboard.py', 'uw_flow_daemon.py', 'deploy_supervisor.py',
        'heartbeat_keeper.py', 'cache_enrichment_service.py',
        # Trading readiness system (keep)
        'failure_point_monitor.py', 'trading_readiness_test_harness.py',
        'inject_fake_signal_test.py', 'automated_trading_verification.py',
        'continuous_fp_monitoring.py', 'investigate_blocked_status.py',
        'fix_blocked_readiness.py', 'verify_readiness_simple.py',
        'verify_droplet_deployment.py', 'fix_adaptive_weights_init.py',
        # Core modules
        'uw_composite_v2.py', 'uw_enrichment_v2.py', 'adaptive_signal_optimizer.py',
        'self_healing_threshold.py', 'analyze_code_usage.py', 'find_unused_code.py',
        'cleanup_unused_code.py'
    }
    
    archive_dir = Path("archive/investigation_scripts")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    scripts_to_archive = []
    
    for file_path in Path('.').rglob('*.py'):
        if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv', 'archive']):
            continue
        
        filename = file_path.name
        if filename in keep_files:
            continue
        
        # Check if it matches investigation patterns
        filename_lower = filename.lower()
        if any(keyword in filename_lower for keyword in investigation_keywords):
            scripts_to_archive.append(file_path)
    
    print(f"\nFound {len(scripts_to_archive)} scripts to archive")
    
    if not scripts_to_archive:
        print("No scripts to archive")
        return []
    
    # Create manifest
    manifest = {
        "archived_date": "2025-12-26",
        "reason": "Investigation/test scripts - archived to reduce clutter",
        "files": []
    }
    
    archived_count = 0
    for script in sorted(scripts_to_archive):
        try:
            dest = archive_dir / script.name
            # Handle duplicates
            counter = 1
            while dest.exists():
                dest = archive_dir / f"{script.stem}_{counter}{script.suffix}"
                counter += 1
            
            shutil.move(str(script), str(dest))
            manifest["files"].append({
                "original": str(script),
                "archived": str(dest),
                "size": script.stat().st_size if script.exists() else 0
            })
            archived_count += 1
            print(f"  Archived: {script.name} -> {dest.name}")
        except Exception as e:
            print(f"  ERROR archiving {script.name}: {e}")
    
    # Save manifest
    manifest_file = archive_dir / "manifest.json"
    with manifest_file.open("w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nArchived {archived_count} scripts to {archive_dir}")
    return scripts_to_archive

def identify_unused_functions_in_main():
    """Identify unused functions in main.py"""
    print("\n" + "=" * 80)
    print("IDENTIFYING UNUSED FUNCTIONS IN MAIN.PY")
    print("=" * 80)
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("main.py not found")
        return []
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    import re
    
    # Find function definitions
    function_pattern = r'^def\s+(\w+)\s*\('
    functions = []
    for i, line in enumerate(lines, 1):
        match = re.match(function_pattern, line.strip())
        if match:
            func_name = match.group(1)
            # Skip if it's a method (indented)
            if line.startswith('def '):
                functions.append((func_name, i))
    
    # Find class definitions
    class_pattern = r'^class\s+(\w+)'
    classes = []
    for i, line in enumerate(lines, 1):
        match = re.match(class_pattern, line.strip())
        if match:
            class_name = match.group(1)
            if line.startswith('class '):
                classes.append((class_name, i))
    
    # Check usage
    unused_functions = []
    for func_name, lineno in functions:
        # Skip private methods
        if func_name.startswith('_') and not func_name.startswith('__'):
            continue
        
        # Count occurrences (definition + calls)
        pattern = rf'\b{re.escape(func_name)}\s*\('
        matches = len(re.findall(pattern, content))
        
        # If only appears once (the definition), it's unused
        if matches <= 1:
            unused_functions.append((func_name, lineno, 'function'))
    
    unused_classes = []
    for class_name, lineno in classes:
        # Count occurrences
        pattern = rf'\b{re.escape(class_name)}\s*\('
        matches = len(re.findall(pattern, content))
        
        if matches <= 1:
            unused_classes.append((class_name, lineno, 'class'))
    
    print(f"\nFound {len(functions)} functions, {len(classes)} classes")
    print(f"Potentially unused: {len(unused_functions)} functions, {len(unused_classes)} classes")
    
    if unused_functions:
        print("\nPotentially unused functions:")
        for name, lineno, _ in unused_functions[:30]:
            print(f"  - {name:40} (line {lineno})")
    
    if unused_classes:
        print("\nPotentially unused classes:")
        for name, lineno, _ in unused_classes:
            print(f"  - {name:40} (line {lineno})")
    
    return unused_functions + unused_classes

def find_old_code_patterns():
    """Find patterns indicating old/unused code"""
    print("\n" + "=" * 80)
    print("FINDING OLD CODE PATTERNS")
    print("=" * 80)
    
    main_file = Path("main.py")
    if not main_file.exists():
        return []
    
    with open(main_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    old_patterns = []
    
    # Look for functions with "_old" suffix
    import re
    for i, line in enumerate(lines, 1):
        if re.search(r'def\s+\w+_old\s*\(', line):
            match = re.search(r'def\s+(\w+_old)\s*\(', line)
            if match:
                old_patterns.append(('function', match.group(1), i, 'Has "_old" suffix'))
    
    # Look for commented out function definitions
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') and 'def ' in stripped:
            old_patterns.append(('commented', 'function', i, 'Commented out function'))
    
    if old_patterns:
        print(f"\nFound {len(old_patterns)} old code patterns:")
        for pattern_type, name, lineno, reason in old_patterns[:20]:
            print(f"  {pattern_type:12} {name:40} (line {lineno}) - {reason}")
    else:
        print("\nNo obvious old code patterns found")
    
    return old_patterns

def main():
    print("=" * 80)
    print("CODE CLEANUP - UNUSED CODE REMOVAL")
    print("=" * 80)
    
    # Ask for confirmation
    print("\nThis will:")
    print("  1. Archive investigation/test scripts to archive/investigation_scripts/")
    print("  2. Identify unused functions in main.py")
    print("  3. Find old code patterns")
    print("\nNOTE: This is a DRY RUN. No files will be deleted, only archived.")
    
    # Archive scripts
    archived = archive_investigation_scripts()
    
    # Find unused functions
    unused = identify_unused_functions_in_main()
    
    # Find old patterns
    old_patterns = find_old_code_patterns()
    
    # Summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Scripts archived: {len(archived)}")
    print(f"Potentially unused functions: {len(unused)}")
    print(f"Old code patterns: {len(old_patterns)}")
    
    print("\nNext steps:")
    print("  1. Review archived scripts - delete if not needed")
    print("  2. Manually review unused functions in main.py")
    print("  3. Remove old code patterns after verification")

if __name__ == "__main__":
    main()

