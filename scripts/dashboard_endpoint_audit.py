#!/usr/bin/env python3
"""
Dashboard endpoint audit — runs ON THE DROPLET (or locally).
Calls each endpoint from data/dashboard_panel_inventory.json, validates status/schema/freshness,
classifies failures (ROUTE_MISSING, EXCEPTION, SCHEMA_MISMATCH, STALE_DATA, EMPTY_DATA, SOURCE_MISSING, PERMISSION_ERROR).
Writes: reports/DASHBOARD_ENDPOINT_AUDIT.md, reports/DASHBOARD_TELEMETRY_DIAGNOSIS.md, reports/DASHBOARD_PANEL_INVENTORY.md
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
INVENTORY_PATH = DATA_DIR / "dashboard_panel_inventory.json"

# Prefer localhost (dashboard on same host)
BASE_URL = "http://127.0.0.1:5000"


def _get_auth() -> Optional[Tuple[str, str]]:
    import os
    u = os.getenv("DASHBOARD_USER", "").strip()
    p = os.getenv("DASHBOARD_PASS", "").strip()
    return (u, p) if u and p else None


def _load_inventory() -> Dict[str, Any]:
    if not INVENTORY_PATH.exists():
        return {"tabs": [], "standalone_endpoints": [], "generated_at_utc": ""}
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_dotenv_if_present() -> None:
    """Load ROOT/.env so DASHBOARD_USER/PASS are set when audit runs on droplet (localhost calls need Basic auth)."""
    import os
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in ("DASHBOARD_USER", "DASHBOARD_PASS") and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


def _http_get(url: str, timeout: int = 10, auth: Optional[Tuple[str, str]] = None) -> Tuple[int, float, Optional[dict], Optional[str], Optional[str]]:
    """Returns (status_code, latency_sec, json_data, raw_text, error_message)."""
    try:
        import urllib.request
        import urllib.error
        import base64
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        if auth:
            creds = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        latency = time.perf_counter() - start
        try:
            data = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            data = None
        return (getattr(resp, "status", 200), latency, data, raw[:2000], None)
    except Exception as e:
        err_msg = str(e)
        # Preserve HTTP status for 4xx/5xx (urllib raises HTTPError)
        try:
            import urllib.error
            if isinstance(e, urllib.error.HTTPError):
                raw = e.read().decode("utf-8", errors="replace")[:2000] if e.fp else None
                data_404 = None
                if raw:
                    try:
                        data_404 = json.loads(raw) if raw.strip() else None
                    except json.JSONDecodeError:
                        pass
                return (e.code, 0.0, data_404, raw, err_msg)
        except Exception:
            pass
        if hasattr(e, "code"):
            return (e.code, 0.0, None, None, err_msg)
        if "404" in err_msg or "Not Found" in err_msg:
            return (404, 0.0, None, None, err_msg)
        if "401" in err_msg or "UNAUTHORIZED" in err_msg.upper():
            return (401, 0.0, None, None, err_msg)
        if "500" in err_msg or "Internal Server" in err_msg:
            return (500, 0.0, None, None, err_msg)
        if "Connection refused" in err_msg or "ConnectionError" in err_msg:
            return (0, 0.0, None, None, err_msg)
        return (0, 0.0, None, None, err_msg)


def _check_freshness(data: dict, expected_keys_ts: List[str], max_age_sec: Optional[int]) -> Tuple[str, Optional[float]]:
    """Returns (status, age_sec). status: 'fresh' | 'stale' | 'unknown'."""
    age_sec = None
    for key in expected_keys_ts:
        val = data.get(key)
        if val is None:
            continue
        ts = None
        if isinstance(val, (int, float)) and val > 1e9:
            ts = float(val)
        elif isinstance(val, str):
            try:
                from datetime import datetime as dt
                dt.fromisoformat(val.replace("Z", "+00:00"))
                # approximate: use string if looks like ISO
                ts = time.time() - 3600  # placeholder
            except Exception:
                pass
        if ts and ts > 1e9:
            age_sec = time.time() - ts
            break
    if age_sec is None and "as_of_ts" in data:
        try:
            s = data["as_of_ts"]
            from datetime import datetime as dt
            d = dt.fromisoformat(s.replace("Z", "+00:00"))
            if d.tzinfo is None:
                import datetime as dto
                d = d.replace(tzinfo=dto.timezone.utc)
            age_sec = time.time() - d.timestamp()
        except Exception:
            pass
    if age_sec is None:
        return ("unknown", age_sec)
    if max_age_sec and age_sec > max_age_sec:
        return ("stale", age_sec)
    return ("fresh", age_sec)


def _classify_failure(status_code: int, data: Optional[dict], err: Optional[str]) -> str:
    if status_code == 404:
        # 404 with error body "artifact missing" etc. = route exists, data missing
        err_msg = (data.get("error", "") if data else "") or (err or "")
        if "missing" in err_msg.lower() or "artifact" in err_msg.lower():
            return "SOURCE_MISSING"
        return "ROUTE_MISSING"
    if status_code == 401:
        return "PERMISSION_ERROR"
    if status_code >= 500:
        return "EXCEPTION"
    if err and ("Permission" in err or "403" in err):
        return "PERMISSION_ERROR"
    if data is None and err:
        return "EXCEPTION"
    if data is not None:
        if data.get("error") and "missing" in str(data.get("error", "")).lower():
            return "SOURCE_MISSING"
        if data.get("error") and "not found" in str(data.get("error", "")).lower():
            return "SOURCE_MISSING"
    return "SCHEMA_MISMATCH"


def _validate_schema(data: dict, expected: Dict[str, str]) -> List[str]:
    """expected: key -> type name ('array','object','number','string','boolean'). Returns list of missing/mismatch keys."""
    issues = []
    for key, typ in expected.items():
        if key not in data:
            issues.append(f"missing:{key}")
            continue
        val = data[key]
        if typ == "array" and not isinstance(val, list):
            issues.append(f"type:{key}=array")
        elif typ == "object" and not isinstance(val, dict):
            issues.append(f"type:{key}=object")
        elif typ == "number" and not isinstance(val, (int, float)):
            issues.append(f"type:{key}=number")
        elif typ == "string" and not isinstance(val, str):
            issues.append(f"type:{key}=string")
        elif typ == "boolean" and not isinstance(val, bool):
            issues.append(f"type:{key}=boolean")
    return issues


def audit_endpoint(
    route: str,
    query_params: Optional[Dict[str, str]] = None,
    expected_schema: Optional[Dict[str, str]] = None,
    freshness_sla_sec: Optional[int] = None,
    panel_name: str = "",
    tab_name: str = "",
) -> Dict[str, Any]:
    url = BASE_URL + route
    if query_params:
        q = {k: v for k, v in query_params.items() if v}
        if q:
            url += "?" + urlencode(q)
    auth = _get_auth()
    status_code, latency, data, raw, err = _http_get(url, auth=auth)
    result = {
        "panel": panel_name,
        "tab": tab_name,
        "endpoint": route,
        "url": url,
        "status_code": status_code,
        "latency_ms": round(latency * 1000, 1),
        "result": "PASS",
        "reason_code": "",
        "freshness": "",
        "notes": "",
        "schema_issues": [],
        "response_excerpt": None,
        "traceback_snippet": None,
    }
    if status_code == 0:
        result["result"] = "FAIL"
        result["reason_code"] = "CONNECTION_REFUSED" if "refused" in (err or "").lower() else "EXCEPTION"
        result["notes"] = err or "Connection failed"
        return result
    if status_code != 200:
        result["reason_code"] = _classify_failure(status_code, data, err)
        # 404 with artifact/data missing = route exists, treat as WARN not FAIL
        if status_code == 404 and result["reason_code"] == "SOURCE_MISSING":
            result["result"] = "WARN"
        else:
            result["result"] = "FAIL"
        result["notes"] = err or data.get("error", "") if data else ""
        result["response_excerpt"] = (raw or (json.dumps(data)[:500] if data else ""))[:500]
        return result
    if data is None:
        result["result"] = "FAIL"
        result["reason_code"] = "SCHEMA_MISMATCH"
        result["notes"] = "Response not valid JSON"
        result["response_excerpt"] = (raw or "")[:500]
        return result
    # 200 + JSON (data may be list for some endpoints)
    if not isinstance(data, dict):
        if result["result"] == "PASS":
            result["reason_code"] = "OK"
        return result
    if expected_schema:
        result["schema_issues"] = _validate_schema(data, expected_schema)
        if result["schema_issues"]:
            result["result"] = "WARN" if result["result"] == "PASS" else result["result"]
            result["reason_code"] = "SCHEMA_MISMATCH"
            result["notes"] = "Schema issues: " + ", ".join(result["schema_issues"])
    # Empty but expected vs wrong
    if isinstance(data.get("events"), list) and len(data["events"]) == 0:
        result["notes"] = (result["notes"] + "; empty events list (allowed)").strip(" ;")
    if isinstance(data.get("signals"), list) and len(data["signals"]) == 0:
        result["notes"] = (result["notes"] + "; no signals yet (allowed)").strip(" ;")
    if data.get("error") and result["result"] == "PASS":
        result["result"] = "WARN"
        result["reason_code"] = "EMPTY_DATA"
        result["notes"] = data.get("error", "")
    # Freshness
    if freshness_sla_sec:
        fresh_status, age_sec = _check_freshness(
            data,
            ["timestamp", "ts", "generated_at_utc", "as_of_ts", "last_order"],
            freshness_sla_sec,
        )
        result["freshness"] = f"{fresh_status}" + (f" (age_sec={round(age_sec, 1)})" if age_sec is not None else "")
        if fresh_status == "stale" and result["result"] == "PASS":
            result["result"] = "WARN"
            result["reason_code"] = "STALE_DATA"
    if result["result"] == "PASS" and not result["reason_code"]:
        result["reason_code"] = "OK"
    return result


def run_telemetry_diagnosis(results: List[Dict[str, Any]]) -> List[str]:
    """Produce Telemetry tab diagnosis lines."""
    lines = []
    telemetry_endpoints = [
        "/api/telemetry/latest/index",
        "/api/telemetry/latest/computed",
        "/api/telemetry/latest/health",
    ]
    for r in results:
        if r["endpoint"] not in telemetry_endpoints:
            continue
        lines.append(f"- **{r['endpoint']}**: {r['result']} — {r['reason_code']} — {r.get('notes', '')}")
        if r.get("response_excerpt"):
            lines.append(f"  Excerpt: {r['response_excerpt'][:200]}...")
    # Check evidence paths
    tdir = ROOT / "telemetry"
    if not tdir.exists():
        lines.append("- Evidence: telemetry/ directory missing.")
    else:
        dirs = [p for p in tdir.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == "-"]
        if not dirs:
            lines.append("- Evidence: No telemetry/YYYY-MM-DD date dirs.")
        else:
            latest = sorted(dirs, key=lambda p: p.name)[-1]
            comp = latest / "computed"
            if not comp.exists():
                lines.append(f"- Evidence: {latest.name}/computed missing.")
            else:
                artifacts = list(comp.glob("*.json"))
                lines.append(f"- Evidence: Latest {latest.name}, computed artifacts: {len(artifacts)}.")
    return lines


def main() -> int:
    _load_dotenv_if_present()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    inv = _load_inventory()
    inv["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2)
    results: List[Dict[str, Any]] = []
    # Build flat list of (route, query_params, expected_schema, freshness_sla, panel, tab)
    for tab in inv.get("tabs", []):
        tab_name = tab.get("tab", "")
        for panel in tab.get("panels", []):
            panel_name = panel.get("panel", "")
            freshness = panel.get("freshness_sla_sec")
            for ep in panel.get("endpoints", []):
                route = ep.get("route", "")
                if not route:
                    continue
                qparams = ep.get("query_params") or []
                # Resolve expected_schema by route
                if route == "/api/telemetry/latest/index":
                    expected = panel.get("expected_schema_index") or {}
                elif route == "/api/telemetry/latest/computed":
                    expected = panel.get("expected_schema_computed") or {}
                elif route == "/api/telemetry/latest/health":
                    expected = panel.get("expected_schema_health") or {}
                elif route == "/api/positions":
                    expected = panel.get("expected_schema_positions") or {}
                elif route == "/api/health_status":
                    expected = panel.get("expected_schema_health_status") or {}
                elif route == "/api/sre/self_heal_events":
                    expected = panel.get("expected_schema_self_heal") or {"events": "array", "count": "number"}
                else:
                    expected = panel.get("expected_schema") or panel.get("expected_schema_sre_health") or panel.get("expected_schema_auditor") or {}
                if route == "/api/telemetry/latest/computed":
                    qparams_dict = {"name": "live_vs_shadow_pnl"}
                else:
                    qparams_dict = {}
                r = audit_endpoint(route, qparams_dict, expected, freshness, panel_name, tab_name)
                results.append(r)
    _version_schema = {
        "service": "string",
        "git_commit": "string",
        "git_commit_short": "string",
        "build_time_utc": "string",
        "process_start_time_utc": "string",
        "python_version": "string",
        "cwd": "string",
    }
    for ep in inv.get("standalone_endpoints", []):
        route = ep.get("route", "")
        if not route:
            continue
        qparams = ep.get("query_params") or []
        qparams_dict = {}
        if "name" in qparams and route == "/api/telemetry/latest/computed":
            qparams_dict["name"] = "live_vs_shadow_pnl"
        expected_schema = _version_schema if route == "/api/version" else None
        r = audit_endpoint(route, qparams_dict, expected_schema, None, "", "")
        results.append(r)
    # Dedupe by endpoint (keep first)
    seen = set()
    unique_results = []
    for r in results:
        key = (r["endpoint"], r.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_results.append(r)
    results = unique_results
    # Version drift check: compare /api/version git_commit to EXPECTED_GIT_COMMIT
    import os
    expected_commit = os.getenv("EXPECTED_GIT_COMMIT", "").strip()
    version_result = next((r for r in results if r.get("endpoint") == "/api/version"), None)
    if version_result is not None:
        url = BASE_URL + "/api/version"
        auth = _get_auth()
        status_code, _, data, _, _ = _http_get(url, auth=auth)
        if status_code == 200 and data:
            running_commit = (data.get("git_commit") or "").strip()
            version_result["git_commit"] = running_commit
            version_result["process_start_time_utc"] = data.get("process_start_time_utc") or ""
            if expected_commit and running_commit != expected_commit:
                version_result["result"] = "FAIL"
                version_result["reason_code"] = "PROCESS_DRIFT"
                version_result["notes"] = f"running={running_commit} expected={expected_commit}"
                version_result["expected_git_commit"] = expected_commit
    # Summary
    pass_count = sum(1 for r in results if r["result"] == "PASS")
    warn_count = sum(1 for r in results if r["result"] == "WARN")
    fail_count = sum(1 for r in results if r["result"] == "FAIL")
    # Version / commit parity section for report
    version_result = next((r for r in results if r.get("endpoint") == "/api/version"), None)
    running_commit = (version_result.get("git_commit") or "").strip() if version_result else ""
    expected_commit_report = expected_commit or "(not set)"

    # Write DASHBOARD_ENDPOINT_AUDIT.md
    lines = [
        "# Dashboard Endpoint Audit",
        "",
        "**Generated:** " + datetime.now(timezone.utc).isoformat() + " (UTC)",
        "**Base URL:** " + BASE_URL,
        "",
        "---",
        "",
        "## Version / commit parity",
        "",
        "- **Running dashboard commit:** " + (running_commit or "(unknown)"),
        "- **Expected commit:** " + expected_commit_report,
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Result | Count |",
        f"|--------|-------|",
        f"| PASS | {pass_count} |",
        f"| WARN | {warn_count} |",
        f"| FAIL | {fail_count} |",
        "",
        "| Panel / Endpoint | Result | reason_code | Freshness | Notes |",
        "|------------------|--------|-------------|-----------|-------|",
    ]
    for r in results:
        panel = (r.get("tab") or "") + " / " + (r.get("panel") or r.get("endpoint", ""))
        lines.append(f"| {panel} | {r['result']} | {r.get('reason_code', '')} | {r.get('freshness', '')} | {str(r.get('notes', ''))[:80]} |")
    lines.append("")
    lines.append("## Failing endpoints (detail)")
    lines.append("")
    for r in results:
        if r["result"] != "FAIL":
            continue
        lines.append(f"### {r['endpoint']}")
        lines.append(f"- Status: {r['status_code']}, Latency: {r['latency_ms']} ms")
        lines.append(f"- reason_code: {r['reason_code']}")
        lines.append(f"- Notes: {r.get('notes', '')}")
        if r.get("response_excerpt"):
            lines.append(f"- Response excerpt (redacted): `{r['response_excerpt'][:300]}...`")
        lines.append("")
    (REPORTS_DIR / "DASHBOARD_ENDPOINT_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    # Telemetry diagnosis
    diag_lines = [
        "# Dashboard Telemetry Diagnosis",
        "",
        "**Generated:** " + datetime.now(timezone.utc).isoformat(),
        "",
        "---",
        "",
        "## Telemetry tab endpoints",
        "",
    ]
    diag_lines.extend(run_telemetry_diagnosis(results))
    diag_lines.append("")
    diag_lines.append("## Root cause classification")
    diag_lines.append("")
    diag_lines.append("1. UI calling wrong endpoint — check frontend fetch URLs.")
    diag_lines.append("2. Backend reading wrong file/log — check dashboard.py route handlers.")
    diag_lines.append("3. Schema mismatch causing UI to drop — check expected_schema vs response.")
    diag_lines.append("4. Data filtered out (time/symbol) — check query params and backend filters.")
    diag_lines.append("5. Data not produced (artifact missing) — check telemetry pipeline / reports.")
    (REPORTS_DIR / "DASHBOARD_TELEMETRY_DIAGNOSIS.md").write_text("\n".join(diag_lines), encoding="utf-8")
    # Panel inventory markdown (from inventory + audit summary)
    inv_lines = [
        "# Dashboard Panel Inventory",
        "",
        "**Generated:** " + datetime.now(timezone.utc).isoformat(),
        "",
        "---",
        "",
        "## Tabs and panels",
        "",
    ]
    for tab in inv.get("tabs", []):
        inv_lines.append(f"## Tab: {tab.get('tab', '')}")
        inv_lines.append("")
        for panel in tab.get("panels", []):
            inv_lines.append(f"### {panel.get('panel', '')}")
            inv_lines.append("- **Endpoints:**")
            for ep in panel.get("endpoints", []):
                inv_lines.append(f"  - `{ep.get('route', '')}` ({ep.get('method', 'GET')})")
            inv_lines.append("- **Evidence sources:** " + ", ".join(panel.get("evidence_sources", [])))
            inv_lines.append("- **Freshness SLA:** " + str(panel.get("freshness_sla_sec", "")) + " sec")
            inv_lines.append("")
    (REPORTS_DIR / "DASHBOARD_PANEL_INVENTORY.md").write_text("\n".join(inv_lines), encoding="utf-8")
    print(f"PASS={pass_count} WARN={warn_count} FAIL={fail_count}")
    for r in results:
        if r["result"] == "FAIL":
            print(f"FAIL {r['endpoint']} {r['reason_code']}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
