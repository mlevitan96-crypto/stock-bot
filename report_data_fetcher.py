#!/usr/bin/env python3
"""
Report Data Fetcher - Single Source of Truth for Trading Report Data

CRITICAL: This module ALWAYS fetches data from Droplet production server.
Never use local files for production reports - they may be outdated or empty.

Usage:
    from report_data_fetcher import ReportDataFetcher
    
    fetcher = ReportDataFetcher(date="2026-01-08")
    trades = fetcher.get_executed_trades()  # Always from Droplet
    blocked = fetcher.get_blocked_trades()  # Always from Droplet
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import paramiko
import subprocess

try:
    from droplet_client import DropletClient
    DROPLET_CLIENT_AVAILABLE = True
except ImportError:
    DROPLET_CLIENT_AVAILABLE = False

# File locations on Droplet (from MEMORY_BANK.md)
DROPLET_LOG_FILES = {
    "attribution": "/root/stock-bot/logs/attribution.jsonl",
    "blocked_trades": "/root/stock-bot/state/blocked_trades.jsonl",
    "exit": "/root/stock-bot/logs/exits.jsonl",
    "signals": "/root/stock-bot/logs/signals.jsonl",
    "orders": "/root/stock-bot/logs/orders.jsonl",
    "gate": "/root/stock-bot/logs/gate.jsonl",
    "uw_attribution": "/root/stock-bot/data/uw_attribution.jsonl",
    "daily_postmortem": "/root/stock-bot/data/daily_postmortem.jsonl",
}

CACHE_DIR = Path("droplet_data_cache")
CACHE_EXPIRY_HOURS = 1  # Cache expires after 1 hour


class ReportDataFetcher:
    """
    Centralized data fetcher that ALWAYS gets data from Droplet.
    
    This is the ONLY way to get production trading data for reports.
    Local files are NEVER used for production reports.
    """
    
    def __init__(self, date: Optional[str] = None, use_cache: bool = True):
        """
        Initialize data fetcher.
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            use_cache: Whether to use cached data if fresh (< 1 hour old)
        """
        if date:
            try:
                self.target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")
        else:
            self.target_date = datetime.now(timezone.utc)
        
        self.use_cache = use_cache
        CACHE_DIR.mkdir(exist_ok=True)
        
        # Connection will be established lazily
        self._ssh_client = None
        self._client = None
    
    def _get_connection(self):
        """Get SSH connection to Droplet (lazy initialization)"""
        if self._ssh_client:
            return self._ssh_client
        
        if DROPLET_CLIENT_AVAILABLE:
            try:
                self._client = DropletClient()
                self._ssh_client = self._client._connect()
                return self._ssh_client
            except Exception as e:
                raise ConnectionError(f"Failed to connect via DropletClient: {e}")
        else:
            # Direct SSH connection
            try:
                result = subprocess.run(['ssh', '-G', 'alpaca'], capture_output=True, text=True, timeout=5)
                hostname = None
                port = 22
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('hostname '):
                        hostname = line.split(' ', 1)[1]
                    elif line.startswith('port '):
                        port = int(line.split(' ', 1)[1])
                
                if not hostname:
                    raise ConnectionError("Could not resolve 'alpaca' from SSH config")
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname, port=port, username='root', timeout=10, 
                           look_for_keys=True, allow_agent=True)
                self._ssh_client = ssh
                return ssh
            except Exception as e:
                raise ConnectionError(f"Failed to connect via SSH: {e}")
    
    def _is_cache_fresh(self, cache_file: Path) -> bool:
        """Check if cache file is fresh (less than CACHE_EXPIRY_HOURS old)"""
        if not cache_file.exists():
            return False
        
        file_age = datetime.now(timezone.utc) - datetime.fromtimestamp(
            cache_file.stat().st_mtime, tz=timezone.utc
        )
        return file_age < timedelta(hours=CACHE_EXPIRY_HOURS)
    
    def _fetch_file_from_droplet(self, remote_path: str, local_cache_path: Path) -> bool:
        """Fetch file from Droplet via SFTP"""
        try:
            ssh = self._get_connection()
            sftp = ssh.open_sftp()
            try:
                sftp.get(remote_path, str(local_cache_path))
                return True
            except FileNotFoundError:
                return False
            finally:
                sftp.close()
        except Exception as e:
            print(f"Error fetching {remote_path}: {e}", file=sys.stderr)
            return False
    
    def _get_file_data(self, file_type: str) -> List[Dict]:
        """Get data for a specific file type, fetching from Droplet if needed"""
        remote_path = DROPLET_LOG_FILES.get(file_type)
        if not remote_path:
            raise ValueError(f"Unknown file type: {file_type}")
        
        cache_file = CACHE_DIR / f"{file_type}_{self.target_date.date().isoformat()}.jsonl"
        
        # Check cache
        if self.use_cache and self._is_cache_fresh(cache_file):
            print(f"  Using cached {file_type} (fresh)", file=sys.stderr)
        else:
            # Fetch from Droplet
            print(f"  Fetching {file_type} from Droplet...", file=sys.stderr, end=" ")
            if self._fetch_file_from_droplet(remote_path, cache_file):
                print("✓", file=sys.stderr)
            else:
                print("✗ (file not found on Droplet)", file=sys.stderr)
                return []
        
        # Load and filter by date
        if not cache_file.exists():
            return []
        
        records = []
        target_date_str = self.target_date.date().isoformat()
        
        with cache_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("ts") or rec.get("timestamp")
                    if ts_str and target_date_str in str(ts_str):
                        records.append(rec)
                except:
                    continue
        
        return records
    
    def get_executed_trades(self) -> List[Dict]:
        """Get executed trades for target date from Droplet"""
        return self._get_file_data("attribution")
    
    def get_blocked_trades(self) -> List[Dict]:
        """Get blocked trades for target date from Droplet"""
        return self._get_file_data("blocked_trades")
    
    def get_exit_events(self) -> List[Dict]:
        """Get exit events for target date from Droplet"""
        return self._get_file_data("exit")
    
    def get_signals(self) -> List[Dict]:
        """Get signals for target date from Droplet"""
        return self._get_file_data("signals")
    
    def get_orders(self) -> List[Dict]:
        """Get orders for target date from Droplet"""
        return self._get_file_data("orders")
    
    def get_gate_events(self) -> List[Dict]:
        """Get gate events for target date from Droplet"""
        return self._get_file_data("gate")
    
    def get_uw_attribution(self) -> List[Dict]:
        """Get UW attribution for target date from Droplet"""
        return self._get_file_data("uw_attribution")
    
    def get_data_source_info(self) -> Dict[str, Any]:
        """Get information about data source (for report metadata)"""
        return {
            "source": "Droplet Production Server",
            "host": "alpaca (via SSH config)",
            "project_dir": "/root/stock-bot",
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": self.target_date.date().isoformat(),
            "cache_used": self.use_cache,
            "cache_dir": str(CACHE_DIR),
        }
    
    def close(self):
        """Close SSH connection"""
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
        if self._client:
            self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick access
def get_report_data(date: Optional[str] = None) -> ReportDataFetcher:
    """
    Get ReportDataFetcher instance.
    
    Usage:
        with get_report_data("2026-01-08") as fetcher:
            trades = fetcher.get_executed_trades()
    """
    return ReportDataFetcher(date=date)
