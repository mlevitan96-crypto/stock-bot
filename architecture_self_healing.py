#!/usr/bin/env python3
"""
Architecture Self-Healing Engine
=================================

Automatically detects and fixes architecture mapping issues:
1. Hardcoded paths → Registry paths
2. Deprecated imports → Updated imports
3. Component name mismatches → Correct mappings
4. Missing registry usage → Registry integration

This runs as part of the health check system to prevent issues from accumulating.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

class ArchitectureHealer:
    """Self-healing engine for architecture mapping issues"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.errors = []
        
        # Registry mappings (escaped properly for regex)
        self.path_mappings = {
            r'Path\("state/fail_counter\.json"\)': 'StateFiles.FAIL_COUNTER',
            r'Path\("state/smart_poller\.json"\)': 'StateFiles.SMART_POLLER',
            r'Path\("state/champions\.json"\)': 'StateFiles.CHAMPIONS',
            r'Path\("state/pre_market_freeze\.flag"\)': 'StateFiles.PRE_MARKET_FREEZE',
            r'Path\("data/governance_events\.jsonl"\)': 'CacheFiles.GOVERNANCE_EVENTS',
            r'Path\("data/execution_quality\.jsonl"\)': 'CacheFiles.EXECUTION_QUALITY',
            r'Path\("data/uw_attribution\.jsonl"\)': 'CacheFiles.UW_ATTRIBUTION',
            r'Path\("logs/reconcile\.jsonl"\)': 'LogFiles.RECONCILE',
            r'"config/theme_risk\.json"': 'ConfigFiles.THEME_RISK',
            r'open\("data/uw_attribution\.jsonl"': 'open(CacheFiles.UW_ATTRIBUTION',
        }
        
        # Import mappings
        self.import_mappings = {
            r'from comprehensive_learning_orchestrator import get_learning_orchestrator':
                'from comprehensive_learning_orchestrator_v2 import load_learning_state',
            r'comprehensive_learning_orchestrator\.get_learning_orchestrator\(\)':
                'comprehensive_learning_orchestrator_v2.load_learning_state()',
        }
    
    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a file for architecture issues"""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for hardcoded paths
            for pattern, replacement in self.path_mappings.items():
                try:
                    # Compile pattern first to catch errors early
                    compiled_pattern = re.compile(pattern)
                    matches = compiled_pattern.finditer(content)
                    for match in matches:
                        issues.append({
                            'type': 'hardcoded_path',
                            'file': str(file_path),
                            'line': content[:match.start()].count('\n') + 1,
                            'pattern': pattern,
                            'replacement': replacement,
                            'match': match.group(0)
                        })
                except re.error as e:
                    # Skip invalid regex patterns - log but don't fail
                    continue
                except Exception as e:
                    # Skip any other errors
                    continue
            
            # Check for deprecated imports
            for pattern, replacement in self.import_mappings.items():
                try:
                    compiled_pattern = re.compile(pattern)
                    matches = compiled_pattern.finditer(content)
                    for match in matches:
                        issues.append({
                            'type': 'deprecated_import',
                            'file': str(file_path),
                            'line': content[:match.start()].count('\n') + 1,
                            'pattern': pattern,
                            'replacement': replacement,
                            'match': match.group(0)
                        })
                except (re.error, Exception):
                    # Skip invalid patterns
                    continue
            
            # Check for missing registry imports
            if any(re.search(pattern, content) for pattern in self.path_mappings.values()):
                # Check if registry is imported
                if 'from config.registry import' not in content:
                    # Check if we're using registry paths
                    uses_registry = any(
                        'StateFiles.' in content or 
                        'CacheFiles.' in content or 
                        'LogFiles.' in content or
                        'ConfigFiles.' in content
                    )
                    if uses_registry:
                        issues.append({
                            'type': 'missing_import',
                            'file': str(file_path),
                            'line': 1,
                            'pattern': 'from config.registry import',
                            'replacement': 'from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles',
                            'match': 'Missing registry import'
                        })
        
        except Exception as e:
            self.errors.append(f"Error checking {file_path}: {e}")
        
        return issues
    
    def fix_file(self, file_path: Path, issues: List[Dict]) -> bool:
        """Fix issues in a file"""
        if not issues:
            return True
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original_content = content
            
            # Apply fixes
            for issue in issues:
                if issue['type'] in ['hardcoded_path', 'deprecated_import']:
                    pattern = issue['pattern']
                    replacement = issue['replacement']
                    try:
                        content = re.sub(pattern, replacement, content)
                        self.fixes_applied.append(f"{file_path.name}: {issue['type']} at line {issue['line']}")
                    except re.error as e:
                        self.errors.append(f"Regex error fixing {file_path.name}: {e}")
                        continue
            
            # Add missing imports if needed
            missing_import_issues = [i for i in issues if i['type'] == 'missing_import']
            if missing_import_issues:
                # Find where to insert import (after existing imports)
                import_match = re.search(r'^from config\.registry import.*$', content, re.MULTILINE)
                if not import_match:
                    # Find last import statement
                    last_import = None
                    for match in re.finditer(r'^(import |from .* import)', content, re.MULTILINE):
                        last_import = match
                    
                    if last_import:
                        insert_pos = content.find('\n', last_import.end()) + 1
                        import_line = "from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles\n"
                        content = content[:insert_pos] + import_line + content[insert_pos:]
                        self.fixes_applied.append(f"{file_path.name}: Added missing registry import")
            
            # Only write if content changed
            if content != original_content:
                if not self.dry_run:
                    file_path.write_text(content, encoding='utf-8')
                    return True
                else:
                    return True  # Would fix in non-dry-run mode
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error fixing {file_path}: {e}")
            return False
    
    def heal_all(self, directory: Path = Path(".")) -> Dict:
        """Heal all architecture issues in the codebase"""
        results = {
            'files_checked': 0,
            'issues_found': 0,
            'fixes_applied': 0,
            'errors': []
        }
        
        # Check all Python files
        for py_file in directory.glob("*.py"):
            if py_file.name in ['architecture_self_healing.py', 'architecture_mapping_audit.py']:
                continue
            
            results['files_checked'] += 1
            issues = self.check_file(py_file)
            results['issues_found'] += len(issues)
            
            if issues:
                fixed = self.fix_file(py_file, issues)
                if fixed:
                    results['fixes_applied'] += len(issues)
        
        results['errors'] = self.errors
        results['fixes_applied_list'] = self.fixes_applied
        
        return results

def main():
    """Run self-healing in dry-run mode by default"""
    import sys
    
    dry_run = '--apply' not in sys.argv
    
    print("=" * 80)
    print("ARCHITECTURE SELF-HEALING ENGINE")
    print("=" * 80)
    print()
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
        print("Use --apply to actually fix issues")
    else:
        print("APPLY MODE - Fixes will be applied")
    print()
    
    healer = ArchitectureHealer(dry_run=dry_run)
    results = healer.heal_all()
    
    print(f"Files checked: {results['files_checked']}")
    print(f"Issues found: {results['issues_found']}")
    print(f"Fixes {'would be applied' if dry_run else 'applied'}: {results['fixes_applied']}")
    print()
    
    if results['fixes_applied_list']:
        print("Fixes:")
        for fix in results['fixes_applied_list']:
            print(f"  - {fix}")
        print()
    
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")
        print()
    
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    main()
