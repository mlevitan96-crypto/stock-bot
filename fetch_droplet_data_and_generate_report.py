#!/usr/bin/env python3
"""
Fetch Real Trading Data from Droplet and Generate Comprehensive Report
This script connects to the Droplet, fetches actual log files, and generates
accurate reports with real trading data.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict
import paramiko
from io import StringIO

try:
    from droplet_client import DropletClient
    DROPLET_CLIENT_AVAILABLE = True
except ImportError:
    DROPLET_CLIENT_AVAILABLE = False
    print("Warning: droplet_client not available, using direct SSH", file=sys.stderr)

# File locations on Droplet (from MEMORY_BANK.md and config/registry.py)
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

LOCAL_DATA_DIR = Path("droplet_data")
LOCAL_DATA_DIR.mkdir(exist_ok=True)

def fetch_file_from_droplet(ssh_client, remote_path: str, local_path: Path) -> bool:
    """Fetch a file from droplet via SFTP"""
    try:
        sftp = ssh_client.open_sftp()
        try:
            sftp.get(remote_path, str(local_path))
            return True
        except FileNotFoundError:
            print(f"  File not found on droplet: {remote_path}", file=sys.stderr)
            return False
        finally:
            sftp.close()
    except Exception as e:
        print(f"  Error fetching {remote_path}: {e}", file=sys.stderr)
        return False

def execute_ssh_command(ssh_client, command: str) -> tuple[str, str, int]:
    """Execute a command on the droplet via SSH"""
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return output, error, exit_code
    except Exception as e:
        return "", str(e), -1

def fetch_all_data_from_droplet() -> Dict[str, Path]:
    """Fetch all log files from droplet"""
    print("Connecting to Droplet...", file=sys.stderr)
    
    ssh_client = None
    use_client = False
    
    if DROPLET_CLIENT_AVAILABLE:
        try:
            client = DropletClient()
            ssh_client = client._connect()  # Use private method
            use_client = True
            print("  Connected via DropletClient", file=sys.stderr)
        except Exception as e:
            print(f"  Error connecting via DropletClient: {e}", file=sys.stderr)
            print("  Trying direct SSH connection...", file=sys.stderr)
            use_client = False
    
    if not ssh_client:
        # Direct SSH connection using SSH config
        try:
            import subprocess
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
                print("  Could not resolve 'alpaca' from SSH config", file=sys.stderr)
                return {}
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, port=port, username='root', timeout=10, look_for_keys=True, allow_agent=True)
            ssh_client = ssh
            print(f"  Connected via direct SSH to {hostname}", file=sys.stderr)
        except Exception as e:
            print(f"  Error connecting via direct SSH: {e}", file=sys.stderr)
            return {}
    
    print("Fetching log files from Droplet...", file=sys.stderr)
    fetched_files = {}
    
    for file_type, remote_path in DROPLET_LOG_FILES.items():
        local_path = LOCAL_DATA_DIR / f"{file_type}.jsonl"
        print(f"  Fetching {file_type}...", file=sys.stderr, end=" ")
        
        # First check if file exists
        if use_client:
            stdout, stderr, exit_code = client._execute(f"test -f {remote_path} && echo 'exists' || echo 'missing'")
            file_exists = 'exists' in stdout
        else:
            output, error, exit_code = execute_ssh_command(ssh_client, f"test -f {remote_path} && echo 'exists' || echo 'missing'")
            file_exists = 'exists' in output
        
        if file_exists:
            if fetch_file_from_droplet(ssh_client, remote_path, local_path):
                # Check file size
                size = local_path.stat().st_size if local_path.exists() else 0
                try:
                    line_count = len(local_path.read_text().splitlines()) if local_path.exists() else 0
                    print(f"✓ ({line_count} lines, {size} bytes)", file=sys.stderr)
                except:
                    print(f"✓ ({size} bytes)", file=sys.stderr)
                fetched_files[file_type] = local_path
            else:
                print("✗", file=sys.stderr)
        else:
            print("✗ (not found)", file=sys.stderr)
    
    if ssh_client:
        ssh_client.close()
    
    return fetched_files

def load_jsonl_file(file_path: Path, target_date: datetime) -> List[Dict]:
    """Load and filter JSONL file for target date"""
    records = []
    if not file_path.exists():
        return records
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    
                    # Try to find timestamp
                    dt = None
                    for ts_field in ["timestamp", "ts", "_ts", "_dt", "entry_ts", "exit_ts", "time"]:
                        ts_val = rec.get(ts_field)
                        if ts_val:
                            try:
                                if isinstance(ts_val, (int, float)):
                                    dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
                                elif isinstance(ts_val, str):
                                    ts_val = ts_val.replace("Z", "+00:00")
                                    dt = datetime.fromisoformat(ts_val)
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=timezone.utc)
                                if dt:
                                    break
                            except:
                                pass
                    
                    # Also check context
                    if not dt and "context" in rec:
                        ctx = rec.get("context", {})
                        for ts_field in ["timestamp", "ts", "entry_ts", "exit_ts"]:
                            ts_val = ctx.get(ts_field)
                            if ts_val:
                                try:
                                    if isinstance(ts_val, (int, float)):
                                        dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
                                    elif isinstance(ts_val, str):
                                        ts_val = ts_val.replace("Z", "+00:00")
                                        dt = datetime.fromisoformat(ts_val)
                                        if dt.tzinfo is None:
                                            dt = dt.replace(tzinfo=timezone.utc)
                                    if dt:
                                        break
                                except:
                                    pass
                    
                    # Filter by date
                    if dt and dt.date() == target_date.date():
                        rec["_parsed_timestamp"] = dt
                        records.append(rec)
                    # Also include records without timestamp if we're looking for recent data
                    elif not dt and target_date.date() == datetime.now(timezone.utc).date():
                        records.append(rec)
                        
                except json.JSONDecodeError as e:
                    if line_num <= 5:  # Only warn for first few errors
                        print(f"  Warning: JSON decode error line {line_num}: {e}", file=sys.stderr)
                    continue
                except Exception as e:
                    if line_num <= 5:
                        print(f"  Warning: Error parsing line {line_num}: {e}", file=sys.stderr)
                    continue
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    return records

def analyze_real_data(fetched_files: Dict[str, Path], target_date: datetime) -> Dict[str, Any]:
    """Analyze real data from droplet"""
    print(f"\nAnalyzing data for {target_date.date()}...", file=sys.stderr)
    
    # Load all data
    executed_trades = []
    blocked_trades = []
    exit_events = []
    signals = []
    orders = []
    gate_events = []
    uw_attribution = []
    
    if "attribution" in fetched_files:
        executed_trades = load_jsonl_file(fetched_files["attribution"], target_date)
        print(f"  Executed trades: {len(executed_trades)}", file=sys.stderr)
    
    if "blocked_trades" in fetched_files:
        blocked_trades = load_jsonl_file(fetched_files["blocked_trades"], target_date)
        print(f"  Blocked trades: {len(blocked_trades)}", file=sys.stderr)
    
    if "exit" in fetched_files:
        exit_events = load_jsonl_file(fetched_files["exit"], target_date)
        print(f"  Exit events: {len(exit_events)}", file=sys.stderr)
    
    if "signals" in fetched_files:
        signals = load_jsonl_file(fetched_files["signals"], target_date)
        print(f"  Signals: {len(signals)}", file=sys.stderr)
    
    if "orders" in fetched_files:
        orders = load_jsonl_file(fetched_files["orders"], target_date)
        print(f"  Orders: {len(orders)}", file=sys.stderr)
    
    if "gate" in fetched_files:
        gate_events = load_jsonl_file(fetched_files["gate"], target_date)
        print(f"  Gate events: {len(gate_events)}", file=sys.stderr)
    
    if "uw_attribution" in fetched_files:
        uw_attribution = load_jsonl_file(fetched_files["uw_attribution"], target_date)
        print(f"  UW attribution: {len(uw_attribution)}", file=sys.stderr)
    
    # Analyze executed trades
    total_pnl_usd = sum(float(t.get("pnl_usd", 0) or 0) for t in executed_trades)
    total_pnl_pct = sum(float(t.get("pnl_pct", 0) or 0) for t in executed_trades)
    wins = [t for t in executed_trades if t.get("pnl_usd", 0) > 0 or t.get("pnl_pct", 0) > 0]
    losses = [t for t in executed_trades if t.get("pnl_usd", 0) < 0 or t.get("pnl_pct", 0) < 0]
    
    # Analyze blocked trades
    blocked_by_reason = defaultdict(int)
    for blocked in blocked_trades:
        reason = blocked.get("reason", "unknown")
        blocked_by_reason[reason] += 1
    
    # Analyze gate events
    gate_by_type = defaultdict(int)
    for gate in gate_events:
        gate_type = gate.get("gate_type") or gate.get("gate_name") or gate.get("decision") or "unknown"
        gate_by_type[gate_type] += 1
    
    report = {
        "report_date": target_date.date().isoformat(),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "Droplet (Production Server)",
        "executed_trades": {
            "count": len(executed_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / len(executed_trades) * 100) if executed_trades else 0.0,
            "total_pnl_usd": total_pnl_usd,
            "total_pnl_pct": total_pnl_pct,
            "avg_pnl_pct": total_pnl_pct / len(executed_trades) if executed_trades else 0.0,
            "details": executed_trades[:100],  # Limit details
        },
        "blocked_trades": {
            "count": len(blocked_trades),
            "by_reason": dict(blocked_by_reason),
            "details": blocked_trades[:100],
        },
        "exit_events": {
            "count": len(exit_events),
            "details": exit_events[:50],
        },
        "signals": {
            "count": len(signals),
            "details": signals[:50],
        },
        "orders": {
            "count": len(orders),
            "details": orders[:50],
        },
        "gate_events": {
            "count": len(gate_events),
            "by_type": dict(gate_by_type),
            "details": gate_events[:100],
        },
        "uw_attribution": {
            "count": len(uw_attribution),
            "blocked": len([u for u in uw_attribution if u.get("decision") == "rejected" or u.get("decision") == "ENTRY_BLOCKED"]),
            "details": uw_attribution[:50],
        },
    }
    
    return report

def format_report(report: Dict[str, Any]) -> str:
    """Format comprehensive report"""
    lines = []
    lines.append("=" * 100)
    lines.append(f"COMPREHENSIVE TRADING REVIEW - {report['report_date']}")
    lines.append("=" * 100)
    lines.append(f"Generated: {report['report_generated_at']}")
    lines.append(f"Data Source: {report['data_source']}")
    lines.append("")
    
    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 100)
    exec_trades = report["executed_trades"]
    lines.append(f"Executed Trades: {exec_trades['count']}")
    lines.append(f"  Win Rate: {exec_trades['win_rate']:.1f}% ({exec_trades['wins']}W / {exec_trades['losses']}L)")
    lines.append(f"  Total P&L: ${exec_trades['total_pnl_usd']:.2f} ({exec_trades['total_pnl_pct']:.2f}%)")
    lines.append(f"  Average P&L per Trade: {exec_trades['avg_pnl_pct']:.2f}%")
    lines.append("")
    
    # Blocked Trades
    blocked = report["blocked_trades"]
    lines.append(f"BLOCKED TRADES: {blocked['count']} total")
    if blocked['by_reason']:
        lines.append("Blocked by Reason:")
        for reason, count in sorted(blocked['by_reason'].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {reason}: {count}")
    lines.append("")
    
    # Gate Events
    gates = report["gate_events"]
    lines.append(f"GATE EVENTS: {gates['count']} total")
    if gates['by_type']:
        lines.append("Gate Events by Type:")
        for gate_type, count in sorted(gates['by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {gate_type}: {count}")
    lines.append("")
    
    # Signals
    signals = report["signals"]
    lines.append(f"SIGNALS: {signals['count']} generated")
    execution_rate = (exec_trades['count'] / signals['count'] * 100) if signals['count'] > 0 else 0.0
    lines.append(f"Execution Rate: {execution_rate:.1f}%")
    lines.append("")
    
    # UW Attribution
    uw = report["uw_attribution"]
    lines.append(f"UW ATTRIBUTION: {uw['count']} total, {uw['blocked']} blocked")
    lines.append("")
    
    lines.append("=" * 100)
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch real data from Droplet and generate report")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now(timezone.utc)
    
    # Fetch data from Droplet
    fetched_files = fetch_all_data_from_droplet()
    
    if not fetched_files:
        print("ERROR: Could not fetch any data from Droplet", file=sys.stderr)
        sys.exit(1)
    
    # Analyze data
    report = analyze_real_data(fetched_files, target_date)
    
    # Format output
    if args.json:
        output = json.dumps(report, indent=2, default=str)
    else:
        output = format_report(report)
    
    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nReport written to {args.output}", file=sys.stderr)
    else:
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode('ascii', 'replace').decode('ascii'))

if __name__ == "__main__":
    main()
