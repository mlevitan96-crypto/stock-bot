#!/bin/bash
# Analyze diagnostics and create comprehensive report for GitHub

set +e

DIAG_DIR="diagnostics_20251223-214828"
REPORT_FILE="DIAGNOSTIC_ANALYSIS_REPORT.json"

if [ ! -d "$DIAG_DIR" ]; then
    echo "❌ Diagnostics directory not found: $DIAG_DIR"
    exit 1
fi

echo "Analyzing diagnostics and creating report..."

python3 << 'PYTHON_EOF' > "$REPORT_FILE"
import json
from pathlib import Path
from datetime import datetime, timezone

diag_dir = Path("diagnostics_20251223-214828")
report = {
    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
    "diagnostics_directory": str(diag_dir),
    "findings": {}
}

# 1. Dashboard API Analysis
dashboard_apis = {}
api_dir = diag_dir / "dashboard_apis"
if api_dir.exists():
    for api_file in api_dir.glob("*.json"):
        try:
            data = json.loads(api_file.read_text())
            api_name = api_file.stem
            dashboard_apis[api_name] = {
                "status": "ok" if "error" not in str(data) else "error",
                "data_preview": str(data)[:200] if isinstance(data, dict) else str(data)[:200]
            }
            
            # Specific analysis for health_status
            if api_name == "health_status" and isinstance(data, dict):
                last_order = data.get("last_order", {})
                doctor = data.get("doctor", {})
                dashboard_apis[api_name]["analysis"] = {
                    "last_order_age_hours": last_order.get("age_hours"),
                    "last_order_status": last_order.get("status"),
                    "doctor_age_minutes": doctor.get("age_minutes"),
                    "doctor_status": doctor.get("status")
                }
        except Exception as e:
            dashboard_apis[api_file.stem] = {"error": str(e)}

report["findings"]["dashboard_apis"] = dashboard_apis

# 2. SRE Health Analysis
sre_health = {}
sre_dir = diag_dir / "sre"
if sre_dir.exists():
    sre_file = sre_dir / "sre_health_direct.json"
    if sre_file.exists():
        try:
            data = json.loads(sre_file.read_text())
            if "error" not in data:
                sre_health["status"] = "ok"
                sre_health["market_open"] = data.get("market_open", "unknown")
                sre_health["bot_running"] = data.get("bot_process", {}).get("running", False)
                sre_health["last_order_age_hours"] = data.get("last_order", {}).get("age_hours")
                sre_health["comprehensive_learning"] = data.get("comprehensive_learning", {})
            else:
                sre_health["status"] = "error"
                sre_health["error"] = data.get("error")
        except Exception as e:
            sre_health["error"] = str(e)

report["findings"]["sre_health"] = sre_health

# 3. Process Status
process_status = {}
hb_dir = diag_dir / "heartbeats"
if hb_dir.exists():
    proc_file = hb_dir / "process_status.json"
    if proc_file.exists():
        try:
            data = json.loads(proc_file.read_text())
            processes = data.get("processes", {})
            process_status = {
                "main_py_running": processes.get("main.py", {}).get("running", False),
                "dashboard_py_running": processes.get("dashboard.py", {}).get("running", False)
            }
        except Exception as e:
            process_status["error"] = str(e)

report["findings"]["process_status"] = process_status

# 4. Heartbeat Files
heartbeats = {}
if hb_dir.exists():
    for hb_file in hb_dir.glob("*.json"):
        if hb_file.name != "process_status.json":
            try:
                data = json.loads(hb_file.read_text())
                hb_ts = data.get("last_heartbeat_ts") or data.get("timestamp") or data.get("_ts")
                if hb_ts:
                    import time
                    age_sec = time.time() - float(hb_ts)
                    heartbeats[hb_file.name] = {
                        "timestamp": hb_ts,
                        "age_seconds": age_sec,
                        "age_minutes": age_sec / 60,
                        "age_hours": age_sec / 3600
                    }
            except:
                pass

report["findings"]["heartbeats"] = heartbeats

# 5. Summary & Recommendations
issues = []
recommendations = []

# Check for stale data
if dashboard_apis.get("health_status", {}).get("analysis", {}).get("doctor_age_minutes", 0) > 60:
    issues.append("Doctor/heartbeat is stale (>60 minutes)")
    recommendations.append("Check if bot is generating heartbeats - verify heartbeat() is being called")

if dashboard_apis.get("health_status", {}).get("analysis", {}).get("last_order_age_hours", 0) > 24:
    issues.append("Last order is very old (>24 hours)")
    recommendations.append("Check if bot is processing signals and submitting orders")

if not process_status.get("main_py_running", False):
    issues.append("main.py process is not running")
    recommendations.append("Restart the bot using RESTART_BOT_NOW.sh")

if not process_status.get("dashboard_py_running", False):
    issues.append("dashboard.py process is not running")
    recommendations.append("Restart dashboard: pkill -f dashboard.py && python3 dashboard.py > logs/dashboard.log 2>&1 &")

if sre_health.get("status") == "error":
    issues.append("SRE health check failed")
    recommendations.append("Check sre_monitoring.py for errors")

report["issues"] = issues
report["recommendations"] = recommendations

print(json.dumps(report, indent=2, default=str))
PYTHON_EOF

echo "✅ Analysis complete: $REPORT_FILE"
echo ""
echo "Report summary:"
python3 -c "import json; r=json.load(open('$REPORT_FILE')); print(f\"Issues found: {len(r.get('issues', []))}\"); [print(f\"  - {i}\") for i in r.get('issues', [])]"
