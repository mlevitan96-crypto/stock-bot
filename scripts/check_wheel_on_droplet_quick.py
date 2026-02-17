#!/usr/bin/env python3
"""Quick wheel engine check on droplet: event counts, last run_started, worker log, service."""
from pathlib import Path
import sys
REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

def main():
    from droplet_client import DropletClient
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && "
        "echo '=== WHEEL EVENT COUNTS ===' && "
        "grep '\"subsystem\": \"wheel\"' logs/system_events.jsonl 2>/dev/null | grep -o '\"event_type\": \"[^\"]*\"' | sort | uniq -c || echo 'No wheel events'; "
        "echo '' && echo '=== LAST 3 wheel_run_started ===' && "
        "grep '\"event_type\": \"wheel_run_started\"' logs/system_events.jsonl 2>/dev/null | tail -3 || echo 'None'; "
        "echo '' && echo '=== LAST wheel_order_submitted / wheel_order_filled ===' && "
        "grep -E 'wheel_order_submitted|wheel_order_filled' logs/system_events.jsonl 2>/dev/null | tail -3 || echo 'None'; "
        "echo '' && echo '=== WORKER DEBUG (last 12 lines) ===' && "
        "tail -12 logs/worker_debug.log 2>/dev/null || echo 'No worker_debug.log'; "
        "echo '' && echo '=== SERVICE ===' && "
        "systemctl is-active stock-bot 2>/dev/null; systemctl show stock-bot -p ActiveEnterTimestamp --value 2>/dev/null; "
        "echo '' && echo '=== WHEEL ENABLED ===' && "
        "python3 -c \"import yaml; from pathlib import Path; p=Path('config/strategies.yaml'); c=yaml.safe_load(p.open()) if p.exists() else {}; print('wheel.enabled:', c.get('strategies',{}).get('wheel',{}).get('enabled'))\" 2>/dev/null || echo 'N/A'"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=90)
    print(out or "")
    if err:
        print("STDERR:", err, file=sys.stderr)
    return 0 if rc == 0 else rc

if __name__ == "__main__":
    sys.exit(main())
