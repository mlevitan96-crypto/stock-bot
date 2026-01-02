#!/usr/bin/env python3
"""
Generate concatenated export of core system files for audit.
Output: FULL_SYSTEM_AUDIT_EXPORT_2026-01-02.md
"""

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
OUTPUT_FILE = BASE_DIR / "FULL_SYSTEM_AUDIT_EXPORT_2026-01-02.md"

FILES_TO_EXPORT = {
    "main.py": BASE_DIR / "main.py",
    "uw_composite_v2.py": BASE_DIR / "uw_composite_v2.py",
    "adaptive_signal_optimizer.py": BASE_DIR / "adaptive_signal_optimizer.py",
    "momentum_ignition_filter.py": BASE_DIR / "momentum_ignition_filter.py",
    "regime_detector.py": BASE_DIR / "structural_intelligence" / "regime_detector.py"
}

def main():
    output_lines = [
        "# Full System Audit - Core Files Export",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}",
        "**Purpose:** Complete concatenation of core system files for audit and review",
        "**Authoritative Source:** MEMORY_BANK.md",
        "",
        "This document contains the complete source code for the five core system files required for the full system audit.",
        "",
        "---",
        ""
    ]
    
    for i, (name, file_path) in enumerate(FILES_TO_EXPORT.items(), 1):
        if not file_path.exists():
            print(f"WARNING: {file_path} does not exist, skipping...")
            continue
        
        output_lines.append(f"## File {i}: {name}")
        output_lines.append("")
        output_lines.append(f"**Path:** `{file_path.relative_to(BASE_DIR)}`")
        output_lines.append("")
        output_lines.append("```python")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                output_lines.append(f.read())
        except Exception as e:
            output_lines.append(f"# ERROR READING FILE: {e}")
        
        output_lines.append("```")
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
    
    OUTPUT_FILE.write_text('\n'.join(output_lines), encoding='utf-8')
    print(f"Export generated: {OUTPUT_FILE}")
    print(f"Total files: {len(FILES_TO_EXPORT)}")

if __name__ == "__main__":
    main()
