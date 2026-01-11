#!/usr/bin/env python3
"""
Migration Verification Script
Checks if everything is properly configured after migrating to a new laptop/folder.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

class MigrationChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.checks_passed = 0
        self.workspace_root = Path.cwd()
        
    def log_pass(self, msg: str):
        print(f"{GREEN}✅{RESET} {msg}")
        self.checks_passed += 1
    
    def log_warning(self, msg: str):
        print(f"{YELLOW}⚠️ {RESET} {msg}")
        self.warnings.append(msg)
    
    def log_error(self, msg: str):
        print(f"{RED}❌{RESET} {msg}")
        self.issues.append(msg)
    
    def log_info(self, msg: str):
        print(f"   {msg}")
    
    def check_config_registry(self):
        """Check if config/registry.py uses relative paths."""
        print(f"\n{BOLD}1. Checking Configuration Registry{RESET}")
        print("-" * 50)
        
        try:
            registry_path = self.workspace_root / "config" / "registry.py"
            if not registry_path.exists():
                self.log_error("config/registry.py not found")
                return
            
            content = registry_path.read_text()
            
            # Check for relative paths (good)
            if 'Path(".")' in content or 'Path("data")' in content:
                self.log_pass("Using relative paths in registry (good for portability)")
            else:
                self.log_warning("Registry may contain absolute paths")
            
            # Check for hardcoded /root paths (bad for Windows)
            if '/root/' in content or '/opt/' in content:
                self.log_warning("Registry contains Linux-specific paths")
                self.log_info("These are OK if only used on the droplet")
            
            self.log_pass("config/registry.py exists and looks OK")
            
        except Exception as e:
            self.log_error(f"Error checking registry: {e}")
    
    def check_droplet_config(self):
        """Check droplet_config.json for path issues."""
        print(f"\n{BOLD}2. Checking Droplet Configuration{RESET}")
        print("-" * 50)
        
        try:
            config_path = self.workspace_root / "droplet_config.json"
            if not config_path.exists():
                self.log_warning("droplet_config.json not found (OK if not using droplet_client)")
                return
            
            with open(config_path) as f:
                config = json.load(f)
            
            project_dir = config.get("project_dir", "")
            
            # Check for known path inconsistencies
            if "/root/trading-bot-B" in project_dir:
                self.log_warning(f"Project directory is '/root/trading-bot-B'")
                self.log_info("Most scripts reference '~/stock-bot' or '/root/stock-bot'")
                self.log_info("Verify this matches your actual droplet directory")
            elif "stock-bot" in project_dir.lower():
                self.log_pass(f"Project directory looks correct: {project_dir}")
            else:
                self.log_warning(f"Unusual project directory: {project_dir}")
            
            # Check SSH config reference
            if config.get("use_ssh_config"):
                self.log_pass("Using SSH config (good for portability)")
                self.log_info("Verify 'alpaca' host is in ~/.ssh/config")
            else:
                self.log_warning("Not using SSH config - paths may be hardcoded")
            
        except Exception as e:
            self.log_error(f"Error checking droplet config: {e}")
    
    def check_required_dirs(self):
        """Check if required directories exist."""
        print(f"\n{BOLD}3. Checking Required Directories{RESET}")
        print("-" * 50)
        
        required_dirs = ["config", "data", "state", "logs", "signals"]
        optional_dirs = ["archive", "reports", "droplet_data"]
        
        for dir_name in required_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists():
                self.log_pass(f"{dir_name}/ exists")
            else:
                self.log_warning(f"{dir_name}/ missing (will be created at runtime)")
        
        for dir_name in optional_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists():
                self.log_pass(f"{dir_name}/ exists")
    
    def check_key_files(self):
        """Check if key files exist."""
        print(f"\n{BOLD}4. Checking Key Files{RESET}")
        print("-" * 50)
        
        key_files = [
            "main.py",
            "dashboard.py",
            "deploy_supervisor.py",
            "requirements.txt",
            "README.md",
            "MEMORY_BANK.md",
            ".gitignore",
        ]
        
        for file_name in key_files:
            file_path = self.workspace_root / file_name
            if file_path.exists():
                self.log_pass(f"{file_name} exists")
            else:
                self.log_error(f"{file_name} missing")
    
    def check_hardcoded_paths(self):
        """Check for problematic hardcoded paths in key files."""
        print(f"\n{BOLD}5. Checking for Hardcoded Paths{RESET}")
        print("-" * 50)
        
        # Files that should use registry, not hardcoded paths
        key_files = ["main.py", "deploy_supervisor.py", "dashboard.py"]
        
        problematic_patterns = [
            ('/root/stock-bot', 'Linux absolute path'),
            ('C:\\', 'Windows absolute path'),
            ('~/stock-bot', 'Home directory path (may not expand on Windows)'),
        ]
        
        found_issues = False
        for file_name in key_files:
            file_path = self.workspace_root / file_name
            if not file_path.exists():
                continue
            
            content = file_path.read_text()
            for pattern, description in problematic_patterns:
                if pattern in content:
                    # Count occurrences
                    count = content.count(pattern)
                    if count > 0:
                        found_issues = True
                        self.log_warning(f"{file_name}: Contains {count} instances of {pattern} ({description})")
                        self.log_info("These are OK if used in SSH commands for droplet deployment")
        
        if not found_issues:
            self.log_pass("No problematic hardcoded paths found in key files")
    
    def check_git_setup(self):
        """Check Git configuration."""
        print(f"\n{BOLD}6. Checking Git Setup{RESET}")
        print("-" * 50)
        
        git_dir = self.workspace_root / ".git"
        if git_dir.exists():
            self.log_pass(".git directory exists")
        else:
            self.log_warning(".git directory not found - repository may not be initialized")
        
        # Check for .gitignore
        gitignore = self.workspace_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".env" in content:
                self.log_pass(".gitignore includes .env (good for security)")
            else:
                self.log_warning(".gitignore may not exclude .env files")
    
    def check_python_environment(self):
        """Check Python environment (optional, since bot runs on droplet)."""
        print(f"\n{BOLD}7. Checking Python Environment (Optional){RESET}")
        print("-" * 50)
        
        python_cmd = sys.executable
        self.log_info(f"Python: {python_cmd}")
        self.log_info("Note: Bot runs on remote droplet, not locally")
        self.log_info("Python here is only needed for local scripts/tests")
        
        # Check if requirements.txt exists
        req_file = self.workspace_root / "requirements.txt"
        if req_file.exists():
            self.log_pass("requirements.txt exists")
            self.log_info("Install with: pip install -r requirements.txt (if needed locally)")
        else:
            self.log_warning("requirements.txt not found")
    
    def check_ssh_config_hint(self):
        """Provide hints about SSH configuration."""
        print(f"\n{BOLD}8. SSH Configuration Check{RESET}")
        print("-" * 50)
        
        ssh_config_path = Path.home() / ".ssh" / "config"
        if ssh_config_path.exists():
            self.log_pass("~/.ssh/config exists")
            try:
                content = ssh_config_path.read_text()
                if "alpaca" in content.lower():
                    self.log_pass("SSH config contains 'alpaca' host")
                else:
                    self.log_warning("SSH config doesn't mention 'alpaca' host")
                    self.log_info("Add entry for droplet access if needed")
            except Exception:
                self.log_warning("Could not read SSH config (permissions?)")
        else:
            self.log_warning("~/.ssh/config not found")
            self.log_info("Create it if you need to access the droplet")
    
    def check_documentation(self):
        """Check if key documentation exists."""
        print(f"\n{BOLD}9. Checking Documentation{RESET}")
        print("-" * 50)
        
        doc_files = [
            "MEMORY_BANK.md",
            "README.md",
            "SETUP_NEW_LAPTOP.md",
        ]
        
        for doc_file in doc_files:
            doc_path = self.workspace_root / doc_file
            if doc_path.exists():
                self.log_pass(f"{doc_file} exists")
            else:
                self.log_warning(f"{doc_file} missing")
    
    def generate_summary(self):
        """Generate summary report."""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}MIGRATION VERIFICATION SUMMARY{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")
        
        print(f"{GREEN}✅ Checks Passed: {self.checks_passed}{RESET}")
        print(f"{YELLOW}⚠️  Warnings: {len(self.warnings)}{RESET}")
        print(f"{RED}❌ Issues: {len(self.issues)}{RESET}\n")
        
        if self.issues:
            print(f"{BOLD}Issues to Address:{RESET}")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
            print()
        
        if self.warnings:
            print(f"{BOLD}Warnings (may need attention):{RESET}")
            for i, warning in enumerate(self.warnings[:5], 1):  # Show first 5
                print(f"  {i}. {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more warnings")
            print()
        
        # Recommendations
        print(f"{BOLD}Recommendations:{RESET}")
        print("  1. Verify droplet_config.json project_dir matches actual droplet path")
        print("  2. Ensure SSH config has 'alpaca' host if using droplet_client.py")
        print("  3. Bot runs on remote droplet - local Python is optional")
        print("  4. Read SETUP_NEW_LAPTOP.md for detailed setup instructions")
        print("  5. Read MEMORY_BANK.md for complete project context")
        print()
        
        if len(self.issues) == 0:
            print(f"{GREEN}{BOLD}✓ Migration looks good! No critical issues found.{RESET}")
            return 0
        else:
            print(f"{YELLOW}{BOLD}⚠ Some issues found. Review and fix as needed.{RESET}")
            return 1
    
    def run_all_checks(self):
        """Run all verification checks."""
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}STOCK BOT - MIGRATION VERIFICATION{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"\nWorkspace: {self.workspace_root}\n")
        
        self.check_config_registry()
        self.check_droplet_config()
        self.check_required_dirs()
        self.check_key_files()
        self.check_hardcoded_paths()
        self.check_git_setup()
        self.check_python_environment()
        self.check_ssh_config_hint()
        self.check_documentation()
        
        return self.generate_summary()

if __name__ == "__main__":
    checker = MigrationChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)
