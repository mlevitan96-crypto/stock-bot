#!/usr/bin/env python3
"""
Find unused code in the codebase
"""

import ast
import os
from pathlib import Path
from collections import defaultdict

def get_all_python_files():
    """Get all Python files in the project"""
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip common directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'node_modules', '.venv']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def extract_imports_and_definitions(file_path):
    """Extract imports and function/class definitions from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        
        imports = set()
        definitions = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                definitions.add(node.name)
        
        return imports, definitions
    except Exception as e:
        return set(), set()

def find_unused_files():
    """Find Python files that are never imported"""
    print("=" * 80)
    print("FINDING UNUSED CODE")
    print("=" * 80)
    
    python_files = get_all_python_files()
    print(f"\nFound {len(python_files)} Python files")
    
    # Files that are definitely used (entry points, main modules)
    used_files = {
        'main.py', 'dashboard.py', 'uw_flow_daemon.py', 'deploy_supervisor.py',
        'heartbeat_keeper.py', 'cache_enrichment_service.py'
    }
    
    # Build import graph
    file_imports = {}
    file_definitions = {}
    
    for file_path in python_files:
        rel_path = str(file_path.relative_to('.'))
        imports, definitions = extract_imports_and_definitions(file_path)
        file_imports[rel_path] = imports
        file_definitions[rel_path] = definitions
        
        # Check if it's a main/entry point
        if '__main__' in open(file_path).read():
            used_files.add(rel_path)
    
    # Find files that are imported
    for file_path, imports in file_imports.items():
        for imp in imports:
            # Check if any file imports this module
            for other_file, other_imports in file_imports.items():
                if file_path.replace('.py', '').replace('/', '.').replace('\\', '.') in str(other_imports):
                    used_files.add(file_path)
                    break
    
    # Find unused files
    unused_files = []
    for file_path in python_files:
        rel_path = str(file_path.relative_to('.'))
        if rel_path not in used_files:
            unused_files.append(rel_path)
    
    print(f"\nPotentially unused files ({len(unused_files)}):")
    for f in sorted(unused_files):
        print(f"  - {f}")
    
    # Find test/investigation scripts (likely temporary)
    investigation_scripts = [f for f in unused_files if any(x in f.lower() for x in ['test', 'investigate', 'check', 'verify', 'diagnose', 'fix_', 'audit'])]
    
    print(f"\nInvestigation/test scripts ({len(investigation_scripts)}):")
    for f in sorted(investigation_scripts):
        print(f"  - {f}")
    
    return unused_files, investigation_scripts

if __name__ == "__main__":
    unused, investigation = find_unused_files()
    print(f"\n\nTotal unused files: {len(unused)}")
    print(f"Investigation scripts: {len(investigation)}")

