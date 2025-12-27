#!/usr/bin/env python3
"""
Analyze code usage to find unused functions, classes, and files
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_file(file_path):
    """Analyze a Python file for definitions and usage"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        definitions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                definitions.append(('function', node.name, node.lineno))
            elif isinstance(node, ast.ClassDef):
                definitions.append(('class', node.name, node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return definitions, imports, content
    except Exception as e:
        return [], [], ""

def find_unused_in_main():
    """Find unused functions/classes in main.py"""
    print("=" * 80)
    print("ANALYZING MAIN.PY FOR UNUSED CODE")
    print("=" * 80)
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("main.py not found")
        return
    
    definitions, imports, content = analyze_file(main_file)
    
    print(f"\nFound {len(definitions)} definitions in main.py")
    
    # Check which definitions are used
    unused = []
    used = []
    
    for def_type, name, lineno in definitions:
        # Skip private methods (starting with _)
        if name.startswith('_') and not name.startswith('__'):
            continue
        
        # Check if it's called anywhere
        # Look for function calls
        pattern = rf'\b{re.escape(name)}\s*\('
        matches = re.findall(pattern, content)
        
        # Also check for decorators, class instantiation, etc.
        class_pattern = rf'\b{re.escape(name)}\s*\('
        decorator_pattern = rf'@{re.escape(name)}'
        
        all_matches = len(re.findall(pattern, content)) + len(re.findall(decorator_pattern, content))
        
        # If it's defined but only appears once (the definition), it's unused
        if all_matches <= 1:
            unused.append((def_type, name, lineno))
        else:
            used.append((def_type, name, lineno))
    
    print(f"\nUsed definitions: {len(used)}")
    print(f"Potentially unused: {len(unused)}")
    
    if unused:
        print("\nPotentially unused definitions:")
        for def_type, name, lineno in unused[:20]:  # Show first 20
            print(f"  {def_type:10} {name:40} (line {lineno})")
    
    return unused

def find_investigation_scripts():
    """Find investigation/test scripts that might be temporary"""
    print("\n" + "=" * 80)
    print("FINDING INVESTIGATION/TEST SCRIPTS")
    print("=" * 80)
    
    investigation_keywords = [
        'investigate', 'diagnose', 'check_', 'verify_', 'test_', 
        'fix_', 'audit', 'debug', 'troubleshoot', 'analyze_'
    ]
    
    scripts = []
    for file_path in Path('.').rglob('*.py'):
        if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv']):
            continue
        
        filename = file_path.name.lower()
        if any(keyword in filename for keyword in investigation_keywords):
            scripts.append(str(file_path))
    
    print(f"\nFound {len(scripts)} investigation/test scripts:")
    for script in sorted(scripts):
        print(f"  - {script}")
    
    return scripts

def find_old_commented_code():
    """Find large blocks of commented code"""
    print("\n" + "=" * 80)
    print("FINDING COMMENTED CODE BLOCKS")
    print("=" * 80)
    
    commented_blocks = []
    
    for file_path in Path('.').rglob('*.py'):
        if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv']):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_comment_block = False
            comment_start = 0
            comment_lines = []
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Check for large comment blocks (5+ lines)
                if stripped.startswith('#'):
                    if not in_comment_block:
                        in_comment_block = True
                        comment_start = i
                        comment_lines = [line]
                    else:
                        comment_lines.append(line)
                else:
                    if in_comment_block and len(comment_lines) >= 5:
                        commented_blocks.append({
                            'file': str(file_path),
                            'start': comment_start,
                            'end': i - 1,
                            'lines': len(comment_lines)
                        })
                    in_comment_block = False
                    comment_lines = []
        except:
            pass
    
    if commented_blocks:
        print(f"\nFound {len(commented_blocks)} large comment blocks:")
        for block in commented_blocks[:10]:  # Show first 10
            print(f"  {block['file']}: lines {block['start']}-{block['end']} ({block['lines']} lines)")
    else:
        print("\nNo large comment blocks found")
    
    return commented_blocks

def main():
    print("=" * 80)
    print("CODE USAGE ANALYSIS")
    print("=" * 80)
    
    # Analyze main.py
    unused_main = find_unused_in_main()
    
    # Find investigation scripts
    investigation_scripts = find_investigation_scripts()
    
    # Find commented code
    commented_blocks = find_old_commented_code()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Potentially unused in main.py: {len(unused_main)}")
    print(f"Investigation scripts: {len(investigation_scripts)}")
    print(f"Large comment blocks: {len(commented_blocks)}")
    
    print("\nRecommendations:")
    if investigation_scripts:
        print(f"  - Consider archiving {len(investigation_scripts)} investigation scripts")
    if unused_main:
        print(f"  - Review {len(unused_main)} potentially unused definitions in main.py")
    if commented_blocks:
        print(f"  - Review {len(commented_blocks)} large comment blocks")

if __name__ == "__main__":
    main()

