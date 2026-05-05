#!/usr/bin/env python3
"""
Position Dashboard - Fast Start Version
Binds port **5005** (sovereign Command Desk; firewall/DNS target). Ignores ``PORT`` env for bind selection, then lazy-loads heavy dependencies.

IMPORTANT: For project context, common issues, and solutions, see MEMORY_BANK_ALPACA.md
"""

import os
import sys
import json
import subprocess
import threading
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure repo root is on path and cwd so state/logs paths resolve (e.g. systemd may start with different cwd)
_DASHBOARD_ROOT = Path(__file__).resolve().parent
TELEMETRY_ROOT = _DASHBOARD_ROOT / "telemetry"
if str(_DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_ROOT))
try:
    os.chdir(_DASHBOARD_ROOT)
except Exception:
    pass

# When false (default), GET / requires HTTP Basic Auth so the browser attaches Authorization
# to same-origin fetches (/api/positions, header strip, etc.). Set DASHBOARD_ALLOW_PUBLIC_HTML=1
# to allow unauthenticated HTML (legacy proxies); protected APIs still require auth.
_DASHBOARD_ALLOW_PUBLIC_HTML = os.getenv("DASHBOARD_ALLOW_PUBLIC_HTML", "").strip().lower() in ("1", "true", "yes")

# Process-start timestamps for /api/version (source of truth for build/version contract)
_BUILD_TIME_UTC = datetime.now(timezone.utc).isoformat()
_PROCESS_START_TIME_UTC = _BUILD_TIME_UTC

# Optional env checks (non-blocking)
_FLASK_AVAILABLE = True
try:
    import flask  # type: ignore
except Exception:
    _FLASK_AVAILABLE = False
    print("WARNING: Flask not installed in this environment; dashboard endpoints cannot be simulated locally.", flush=True)

try:
    from flask import Flask, render_template, render_template_string, jsonify, Response, request, send_from_directory
except Exception:
    _FLASK_AVAILABLE = False
    # Provide a minimal stub so `import dashboard` works for local audits.
    Flask = None  # type: ignore
    Response = None  # type: ignore
    request = None  # type: ignore
    def jsonify(obj=None, **kwargs):  # type: ignore
        return obj if obj is not None else kwargs
    def render_template_string(*args, **kwargs):  # type: ignore
        return ""

    def render_template(*args, **kwargs):  # type: ignore
        return ""

    def send_from_directory(*args, **kwargs):  # type: ignore
        return ""

    class _DummyApp:
        def route(self, *args, **kwargs):
            def _decorator(fn):
                return fn
            return _decorator
        def run(self, *args, **kwargs):
            print("WARNING: Flask not installed; dashboard cannot run.", flush=True)
        def test_client(self, *args, **kwargs):
            raise RuntimeError("Flask not installed; test_client unavailable.")

    app = _DummyApp()
else:
    print("[Dashboard] Starting Flask app...", flush=True)
    app = Flask(__name__, template_folder=str(_DASHBOARD_ROOT / "templates"))
    # Static SPA / send_from_directory: avoid default immutable caching hints in downstream caches.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    def _load_dotenv_if_available() -> None:
        """
        Best-effort: load ``<repo>/.env`` so manual dashboard starts inherit secrets.

        WHY:
        - MEMORY_BANK_ALPACA.md allows manual `nohup python3 dashboard.py ...` starts.
        - The dashboard auth contract requires DASHBOARD_USER/PASS in the repo ``.env``.
        """
        try:
            from dotenv import load_dotenv  # type: ignore
        except Exception:
            return
        try:
            env_path = _DASHBOARD_ROOT / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=True)
        except Exception:
            return

    # ===========================
    # SECURITY: HTTP BASIC AUTH
    # ===========================
    #
    # Contract:
    # - Must protect ALL routes (HTML + APIs) before any content loads.
    # - Must NOT hardcode credentials.
    # - Must be fail-closed on startup if env vars missing (enforced in __main__).
    #
    def _unauthorized_response():
        return Response(
            "Authentication required",
            401,
            {"WWW-Authenticate": 'Basic realm="stock-bot-dashboard"'},
        )

    @app.before_request
    def _enforce_basic_auth():  # type: ignore
        try:
            # Public read-only JSON (no secrets). HTML "/" is public only if DASHBOARD_ALLOW_PUBLIC_HTML=1.
            _public_get = {
                "/api/direction_banner",
                "/api/situation",
                "/api/telemetry_health",
                "/api/dashboard/data_integrity",
                "/api/learning_readiness",
                "/api/profitability_learning",
                "/api/alpaca_operational_activity",
            }
            if request.method == "GET" and (
                request.path in _public_get or (_DASHBOARD_ALLOW_PUBLIC_HTML and request.path == "/")
            ):
                return None

            # Validate env contract at request time too (defensive).
            # Primary fail-closed enforcement is in __main__ before binding the port.
            from config.registry import DashboardAuthConfig
            DashboardAuthConfig.validate_or_die()

            expected_user = os.getenv("DASHBOARD_USER", "")
            expected_pass = os.getenv("DASHBOARD_PASS", "")

            auth = request.authorization
            if not auth:
                return _unauthorized_response()

            # Constant-time comparisons to avoid timing side-channels.
            if not secrets.compare_digest(str(auth.username or ""), str(expected_user)):
                return _unauthorized_response()
            if not secrets.compare_digest(str(auth.password or ""), str(expected_pass)):
                return _unauthorized_response()
            return None
        except SystemExit:
            raise
        except Exception:
            # Fail closed on unexpected auth errors.
            return _unauthorized_response()

    @app.after_request
    def _disable_cache_for_dashboard_ui(response):  # type: ignore
        """Defeat browser/CDN caching for HTML and JS so dashboard UI updates are visible immediately."""
        try:
            path = getattr(request, "path", "") or ""
            ct = (response.headers.get("Content-Type") or "").lower()
            ui_path = path == "/" or path.startswith("/static/")
            ui_ct = "text/html" in ct or "javascript" in ct
            if ui_path or ui_ct:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        except Exception:
            pass
        return response


_alpaca_api = None
_registry_loaded = False

# Short-lived memoization for hot dashboard reads (bounded polling load).
_DASH_TTL_SEC = 5.0
_dash_ttl_store: dict[str, tuple[float, object]] = {}
def _dash_cache_get(key: str, builder, *, ttl_sec: Optional[float] = None):
    now = time.monotonic()
    ent = _dash_ttl_store.get(key)
    ttl = _DASH_TTL_SEC if ttl_sec is None else float(ttl_sec)
    if ent is not None and (now - ent[0]) < ttl:
        return ent[1]
    val = builder()
    _dash_ttl_store[key] = (now, val)
    return val


def _dash_parse_limit(default: int = 50, cap: int = 500) -> int:
    try:
        raw = request.args.get("limit", default=default, type=int)  # type: ignore[union-attr]
    except Exception:
        return default
    if raw is None:
        return default
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, cap))

def lazy_load_dependencies():
    """Load heavy dependencies in background after server starts."""
    global _alpaca_api, _registry_loaded
    try:
        print("[Dashboard] Loading dependencies...", flush=True)
        
        from pathlib import Path
        Path("logs").mkdir(exist_ok=True)
        Path("state").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("config").mkdir(exist_ok=True)
        
        try:
            import alpaca_trade_api as tradeapi
            key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
            secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            if key and secret:
                _alpaca_api = tradeapi.REST(key, secret, base_url)
                print("[Dashboard] Alpaca API connected", flush=True)
        except Exception as e:
            print(f"[Dashboard] Alpaca not available: {e}", flush=True)
        
        _registry_loaded = True
        print("[Dashboard] Dependencies loaded", flush=True)
    except Exception as e:
        print(f"[Dashboard] Error loading dependencies: {e}", flush=True)


SRE_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SRE Monitoring Dashboard - Trading Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        .header {
            background: #1e293b;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 2px solid #334155;
        }
        h1 { color: #60a5fa; font-size: 2em; margin-bottom: 10px; }
        .overall-health {
            background: #1e293b;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            border: 3px solid;
        }
        .overall-health.healthy { border-color: #10b981; background: #064e3b; }
        .overall-health.degraded { border-color: #f59e0b; background: #78350f; }
        .overall-health.critical { border-color: #ef4444; background: #7f1d1d; }
        .overall-health h2 { font-size: 2.5em; margin-bottom: 10px; }
        .overall-health.healthy h2 { color: #10b981; }
        .overall-health.degraded h2 { color: #f59e0b; }
        .overall-health.critical h2 { color: #ef4444; }
        .section {
            background: #1e293b;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        }
        .section h2 {
            color: #60a5fa;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 2px solid #334155;
            padding-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .health-card {
            background: #0f172a;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid;
            transition: transform 0.2s;
        }
        .health-card:hover { transform: translateY(-2px); }
        .health-card.healthy { border-color: #10b981; }
        .health-card.degraded { border-color: #f59e0b; }
        .health-card.critical { border-color: #ef4444; }
        .health-card.no_data { border-color: #64748b; }
        .health-card.unknown { border-color: #64748b; }
        .health-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .health-card-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #e2e8f0;
        }
        .health-status {
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }
        .health-status.healthy { background: #10b981; color: white; }
        .health-status.degraded { background: #f59e0b; color: white; }
        .health-status.critical { background: #ef4444; color: white; }
        .health-status.no_data { background: #64748b; color: white; }
        .health-status.unknown { background: #64748b; color: white; }
        .health-details {
            font-size: 0.9em;
            color: #94a3b8;
            line-height: 1.6;
        }
        .health-details strong { color: #e2e8f0; }
        .update-info {
            font-size: 0.85em;
            color: #94a3b8;
            margin-top: 10px;
        }
        .loading { text-align: center; padding: 40px; color: #94a3b8; }
        .nav-link {
            color: #60a5fa;
            text-decoration: none;
            font-weight: bold;
        }
        .nav-link:hover { text-decoration: underline; }
        .market-status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 600;
            margin-left: 10px;
        }
        .market-status.open { background: #10b981; color: white; }
        .market-status.closed { background: #64748b; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 SRE Monitoring Dashboard</h1>
            <p>Comprehensive system health monitoring for all signals, APIs, and trade engine</p>
            <p class="update-info">
                Auto-refresh: 10 seconds | Last update: <span id="last-update">-</span> | 
                <a href="/" class="nav-link">← Back to Positions Dashboard</a>
            </p>
        </div>
        
        <div id="overall-health" class="overall-health unknown">
            <h2>Loading...</h2>
            <p>Checking system health...</p>
        </div>
        
        <div class="section">
            <h2>📊 Signal Components Health</h2>
            <div id="signals-container" class="grid">
                <div class="loading">Loading signal components...</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🌐 UW API Endpoints Health</h2>
            <div id="api-container" class="grid">
                <div class="loading">Loading API endpoints...</div>
            </div>
        </div>
        
        <div class="section">
            <h2>⚙️ Trade Engine & Execution Pipeline</h2>
            <div id="engine-container" class="grid">
                <div class="loading">Loading trade engine status...</div>
            </div>
        </div>
    </div>
    
    <script>
        function formatTimeAgo(seconds) {
            if (!seconds && seconds !== 0) return 'N/A';
            if (seconds < 60) return Math.floor(seconds) + 's';
            if (seconds < 3600) return Math.floor(seconds / 60) + 'm';
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return hours + 'h ' + minutes + 'm';
        }
        
        function getStatusClass(status) {
            if (!status) return 'unknown';
            status = status.toLowerCase();
            if (status === 'healthy' || status === 'ok') return 'healthy';
            if (status === 'degraded' || status === 'warning') return 'degraded';
            if (status === 'critical' || status === 'down' || status === 'error') return 'critical';
            if (status === 'no_data' || status === 'no_api_key') return 'no_data';
            return 'unknown';
        }
        
        function updateSREDashboard() {
            fetch('/api/sre/health', { credentials: 'same-origin' })
                .then(response => { if (!response.ok) return Promise.reject(new Error('HTTP ' + response.status)); return response.json(); })
                .then(data => {
                    // Debug: Log UW endpoints to console
                    console.log('SRE Health Data:', data);
                    console.log('UW API Endpoints:', data.uw_api_endpoints);
                    
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    // Update overall health
                    const overallHealth = data.overall_health || 'unknown';
                    const botProcess = data.bot_process || {};
                    const botRunning = botProcess.running || false;
                    const botPid = botProcess.pid || null;
                    const botCheckMethod = botProcess.check_method || 'unknown';
                    
                    const overallEl = document.getElementById('overall-health');
                    overallEl.className = 'overall-health ' + getStatusClass(overallHealth);
                    overallEl.innerHTML = `
                        <h2>${overallHealth.toUpperCase()}</h2>
                        <p>Market: <span class="market-status ${data.market_open ? 'open' : 'closed'}">${data.market_status || 'unknown'}</span></p>
                        <p>Bot Process: <span class="market-status ${botRunning ? 'open' : 'closed'}">${botRunning ? 'RUNNING' : 'NOT RUNNING'}</span>${botPid ? ` (PID: ${botPid})` : ''}</p>
                        ${data.critical_issues ? '<p style="color: #ef4444; margin-top: 10px;"><strong>Critical Issues:</strong> ' + data.critical_issues.join(', ') + '</p>' : ''}
                        ${data.warnings ? '<p style="color: #f59e0b; margin-top: 10px;"><strong>Warnings:</strong> ' + data.warnings.join(', ') + '</p>' : ''}
                    `;
                    
                    // Update signal components
                    const signals = data.signal_components || {};
                    const signalsContainer = document.getElementById('signals-container');
                    if (Object.keys(signals).length === 0) {
                        signalsContainer.innerHTML = '<div class="loading">No signal components found</div>';
                    } else {
                        signalsContainer.innerHTML = Object.entries(signals).map(([name, health]) => {
                            const status = health.status || 'unknown';
                            const statusClass = getStatusClass(status);
                            return `
                                <div class="health-card ${statusClass}">
                                    <div class="health-card-header">
                                        <span class="health-card-name">${name}</span>
                                        <span class="health-status ${statusClass}">${status}</span>
                                    </div>
                                    <div class="health-details">
                                        <div><strong>Last Update:</strong> ${formatTimeAgo(health.last_update_age_sec)}</div>
                                        ${health.data_freshness_sec !== null && health.data_freshness_sec !== undefined ? 
                                            `<div><strong>Data Freshness:</strong> ${formatTimeAgo(health.data_freshness_sec)}</div>` : ''}
                                        ${health.error_rate_1h !== undefined ? 
                                            `<div><strong>Error Rate (1h):</strong> ${(health.error_rate_1h * 100).toFixed(1)}%</div>` : ''}
                                        ${health.last_error ? 
                                            `<div style="color: #ef4444; margin-top: 5px;"><strong>Error:</strong> ${health.last_error}</div>` : ''}
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                    
                    // Update API endpoints
                    const apis = data.uw_api_endpoints || {};
                    const apiContainer = document.getElementById('api-container');
                    if (Object.keys(apis).length === 0) {
                        apiContainer.innerHTML = '<div class="loading" style="grid-column: 1 / -1; padding: 20px; text-align: center; color: #f59e0b;">⚠️ No UW API endpoints found in response. Check console for errors.</div>';
                    } else {
                        apiContainer.innerHTML = Object.entries(apis).map(([name, health]) => {
                            const status = health.status || 'unknown';
                            const statusClass = getStatusClass(status);
                            const endpoint = health.endpoint || name;
                            return `
                                <div class="health-card ${statusClass}" style="min-height: 150px;">
                                    <div class="health-card-header">
                                        <span class="health-card-name" style="font-weight: bold; font-size: 1.1em;">${name}</span>
                                        <span class="health-status ${statusClass}">${status}</span>
                                    </div>
                                    <div class="health-details" style="margin-top: 10px;">
                                        <div style="font-size: 0.85em; color: #64748b; margin-bottom: 8px; word-break: break-all;">
                                            <strong>Endpoint:</strong> ${endpoint}
                                        </div>
                                        ${health.last_success_age_sec !== null && health.last_success_age_sec !== undefined ? 
                                            `<div><strong>Last Success:</strong> ${formatTimeAgo(health.last_success_age_sec)} ago</div>` : ''}
                                        ${health.avg_latency_ms !== null && health.avg_latency_ms !== undefined ? 
                                            `<div><strong>Avg Latency:</strong> ${health.avg_latency_ms.toFixed(0)}ms</div>` : 
                                            '<div><strong>Latency:</strong> N/A (cache-based check)</div>'}
                                        ${health.error_rate_1h !== undefined ? 
                                            `<div><strong>Error Rate (1h):</strong> ${(health.error_rate_1h * 100).toFixed(1)}%</div>` : ''}
                                        ${health.rate_limit_remaining !== null && health.rate_limit_remaining !== undefined ? 
                                            `<div><strong>Rate Limit:</strong> ${health.rate_limit_remaining} remaining</div>` : ''}
                                        ${health.last_error ? 
                                            `<div style="color: #ef4444; margin-top: 8px; padding: 8px; background: #fee2e2; border-radius: 4px; font-size: 0.9em;"><strong>⚠️ Error:</strong> ${health.last_error.substring(0, 100)}</div>` : 
                                            '<div style="color: #10b981; margin-top: 8px;">✅ No recent errors</div>'}
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                    
                    // Update trade engine
                    const engine = data.order_execution || {};
                    const engineStatus = engine.status || 'unknown';
                    const engineClass = getStatusClass(engineStatus);
                    const engineContainer = document.getElementById('engine-container');
                    engineContainer.innerHTML = `
                        <div class="health-card ${engineClass}" style="grid-column: 1 / -1;">
                            <div class="health-card-header">
                                <span class="health-card-name">Order Execution Pipeline</span>
                                <span class="health-status ${engineClass}">${engineStatus}</span>
                            </div>
                            <div class="health-details" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                ${engine.last_order_age_sec !== null && engine.last_order_age_sec !== undefined ? 
                                    `<div><strong>Last Order:</strong> ${formatTimeAgo(engine.last_order_age_sec)}</div>` : 
                                    '<div><strong>Last Order:</strong> N/A</div>'}
                                <div><strong>Orders (1h):</strong> ${engine.orders_1h || 0}</div>
                                <div><strong>Orders (3h):</strong> ${engine.orders_3h || 0}</div>
                                <div><strong>Orders (24h):</strong> ${engine.orders_24h || 0}</div>
                                ${engine.fill_rate !== undefined ? 
                                    `<div><strong>Fill Rate:</strong> ${(engine.fill_rate * 100).toFixed(1)}%</div>` : ''}
                                ${engine.avg_fill_time_sec !== null && engine.avg_fill_time_sec !== undefined ? 
                                    `<div><strong>Avg Fill Time:</strong> ${formatTimeAgo(engine.avg_fill_time_sec)}</div>` : ''}
                                ${engine.errors_1h !== undefined ? 
                                    `<div><strong>Errors (1h):</strong> ${engine.errors_1h}</div>` : ''}
                            </div>
                        </div>
                    `;
                })
                .catch(error => {
                    console.error('Error fetching SRE health:', error);
                    document.getElementById('overall-health').innerHTML = `
                        <h2 style="color: #ef4444;">ERROR</h2>
                        <p>Failed to load health data: ${error.message}</p>
                    `;
                });
        }
        
        updateSREDashboard();
        setInterval(updateSREDashboard, 60000);  // 60 seconds - reduce load
    </script>
</body>
</html>
"""

def _parse_log_ts_ops(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("Z", "+00:00")
    try:
        t = datetime.fromisoformat(s)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _iter_jsonl_ops(path: Path):
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _alpaca_operational_activity_payload(root: Path, hours: int) -> dict:
    """
    Read-only snapshot from local logs. Does not certify learning or attribution.
    Always returns ok=True with explicit partial/disabled flags — never empty without explanation.

    Scans only the **tail** of each JSONL (last N lines / bytes) so multi-GB logs cannot block
    the Flask worker (which would otherwise stall direction_banner, situation, and this panel).
    """
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max(1, min(int(hours), 24 * 30)))
    cut_ts = cutoff.timestamp()
    logs = root / "logs"
    disclaimer = (
        "Trades are executing on Alpaca. Data is NOT certified for learning or attribution."
    )
    tail_lines = 12_000
    tail_chunk = 2_500_000
    tail_note = (
        f"Counts use the last ~{tail_lines} lines per log file (plus up to {tail_chunk // 1_000_000}MB read each). "
        "If volume is extreme, figures are a lower bound for the time window."
    )

    last_exit_ts: float | None = None
    last_entry_ts: float | None = None
    exit_attr_n = 0
    unified_exit_n = 0
    unified_entry_n = 0
    run_entered_n = 0
    orders_n = 0
    fills_h = 0

    def _consume_tail(path: Path, handle):
        for line in _tail_file_lines(path, max_lines=tail_lines, max_chunk_bytes=tail_chunk):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            handle(rec)

    def _h_exit(r):
        nonlocal exit_attr_n, last_exit_ts
        ts = _parse_log_ts_ops(r.get("timestamp"))
        if ts is not None and ts < cut_ts:
            return
        exit_attr_n += 1
        if ts is not None and (last_exit_ts is None or ts > last_exit_ts):
            last_exit_ts = ts

    def _h_unified(r):
        nonlocal unified_exit_n, unified_entry_n, last_exit_ts, last_entry_ts
        et = r.get("event_type")
        ts = _parse_log_ts_ops(r.get("timestamp") or r.get("ts"))
        if ts is not None and ts < cut_ts:
            return
        if et == "alpaca_exit_attribution":
            unified_exit_n += 1
            if ts is not None and (last_exit_ts is None or ts > last_exit_ts):
                last_exit_ts = ts
        elif et == "alpaca_entry_attribution":
            unified_entry_n += 1
            if ts is not None and (last_entry_ts is None or ts > last_entry_ts):
                last_entry_ts = ts

    def _h_run(r):
        nonlocal run_entered_n, last_entry_ts
        ts = _parse_log_ts_ops(r.get("timestamp") or r.get("ts") or r.get("_ts"))
        if isinstance(r.get("_ts"), (int, float)) and ts is None:
            ts = float(r["_ts"])
        if ts is not None and ts < cut_ts:
            return
        if r.get("event_type") == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered":
            run_entered_n += 1
            if ts is not None and (last_entry_ts is None or ts > last_entry_ts):
                last_entry_ts = ts

    _consume_tail(logs / "exit_attribution.jsonl", _h_exit)
    _consume_tail(logs / "alpaca_unified_events.jsonl", _h_unified)
    _consume_tail(logs / "run.jsonl", _h_run)

    op_path = logs / "orders.jsonl"
    orders_state = "OK"
    orders_reason = ""
    if not op_path.is_file() or op_path.stat().st_size == 0:
        orders_state = "PARTIAL"
        orders_reason = "orders.jsonl missing or empty on this host — order/fill counts may be zero while trading still occurs."
    else:
        def _h_ord(r):
            nonlocal orders_n, fills_h
            ts = _parse_log_ts_ops(r.get("timestamp") or r.get("_ts") or r.get("ts"))
            if ts is not None and ts < cut_ts:
                return
            orders_n += 1
            st = str(r.get("status", "")).lower()
            typ = str(r.get("type", "")).lower()
            if st == "filled" or typ == "fill" or (r.get("filled_qty") not in (None, 0, "0")):
                fills_h += 1

        _consume_tail(op_path, _h_ord)

    trades_observed = max(exit_attr_n, unified_exit_n, run_entered_n)

    def _iso(u: float | None) -> str | None:
        if u is None:
            return None
        return datetime.fromtimestamp(u, tz=timezone.utc).isoformat()

    panel_state = "OK"
    if orders_state == "PARTIAL":
        panel_state = "PARTIAL"
    if exit_attr_n == 0 and unified_exit_n == 0 and run_entered_n == 0:
        panel_state = "PARTIAL"

    return {
        "ok": True,
        "state": panel_state,
        "hours": int(hours),
        "generated_at_utc": now.isoformat(),
        "window_start_utc": cutoff.isoformat(),
        "disclaimer": disclaimer,
        "scan_method": "tail",
        "scan_note": tail_note,
        "trades_observed": trades_observed,
        "exit_attribution_rows_in_window": exit_attr_n,
        "unified_exit_rows_in_window": unified_exit_n,
        "unified_entry_rows_in_window": unified_entry_n,
        "trade_intent_entered_in_window": run_entered_n,
        "last_exit_timestamp_utc": _iso(last_exit_ts),
        "last_entry_timestamp_utc": _iso(last_entry_ts),
        "orders_rows_in_window": orders_n,
        "fills_seen_heuristic": fills_h,
        "orders_log": {"state": orders_state, "reason": orders_reason or None},
        "does_not_claim": [
            "learning_certification",
            "attribution_completeness",
            "broker_reconciliation",
        ],
    }


def _daily_trade_volume_payload(root: Path, days: int) -> dict:
    """
    UTC daily trade activity + immutable past-day ledger (see telemetry.command_center_dashboard).
    """
    from telemetry.command_center_dashboard import daily_trade_volume_utc_with_ledger

    return daily_trade_volume_utc_with_ledger(root, days, tail_lines=_tail_file_lines)


@app.route("/api/dashboard/daily_trade_volume", methods=["GET"])
def api_dashboard_daily_trade_volume():
    """Minimal daily fill/trade counts for the Positions tab chart (read-only JSONL tail)."""
    import concurrent.futures

    try:
        d = int(request.args.get("days", "30"))
    except Exception:
        d = 30
    d = max(7, min(d, 90))
    root = Path(_DASHBOARD_ROOT)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_daily_trade_volume_payload, root, d)
            payload = fut.result(timeout=12)
        return jsonify(payload), 200
    except concurrent.futures.TimeoutError:
        return jsonify(
            {
                "ok": False,
                "error": "scan_timeout",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "series": [],
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "ok": False,
                "error": str(e)[:300],
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "series": [],
            }
        ), 200


@app.route("/api/dashboard/dual_barrel_cumulative_pnl", methods=["GET"])
def api_dashboard_dual_barrel_cumulative_pnl():
    """Cumulative realized live vs V3-shadow-filtered PnL for Command Center (Chart.js)."""
    import concurrent.futures

    from telemetry.command_center_dashboard import dual_barrel_cumulative_pnl_series

    root = Path(_DASHBOARD_ROOT)
    try:
        mx = int(request.args.get("max_points", "600"))
    except Exception:
        mx = 600
    mx = max(50, min(mx, 5000))
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(dual_barrel_cumulative_pnl_series, root, max_points=mx, tail_lines=_tail_file_lines)
            payload = fut.result(timeout=20)
        return jsonify(payload), 200
    except concurrent.futures.TimeoutError:
        return jsonify(
            {
                "ok": False,
                "error": "scan_timeout",
                "points": [],
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "ok": False,
                "error": str(e)[:300],
                "points": [],
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ), 200


@app.route("/api/alpaca_operational_activity", methods=["GET"])
def api_alpaca_operational_activity():
    """Alpaca operational activity from logs (read-only). Always HTTP 200; bounded wall time."""
    import concurrent.futures

    try:
        h = int(request.args.get("hours", "72"))
    except Exception:
        h = 72
    root = Path(_DASHBOARD_ROOT)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_alpaca_operational_activity_payload, root, h)
            payload = fut.result(timeout=14)
        return jsonify(payload), 200
    except concurrent.futures.TimeoutError:
        return jsonify(
            {
                "ok": True,
                "state": "PARTIAL",
                "hours": h,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "disclaimer": "Log scan exceeded time budget (14s); retry or narrow hours=. Worker was not blocked indefinitely.",
                "scan_note": "Timeout — large JSONL tails can be slow; counts may be incomplete.",
                "trades_observed": None,
                "exit_attribution_rows_in_window": None,
                "unified_exit_rows_in_window": None,
                "unified_entry_rows_in_window": None,
                "trade_intent_entered_in_window": None,
                "last_exit_timestamp_utc": None,
                "last_entry_timestamp_utc": None,
                "orders_rows_in_window": None,
                "fills_seen_heuristic": None,
                "orders_log": {"state": "PARTIAL", "reason": "scan_timeout"},
                "does_not_claim": ["learning_certification", "attribution_completeness", "broker_reconciliation"],
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "ok": False,
                "state": "DISABLED",
                "reason": str(e)[:300],
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "disclaimer": "Operational activity snapshot unavailable.",
                "trades_observed": None,
                "orders_rows_in_window": None,
                "fills_seen_heuristic": None,
            }
        ), 200


def _load_attribution_closed_trades_tail(root: Path, *, max_lines: int = 18_000, max_chunk_bytes: int = 4_000_000) -> list:
    """
    Parse closed attribution rows from the tail of logs/attribution.jsonl only.
    Same inclusion rules as executive_summary_generator.get_all_trades (no full-file read).
    """
    try:
        from config.registry import LogFiles

        path = (root / LogFiles.ATTRIBUTION).resolve()
    except Exception:
        path = (root / "logs" / "attribution.jsonl").resolve()
    if not path.is_file():
        return []
    trades: list = []
    for line in _tail_file_lines(path, max_lines=max_lines, max_chunk_bytes=max_chunk_bytes):
        line = line.strip()
        if not line:
            continue
        try:
            trade = json.loads(line)
        except json.JSONDecodeError:
            continue
        if trade.get("type") != "attribution":
            continue
        trade_id = trade.get("trade_id", "")
        if trade_id and str(trade_id).startswith("open_"):
            continue
        context = trade.get("context", {}) or {}
        pnl_usd = float(trade.get("pnl_usd", 0.0))
        close_reason = context.get("close_reason", "") or trade.get("close_reason", "")
        if pnl_usd == 0.0 and (not close_reason or close_reason in ("unknown", "N/A")):
            continue
        ts_str = trade.get("ts", "")
        if not ts_str:
            continue
        trades.append(trade)
    return trades


def _header_strip_payload() -> dict:
    """
    Single fast response for the dashboard top strip (avoids 3 queued heavy requests on one Flask worker).
    """
    from datetime import datetime, timezone
    import time as time_module

    now = datetime.now(timezone.utc)
    out: dict = {
        "ok": True,
        "generated_at_utc": now.isoformat(),
        "overall_health": None,
        "overall_health_source": None,
        "market_open": None,
        "broker_day_pnl": None,
        "pnl_24h_attribution": None,
        "pnl_7d_attribution": None,
        "trades_24h_attribution": None,
        "trades_7d_attribution": None,
        "attribution_tail_note": None,
        "definitions": {
            "broker_day_pnl": "Alpaca session/day P&L: equity minus daily_start_equity.json (if today) else equity - last_equity.",
            "pnl_24h_attribution": "Sum of pnl_usd on closed attribution rows with exit ts in rolling 24h (logs/attribution.jsonl tail).",
            "pnl_7d_attribution": "Same, rolling 7d window. For full cohort use Executive Summary tab.",
        },
    }
    try:
        import requests

        resp = requests.get("http://127.0.0.1:8081/api/sre/health", timeout=2)
        if resp.status_code == 200:
            jd = resp.json()
            out["overall_health"] = jd.get("overall_health")
            out["market_open"] = jd.get("market_open")
            out["overall_health_source"] = "bot:8081"
    except Exception:
        pass
    if not out["overall_health"]:
        try:
            hb = (_DASHBOARD_ROOT / "state" / "bot_heartbeat.json").resolve()
            if hb.exists():
                age = time_module.time() - hb.stat().st_mtime
                out["overall_health"] = "healthy" if age < 180 else "degraded"
                out["overall_health_source"] = "bot_heartbeat_mtime"
        except Exception:
            pass
    if not out["overall_health"]:
        out["overall_health"] = "unknown"
        out["overall_health_source"] = "none"

    if _alpaca_api is not None:
        try:
            account = _alpaca_api.get_account()
            day_pnl = float(getattr(account, "equity", 0) or 0) - float(getattr(account, "last_equity", 0) or 0)
            try:
                from datetime import datetime as _dt, timezone as _tz

                date_str = _dt.now(_tz.utc).strftime("%Y-%m-%d")
                p_daily = (_DASHBOARD_ROOT / "state" / "daily_start_equity.json").resolve()
                if p_daily.exists():
                    d0 = json.loads(p_daily.read_text(encoding="utf-8", errors="replace"))
                    if isinstance(d0, dict) and str(d0.get("date", "")) == date_str and d0.get("equity") is not None:
                        day_pnl = float(getattr(account, "equity", 0) or 0) - float(d0["equity"])
            except Exception:
                pass
            out["broker_day_pnl"] = round(day_pnl, 2)
        except Exception as e:
            out["broker_day_pnl_error"] = str(e)[:160]

    max_lines = 18_000
    trades_tail = _load_attribution_closed_trades_tail(_DASHBOARD_ROOT, max_lines=max_lines, max_chunk_bytes=4_000_000)
    try:
        ap = (_DASHBOARD_ROOT / "logs" / "attribution.jsonl").resolve()
        if ap.is_file() and ap.stat().st_size > 3_500_000 and len(trades_tail) >= max_lines - 100:
            out["attribution_tail_note"] = (
                f"P&L uses the last ~{max_lines} closed rows from attribution.jsonl; "
                "very large files may omit older trades inside the 7d window."
            )
    except Exception:
        pass
    try:
        from executive_summary_generator import calculate_pnl_metrics

        m24 = calculate_pnl_metrics(trades_tail, "24h")
        m7 = calculate_pnl_metrics(trades_tail, "7d")
        out["pnl_24h_attribution"] = m24.get("pnl")
        out["pnl_7d_attribution"] = m7.get("pnl")
        out["trades_24h_attribution"] = m24.get("trades")
        out["trades_7d_attribution"] = m7.get("trades")
    except Exception as e:
        out["attribution_error"] = str(e)[:200]

    return out


@app.route("/api/dashboard/header_strip", methods=["GET"])
def api_dashboard_header_strip():
    """Fast top-strip data (one request; avoids blocking the Flask worker with parallel heavy calls)."""
    try:
        return jsonify(_header_strip_payload()), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:300], "generated_at_utc": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/ping", methods=["GET"])
def api_ping():
    """Lightweight connectivity check; returns immediately (no heavy deps)."""
    return jsonify({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})


@app.route("/api/direction_banner", methods=["GET"])
def api_direction_banner():
    """Directional intelligence replay banner state (WAITING | RUNNING | RESULTS | BLOCKED). Always returns 200 so dashboard never sticks on Loading."""
    try:
        root = Path(_DASHBOARD_ROOT)
        try:
            from src.dashboard.direction_banner_state import get_direction_banner_state
            state = get_direction_banner_state(root)
            return jsonify(state), 200
        except Exception as e:
            return jsonify({"state": "WAITING", "message": "Direction banner unavailable", "detail": str(e)[:200], "severity": "info"}), 200
    except Exception:
        return jsonify({"state": "WAITING", "message": "Direction status unavailable", "detail": "", "severity": "info"}), 200


@app.route("/api/situation", methods=["GET"])
def api_situation():
    """
    At-a-glance situation: canonical post-era closed-trade count + milestones, promotion, closed/open counts.
    Feeds the dashboard situation strip so operators see current state and where we are going for profit.
    """
    try:
        data = _get_situation_data_sync()
        if data.get("open_positions_count") is None and _alpaca_api is not None:
            try:
                pos = _alpaca_api.get_all_positions()
                data["open_positions_count"] = len(pos) if pos else 0
            except Exception:
                pass
        return jsonify(data), 200
    except Exception as e:
        return jsonify({
            "error": str(e)[:200],
            "trades_reviewed": 0,
            "trades_reviewed_total": 0,
            "trades_reviewed_target": 100,
            "total_trades_post_era": 0,
            "next_trade_milestone": None,
            "remaining_to_next_milestone": None,
            "promotion_recommendation": "WAIT",
            "promotion_score": None,
            "promotion_reasons": [],
            "governance_joined_count": None,
            "closed_trades_count": 0,
            "open_positions_count": None,
        }), 200


def _canonical_log_status_list(root: Path) -> list:
    """Canonical JSONL paths + last write (UTC ISO). Shared by telemetry_health and data_integrity."""
    logs_dir = root / "logs"
    canonical = [
        ("master_trade_log", logs_dir / "master_trade_log.jsonl"),
        ("attribution", logs_dir / "attribution.jsonl"),
        ("exit_attribution", logs_dir / "exit_attribution.jsonl"),
        ("exit_event", logs_dir / "exit_event.jsonl"),
        ("intel_snapshot_entry", logs_dir / "intel_snapshot_entry.jsonl"),
        ("intel_snapshot_exit", logs_dir / "intel_snapshot_exit.jsonl"),
        ("direction_event", logs_dir / "direction_event.jsonl"),
    ]
    log_status = []
    for name, path in canonical:
        exists = path.exists()
        mtime = path.stat().st_mtime if exists else None
        last_write = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat() if mtime else None
        log_status.append({"log": name, "exists": exists, "last_write": last_write})
    return log_status


def _build_data_integrity_payload(root: Path) -> dict:
    """
    Decision-grade integrity view from existing telemetry files only (read-only).
    Does not run trading or learning schedulers.
    """
    from datetime import datetime, timezone

    run_ts = datetime.now(timezone.utc).isoformat()
    log_status = _canonical_log_status_list(root)
    state_dir = root / "state"
    logs_dir = root / "logs"
    direction_telemetry_trades = direction_total = 0
    direction_ready = False
    direction_updated_ts = None
    try:
        rpath = state_dir / "direction_readiness.json"
        if rpath.exists():
            dr = json.loads(rpath.read_text(encoding="utf-8"))
            direction_telemetry_trades = int(dr.get("telemetry_trades") or 0)
            direction_total = int(dr.get("total_trades") or 0)
            direction_ready = dr.get("ready") is True
            direction_updated_ts = dr.get("updated_ts") or dr.get("last_cron_run_iso")
    except Exception:
        pass
    gate_status = None
    try:
        gate_path = root / "reports" / "audit" / "TELEMETRY_CONTRACT_AUDIT.md"
        if gate_path.exists():
            text = gate_path.read_text(encoding="utf-8", errors="replace")
            gate_status = "FAIL" if "Logs with schema failures" in text else "PASS"
    except Exception:
        pass
    exit_path = logs_dir / "exit_attribution.jsonl"
    visibility_matrix = _compute_visibility_matrix(exit_path, 100)
    alpaca_strict = None
    alpaca_strict_error = None
    try:
        from telemetry.alpaca_strict_completeness_gate import (
            STRICT_EPOCH_START,
            evaluate_completeness,
        )

        alpaca_strict = evaluate_completeness(root, open_ts_epoch=STRICT_EPOCH_START, audit=False)
    except Exception as e:
        alpaca_strict_error = str(e)[:500]
    temporal_flags: list = []
    if alpaca_strict:
        temporal_flags.extend([str(x) for x in (alpaca_strict.get("precheck") or [])])
        rsn = alpaca_strict.get("learning_fail_closed_reason")
        if rsn:
            temporal_flags.append(f"learning_fail_closed_reason:{rsn}")
    last_droplet_analysis = None
    try:
        lap = state_dir / "last_droplet_analysis.json"
        if lap.exists():
            last_droplet_analysis = json.loads(lap.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "generated_at_utc": run_ts,
        "data_sources": {
            "alpaca_strict": "telemetry/alpaca_strict_completeness_gate.evaluate_completeness (read-only, STRICT_EPOCH_START)",
            "direction_readiness": "state/direction_readiness.json (exit_attribution join coverage)",
            "canonical_logs": "logs/*.jsonl mtime scan",
            "join_matrix": "logs/exit_attribution.jsonl last 100 rows",
            "contract_audit": "reports/audit/TELEMETRY_CONTRACT_AUDIT.md",
        },
        "alpaca_strict": alpaca_strict,
        "alpaca_strict_error": alpaca_strict_error,
        "direction_readiness_gate": {
            "telemetry_trades": direction_telemetry_trades,
            "total_trades_window": direction_total,
            "ready": direction_ready,
            "updated_ts": direction_updated_ts,
            "note": "Telemetry-backed direction-replay gate from exit_attribution; distinct from Alpaca strict learning cohort.",
        },
        "canonical_log_staleness": log_status,
        "join_coverage_exit_attribution": visibility_matrix,
        "contract_audit_gate": gate_status,
        "temporal_and_structural_flags": temporal_flags,
        "last_droplet_analysis": last_droplet_analysis,
    }


@app.route("/api/dashboard/data_integrity", methods=["GET"])
def api_dashboard_data_integrity():
    """System Health & Data Integrity tab — JSON from telemetry files only."""
    try:
        root = Path(_DASHBOARD_ROOT)
        return jsonify(_build_data_integrity_payload(root)), 200
    except Exception as e:
        return jsonify({"error": str(e)[:500], "generated_at_utc": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/telemetry_health", methods=["GET"])
def api_telemetry_health():
    """Telemetry Health: canonical log existence + last-write, direction coverage X/100, optional gate status."""
    try:
        root = Path(_DASHBOARD_ROOT)
        state_dir = root / "state"
        log_status = _canonical_log_status_list(root)
        direction_telemetry_trades = 0
        direction_total = 0
        direction_ready = False
        try:
            rpath = state_dir / "direction_readiness.json"
            if rpath.exists():
                data = json.loads(rpath.read_text(encoding="utf-8"))
                direction_telemetry_trades = int(data.get("telemetry_trades") or 0)
                direction_total = int(data.get("total_trades") or 0)
                direction_ready = data.get("ready") is True
        except Exception:
            pass
        gate_status = None
        try:
            gate_path = root / "reports" / "audit" / "TELEMETRY_CONTRACT_AUDIT.md"
            if gate_path.exists():
                text = gate_path.read_text(encoding="utf-8", errors="replace")
                gate_status = "FAIL" if "Logs with schema failures" in text else "PASS"
        except Exception:
            pass
        last_droplet_analysis = None
        try:
            lap = state_dir / "last_droplet_analysis.json"
            if lap.exists():
                last_droplet_analysis = json.loads(lap.read_text(encoding="utf-8"))
        except Exception:
            pass
        return jsonify({
            "log_status": log_status,
            "direction_telemetry_trades": direction_telemetry_trades,
            "direction_total_trades": direction_total,
            "direction_ready": direction_ready,
            "direction_coverage": f"{direction_telemetry_trades}/100",
            "gate_status": gate_status,
            "last_droplet_analysis": last_droplet_analysis,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "log_status": [], "direction_coverage": "0/100"}), 200


def _compute_visibility_matrix(exit_path: Path, sample_size: int = 100) -> list:
    """
    Compute per-field coverage over last N lines of logs/exit_attribution.jsonl only.
    Sizing = present if qty or notional is present (documented rule).
    Returns list of {field, present, total, pct}.
    """
    matrix = []
    if not exit_path.exists():
        return matrix
    try:
        lines = exit_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except Exception:
        return matrix
    recent = [ln for ln in lines if ln.strip()][-sample_size:]
    total = len(recent)
    if total == 0:
        return matrix
    counts = {
        "intel_snapshot_entry": 0,
        "intel_snapshot_exit": 0,
        "direction": 0,
        "side": 0,
        "position_side": 0,
        "symbol": 0,
        "sizing": 0,
    }
    for line in recent:
        try:
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
            embed = rec.get("direction_intel_embed") if isinstance(rec.get("direction_intel_embed"), dict) else {}
            snap_e = embed.get("intel_snapshot_entry")
            snap_x = embed.get("intel_snapshot_exit")
            if isinstance(snap_e, dict) and snap_e:
                counts["intel_snapshot_entry"] += 1
            if isinstance(snap_x, dict) and snap_x:
                counts["intel_snapshot_exit"] += 1
            if rec.get("direction") not in (None, ""):
                counts["direction"] += 1
            if rec.get("side") not in (None, ""):
                counts["side"] += 1
            if rec.get("position_side") not in (None, ""):
                counts["position_side"] += 1
            if rec.get("symbol"):
                counts["symbol"] += 1
            if rec.get("qty") is not None or rec.get("notional") is not None:
                counts["sizing"] += 1
        except Exception:
            continue
    for name, present in counts.items():
        pct = round(100.0 * present / total, 1) if total else 0.0
        matrix.append({"field": name, "present": present, "total": total, "pct": pct})
    return matrix


def _learning_readiness_safe_payload(
    error: str | None = None,
    error_code: str | None = None,
    run_ts: str | None = None,
    deployed_commit: str = "unknown",
) -> dict:
    """Always-returnable JSON payload for /api/learning_readiness. Never 500."""
    from datetime import datetime, timezone
    ts = run_ts or datetime.now(timezone.utc).isoformat()
    return {
        "ok": False,
        "run_ts": ts,
        "deployed_commit": deployed_commit,
        "telemetry_trades": 0,
        "telemetry_total": 0,
        "total_trades": 0,
        "pct_telemetry": 0.0,
        "ready": False,
        "replay_status": {},
        "update_schedule": "every 5 min (9–21 UTC, Mon–Fri)",
        "visibility_matrix": [],
        "error": (error[:500] if error else None),
        "error_code": error_code or "UNKNOWN",
        "last_cron_run_iso": None,
        "updated_ts": None,
        "fresh": False,
    }


def _get_learning_readiness_payload(root: Path, run_ts: str, deployed_commit: str) -> dict:
    """Build full learning-readiness payload. Can raise; used by API and by server-side render."""
    from datetime import datetime, timezone
    state_dir = root / "state"
    logs_dir = root / "logs"
    readiness = {}
    replay_status = {}
    try:
        rpath = state_dir / "direction_readiness.json"
        if rpath.exists():
            readiness = json.loads(rpath.read_text(encoding="utf-8"))
    except Exception:
        pass
    try:
        spath = state_dir / "direction_replay_status.json"
        if spath.exists():
            replay_status = json.loads(spath.read_text(encoding="utf-8"))
    except Exception:
        pass
    telemetry_trades = int(readiness.get("telemetry_trades") or 0)
    total_trades = int(readiness.get("total_trades") or 0)
    pct_telemetry = float(readiness.get("pct_telemetry") or 0)
    all_time_exits = int(readiness.get("all_time_exits") or 0)
    if not all_time_exits:
        try:
            ep = logs_dir / "exit_attribution.jsonl"
            if ep.exists():
                all_time_exits = sum(1 for ln in ep.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip())
        except Exception:
            pass
    ready = readiness.get("ready") is True
    updated_ts = readiness.get("updated_ts")
    last_cron_iso = updated_ts or readiness.get("last_cron_run_iso")
    if not last_cron_iso and state_dir.joinpath("direction_readiness.json").exists():
        try:
            m = (state_dir / "direction_readiness.json").stat().st_mtime
            last_cron_iso = datetime.fromtimestamp(m, tz=timezone.utc).isoformat()
        except Exception:
            pass
    fresh = False
    if last_cron_iso:
        try:
            s = str(last_cron_iso).replace("Z", "+00:00").strip()[:26]
            if "+" in s or s.endswith("Z"):
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = datetime.fromisoformat(s[:19]).replace(tzinfo=timezone.utc)
            age_min = (datetime.now(timezone.utc) - dt).total_seconds() / 60
            fresh = age_min < 15
        except Exception:
            fresh = True
    promotion_recommendation, promotion_score, promotion_reasons = "WAIT", None, []
    try:
        today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        comb_path = root / "reports" / f"{today}_stock-bot_combined.json"
        if comb_path.exists():
            comb = json.loads(comb_path.read_text(encoding="utf-8", errors="replace"))
            sc = comb.get("strategy_comparison") or {}
            if isinstance(sc, dict):
                promotion_recommendation = sc.get("recommendation", "WAIT")
                promotion_score = sc.get("promotion_readiness_score")
                promotion_reasons = (sc.get("reasons") or [])[:5]
    except Exception:
        pass
    exit_path = logs_dir / "exit_attribution.jsonl"
    visibility_matrix = _compute_visibility_matrix(exit_path, 100)
    replay_safe = {
        "status": replay_status.get("status"),
        "reason": replay_status.get("reason"),
        "last_run_ts": replay_status.get("last_run_ts"),
    }
    last_csa_mission_id = None
    trades_until_next_csa = None
    try:
        state_path = root / "reports" / "state" / "TRADE_CSA_STATE.json"
        if not state_path.exists():
            state_path = root / "reports" / "state" / "test_csa_100" / "TRADE_CSA_STATE.json"
        if state_path.exists():
            csa_state = json.loads(state_path.read_text(encoding="utf-8"))
            total_events = int(csa_state.get("total_trade_events") or 0)
            last_csa_mission_id = csa_state.get("last_csa_mission_id") or csa_state.get("mission_id")
            if total_events > 0:
                trades_until_next_csa = 100 - (total_events % 100)
            else:
                trades_until_next_csa = 100
    except Exception:
        pass
    return {
        "ok": True,
        "run_ts": run_ts,
        "deployed_commit": deployed_commit,
        "telemetry_trades": telemetry_trades,
        "telemetry_total": total_trades,
        "pct_telemetry": round(pct_telemetry, 2),
        "ready": ready,
        "replay_status": replay_safe,
        "update_schedule": "every 5 min (9–21 UTC, Mon–Fri)",
        "visibility_matrix": visibility_matrix,
        "error": None,
        "error_code": None,
        "last_cron_run_iso": last_cron_iso,
        "updated_ts": updated_ts,
        "fresh": fresh,
        "total_trades": total_trades,
        "target_trades": 100,
        "min_pct_telemetry": 90.0,
        "all_time_exits": all_time_exits,
        "last_csa_mission_id": last_csa_mission_id,
        "trades_until_next_csa": trades_until_next_csa,
        "features_reviewed": [
            "Entry intel (premarket, futures, sector, regime at position open)",
            "Exit intel (same at close)",
            "Direction, side, position_side",
            "Sizing (qty or notional)",
            "Join key: symbol + entry_ts",
        ],
        "what_wait_means": (
            "Replay runs when last 100 exits have ≥90% with telemetry. "
            "Until then, no direction-replay-based exit/sizing adjustments."
        ),
        "still_reviewing": True,
        "review_continues_after_100": (
            "Yes. Every exit appends to exit_attribution; cron recomputes every 5 min."
        ),
        "promotion_close_missing": (
            [f"Need 100 exits in review window (have {total_trades})"]
            if total_trades < 100 else []
        ) + (
            [f"Need 90 telemetry-backed in last 100 (have {telemetry_trades})"]
            if total_trades >= 100 and telemetry_trades < 90 else []
        ) + (
            [f"Need 90% telemetry in last 100 (have {pct_telemetry:.1f}%)"]
            if pct_telemetry < 90 else []
        ),
        "promotion_recommendation": promotion_recommendation,
        "promotion_score": promotion_score,
        "promotion_reasons": promotion_reasons,
    }


def _render_learning_readiness_html(payload: dict) -> str:
    """Server-side render Learning & Readiness tab HTML so the tab never shows a blank loading state."""
    import html as html_module
    esc = html_module.escape
    run_ts = esc(str(payload.get("run_ts") or "—"))
    deployed_commit = esc(str(payload.get("deployed_commit") or "—"))
    if payload.get("ok") is False and payload.get("error"):
        err = esc(str(payload.get("error", ""))[:500])
        code = esc(str(payload.get("error_code") or ""))
        return (
            '<div class="stat-card" style="margin-bottom:12px;"><button type="button" onclick="if(typeof loadLearningReadiness===\'function\')loadLearningReadiness();">Refresh</button></div>'
            + '<div class="stat-card" style="border-color:#f59e0b"><h3>State: DEGRADED</h3><p>' + err + '</p><p>Code: ' + code + '</p></div>'
        )
    x = int(payload.get("telemetry_trades") or 0)
    tot = int(payload.get("telemetry_total") or payload.get("total_trades") or 0)
    pct = float(payload.get("pct_telemetry") or 0)
    tgt = int(payload.get("target_trades") or 100)
    min_pct = int(payload.get("min_pct_telemetry") or 90)
    all_time = int(payload.get("all_time_exits") or 0)
    ready = payload.get("ready") is True
    state_label = "OK" if payload.get("ok") is True else ("DEGRADED" if payload.get("error") else "WAITING")
    all_time_line = ("<p><strong>Total exits (all-time):</strong> " + str(all_time) + "</p>") if all_time else ""
    last_csa = payload.get("last_csa_mission_id")
    until_csa = payload.get("trades_until_next_csa")
    csa_line = ""
    if last_csa is not None or until_csa is not None:
        csa_line = "<p><strong>Last CSA mission:</strong> " + esc(str(last_csa) if last_csa is not None else "—") + " · <strong>Trades until next CSA:</strong> " + (str(until_csa) if until_csa is not None else "—") + "</p>"
    link_pl = '<p><button type="button" onclick="switchTab(\'profitability_learning\', event);">See Profitability &amp; Learning</button></p>'
    parts = [
        '<div class="stat-card" style="margin-bottom:12px;"><button type="button" onclick="if(typeof loadLearningReadiness===\'function\')loadLearningReadiness();">Refresh</button>' + link_pl + '</div>',
        '<div class="stat-card"><h3>State: ' + esc(state_label) + '</h3><p>run_ts: ' + run_ts + ' · commit: ' + deployed_commit + '</p></div>',
        '<div class="stat-card"><h3>Trades reviewed</h3>' + all_time_line + csa_line + '<p><strong>Last ' + str(tgt) + ' exits:</strong> ' + str(x) + ' telemetry-backed · ' + f"{pct:.1f}" + '% with full telemetry</p><p><strong>Ready for replay:</strong> ' + ("Yes" if ready else f"No — need ≥{tgt} and ≥{min_pct}%") + '</p></div>',
        '<div class="stat-card"><h3>Still reviewing?</h3><p><strong>Yes.</strong> ' + esc(str(payload.get("review_continues_after_100") or "Counts updated every 5 min from exit_attribution.")) + '</p></div>',
    ]
    mx = payload.get("visibility_matrix") or []
    parts.append('<div class="stat-card"><h3>Visibility matrix (last 100 exits)</h3>')
    if not mx:
        parts.append("<p>No exits yet.</p>")
    else:
        parts.append('<table style="width:100%;border-collapse:collapse"><thead><tr><th style="text-align:left">Field</th><th>Present</th><th>Total</th><th>%</th></tr></thead><tbody>')
        for row in mx:
            fn = esc(str(row.get("field") or row.get("feature") or "—"))
            cnt = row.get("present") if row.get("present") is not None else (row.get("count") or 0)
            tot_row = row.get("total") if row.get("total") is not None else tot
            pc = float(row.get("pct") or 0)
            parts.append(f"<tr><td>{fn}</td><td>{cnt}</td><td>{tot_row}</td><td>{pc:.1f}%</td></tr>")
        parts.append("</tbody></table>")
    parts.append("</div>")
    close_missing = payload.get("promotion_close_missing") or []
    close_str = "; ".join(esc(str(m)) for m in close_missing) if close_missing else "Replay gate: need ≥100 telemetry-backed and ≥90% coverage."
    parts.append('<div class="stat-card"><h3>Close to promotion?</h3><p>' + close_str + '</p></div>')
    last_cron = esc(str(payload.get("last_cron_run_iso") or "—"))
    fresh = payload.get("fresh") is True
    parts.append('<div class="stat-card"><h3>Update schedule</h3><p><strong>' + esc(str(payload.get("update_schedule") or "—")) + '</strong></p><p>Last cron: ' + last_cron + (" (fresh)" if fresh else "") + '</p></div>')
    rs = payload.get("replay_status") or {}
    if rs.get("status") or rs.get("reason"):
        parts.append('<div class="stat-card"><h3>Replay status</h3><p><strong>Status:</strong> ' + esc(str(rs.get("status") or "—")) + '</p>' + (('<p><strong>Reason:</strong> ' + esc(str(rs.get("reason"))) + '</p>') if rs.get("reason") else "") + (('<p><strong>Last run:</strong> ' + esc(str(rs.get("last_run_ts"))) + '</p>') if rs.get("last_run_ts") else "") + "</div>")
    rec = (payload.get("promotion_recommendation") or "WAIT").upper()
    score = payload.get("promotion_score")
    reasons = payload.get("promotion_reasons") or []
    rec_html = esc(rec) + (f" {score}/100" if score is not None else "")
    reasons_str = "; ".join(esc(str(r)) for r in reasons) if reasons else ""
    parts.append('<div class="stat-card"><h3>Promotion readiness</h3><p><strong>Recommendation:</strong> ' + rec_html + '</p>' + (('<p><strong>Reasons:</strong> ' + reasons_str + '</p>') if reasons_str else "") + "</div>")
    return "\n".join(parts)


@app.route("/api/learning_readiness", methods=["GET"])
def api_learning_readiness():
    """
    Learning & Readiness tab API. NEVER returns 500.
    Always 200 JSON with ok/run_ts/deployed_commit/visibility_matrix/error.
    Counts from direction_readiness (cron) or recomputed from exit_attribution.jsonl only.
    """
    from datetime import datetime, timezone
    import traceback
    root = Path(_DASHBOARD_ROOT)
    log_path = root / "logs" / "dashboard_learning_readiness.log"
    run_ts = datetime.now(timezone.utc).isoformat()
    deployed_commit = "unknown"
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0 and r.stdout:
            deployed_commit = r.stdout.strip()[:12]
    except Exception:
        pass

    def _log_error(err: str, code: str) -> None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{run_ts} [{code}] {err}\n{traceback.format_exc()}\n")
        except Exception:
            pass

    try:
        payload = _get_learning_readiness_payload(root, run_ts, deployed_commit)
        return jsonify(payload), 200
    except Exception as e:
        err_msg = str(e)[:500]
        _log_error(err_msg, "API_ERROR")
        payload = _learning_readiness_safe_payload(
            error=err_msg,
            error_code="API_ERROR",
            run_ts=run_ts,
            deployed_commit=deployed_commit,
        )
        return jsonify(payload), 200


def _get_profitability_learning_payload(root: Path) -> dict:
    """Load cockpit, CSA verdict, trade state. Same data as API. Never raises; returns empty dicts on error."""
    out = {"ok": False, "cockpit_md": "", "csa_verdict": {}, "trade_state": {}, "error": None}
    try:
        cockpit_path = root / "reports" / "board" / "PROFITABILITY_COCKPIT.md"
        if cockpit_path.exists():
            out["cockpit_md"] = cockpit_path.read_text(encoding="utf-8", errors="replace")
        verdict_path = root / "reports" / "audit" / "CSA_VERDICT_LATEST.json"
        if verdict_path.exists():
            try:
                out["csa_verdict"] = json.loads(verdict_path.read_text(encoding="utf-8"))
            except Exception:
                out["csa_verdict"] = {}
        state_path = root / "reports" / "state" / "TRADE_CSA_STATE.json"
        if not state_path.exists():
            state_path = root / "reports" / "state" / "test_csa_100" / "TRADE_CSA_STATE.json"
        if state_path.exists():
            try:
                out["trade_state"] = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                out["trade_state"] = {}
        out["ok"] = True
    except Exception as e:
        out["error"] = str(e)[:300]
    return out


def _render_profitability_learning_html(payload: dict) -> str:
    """Server-side render for Profitability & Learning tab so it never sticks on Loading."""
    import html as html_module
    esc = html_module.escape
    if not payload.get("ok"):
        err = esc(str(payload.get("error") or "Could not load data")[:200])
        return (
            f'<div class="stat-card" style="border-color:#f59e0b"><p>{err}</p>'
            '<p><button type="button" onclick="if(typeof loadProfitabilityLearning===\'function\')loadProfitabilityLearning();">Retry</button></p></div>'
        )
    ts = payload.get("trade_state") or {}
    total = int(ts.get("total_trade_events") or 0)
    until = 100 - (total % 100) if total > 0 else 100
    v = payload.get("csa_verdict") or {}
    mission = esc(str(v.get("mission_id") or "—"))
    verdict = esc(str(v.get("verdict") or "—"))
    parts = [
        '<div class="stat-card"><h3>CSA &amp; Trade Count</h3>',
        f'<p><strong>Last mission:</strong> {mission}</p>',
        f'<p><strong>Verdict:</strong> {verdict}</p>',
        f'<p><strong>Total trade events:</strong> {total}</p>',
        f'<p><strong>Trades until next CSA:</strong> {until}</p>',
        '<p><button type="button" onclick="if(typeof loadProfitabilityLearning===\'function\')loadProfitabilityLearning();">Refresh</button></p>',
        "</div>",
    ]
    md = payload.get("cockpit_md") or ""
    md_esc = esc(md).replace("\n", "<br>\n")
    parts.append('<div class="stat-card"><h3>Profitability Cockpit</h3><div style="white-space:pre-wrap;font-size:0.9em;">' + md_esc + "</div></div>")
    return "\n".join(parts)


@app.route("/api/profitability_learning", methods=["GET"])
def api_profitability_learning():
    """
    Profitability & Learning tab: cockpit markdown, CSA verdict, trade state.
    Never 500; returns ok=False and empty payload on error.
    """
    root = Path(_DASHBOARD_ROOT)
    out = _get_profitability_learning_payload(root)
    return jsonify(out), 200


@app.route("/reports/board/<path:filename>", methods=["GET"])
def serve_board_report(filename):
    """Serve board report files so direction banner 'View report' link works (e.g. DIRECTION_REPLAY_30D_RESULTS.md)."""
    try:
        root = Path(_DASHBOARD_ROOT)
        path = (root / "reports" / "board" / filename).resolve()
        if not path.is_file() or not str(path).startswith(str(root.resolve())):
            # HTTP 200: avoid “broken link” 404 in operator browsers; body explains gap.
            return Response(
                "# Board report not on this host\n\n"
                "The requested file is missing or outside the reports/board tree. "
                "This is not a dashboard failure.\n",
                mimetype="text/markdown; charset=utf-8",
                headers={"Content-Disposition": "inline"},
                status=200,
            )
        content = path.read_text(encoding="utf-8", errors="replace")
        return Response(content, mimetype="text/markdown; charset=utf-8", headers={"Content-Disposition": "inline"})
    except Exception:
        return Response(
            "# Board report unavailable\n\nCould not read the requested report.\n",
            mimetype="text/markdown; charset=utf-8",
            status=200,
        )


@app.route("/api/governance/status", methods=["GET"])
def api_governance_status():
    """
    Governance and stopping condition: giveback + stopping_checks from latest lock_or_revert_decision
    and effectiveness_aggregates. For dashboard panel so operators see if stopping condition can be satisfied.
    """
    try:
        root = Path(_DASHBOARD_ROOT)
        out = {
            "avg_profit_giveback": None,
            "stopping_condition_met": False,
            "stopping_checks": {},
            "decision": None,
            "joined_count": None,
            "win_rate": None,
            "expectancy_per_trade": None,
            "source_decision": None,
            "source_aggregates": None,
        }
        # Latest equity_governance run dir
        gov_dir = root / "reports" / "equity_governance"
        if gov_dir.exists():
            runs = sorted(gov_dir.glob("equity_governance_*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for run_dir in runs[:1]:
                dec_path = run_dir / "lock_or_revert_decision.json"
                if dec_path.exists():
                    try:
                        dec = json.loads(dec_path.read_text(encoding="utf-8"))
                        out["decision"] = dec.get("decision")
                        out["stopping_condition_met"] = bool(dec.get("stopping_condition_met"))
                        out["stopping_checks"] = dec.get("stopping_checks") or {}
                        cand = dec.get("candidate") or {}
                        out["joined_count"] = cand.get("joined_count")
                        out["win_rate"] = cand.get("win_rate")
                        out["expectancy_per_trade"] = cand.get("expectancy_per_trade")
                        out["avg_profit_giveback"] = cand.get("avg_profit_giveback")
                        out["source_decision"] = str(dec_path.relative_to(root))
                        break
                    except Exception:
                        pass
        # Fallback: effectiveness_aggregates from baseline or latest effectiveness dir
        eff_dirs = list((root / "reports").glob("effectiveness_*"))
        if not eff_dirs and (root / "reports" / "effectiveness_baseline_blame").exists():
            eff_dirs = [root / "reports" / "effectiveness_baseline_blame"]
        for d in sorted(eff_dirs, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:1]:
            agg_path = d / "effectiveness_aggregates.json"
            if agg_path.exists():
                try:
                    agg = json.loads(agg_path.read_text(encoding="utf-8"))
                    if out["avg_profit_giveback"] is None:
                        out["avg_profit_giveback"] = agg.get("avg_profit_giveback")
                    if out["joined_count"] is None:
                        out["joined_count"] = agg.get("joined_count")
                    if out["win_rate"] is None:
                        out["win_rate"] = agg.get("win_rate")
                    if out["expectancy_per_trade"] is None:
                        out["expectancy_per_trade"] = agg.get("expectancy_per_trade")
                    out["source_aggregates"] = str(agg_path.relative_to(root))
                    break
                except Exception:
                    pass
        last_droplet_analysis = None
        try:
            lap = root / "state" / "last_droplet_analysis.json"
            if lap.exists():
                last_droplet_analysis = json.loads(lap.read_text(encoding="utf-8"))
        except Exception:
            pass
        out["last_droplet_analysis"] = last_droplet_analysis
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"error": str(e), "avg_profit_giveback": None, "stopping_condition_met": False, "stopping_checks": {}}), 200


def _get_banner_state_sync():
    """Same data as /api/direction_banner; used for server-side initial render."""
    try:
        root = Path(_DASHBOARD_ROOT)
        from src.dashboard.direction_banner_state import get_direction_banner_state
        return get_direction_banner_state(root)
    except Exception:
        return {"state": "WAITING", "message": "Direction status unavailable", "detail": "", "severity": "info"}


def _get_situation_data_sync():
    """Same data as /api/situation; used for server-side initial render. Avoids _load_stock_closed_trades on page load for speed; closed/open may be 0/None until JS refresh."""
    try:
        root = Path(_DASHBOARD_ROOT)
        state_dir = root / "state"
        reports_dir = root / "reports"
        today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        trades_reviewed = trades_reviewed_total = 0
        try:
            rpath = state_dir / "direction_readiness.json"
            if rpath.exists():
                data = json.loads(rpath.read_text(encoding="utf-8"))
                trades_reviewed = int(data.get("telemetry_trades") or 0)
                trades_reviewed_total = int(data.get("total_trades") or 0)
        except Exception:
            pass
        if trades_reviewed == 0 and trades_reviewed_total == 0:
            try:
                from src.governance.direction_readiness import count_direction_intel_backed_trades_tail

                trades_reviewed_total, trades_reviewed, _ = count_direction_intel_backed_trades_tail(root)
            except Exception:
                pass
        promotion_recommendation, promotion_score, promotion_reasons = "WAIT", None, []
        try:
            comb_path = reports_dir / f"{today}_stock-bot_combined.json"
            if comb_path.exists():
                comb = json.loads(comb_path.read_text(encoding="utf-8", errors="replace"))
                sc = comb.get("strategy_comparison") or {}
                if isinstance(sc, dict):
                    promotion_recommendation = sc.get("recommendation", "WAIT")
                    promotion_score = sc.get("promotion_readiness_score")
                    promotion_reasons = (sc.get("reasons") or [])[:5]
        except Exception:
            pass
        governance_joined_count = None
        try:
            gov_dir = root / "reports" / "equity_governance"
            if gov_dir.exists():
                runs = sorted(gov_dir.glob("equity_governance_*"), key=lambda p: p.stat().st_mtime, reverse=True)
                for run_dir in runs[:1]:
                    dec_path = run_dir / "lock_or_revert_decision.json"
                    if dec_path.exists():
                        dec = json.loads(dec_path.read_text(encoding="utf-8"))
                        governance_joined_count = (dec.get("candidate") or {}).get("joined_count")
                        break
        except Exception:
            pass
        closed_trades_count = 0
        open_positions_count = None
        try:
            closed_trades_count = len(_load_stock_closed_trades())
        except Exception:
            pass
        try:
            ip_path = state_dir / "internal_positions.json"
            if ip_path.exists():
                data = json.loads(ip_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, list):
                    open_positions_count = len(data)
                elif isinstance(data, dict) and "positions" in data:
                    open_positions_count = len(data.get("positions") or [])
            if open_positions_count is None and state_dir.joinpath("position_metadata.json").exists():
                data = json.loads((state_dir / "position_metadata.json").read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, dict):
                    open_positions_count = len([k for k in data if k and not str(k).startswith("_")])
        except Exception:
            pass
        total_post_era = 0
        next_ms = None
        rem_ms = None
        try:
            from src.governance.canonical_trade_count import compute_canonical_trade_count

            ctc = compute_canonical_trade_count(root, floor_epoch=None)
            total_post_era = int(ctc.get("total_trades_post_era") or 0)
            nm = ctc.get("next_milestone")
            next_ms = int(nm) if nm is not None else None
            rem_ms = int(ctc.get("remaining_to_next_milestone") or 0)
        except Exception:
            pass
        return {
            "trades_reviewed": trades_reviewed,
            "trades_reviewed_total": trades_reviewed_total,
            "trades_reviewed_target": 100,
            "total_trades_post_era": total_post_era,
            "next_trade_milestone": next_ms,
            "remaining_to_next_milestone": rem_ms,
            "promotion_recommendation": promotion_recommendation,
            "promotion_score": promotion_score,
            "promotion_reasons": promotion_reasons,
            "governance_joined_count": governance_joined_count,
            "closed_trades_count": closed_trades_count,
            "open_positions_count": open_positions_count,
        }
    except Exception:
        return {
            "trades_reviewed": 0,
            "trades_reviewed_total": 0,
            "total_trades_post_era": 0,
            "next_trade_milestone": None,
            "remaining_to_next_milestone": None,
            "promotion_recommendation": "WAIT",
            "closed_trades_count": 0,
            "open_positions_count": None,
        }


def _escape_html(s):
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def _render_initial_banner_html(state):
    """Render direction banner HTML for server-side first paint. Never returns 'Loading...'."""
    if not state:
        return _escape_html("Direction status unavailable"), "info"
    msg = _escape_html(state.get("message") or "")
    detail = _escape_html(state.get("detail") or "")
    link = _escape_html(state.get("link") or "")
    severity = (state.get("severity") or "info").strip()
    out = msg
    if detail:
        out += ' <span style="opacity:0.9;">' + detail + "</span>"
    if link:
        out += ' <a href="' + link + '" target="_blank" rel="noopener">View report</a>'
    return out, severity


def _render_initial_situation_html(data):
    """Render situation strip HTML for server-side first paint. Never returns 'Loading...'."""
    if not data or data.get("error"):
        return '<span class="sit-label">Situation</span><span class="sit-value">—</span>'
    n = data.get("total_trades_post_era")
    if n is None:
        n = 0
    next_m = data.get("next_trade_milestone")
    if next_m is None:
        next_m = "—"
    rem = data.get("remaining_to_next_milestone")
    if rem is None:
        rem = "—"
    rec = ((data.get("promotion_recommendation") or "WAIT") or "WAIT").upper()
    score = data.get("promotion_score")
    reasons = data.get("promotion_reasons") or []
    gov = data.get("governance_joined_count")
    closed = data.get("closed_trades_count", 0) or 0
    open_ = data.get("open_positions_count")
    rec_cls = "promote" if rec == "PROMOTE" else ("dnp" if rec == "DO NOT PROMOTE" else "wait")
    promo = '<span class="promo-badge ' + rec_cls + '">' + rec + ((' ' + str(score) + '/100') if score is not None else '') + "</span>"
    if reasons:
        promo += ' <span style="opacity:0.85;">(' + _escape_html("; ".join(reasons[:2])) + ")</span>"
    h = (
        '<span class="sit-label">Total trades (post-era):</span><span class="sit-value">'
        + str(n)
        + '</span> <span class="sit-label">Next milestone:</span><span class="sit-value">'
        + str(next_m)
        + '</span> <span class="sit-label">Remaining:</span><span class="sit-value">'
        + str(rem)
        + "</span>"
    )
    h += ' <span class="sit-label">Promotion:</span> ' + promo
    if gov is not None:
        h += ' <span class="sit-label">Governance (joined):</span><span class="sit-value">' + str(gov) + "</span>"
    h += ' <span class="sit-label">Closed (90d):</span><span class="sit-value">' + str(closed) + "</span>"
    h += ' <span class="sit-label">Open:</span><span class="sit-value">' + (str(open_) if open_ is not None else "—") + "</span>"
    return h


def _wheel_ledger_safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _wheel_ledger_fmt_day(ts: Any) -> str:
    if ts is None:
        return "—"
    s = str(ts).strip()
    if not s or s == "—":
        return "—"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return s[:16] if len(s) > 16 else s


def _wheel_ledger_parse_ts(raw: Any) -> float:
    if raw is None or raw == "—":
        return 0.0
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _ledger_rows_from_wheel_state(state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Build closed-trade rows from ``csp_history`` in wheel_state.json.
    CC closes / OTM expiry without reconciliation may not appear here.
    """
    hist = state.get("csp_history") if isinstance(state, dict) else None
    if not isinstance(hist, list):
        return [], 0.0

    out: List[Dict[str, Any]] = []
    total = 0.0

    for raw in hist:
        if not isinstance(raw, dict):
            continue
        sym = (
            str(raw.get("underlying_symbol") or raw.get("underlying") or "").strip().upper()
            or "—"
        )
        status = str(raw.get("status") or "").strip().lower()
        opened = raw.get("opened_at") or raw.get("openedAt")
        closed_raw = raw.get("closed_at") or raw.get("closedAt")

        oc = _wheel_ledger_safe_float(raw.get("open_credit"))
        cl = _wheel_ledger_safe_float(raw.get("close_limit"))
        try:
            qty = max(1, int(float(raw.get("qty") or 1)))
        except (TypeError, ValueError):
            qty = 1

        exit_reason = status or "RECORDED"
        exit_display = _wheel_ledger_fmt_day(closed_raw)
        sort_ts = _wheel_ledger_parse_ts(closed_raw) or _wheel_ledger_parse_ts(opened)

        if status == "assigned":
            exit_reason = "ASSIGNED (CSP → stock)"
            exit_display = "—"
            pnl = oc
        elif status.startswith("closed_"):
            exit_reason = status.upper().replace("_", " ")
            if oc is not None and cl is not None:
                pnl = oc - (cl * 100.0 * qty)
            else:
                pnl = oc
        else:
            exit_reason = (status or "LEGACY / UNKNOWN").upper()
            pnl = oc

        pnl_fin: Optional[float]
        if pnl is None:
            pnl_fin = None
        else:
            pnl_fin = round(float(pnl), 2)
            total += pnl_fin

        row = {
            "symbol": sym,
            "side": "SHORT PUT (CSP)",
            "entry_date": _wheel_ledger_fmt_day(opened),
            "exit_date": exit_display,
            "_sort_ts": sort_ts,
            "realized_pnl_usd": pnl_fin,
            "exit_reason": exit_reason,
        }
        out.append(row)

    out.sort(key=lambda r: float(r.get("_sort_ts") or 0.0), reverse=True)
    for r in out:
        r.pop("_sort_ts", None)

    return out, round(total, 2)


def _wheel_closed_trades_payload() -> Dict[str, Any]:
    from config.registry import StateFiles, read_json

    state = read_json(StateFiles.WHEEL_STATE, default={})
    rows, total = _ledger_rows_from_wheel_state(state if isinstance(state, dict) else {})
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_realized_pnl_usd": total,
        "rows": rows,
        "note": "Sourced from state/wheel_state.json `csp_history` (buy-to-close exits + assignments). "
        "OTM CSP expiry without a history row will not appear.",
    }


@app.route("/")
def index():
    """Institutional V3 HUD — Tailwind shell in ``templates/index.html``."""
    try:
        cp = _wheel_closed_trades_payload()
    except Exception:
        cp = {
            "rows": [],
            "total_realized_pnl_usd": 0.0,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": "wheel_closed_trades_bootstrap_failed",
        }
    return render_template(
        "index.html",
        wheel_closed_rows=cp.get("rows") or [],
        wheel_closed_total_pnl=cp.get("total_realized_pnl_usd") or 0.0,
        wheel_closed_generated=cp.get("generated_at_utc"),
    )


def _health_payload():
    """Build /health JSON (cached for a few seconds to absorb polling)."""
    try:
        from sre_monitoring import get_sre_health

        sre_health = get_sre_health()
        overall_health = sre_health.get("overall_health", "unknown")

        bot_running = False
        try:
            result = subprocess.run(
                ["pgrep", "-f", "python.*main.py"],
                capture_output=True,
                timeout=2,
            )
            bot_running = result.returncode == 0
        except Exception:
            pass

        return (
            {
                "status": "healthy" if overall_health == "healthy" and bot_running else "degraded",
                "overall_health": overall_health,
                "bot_running": bot_running,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dependencies_loaded": _registry_loaded,
                "alpaca_connected": _alpaca_api is not None,
                "sre_health": {
                    "market_open": sre_health.get("market_open", False),
                    "last_order": sre_health.get("last_order", {}),
                },
            },
            200,
        )
    except Exception as e:
        return (
            {
                "status": "unknown",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dependencies_loaded": _registry_loaded,
                "alpaca_connected": _alpaca_api is not None,
            },
            500,
        )


@app.route("/health")
def health():
    """Health check endpoint - checks actual system health"""
    payload, code = _dash_cache_get("health_v1", _health_payload)
    return jsonify(payload), code


@app.route("/api/version", methods=["GET"])
def api_version():
    """
    Source of truth for dashboard build/version contract. Never raises; returns 503 with reason_code on error.
    """
    try:
        git_commit = os.getenv("GIT_COMMIT", "").strip()
        if not git_commit:
            for git_cmd in ("git", "/usr/bin/git"):
                try:
                    r = subprocess.run(
                        [git_cmd, "rev-parse", "HEAD"],
                        cwd=_DASHBOARD_ROOT,
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if r.returncode == 0 and r.stdout:
                        git_commit = r.stdout.strip()
                        break
                except Exception:
                    continue
        git_commit_short = (git_commit[:7] if git_commit else "")
        expected = os.getenv("EXPECTED_GIT_COMMIT", "").strip()
        payload = {
            "service": "stock-bot-dashboard",
            "git_commit": git_commit,
            "git_commit_short": git_commit_short,
            "build_time_utc": _BUILD_TIME_UTC,
            "process_start_time_utc": _PROCESS_START_TIME_UTC,
            "python_version": sys.version,
            "cwd": os.getcwd(),
        }
        if expected:
            payload["matches_expected"] = git_commit == expected
        return jsonify(payload)
    except Exception as e:
        return (
            jsonify({"error": str(e), "reason_code": "version_unavailable"}),
            503,
            {"Content-Type": "application/json"},
        )


@app.route("/api/versions", methods=["GET"])
def api_versions():
    """Multi-universe versioning: live, paper, shadow (version + commit per mode)."""
    try:
        from config.version_loader import get_all_versions
        data = get_all_versions()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "live": {"version": "", "commit": None},
            "paper": {"version": "", "commit": None},
            "shadow": {"version": "", "commit": None},
            "error": str(e),
        })


def _open_position_entry_context_display(meta: dict) -> str:
    """
    Human-readable entry line from position_metadata only (read-only; no trading-path changes).
    Prefer explicit reason fields; otherwise synthesize from persisted regime/direction/components.
    """
    if not isinstance(meta, dict):
        return "—"
    raw = meta.get("final_decision_primary_reason") or meta.get("entry_reason")
    if raw is not None and str(raw).strip():
        return str(raw).strip()[:240]
    parts: list[str] = []
    mr = meta.get("market_regime")
    if mr is not None and str(mr).strip() and str(mr).strip().lower() != "unknown":
        parts.append(f"regime={str(mr).strip()[:40]}")
    dr = meta.get("direction")
    if dr is not None and str(dr).strip() and str(dr).strip().lower() != "unknown":
        parts.append(f"dir={str(dr).strip()[:32]}")
    ig = meta.get("ignition_status")
    if ig is not None and str(ig).strip() and str(ig).strip().lower() != "unknown":
        parts.append(f"ignition={str(ig).strip()[:28]}")
    vid = meta.get("variant_id")
    if vid is not None and str(vid).strip() and str(vid).strip().lower() != "unknown":
        parts.append(f"variant={str(vid).strip()[:28]}")
    try:
        rm = meta.get("regime_modifier")
        if rm is not None and float(rm) != 1.0:
            parts.append(f"reg_mod={float(rm):.2f}")
    except (TypeError, ValueError):
        pass
    comps = meta.get("components")
    if isinstance(comps, dict) and comps:
        scored: list[tuple[float, str, float]] = []
        for k, v in comps.items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if abs(fv) > 1e-9:
                scored.append((abs(fv), str(k)[:32], fv))
        scored.sort(reverse=True)
        for _, k, fv in scored[:5]:
            parts.append(f"{k}={fv:.2f}")
    v2 = meta.get("v2")
    if isinstance(v2, dict):
        ver = v2.get("uw_intel_version")
        if ver is not None and str(ver).strip():
            parts.append(f"uw_intel={str(ver).strip()[:24]}")
    if not parts:
        return "—"
    out = "; ".join(parts)
    if len(out) > 240:
        return out[:237] + "…"
    return out


def _api_positions_impl():
    """Inner implementation so we can run it with a timeout (prevents dashboard stuck)."""
    if _alpaca_api is None:
        return {
            "positions": [],
            "total_value": 0,
            "unrealized_pnl": 0,
            "day_pnl": 0,
            "error": "Alpaca API not connected",
            "missed_alpha_usd": 0,
            "account_equity": None,
            "account_last_equity": None,
            "account_buying_power": None,
            "broker_currency": None,
        }
    positions = _alpaca_api.list_positions()
    account = _alpaca_api.get_account()

    # CRITICAL FIX: Load entry scores from position metadata (resolve against repo root so cwd-independent)
    metadata = {}
    try:
        from config.registry import StateFiles, read_json
        metadata_path = (Path(_DASHBOARD_ROOT) / StateFiles.POSITION_METADATA).resolve()
        if metadata_path.exists():
            metadata = read_json(metadata_path, default={})
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load position metadata: {e}", flush=True)

    def _underlying_for_position(alpaca_symbol: str, asset_class: str) -> str:
        """Underlying root for options (first chars); equity uses symbol as-is."""
        if getattr(asset_class, "lower", lambda: "")() == "option" and len(alpaca_symbol) >= 6:
            return alpaca_symbol[:6]
        return alpaca_symbol

    # Load UW cache for current score calculation (paths resolved against repo root for cwd-independence)
    uw_cache = {}
    current_regime = "mixed"
    try:
        from config.registry import CacheFiles, read_json, StateFiles
        import json as json_module
        cache_file = (Path(_DASHBOARD_ROOT) / CacheFiles.UW_FLOW_CACHE).resolve()
        if cache_file.exists():
            uw_cache = read_json(cache_file, default={})
        for regime_file in [getattr(StateFiles, "REGIME_DETECTOR_STATE", None), StateFiles.REGIME_DETECTOR]:
            if not regime_file:
                continue
            rp = (Path(_DASHBOARD_ROOT) / regime_file).resolve()
            if rp.exists():
                try:
                    regime_data = json_module.loads(rp.read_text())
                    if isinstance(regime_data, dict):
                        current_regime = regime_data.get("current_regime") or regime_data.get("regime") or "mixed"
                        break
                except Exception:
                    pass
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load UW cache for current scores: {e}", flush=True)

    # Signal propagation: prefer persisted signal_strength_cache (paths resolved against repo root)
    signal_strength_cache = {}
    try:
        from config.registry import StateFiles
        cache_path = getattr(StateFiles, "SIGNAL_STRENGTH_CACHE", None)
        if cache_path:
            cp = (Path(_DASHBOARD_ROOT) / cache_path).resolve()
            if cp.exists():
                signal_strength_cache = json.loads(cp.read_text(encoding="utf-8", errors="replace")) or {}
        if not isinstance(signal_strength_cache, dict):
            signal_strength_cache = {}
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load signal_strength_cache: {e}", flush=True)

    pos_list = []
    for p in positions:
        symbol = p.symbol
        asset_class = getattr(p, "asset_class", None) or "us_equity"
        underlying = _underlying_for_position(symbol, asset_class)
        strategy_id = (metadata.get(symbol, {}) or {}).get("strategy_id") or (metadata.get(underlying, {}) or {}).get("strategy_id") or "equity"
        meta = (metadata.get(symbol, metadata.get(underlying, {})) or {}) if metadata else {}
        entry_score = meta.get("entry_score")
        if entry_score is None or (isinstance(entry_score, (int, float)) and float(entry_score) <= 0):
            try:
                from utils.entry_score_recovery import recover_entry_score_for_symbol
                recovered = recover_entry_score_for_symbol(symbol, pop_pending=False)
                if recovered is not None and float(recovered) > 0:
                    entry_score = float(recovered)
            except Exception:
                pass
        if entry_score is None or (isinstance(entry_score, (int, float)) and float(entry_score) <= 0):
            entry_score = 0.0
        else:
            entry_score = float(entry_score)
        current_score = None
        current_signal_evaluated = False
        cached = signal_strength_cache.get(symbol) if isinstance(signal_strength_cache.get(symbol), dict) else None
        prev_score = None
        signal_delta = None
        signal_trend = None
        if cached is not None and "signal_strength" in cached:
            try:
                current_score = float(cached["signal_strength"])
                current_signal_evaluated = True
                if "prev_signal_strength" in cached and cached["prev_signal_strength"] is not None:
                    try:
                        prev_score = float(cached["prev_signal_strength"])
                    except (TypeError, ValueError):
                        pass
                if "signal_delta" in cached and cached["signal_delta"] is not None:
                    try:
                        signal_delta = float(cached["signal_delta"])
                    except (TypeError, ValueError):
                        pass
                signal_trend = cached.get("signal_trend") if isinstance(cached.get("signal_trend"), str) else None
            except (TypeError, ValueError):
                pass
        if not current_signal_evaluated:
            try:
                if uw_cache and symbol in uw_cache:
                    enriched = uw_cache.get(symbol, {})
                    if enriched:
                        import uw_composite_v2 as uw_v2
                        try:
                            import uw_enrichment_v2 as uw_enrich
                            enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, current_regime) or enriched
                        except Exception:
                            enriched_live = enriched
                        composite = uw_v2.compute_composite_score_v2(symbol, enriched_live, current_regime)
                        if composite:
                            current_score = float(composite.get("score", 0.0))
                            current_signal_evaluated = True
            except Exception as e:
                print(f"[Dashboard] Warning: Failed to compute current score for {symbol}: {e}", flush=True)
            if not current_signal_evaluated:
                print(f"[Dashboard] Warning: No signal evaluation for open position {symbol}; show as N/A (run engine so open_position_refresh runs).", flush=True)
        # When entry was high but current score is very low, signal data may be stale (e.g. injected test or weak flow).
        current_score_val = float(current_score) if current_score is not None else None
        current_score_likely_stale = (
            current_signal_evaluated
            and entry_score >= 3.0
            and current_score_val is not None
            and current_score_val < 0.5
        )
        entry_ts_raw = meta.get("entry_ts") or meta.get("entry_timestamp") or ""
        entry_reason_raw = meta.get("final_decision_primary_reason") or meta.get("entry_reason")
        entry_ctx = _open_position_entry_context_display(meta)
        v2_blk = meta.get("v2") if isinstance(meta.get("v2"), dict) else {}
        v2_nonempty = len(v2_blk) > 0
        repaired_sf = v2_blk.get("repaired_from") == "scoring_flow.jsonl" and bool(meta.get("metadata_repair"))
        metadata_instrumented = bool(float(entry_score) > 0 and v2_nonempty and not repaired_sf)
        metadata_reconciled_only = bool(float(entry_score) > 0 and repaired_sf)
        era_legacy = False
        try:
            from utils.era_cut import entry_ts_is_before_era_cut

            era_legacy = bool(entry_ts_is_before_era_cut(entry_ts_raw))
        except Exception:
            era_legacy = False
        gap_flags = []
        if era_legacy:
            # Pre-era-cut rows: do not surface metadata gaps for governance certification views.
            gap_flags = []
        else:
            if float(entry_score) <= 0:
                gap_flags.append("entry_score_missing")
            if not v2_nonempty:
                gap_flags.append("v2_block_missing")
            if not entry_reason_raw:
                gap_flags.append("entry_reason_missing")
        # Capital at entry (notional): |qty| × avg_entry_price (same units as Alpaca position fields).
        _qty_abs = abs(float(p.qty))
        _avg_entry = float(p.avg_entry_price)
        _total_outlay = round(_qty_abs * _avg_entry, 2)
        pos_list.append({
            "symbol": symbol,
            "side": "long" if float(p.qty) > 0 else "short",
            "qty": _qty_abs,
            "avg_entry_price": _avg_entry,
            "current_price": float(p.current_price),
            "market_value": abs(float(p.market_value)),
            "unrealized_pnl": float(p.unrealized_pl),
            "unrealized_pnl_pct": float(p.unrealized_plpc) * 100,
            "total_outlay": _total_outlay,
            "entry_score": float(entry_score),
            "metadata_instrumented": metadata_instrumented,
            "metadata_reconciled_repair_only": metadata_reconciled_only,
            "metadata_gap_flags": gap_flags,
            "era_cut_legacy_row": era_legacy,
            "governance_certification_excluded": era_legacy,
            "current_score": current_score_val,
            "current_signal_evaluated": current_signal_evaluated,
            "current_score_likely_stale": current_score_likely_stale,
            "prev_score": float(prev_score) if prev_score is not None else None,
            "signal_delta": float(signal_delta) if signal_delta is not None else None,
            "signal_trend": signal_trend,
            "strategy_id": strategy_id,
            "entry_ts": entry_ts_raw,
            "entry_reason": entry_reason_raw,
            # Open positions: synthesized from metadata when no explicit reason (dashboard-only).
            "entry_reason_display": (
                str(entry_reason_raw)[:240] if entry_reason_raw else entry_ctx
            ),
            "entry_context_display": entry_ctx,
            "exit_reason_display": "— (open position)",
            "row_data_source": "Alpaca positions API + state/position_metadata.json",
        })

    missed_alpha_usd = 0.0
    try:
        from shadow_tracker import get_shadow_tracker
        from signal_history_storage import get_signal_history
        signal_history = get_signal_history(limit=120)
        capacity_blocked_signals = [
            s for s in signal_history
            if "capacity_limit" in s.get("decision", "").lower()
            and s.get("final_score", 0) >= 3.0
            and s.get("shadow_created", False)
        ]
        shadow_tracker = get_shadow_tracker()
        base_position_size = float(os.getenv("POSITION_SIZE_USD", "500"))
        for signal in capacity_blocked_signals:
            symbol = signal.get("symbol", "")
            virtual_pnl_pct = signal.get("virtual_pnl", 0.0)
            shadow_pos = shadow_tracker.get_position(symbol)
            if shadow_pos:
                virtual_pnl_pct = shadow_pos.max_profit_pct
            if virtual_pnl_pct is not None and virtual_pnl_pct != 0:
                missed_alpha_usd += (virtual_pnl_pct / 100.0) * base_position_size
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to calculate missed alpha: {e}", flush=True)
        missed_alpha_usd = 0.0

    signal_correlation = {}
    try:
        from config.registry import StateFiles
        corr_path = getattr(StateFiles, "SIGNAL_CORRELATION_CACHE", None)
        if corr_path and corr_path.exists():
            signal_correlation = json.loads(corr_path.read_text(encoding="utf-8", errors="replace")) or {}
        if not isinstance(signal_correlation, dict):
            signal_correlation = {}
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load signal_correlation_cache: {e}", flush=True)

    # Day P&L: prefer session baseline (state/daily_start_equity.json) for accuracy.
    # Broker day_pnl (equity - last_equity) can be misleading if last_equity is from broker's day boundary or stale.
    day_pnl = float(getattr(account, "equity", 0) or 0) - float(getattr(account, "last_equity", 0) or 0)
    try:
        from datetime import datetime as _dt, timezone as _tz
        _date_str = _dt.now(_tz.utc).strftime("%Y-%m-%d")
        _p = (Path(_DASHBOARD_ROOT) / "state" / "daily_start_equity.json").resolve()
        if _p.exists():
            _data = json.loads(_p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(_data, dict) and str(_data.get("date", "")) == _date_str:
                _start = _data.get("equity")
                if _start is not None:
                    _start = float(_start)
                    day_pnl = float(getattr(account, "equity", 0) or 0) - _start
    except Exception:
        pass

    return {
        "positions": pos_list,
        "signal_correlation": signal_correlation,
        "total_value": float(account.portfolio_value),
        "unrealized_pnl": sum(p["unrealized_pnl"] for p in pos_list),
        "day_pnl": round(day_pnl, 2),
        "missed_alpha_usd": round(missed_alpha_usd, 2),
        # Authoritative broker snapshot (same REST calls as Alpaca dashboard / portfolio_value).
        "account_equity": float(getattr(account, "equity", 0) or 0),
        "account_last_equity": float(getattr(account, "last_equity", 0) or 0),
        "account_buying_power": float(getattr(account, "buying_power", 0) or 0),
        "broker_currency": str(getattr(account, "currency", "USD") or "USD"),
    }


def _positions_cached_fetch():
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_api_positions_impl)
        return future.result(timeout=8)


@app.route("/api/positions")
@app.route("/open_positions", methods=["GET"])
def api_positions():
    """Positions endpoint with 8s timeout so dashboard never blocks other tabs."""
    import concurrent.futures

    try:
        result = _dash_cache_get("positions_bundle_v1", _positions_cached_fetch)
    except concurrent.futures.TimeoutError:
        return jsonify(
            {
                "positions": [],
                "total_value": 0,
                "unrealized_pnl": 0,
                "day_pnl": 0,
                "missed_alpha_usd": 0,
                "error": "Request timed out (8s). You can switch tabs.",
            }
        )
    except Exception as e:
        return jsonify(
            {
                "positions": [],
                "total_value": 0,
                "unrealized_pnl": 0,
                "day_pnl": 0,
                "missed_alpha_usd": 0,
                "error": str(e),
            }
        )

    limit = _dash_parse_limit(default=50, cap=200)
    out = dict(result)
    plist = out.get("positions") or []
    if isinstance(plist, list) and len(plist) > limit:
        out["positions"] = plist[:limit]
    out["limit_applied"] = limit
    out["positions_total_before_limit"] = len(plist) if isinstance(plist, list) else 0
    return jsonify(out)


@app.route("/api/pnl/reconcile", methods=["GET"])
def api_pnl_reconcile():
    """
    WHY: Production has conflicting P&L definitions (broker day_pnl vs attribution vs bot session baseline).
    HOW TO VERIFY:
      - broker_day_pnl equals account.equity - account.last_equity
      - window_pnl equals account.equity - state/daily_start_equity.json equity (if present)
      - attribution_closed_pnl_sum matches recomputation from attribution context (within expected differences).
    """
    try:
        if _alpaca_api is None:
            return jsonify({"error": "Alpaca API not connected"}), 503

        date_str = request.args.get("date")
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        account = _alpaca_api.get_account()
        equity_now = float(getattr(account, "equity", 0.0) or 0.0)
        last_equity = float(getattr(account, "last_equity", 0.0) or 0.0)
        broker_day_pnl = equity_now - last_equity

        # Window P&L (session baseline via risk_management daily_start_equity)
        window_pnl = None
        start_equity = None
        try:
            # Avoid importing `risk_management` here: it may import `main` in some runtimes,
            # which can start worker threads inside the dashboard process.
            # This endpoint only needs the persisted baseline written to state/daily_start_equity.json.
            p = (_DASHBOARD_ROOT / "state" / "daily_start_equity.json").resolve()
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
                if isinstance(data, dict) and str(data.get("date", "")) == str(date_str):
                    start_equity = data.get("equity")
                    if start_equity is not None:
                        window_pnl = equity_now - float(start_equity)
        except Exception:
            window_pnl = None

        # Attribution sums for that date (recompute from context when possible)
        def _normalize_position_side(side: str) -> str:
            s = (side or "").strip().lower()
            if s in ("buy", "long"):
                return "long"
            if s in ("sell", "short"):
                return "short"
            return "unknown"

        def _compute_trade_pnl(entry_price, exit_price, qty, position_side: str) -> float:
            try:
                entry_price = float(entry_price)
                exit_price = float(exit_price)
                qty = float(qty)
            except Exception:
                return 0.0
            if entry_price <= 0 or exit_price <= 0 or qty <= 0:
                return 0.0
            if position_side == "long":
                return qty * (exit_price - entry_price)
            if position_side == "short":
                return qty * (entry_price - exit_price)
            return 0.0

        closed_pnl_sum_logged = 0.0
        closed_pnl_sum_recomputed = 0.0
        entered_today_closed_today_sum = 0.0
        recompute_mismatch_count = 0
        counted = 0

        try:
            from config.registry import LogFiles
            attr_path = LogFiles.ATTRIBUTION
            if attr_path.exists():
                with attr_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        ts = rec.get("ts")
                        if not ts or not str(ts).startswith(date_str):
                            continue
                        pnl_usd_logged = float(rec.get("pnl_usd", 0.0) or 0.0)
                        closed_pnl_sum_logged += pnl_usd_logged
                        counted += 1

                        ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
                        entry_ts = ctx.get("entry_ts")
                        if entry_ts and str(entry_ts).startswith(date_str):
                            entered_today_closed_today_sum += pnl_usd_logged

                        # Recompute P&L from context if possible (prefers position_side if present)
                        position_side = ctx.get("position_side") or _normalize_position_side(ctx.get("side"))
                        entry_price = ctx.get("entry_price")
                        exit_price = ctx.get("exit_price")
                        qty = ctx.get("qty")
                        pnl_usd_re = _compute_trade_pnl(entry_price, exit_price, qty, str(position_side).lower())
                        closed_pnl_sum_recomputed += pnl_usd_re
                        if abs(pnl_usd_re - pnl_usd_logged) > 0.05:
                            recompute_mismatch_count += 1
        except Exception:
            pass

        payload = {
            "date": date_str,
            "equity_now": equity_now,
            "last_equity": last_equity,
            "broker_day_pnl": broker_day_pnl,
            "daily_start_equity": start_equity,
            "window_pnl": window_pnl,
            "attribution_closed_pnl_sum_logged": round(closed_pnl_sum_logged, 2),
            "attribution_closed_pnl_sum_recomputed": round(closed_pnl_sum_recomputed, 2),
            "attribution_entered_today_closed_today_sum": round(entered_today_closed_today_sum, 2),
            "attribution_records_counted": counted,
            "recompute_mismatch_count": recompute_mismatch_count,
            "notes": [
                "broker_day_pnl is equity_now - last_equity (broker day).",
                "window_pnl is equity_now - daily_start_equity (session baseline), if daily_start_equity is available.",
                "attribution_* sums are from logs/attribution.jsonl for records whose ts startswith date.",
                "logged vs recomputed differences indicate attribution integrity issues (should shrink after fixes).",
            ],
        }

        try:
            from config.registry import append_jsonl, LogFiles
            append_jsonl(LogFiles.PNL_RECONCILIATION, payload)
        except Exception:
            pass

        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _dashboard_pick_entry_reason(context: dict) -> str | None:
    if not isinstance(context, dict):
        return None
    for k in ("final_decision_primary_reason", "entry_signal", "primary_entry_reason"):
        v = context.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()[:240]
    return None


def _dashboard_fee_usd_from_rec(rec: dict, context: dict | None) -> float | None:
    ctx = context if isinstance(context, dict) else {}
    for k in ("fees_usd", "commission_usd", "fee_usd"):
        v = rec.get(k)
        if v is None:
            v = ctx.get(k)
        if v is not None:
            try:
                return round(float(v), 4)
            except (TypeError, ValueError):
                pass
    return None


def _strict_alpaca_chain_badge(trade_id: str | None, gate: dict | None, gate_error: str | None) -> str:
    """Per-row label from one evaluate_completeness snapshot; no hidden defaults."""
    if gate_error:
        return f"UNAVAILABLE: {gate_error[:120]}"
    tid = str(trade_id or "").strip()
    if not tid.startswith("open_"):
        return "NOT_APPLICABLE"
    if not gate:
        return "UNKNOWN"
    inc = {
        str(x.get("trade_id"))
        for x in (gate.get("incomplete_examples") or [])
        if x.get("trade_id")
    }
    if tid in inc:
        return "INCOMPLETE"
    if gate.get("LEARNING_STATUS") == "ARMED" and int(gate.get("trades_seen") or 0) > 0:
        return "COMPLETE"
    try:
        import re

        from telemetry.alpaca_strict_completeness_gate import (
            STRICT_EPOCH_START,
            _open_epoch_from_trade_id,
        )

        tid_re = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
        oep = _open_epoch_from_trade_id(tid, tid_re)
        if oep is not None and oep < STRICT_EPOCH_START:
            return "EXCLUDED_PREERA"
    except Exception:
        pass
    if int(gate.get("trades_seen") or 0) == 0:
        return "VACUOUS_STRICT_COHORT"
    return "UNKNOWN"


def _load_stock_closed_trades(max_days=90, max_attribution_lines=10000, max_telemetry_lines=500):
    """
    Load closed trades from attribution.jsonl and exit_attribution.jsonl (equity-focused).
    Omits legacy options-strategy rows (strategy_id filtered). option_phase and option metadata
    are populated from attribution context when present.
    """
    from pathlib import Path
    from datetime import datetime, timezone, timedelta
    try:
        from config.registry import LogFiles
        attr_path = (_DASHBOARD_ROOT / LogFiles.ATTRIBUTION).resolve()
        exit_attr_path = (_DASHBOARD_ROOT / LogFiles.EXIT_ATTRIBUTION).resolve()
    except ImportError:
        attr_path = (_DASHBOARD_ROOT / "logs" / "attribution.jsonl").resolve()
        exit_attr_path = (_DASHBOARD_ROOT / "logs" / "exit_attribution.jsonl").resolve()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_days)).isoformat()[:10]
    out = []
    seen_keys = set()  # (symbol, ts_precision) for deduplication
    # 1) Attribution: closed trades (strategy_id and options context from engine when present)
    if attr_path.exists():
        line_count = 0
        with attr_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_count += 1
                if line_count > max_attribution_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "attribution":
                    continue
                trade_id = rec.get("trade_id", "")
                if trade_id and str(trade_id).startswith("open_"):
                    continue
                symbol = str(rec.get("symbol", "")).upper()
                if not symbol or "TEST" in symbol:
                    continue
                context = rec.get("context") or {}
                if not isinstance(context, dict):
                    context = {}
                pnl_usd = float(rec.get("pnl_usd", 0) or 0)
                close_reason = context.get("close_reason") or rec.get("close_reason") or ""
                if pnl_usd == 0 and not (close_reason and close_reason not in ("unknown", "N/A", "")):
                    continue
                ts_str = rec.get("ts") or rec.get("timestamp") or ""
                if not ts_str or str(ts_str)[:10] < cutoff:
                    continue
                strategy_id = rec.get("strategy_id") or "equity"
                er = _dashboard_pick_entry_reason(context)
                fee = _dashboard_fee_usd_from_rec(rec, context)
                row = {
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "timestamp": ts_str,
                    "pnl_usd": round(pnl_usd, 2),
                    "close_reason": close_reason,
                    "trade_id": str(rec.get("trade_id") or ""),
                    "entry_timestamp": context.get("entry_ts") or context.get("entry_timestamp") or "",
                    "exit_timestamp": ts_str,
                    "entry_reason": er if er else None,
                    "entry_reason_display": er if er else "INCOMPLETE",
                    "fees_usd": fee,
                    "fees_display": (f"${fee:.2f}" if fee is not None else "INCOMPLETE"),
                    "data_sources": ["logs/attribution.jsonl"],
                    "option_phase": context.get("phase"),
                    "option_type": context.get("option_type"),
                    "strike": context.get("strike"),
                    "expiry": context.get("expiry"),
                    "dte": context.get("dte"),
                    "delta_at_entry": context.get("delta_at_entry"),
                    "premium": context.get("premium"),
                    "assigned": context.get("assigned"),
                    "called_away": context.get("called_away"),
                }
                key = (symbol, str(ts_str)[:16])
                if key not in seen_keys:
                    seen_keys.add(key)
                    out.append(row)
    # 2) Exit attribution (v2 equity exits): supplementary source per MEMORY_BANK 7.12
    if exit_attr_path.exists():
        try:
            lines = exit_attr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-3000:]
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                symbol = str(rec.get("symbol", "")).upper()
                if not symbol or "TEST" in symbol:
                    continue
                ts_str = rec.get("timestamp") or rec.get("exit_timestamp") or ""
                if not ts_str or str(ts_str)[:10] < cutoff:
                    continue
                pnl = rec.get("pnl")
                pnl_usd = float(pnl) if pnl is not None else None
                key = (symbol, str(ts_str)[:16])
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                er2 = _dashboard_pick_entry_reason(rec if isinstance(rec, dict) else {})
                fee2 = _dashboard_fee_usd_from_rec(rec, None)
                tid_e = str(rec.get("trade_id") or "")
                row = {
                    "strategy_id": "equity",
                    "symbol": symbol,
                    "timestamp": ts_str,
                    "pnl_usd": round(pnl_usd, 2) if pnl_usd is not None else None,
                    "close_reason": rec.get("exit_reason") or "",
                    "trade_id": tid_e,
                    "entry_timestamp": rec.get("entry_timestamp") or "",
                    "exit_timestamp": ts_str,
                    "entry_reason": er2 if er2 else None,
                    "entry_reason_display": er2 if er2 else "INCOMPLETE",
                    "fees_usd": fee2,
                    "fees_display": (f"${fee2:.2f}" if fee2 is not None else "INCOMPLETE"),
                    "data_sources": ["logs/exit_attribution.jsonl"],
                    "option_phase": None,
                    "option_type": None,
                    "strike": None,
                    "expiry": None,
                    "dte": None,
                    "delta_at_entry": None,
                    "premium": None,
                    "assigned": None,
                    "called_away": None,
                }
                out.append(row)
        except Exception:
            pass
    _ = max_telemetry_lines  # legacy signature; telemetry merge removed
    out = [r for r in out if (r.get("strategy_id") or "equity").lower() == "equity"]
    out.sort(key=lambda x: (x.get("timestamp") or ""), reverse=True)
    return out[:500]


def _stockbot_closed_trades_bundle():
    """
    Full closed-trades payload (cached); per-request ?limit= slices without re-reading logs.
    """
    trades = _load_stock_closed_trades()
    gate = None
    gate_err = None
    try:
        from telemetry.alpaca_strict_completeness_gate import (
            STRICT_EPOCH_START,
            evaluate_completeness,
        )

        gate = evaluate_completeness(
            Path(_DASHBOARD_ROOT), open_ts_epoch=STRICT_EPOCH_START, audit=False
        )
    except Exception as e:
        gate_err = str(e)
    asg = None
    if gate:
        asg = {
            "LEARNING_STATUS": gate.get("LEARNING_STATUS"),
            "learning_fail_closed_reason": gate.get("learning_fail_closed_reason"),
            "trades_seen": gate.get("trades_seen"),
            "trades_complete": gate.get("trades_complete"),
            "trades_incomplete": gate.get("trades_incomplete"),
            "STRICT_EPOCH_START": gate.get("STRICT_EPOCH_START"),
        }
    for t in trades:
        t["strict_alpaca_chain"] = _strict_alpaca_chain_badge(t.get("trade_id"), gate, gate_err)
    return {
        "closed_trades": trades,
        "response_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "alpaca_strict_summary": asg,
        "alpaca_strict_eval_error": gate_err,
    }


@app.route("/api/stockbot/closed_trades", methods=["GET"])
@app.route("/closed_trades", methods=["GET"])
def api_stockbot_closed_trades():
    """
    Closed trades for equity cohort: strategy_id, option_phase, option_type, strike, expiry, etc.
    Legacy options-strategy rows are excluded from the merged list.
    """
    try:
        base = _dash_cache_get("stockbot_closed_trades_v1", _stockbot_closed_trades_bundle)
        limit = _dash_parse_limit(default=50, cap=100)
        trades = base.get("closed_trades") or []
        if not isinstance(trades, list):
            trades = []
        sliced = trades[:limit]
        return jsonify(
            {
                "closed_trades": sliced,
                "count": len(sliced),
                "count_total_loaded": len(trades),
                "limit_applied": limit,
                "response_generated_at_utc": base.get("response_generated_at_utc"),
                "alpaca_strict_summary": base.get("alpaca_strict_summary"),
                "alpaca_strict_eval_error": base.get("alpaca_strict_eval_error"),
            }
        ), 200
    except Exception as e:
        return jsonify({"closed_trades": [], "count": 0, "error": str(e)}), 200


def _load_fast_lane_ledger():
    """Load Alpaca fast-lane shadow ledger (25-trade cycles). Read-only from state/fast_lane_experiment/."""
    try:
        ledger_path = Path(_DASHBOARD_ROOT) / "state" / "fast_lane_experiment" / "fast_lane_ledger.json"
        if not ledger_path.exists():
            return {"cycles": [], "total_trades": 0, "cumulative_pnl": 0.0}
        data = json.loads(ledger_path.read_text(encoding="utf-8", errors="replace"))
        cycles = data if isinstance(data, list) else []
        total_trades = sum(c.get("trade_count", 0) for c in cycles)
        cumulative_pnl = sum(c.get("pnl_usd", 0) for c in cycles)
        return {"cycles": cycles, "total_trades": total_trades, "cumulative_pnl": cumulative_pnl}
    except Exception as e:
        return {"cycles": [], "total_trades": 0, "cumulative_pnl": 0.0, "error": str(e)}


@app.route("/api/stockbot/fast_lane_ledger", methods=["GET"])
def api_stockbot_fast_lane_ledger():
    """Alpaca fast-lane 25-trade cycle ledger: PnL per cycle and cumulative. Shadow-only; no execution impact."""
    try:
        data = _load_fast_lane_ledger()
        cyc = data.get("cycles") if isinstance(data, dict) else None
        if isinstance(cyc, list) and len(cyc) > 50:
            data = dict(data)
            data["cycles"] = cyc[-50:]
            data["cycles_total_before_cap"] = len(cyc)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"cycles": [], "total_trades": 0, "cumulative_pnl": 0.0, "error": str(e)}), 200


def _wheel_hud_bundle():
    """Wheel HUD: prefer ``wheel_dashboard_sink.json``; fallback builds from ``wheel_state`` + epoch only."""
    from config.registry import StateFiles, read_json

    try:
        p = StateFiles.WHEEL_DASHBOARD_SINK
        if p.exists():
            data = read_json(p, default={})
            if isinstance(data, dict) and isinstance(data.get("rows"), list):
                return data
    except Exception:
        pass
    try:
        from src.wheel_dashboard_sink import minimal_sink_from_files

        return minimal_sink_from_files()
    except Exception as e:
        return {
            "schema_version": 1,
            "rows": [],
            "drift_alerts": [],
            "error": str(e),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }


def _safe_num(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        x = float(v)
        if x != x:
            return None
        return x
    except (TypeError, ValueError):
        return None


def _enrich_wheel_hud_row(row: dict[str, Any]) -> dict[str, Any]:
    """Premium income vs underlying price-action decomposition for Wheel Matrix."""
    out = dict(row)
    rp = _safe_num(out.get("realized_premium_usd")) or 0.0
    oc = _safe_num(out.get("open_leg_credit_usd")) or 0.0
    out["premium_income_usd"] = round(rp + oc, 2)
    st = str(out.get("stage") or "")
    spot = _safe_num(out.get("spot"))
    strike = _safe_num(out.get("strike"))
    qty = _safe_num(out.get("qty_shares"))
    if st == "CC_STOCK" and qty and spot is not None and strike is not None:
        out["underlying_price_action_usd"] = round((spot - strike) * qty, 2)
    elif st in ("CSP", "CC") and spot is not None and strike is not None:
        out["underlying_price_action_usd"] = round((spot - strike) * 100.0, 2)
    else:
        out["underlying_price_action_usd"] = None
    return out


def _enrich_wheel_hud_payload(data: dict[str, Any]) -> dict[str, Any]:
    rows = data.get("rows")
    if not isinstance(rows, list):
        return data
    out = dict(data)
    out["rows"] = [_enrich_wheel_hud_row(r) for r in rows if isinstance(r, dict)]
    return out


@app.route("/api/stockbot/wheel_hud", methods=["GET"])
def api_stockbot_wheel_hud():
    """Options Wheel HUD (CSP/CC stages, premium roll-up, epoch). Cached a few seconds for polling."""
    try:
        data = _dash_cache_get("stockbot_wheel_hud_v1", _wheel_hud_bundle, ttl_sec=5.0)
        if not isinstance(data, dict):
            data = {"rows": [], "schema_version": 1}
        data = _enrich_wheel_hud_payload(data)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"rows": [], "schema_version": 1, "error": str(e)}), 200


@app.route("/api/stockbot/wheel_closed_trades", methods=["GET"])
def api_stockbot_wheel_closed_trades():
    """Chronological wheel CSP closures from ``csp_history`` + aggregate realized PnL (dashboard ledger)."""
    try:
        payload = _dash_cache_get(
            "stockbot_wheel_closed_trades_v1",
            _wheel_closed_trades_payload,
            ttl_sec=5.0,
        )
        if not isinstance(payload, dict):
            payload = {"rows": [], "total_realized_pnl_usd": 0.0}
        return jsonify(payload), 200
    except Exception as e:
        return jsonify(
            {
                "schema_version": 1,
                "rows": [],
                "total_realized_pnl_usd": 0.0,
                "error": str(e),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ), 200


@app.route("/api/stockbot/quota_status", methods=["GET"])
def api_stockbot_quota_status():
    """UW REST usage (local state) for dashboard quota strip. Alpaca has no single counter here."""
    try:
        from src.uw.uw_client import _load_usage_state, uw_daily_usage_ratio, uw_effective_daily_cap

        st = _load_usage_state()
        ratio = uw_daily_usage_ratio()
        cap = uw_effective_daily_cap()
        calls = int(st.get("calls_today") or 0)
        pct = round(100.0 * float(ratio), 2) if ratio is not None else None
        return jsonify(
            {
                "uw_calls_today": calls,
                "uw_daily_cap_effective": cap,
                "uw_daily_usage_ratio": ratio,
                "uw_daily_usage_pct": pct,
                "alpaca_note": "Alpaca: use broker dashboard for order/fill rate limits (no aggregate in-repo).",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ), 200
    except Exception as e:
        return jsonify({"uw_calls_today": None, "error": str(e)}), 200


@app.route("/api/closed_positions")
def api_closed_positions():
    try:
        closed = []
        state_file = (_DASHBOARD_ROOT / "state" / "closed_positions.json").resolve()
        if state_file.exists():
            data = json.loads(state_file.read_text())
            closed = data if isinstance(data, list) else data.get("positions", [])

        limit = _dash_parse_limit(default=50, cap=100)
        if isinstance(closed, list) and len(closed) > limit:
            closed = closed[-limit:]
        return jsonify({"closed_positions": closed, "limit_applied": limit})
    except Exception as e:
        return jsonify({"closed_positions": [], "error": str(e)})

@app.route("/sre")
def sre_dashboard():
    """Comprehensive SRE monitoring dashboard"""
    return render_template_string(SRE_DASHBOARD_HTML)

@app.route("/api/system/health", methods=["GET"])
def api_system_health():
    """Get aggregated system health from supervisor health.json (Risk #9)."""
    try:
        from pathlib import Path
        import json
        from datetime import datetime, timezone
        
        health_file = (_DASHBOARD_ROOT / "state" / "health.json").resolve()
        if not health_file.exists():
            return jsonify({
                "overall_status": "UNKNOWN",
                "services": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Health file not found"
            }), 200
        
        with open(health_file, 'r') as f:
            health_data = json.load(f)
        
        return jsonify(health_data), 200
    except Exception as e:
        return jsonify({
            "overall_status": "UNKNOWN",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route("/api/system-events", methods=["GET"])
def api_system_events():
    """
    Return last N system events (default 500) with optional filters:
    - subsystem
    - severity
    - symbol
    """
    try:
        limit = 100
        try:
            limit = min(300, max(1, int(request.args.get("limit", "100"))))
        except Exception:
            limit = 100
        subsystem = request.args.get("subsystem") or None
        severity = request.args.get("severity") or None
        symbol = request.args.get("symbol") or None
        try:
            from utils.system_events import read_last_system_events
            rows = read_last_system_events(limit=limit, subsystem=subsystem, severity=severity, symbol=symbol)
        except Exception as e:
            rows = []
        return jsonify({"events": rows})
    except Exception as e:
        return jsonify({"events": [], "error": str(e)}), 500


@app.route("/system-events", methods=["GET"])
def system_events_page():
    """Simple system events panel (permanent observability)."""
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>System Events</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 16px; background: #0b1220; color: #e5e7eb; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
    input, select { padding: 8px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #e5e7eb; }
    button { padding: 8px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; border-bottom: 1px solid #334155; vertical-align: top; font-size: 12px; }
    th { text-align: left; color: #cbd5e1; position: sticky; top: 0; background: #0b1220; }
    .sev-CRITICAL { color: #fecaca; font-weight: 700; }
    .sev-ERROR { color: #fca5a5; font-weight: 600; }
    .sev-WARN { color: #fde68a; font-weight: 600; }
    .sev-INFO { color: #93c5fd; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; white-space: pre-wrap; word-break: break-word; }
  </style>
</head>
<body>
  <h2>System Events (last 100)</h2>
  <div class="row">
    <input id="subsystem" placeholder="subsystem (e.g. gate, exit, order)" />
    <select id="severity">
      <option value="">severity (all)</option>
      <option>CRITICAL</option>
      <option>ERROR</option>
      <option>WARN</option>
      <option>INFO</option>
    </select>
    <input id="symbol" placeholder="symbol (e.g. AAPL)" />
    <button onclick="loadEvents()">Refresh</button>
  </div>
  <table>
    <thead>
      <tr>
        <th style="width: 220px;">timestamp</th>
        <th style="width: 110px;">subsystem</th>
        <th style="width: 120px;">severity</th>
        <th style="width: 220px;">event_type</th>
        <th style="width: 90px;">symbol</th>
        <th>details</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <script>
    async function loadEvents() {
      const subsystem = document.getElementById('subsystem').value.trim();
      const severity = document.getElementById('severity').value.trim();
      const symbol = document.getElementById('symbol').value.trim();
      const params = new URLSearchParams();
      if (subsystem) params.set('subsystem', subsystem);
      if (severity) params.set('severity', severity);
      if (symbol) params.set('symbol', symbol);
      params.set('limit', '500');
      const resp = await fetch('/api/system-events?' + params.toString(), { credentials: 'same-origin' });
      const data = await resp.json();
      const rows = (data && data.events) ? data.events : [];
      const tbody = document.getElementById('tbody');
      tbody.innerHTML = '';
      for (const r of rows) {
        const sev = (r.severity || '').toUpperCase();
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="mono">${r.timestamp || ''}</td>
          <td>${r.subsystem || ''}</td>
          <td class="sev-${sev}">${sev}</td>
          <td class="mono">${r.event_type || ''}</td>
          <td class="mono">${r.symbol || ''}</td>
          <td class="mono">${JSON.stringify(r.details || {}, null, 2)}</td>
        `;
        tbody.appendChild(tr);
      }
    }
    loadEvents();
    setInterval(loadEvents, 15000);
  </script>
</body>
</html>
"""
    return render_template_string(html)

def _get_supervisor_health():
    """Get supervisor health data from health.json (Risk #9)."""
    try:
        from pathlib import Path
        import json
        
        health_file = (_DASHBOARD_ROOT / "state" / "health.json").resolve()
        if health_file.exists():
            with open(health_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def _merge_health_subsystem(health_dict):
    """Merge data/health_status.json (health runner snapshot) into SRE health response."""
    try:
        from config.registry import CacheFiles
        p = CacheFiles.HEALTH_STATUS
        if p.exists() and p.stat().st_size > 0:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            health_dict["health_subsystem"] = {
                "overall": data.get("overall"),
                "checks": data.get("checks"),
                "last_remediation_attempts": data.get("last_remediation_attempts"),
                "health_safe_mode_active": data.get("health_safe_mode_active"),
                "self_heal_required": data.get("self_heal_required"),
                "self_heal_reason_codes": data.get("self_heal_reason_codes", []),
                "active_heal_ids": data.get("active_heal_ids", []),
                "escalations_active": data.get("escalations_active", []),
                "banner_level": data.get("banner_level", "none"),
                "ts": data.get("ts"),
            }
            if data.get("overall") == "fail":
                health_dict["overall_health"] = "critical"
            elif data.get("health_safe_mode_active"):
                health_dict["overall_health"] = "critical"
            elif data.get("banner_level") == "critical":
                health_dict["overall_health"] = "critical"
    except Exception:
        pass


@app.route("/api/sre/health", methods=["GET"])
def api_sre_health():
    """Get comprehensive SRE health data"""
    def _build() -> tuple[dict, int]:
        try:
            import requests

            # Try to get from main bot API first
            try:
                resp = requests.get("http://localhost:8081/api/sre/health", timeout=2)
                if resp.status_code == 200:
                    health_data = resp.json()
                    _merge_health_subsystem(health_data)

                    # Enhance with SRE metrics and RCA fixes
                    try:
                        from sre_diagnostics import get_sre_metrics, SREDiagnostics

                        health_data["sre_metrics"] = get_sre_metrics()
                        health_data["recent_rca_fixes"] = SREDiagnostics().get_recent_fixes(limit=5)
                    except Exception:
                        pass

                    # Same dashboard-side watchdog as fallback path (8081 health may omit it).
                    if not health_data.get("stagnation_watchdog"):
                        try:
                            health_data["stagnation_watchdog"] = _calculate_stagnation_watchdog()
                        except Exception:
                            pass
                    return health_data, 200
            except Exception:
                pass

            # Fallback to local sre_monitoring
            from sre_monitoring import get_sre_health

            health = get_sre_health()

            # Add supervisor health (Risk #9 - Aggregated Health)
            supervisor_health = _get_supervisor_health()
            if supervisor_health:
                health["supervisor_health"] = supervisor_health
                # Override overall_health with supervisor's aggregated health if available
                if supervisor_health.get("overall_status"):
                    supervisor_status = str(supervisor_health["overall_status"]).lower()
                    if supervisor_status == "failed":
                        health["overall_health"] = "critical"
                    elif supervisor_status == "degraded":
                        health["overall_health"] = "degraded"

            # Enhance with SRE metrics and RCA fixes
            try:
                from sre_diagnostics import get_sre_metrics, SREDiagnostics

                health["sre_metrics"] = get_sre_metrics()
                health["recent_rca_fixes"] = SREDiagnostics().get_recent_fixes(limit=5)

                # V3.0: Add Signal Funnel metrics and Stagnation Watchdog
                try:
                    health["signal_funnel"] = _calculate_signal_funnel()
                except Exception:
                    pass

                try:
                    health["stagnation_watchdog"] = _calculate_stagnation_watchdog()
                except Exception as e:
                    print(f"[Dashboard] Warning: Failed to calculate stagnation watchdog: {e}", flush=True)
                    health["stagnation_watchdog"] = {
                        "status": "OK",
                        "alerts_received": 0,
                        "trades_executed": 0,
                        "stagnation_detected": False,
                    }
            except Exception as outer_e:
                print(f"[Dashboard] Warning: Error in SRE health enhancement: {outer_e}", flush=True)
                # Ensure stagnation watchdog is added even if other enhancements fail
                try:
                    health["stagnation_watchdog"] = _calculate_stagnation_watchdog()
                except Exception:
                    health["stagnation_watchdog"] = {
                        "status": "OK",
                        "alerts_received": 0,
                        "trades_executed": 0,
                        "stagnation_detected": False,
                    }

            _merge_health_subsystem(health)
            return health, 200
        except Exception as e:
            return {"error": f"Failed to load SRE health: {str(e)}"}, 500

    payload, code = _dash_cache_get("sre_health_v2", _build, ttl_sec=15.0)
    return jsonify(payload), code


def _read_self_heal_events_fallback(
    path: Path,
    since_ts: Optional[str] = None,
    check_name: Optional[str] = None,
    severity: Optional[str] = None,
    auto_healed: Optional[bool] = None,
    limit: int = 500,
) -> list:
    """Read self_heal_events.jsonl when health module not available (e.g. systemd cwd)."""
    if not path.exists():
        return []
    raw: list = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw.append(json.loads(line))
        except Exception:
            continue
    by_id: dict = {}
    for rec in raw:
        hid = rec.get("heal_id")
        if not hid:
            continue
        if rec.get("_update"):
            if hid in by_id:
                for k, v in rec.items():
                    if k not in ("heal_id", "_update") and v is not None:
                        by_id[hid][k] = v
        else:
            by_id[hid] = dict(rec)
    out = list(by_id.values())
    if since_ts:
        out = [e for e in out if (e.get("ts_detected") or "") >= since_ts]
    if check_name:
        out = [e for e in out if e.get("check_name") == check_name]
    if severity:
        out = [e for e in out if e.get("severity") == severity]
    if auto_healed is not None:
        out = [e for e in out if e.get("auto_healed") is auto_healed]
    out.sort(key=lambda e: e.get("ts_detected") or "", reverse=True)
    return out[:limit]


@app.route("/api/sre/self_heal_events", methods=["GET"])
def api_sre_self_heal_events():
    """Self-healing ledger: durable, queryable events (like closed trades)."""
    try:
        check_name = request.args.get("check_name")
        severity = request.args.get("severity")
        auto_healed = request.args.get("auto_healed")
        since = request.args.get("since")  # ISO ts or "24h" / "7d"
        limit = request.args.get("limit", 200, type=int)
        if auto_healed is not None:
            auto_healed = auto_healed.lower() in ("1", "true", "yes", "y")
        since_ts = None
        if since:
            from datetime import datetime, timezone, timedelta
            if since == "24h":
                since_ts = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            elif since == "7d":
                since_ts = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            else:
                since_ts = since
        events_path = _DASHBOARD_ROOT / "data" / "self_heal_events.jsonl"
        try:
            from config.registry import CacheFiles
            from health.self_heal_events import read_self_heal_events
            events_path = CacheFiles.SELF_HEAL_EVENTS
            events = read_self_heal_events(
                path=events_path,
                since_ts=since_ts,
                check_name=check_name or None,
                severity=severity or None,
                auto_healed=auto_healed,
                limit=limit,
            )
        except ImportError:
            events = _read_self_heal_events_fallback(
                events_path,
                since_ts=since_ts,
                check_name=check_name or None,
                severity=severity or None,
                auto_healed=auto_healed,
                limit=limit,
            )
        return jsonify({"events": events, "count": len(events)}), 200
    except Exception as e:
        return jsonify({"error": str(e), "events": []}), 500


def _tail_lines(path, max_lines=2000):
    """Read last max_lines from file without loading entire file (perf)."""
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            # Read last ~150KB (enough for ~2000 lines); avoid loading 100MB+ files
            size = path.stat().st_size
            chunk = min(150000, size)
            if size > chunk:
                f.seek(max(0, size - chunk))
                f.readline()  # skip partial line
            return f.read().splitlines()[-max_lines:]
    except Exception:
        return []


def _tail_file_lines(path: Path, max_lines: int = 40000, max_chunk_bytes: int = 12_000_000) -> list:
    """
    Read up to max_lines from end of file, reading at most max_chunk_bytes from disk.
    Used for operational-activity scans so huge JSONL files cannot block the dashboard worker.
    """
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            size = path.stat().st_size
            chunk = min(max_chunk_bytes, size)
            if size > chunk:
                f.seek(max(0, size - chunk))
                f.readline()
            lines = f.read().splitlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception:
        return []


def _calculate_signal_funnel():
    """Calculate Signal Funnel metrics: [UW Alerts] -> [Parsed] -> [Scored > 3.0] -> [Orders]"""
    from pathlib import Path
    import json
    from datetime import datetime, timezone, timedelta
    
    try:
        from config.registry import LogFiles, CacheFiles
        
        alerts_count = 0
        parsed_count = 0
        scored_above_3 = 0
        orders_sent = 0
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        uw_logs = [
            (_DASHBOARD_ROOT / CacheFiles.UW_ATTRIBUTION).resolve(),
            (_DASHBOARD_ROOT / "logs" / "uw_flow.jsonl").resolve(),
            (_DASHBOARD_ROOT / "data" / "uw_flow_cache.log.jsonl").resolve(),
        ]
        
        for uw_log in uw_logs:
            if not uw_log.exists():
                continue
            try:
                for line in _tail_lines(uw_log, 2000):
                        try:
                            rec = json.loads(line.strip())
                            ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                            if ts_str:
                                try:
                                    if isinstance(ts_str, (int, float)):
                                        ts_dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                    else:
                                        ts_dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                                        if ts_dt.tzinfo is None:
                                            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                                    if ts_dt >= cutoff:
                                        alerts_count += 1
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                pass
        
        # Count parsed signals (from gate logs or attribution)
        gate_logs = [
            (_DASHBOARD_ROOT / "logs" / "gate.jsonl").resolve(),
            (_DASHBOARD_ROOT / LogFiles.ATTRIBUTION).resolve(),
            (_DASHBOARD_ROOT / "logs" / "composite_attribution.jsonl").resolve(),
        ]
        
        for gate_log in gate_logs:
            if not gate_log.exists():
                continue
            try:
                for line in _tail_lines(gate_log, 2000):
                        try:
                            rec = json.loads(line.strip())
                            ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                            if ts_str:
                                try:
                                    if isinstance(ts_str, (int, float)):
                                        ts_dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                    else:
                                        ts_dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                                        if ts_dt.tzinfo is None:
                                            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                                    if ts_dt >= cutoff:
                                        parsed_count += 1
                                        score = rec.get("signal_score") or rec.get("score") or rec.get("entry_score") or 0.0
                                        try:
                                            if float(score) >= 3.0:
                                                scored_above_3 += 1
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                pass
        
        # Count orders sent (from attribution or orders logs)
        orders_logs = [
            (_DASHBOARD_ROOT / LogFiles.ATTRIBUTION).resolve(),
            (_DASHBOARD_ROOT / LogFiles.ORDERS).resolve(),
            (_DASHBOARD_ROOT / "data" / "live_orders.jsonl").resolve(),
        ]
        
        for orders_log in orders_logs:
            if not orders_log.exists():
                continue
            try:
                for line in _tail_lines(orders_log, 2000):
                        try:
                            rec = json.loads(line.strip())
                            action = rec.get("action", "") or rec.get("event", "") or rec.get("type", "")
                            if "submit" in str(action).lower() or "entry" in str(action).lower() or rec.get("type") == "order":
                                ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                                if ts_str:
                                    try:
                                        if isinstance(ts_str, (int, float)):
                                            ts_dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                        else:
                                            ts_dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                                            if ts_dt.tzinfo is None:
                                                ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                                        if ts_dt >= cutoff:
                                            orders_sent += 1
                                    except Exception:
                                        pass
                        except Exception:
                            continue
            except Exception:
                pass
            if orders_sent > 0:
                break
        
        # Calculate conversion rates
        parsed_rate = (parsed_count / alerts_count * 100) if alerts_count > 0 else 0
        scored_rate = (scored_above_3 / alerts_count * 100) if alerts_count > 0 else 0
        order_rate = (orders_sent / alerts_count * 100) if alerts_count > 0 else 0
        overall_conversion = order_rate  # Overall: alerts -> orders
        
        return {
            "alerts": alerts_count,
            "parsed": parsed_count,
            "scored_above_3": scored_above_3,
            "scored_above_threshold": scored_above_3,  # Frontend expects this name
            "orders_sent": orders_sent,
            "parsed_rate": round(parsed_rate, 2),
            "parsed_rate_pct": round(parsed_rate, 2),  # Frontend expects _pct suffix
            "scored_rate": round(scored_rate, 2),
            "scored_rate_pct": round(scored_rate, 2),  # Frontend expects _pct suffix
            "order_rate": round(order_rate, 2),
            "order_rate_pct": round(order_rate, 2),  # Frontend expects _pct suffix
            "overall_conversion_pct": round(overall_conversion, 2),  # Frontend expects this
            "conversion_healthy": order_rate >= 2.0  # Healthy if > 2% conversion
        }
    except Exception as e:
        return {
            "alerts": 0,
            "parsed": 0,
            "scored_above_3": 0,
            "orders_sent": 0,
            "error": str(e)
        }

def _calculate_stagnation_watchdog():
    """Calculate Stagnation Watchdog: > 50 alerts but 0 trades = STAGNATION status"""
    from pathlib import Path
    import json
    from datetime import datetime, timezone, timedelta
    
    try:
        from config.registry import LogFiles
        
        alerts_received = 0
        trades_executed = 0
        parser_reload_triggered = False
        
        # Check last 30 minutes (matching dashboard display)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        # Count alerts from multiple UW log sources
        from config.registry import CacheFiles
        uw_logs = [
            CacheFiles.UW_ATTRIBUTION if hasattr(CacheFiles, 'UW_ATTRIBUTION') else CacheFiles.UW_ATTRIBUTION,
            Path("logs/uw_flow.jsonl"),
            CacheFiles.UW_FLOW_CACHE_LOG if hasattr(CacheFiles, 'UW_FLOW_CACHE_LOG') else Path("data/uw_flow_cache.log.jsonl")
        ]
        
        for uw_log in uw_logs:
            if isinstance(uw_log, str):
                uw_log = Path(uw_log)
            if uw_log.exists():
                try:
                    with uw_log.open('r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                rec = json.loads(line.strip())
                                ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                                if ts_str:
                                    try:
                                        if isinstance(ts_str, (int, float)):
                                            ts_dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                        else:
                                            ts_dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                                            if ts_dt.tzinfo is None:
                                                ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                                        if ts_dt >= cutoff:
                                            alerts_received += 1
                                    except:
                                        pass
                            except:
                                continue
                except:
                    pass
        
        # Count trades (from attribution - only closed trades count as executed)
        attribution_logs = [
            LogFiles.ATTRIBUTION
        ]
        
        for attribution_log in attribution_logs:
            if isinstance(attribution_log, str):
                attribution_log = Path(attribution_log)
            if attribution_log.exists():
                try:
                    with attribution_log.open('r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                rec = json.loads(line.strip())
                                # Only count closed trades (have P&L or close_reason, not open_ trade_ids)
                                trade_id = rec.get("trade_id", "")
                                if trade_id and trade_id.startswith("open_"):
                                    continue  # Skip open positions
                                
                                if rec.get("type") == "attribution" and (rec.get("pnl_usd") or rec.get("context", {}).get("close_reason")):
                                    ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                                    if ts_str:
                                        try:
                                            if isinstance(ts_str, (int, float)):
                                                ts_dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                            else:
                                                ts_dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                                                if ts_dt.tzinfo is None:
                                                    ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                                            if ts_dt >= cutoff:
                                                trades_executed += 1
                                        except:
                                            pass
                            except:
                                continue
                except:
                    pass
        
        # Check if stagnation detected (>50 alerts, 0 trades)
        status = "STAGNATION" if (alerts_received > 50 and trades_executed == 0) else "OK"
        
        # Check if parser reload was triggered (would be in logs)
        # In production, this would trigger an autonomous parser warm reload
        if status == "STAGNATION":
            parser_reload_triggered = True
            # Log that stagnation was detected (autonomous action would happen here)
            try:
                from pathlib import Path
                import json
                from datetime import datetime, timezone
                log_file = Path("logs/stagnation_watchdog.jsonl")
                log_file.parent.mkdir(exist_ok=True)
                log_rec = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "status": "STAGNATION",
                    "alerts_received": alerts_received,
                    "trades_executed": trades_executed,
                    "action": "parser_warm_reload_required",
                    "message": "Detected braindead behavior: >50 alerts but 0 trades"
                }
                with log_file.open("a") as f:
                    f.write(json.dumps(log_rec) + "\n")
                print(f"[Dashboard] STAGNATION DETECTED: {alerts_received} alerts but {trades_executed} trades in 30min", flush=True)
            except:
                pass
        
        return {
            "status": status,
            "alerts_received": alerts_received,
            "trades_executed": trades_executed,
            "stagnation_detected": (status == "STAGNATION"),
            "parser_reload_triggered": parser_reload_triggered
        }
    except Exception as e:
        print(f"[Dashboard] Error calculating stagnation watchdog: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # Return default structure on error
        return {
            "status": "OK",
            "alerts_received": 0,
            "trades_executed": 0,
            "stagnation_detected": False,
            "parser_reload_triggered": False,
            "error": str(e)
        }

@app.route("/api/xai/auditor", methods=["GET"])
def api_xai_auditor():
    """Get XAI explainable logs for Natural Language Auditor - HARDENED VERSION"""
    trades = []
    weights = []
    errors = []
    
    try:
        from xai.explainable_logger import get_explainable_logger
        explainable = get_explainable_logger()
        
        # Get trades from XAI logs
        xai_trades = []
        try:
            xai_trades = explainable.get_trade_explanations(limit=1000)  # Get more to merge with attribution
        except Exception as e:
            errors.append(f"Failed to get XAI trade explanations: {str(e)}")
            # Fallback: Try reading directly from XAI log file
            try:
                from pathlib import Path
                import json
                log_file = Path("data/explainable_logs.jsonl")
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    rec = json.loads(line)
                                    if rec.get("type") in ("trade_entry", "trade_exit"):
                                        symbol = str(rec.get("symbol", "")).upper()
                                        if symbol and "TEST" not in symbol:
                                            xai_trades.append(rec)
                                except:
                                    continue
            except Exception as fallback_e:
                errors.append(f"XAI fallback also failed: {str(fallback_e)}")
        
        # CRITICAL: Also read from attribution.jsonl to get ALL trades (Executive Summary source)
        # This ensures XAI Auditor shows the same trades as Executive Summary
        attribution_trades = []
        try:
            from pathlib import Path
            import json
            from datetime import datetime, timezone, timedelta
            
            # CRITICAL: Use standardized path from config/registry.py (resolve against _DASHBOARD_ROOT)
            try:
                from config.registry import LogFiles
                attribution_file = (_DASHBOARD_ROOT / LogFiles.ATTRIBUTION).resolve()
                if not attribution_file.exists():
                    for rel in ["logs/attribution.jsonl", "data/attribution.jsonl"]:
                        p = (_DASHBOARD_ROOT / rel).resolve()
                        if p.exists():
                            attribution_file = p
                            break
                    else:
                        attribution_file = None
            except ImportError:
                attribution_file = None
                for rel in ["logs/attribution.jsonl", "data/attribution.jsonl"]:
                    p = (_DASHBOARD_ROOT / rel).resolve()
                    if p.exists():
                        attribution_file = p
                        break
            
            if attribution_file:
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=90)  # Last 90 days
                # CRITICAL FIX: Add line limit to prevent reading entire large files (perf)
                line_count = 0
                max_lines = 3000  # Limit to prevent slowness; XAI auditor shows recent trades
                with attribution_file.open('r', encoding='utf-8') as f:
                    # For large files, read from end if possible
                    try:
                        # Try to seek to end and read backwards
                        f.seek(0, 2)
                        file_size = f.tell()
                        if file_size > 500000:  # If file > 500KB, read from end
                            # Read last ~500KB
                            read_size = min(500000, file_size)
                            f.seek(max(0, file_size - read_size))
                            # Skip first line (might be incomplete)
                            f.readline()
                    except:
                        f.seek(0)  # Fallback to start if seek fails
                    
                    for line in f:
                        line_count += 1
                        if line_count > max_lines:
                            break  # Stop after max_lines to prevent memory issues
                        if line.strip():
                            try:
                                rec = json.loads(line.strip())
                                if rec.get("type") != "attribution":
                                    continue
                                
                                # Skip open trades (same filter as executive summary)
                                trade_id = rec.get("trade_id", "")
                                if trade_id and trade_id.startswith("open_"):
                                    continue
                                
                                symbol = str(rec.get("symbol", "")).upper()
                                if not symbol or "TEST" in symbol:
                                    continue
                                
                                # Only process closed trades (have P&L or close_reason)
                                context = rec.get("context", {})
                                pnl_usd = float(rec.get("pnl_usd", 0.0))
                                close_reason = context.get("close_reason", "") or rec.get("close_reason", "")
                                if pnl_usd == 0.0 and (not close_reason or close_reason in ["unknown", "N/A", ""]):
                                    continue
                                
                                # Get timestamp - try multiple fields
                                ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("_ts")
                                if not ts_str:
                                    # If no timestamp, skip (can't sort properly)
                                    continue
                                
                                try:
                                    if isinstance(ts_str, (int, float)):
                                        trade_time = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                    elif isinstance(ts_str, str):
                                        # Try ISO format first
                                        if 'T' in ts_str or '-' in ts_str:
                                            trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                            if trade_time.tzinfo is None:
                                                trade_time = trade_time.replace(tzinfo=timezone.utc)
                                        else:
                                            # Try as timestamp string
                                            trade_time = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                                    else:
                                        continue
                                except Exception as ts_err:
                                    # Skip if timestamp parsing fails
                                    continue
                                
                                if trade_time < cutoff_time:
                                    continue
                                
                                # CRITICAL: Support both flat schema (mandatory fields) and nested schema (backward compatibility)
                                # Flat schema: symbol, entry_score, exit_pnl, market_regime, stealth_boost_applied at top level
                                
                                # Extract entry_score - try flat schema first, then nested
                                entry_score_flat = rec.get("entry_score")
                                entry_score_nested = context.get("entry_score", 0.0) if isinstance(context, dict) else 0.0
                                entry_score = entry_score_flat if entry_score_flat is not None else entry_score_nested
                                
                                # CRITICAL ERROR: Log if entry_score is missing (should never be 0.0 or missing)
                                if entry_score == 0.0 or entry_score is None:
                                    print(f"[Dashboard] CRITICAL_ERROR: Missing entry_score for trade {rec.get('trade_id', 'unknown')} symbol {rec.get('symbol', 'unknown')}", flush=True, file=sys.stderr)
                                    # Still continue but log the error
                                
                                # Extract market_regime - try flat schema first, then nested
                                market_regime_flat = rec.get("market_regime")
                                market_regime_nested = context.get("market_regime", "unknown") if isinstance(context, dict) else "unknown"
                                market_regime = market_regime_flat if market_regime_flat is not None else market_regime_nested
                                
                                # Extract exit_pnl/pnl_pct - try flat schema first, then nested
                                exit_pnl_flat = rec.get("exit_pnl")
                                pnl_pct_flat = rec.get("pnl_pct")
                                pnl_pct_nested = context.get("pnl_pct", 0.0) if isinstance(context, dict) else 0.0
                                pnl_pct = exit_pnl_flat if exit_pnl_flat is not None else (pnl_pct_flat if pnl_pct_flat is not None else pnl_pct_nested)
                                
                                # Convert attribution format to XAI trade_exit format
                                entry_price = float(context.get("entry_price", 0.0) if isinstance(context, dict) else 0.0)
                                exit_price = float(context.get("exit_price", 0.0) if isinstance(context, dict) else 0.0)
                                pnl_pct = float(rec.get("pnl_pct", 0.0))
                                hold_minutes = float(rec.get("hold_minutes", 0.0))
                                
                                # Build "why" explanation from context (same format as XAI logger)
                                why_parts = []
                                
                                # Exit reason
                                if close_reason and close_reason not in ["unknown", "N/A", ""]:
                                    if "gamma_call_wall" in close_reason.lower():
                                        why_parts.append("reached Gamma Call Wall (structural physics exit)")
                                    elif "liquidity_exhaustion" in close_reason.lower():
                                        why_parts.append("bid-side liquidity exhausted (structural physics exit)")
                                    elif "profit_target" in close_reason.lower():
                                        why_parts.append("profit target reached")
                                    elif "stop_loss" in close_reason.lower() or "trail" in close_reason.lower():
                                        why_parts.append("stop loss triggered")
                                    elif "time_exit" in close_reason.lower() or "time_or_trail" in close_reason.lower():
                                        why_parts.append("maximum hold time reached")
                                    else:
                                        why_parts.append(f"exit reason: {close_reason}")
                                
                                # Regime
                                # market_regime already extracted above with flat/nested schema support
                                if market_regime and market_regime != "unknown":
                                    regime_desc = {
                                        "RISK_ON": "bullish",
                                        "RISK_OFF": "bearish",
                                        "NEUTRAL": "neutral",
                                        "PANIC": "panic"
                                    }.get(market_regime.upper(), market_regime.lower())
                                    why_parts.append(f"market in {regime_desc} regime")
                                
                                # P&L
                                pnl_desc = "profit" if pnl_pct > 0 else "loss"
                                why_parts.append(f"{pnl_desc} of {abs(pnl_pct):.2f}% over {hold_minutes:.0f} minutes")
                                
                                why_sentence = f"Exited {symbol} because: " + ". ".join(why_parts) + "."
                                
                                # Normalize regime
                                regime_normalized = market_regime
                                if not regime_normalized or regime_normalized == "unknown":
                                    regime_normalized = "NEUTRAL"
                                else:
                                    regime_upper = str(regime_normalized).upper()
                                    if regime_upper in ["RISK_ON", "RISK_OFF", "NEUTRAL", "PANIC"]:
                                        regime_normalized = regime_upper
                                    else:
                                        regime_normalized = "NEUTRAL"
                                
                                # Create XAI format trade_exit record
                                # Add flat schema fields to xai_record for consistency
                                xai_record = {
                                    "type": "trade_exit",
                                    "symbol": symbol,
                                    "entry_price": entry_price,
                                    "exit_price": exit_price,
                                    # CRITICAL: Ensure mandatory flat fields are at top level
                                    "entry_score": entry_score,
                                    "exit_pnl": pnl_pct,
                                    "market_regime": market_regime,
                                    "pnl_pct": pnl_pct,
                                    "hold_minutes": hold_minutes,
                                    "exit_reason": close_reason or "unknown",
                                    "regime": regime_normalized,
                                    "why": why_sentence,
                                    "timestamp": trade_time.isoformat(),
                                    "trade_id": trade_id,  # Keep original trade_id for reference
                                    "_from_attribution": True  # Flag to indicate source
                                }
                                # Add flat schema fields to xai_record for consistency
                                xai_record["entry_score"] = entry_score  # Ensure entry_score is at top level
                                xai_record["market_regime"] = market_regime  # Ensure market_regime is at top level
                                xai_record["exit_pnl"] = pnl_pct  # Add exit_pnl for consistency
                                
                                # Extract stealth_boost_applied if available
                                stealth_boost = rec.get("stealth_boost_applied", False)
                                xai_record["stealth_boost_applied"] = stealth_boost
                                
                                attribution_trades.append(xai_record)
                            except Exception as e:
                                continue
        except Exception as e:
            errors.append(f"Failed to read attribution.jsonl: {str(e)}")
        
        # Merge XAI trades and attribution trades, removing duplicates
        # Use symbol + timestamp as key for deduplication (more reliable than trade_id)
        trades_dict = {}  # Key: (symbol, timestamp_normalized)
        
        # Add XAI trades first (these are the "official" XAI logs - prefer these)
        for trade in xai_trades:
            symbol = str(trade.get("symbol", "")).upper()
            timestamp = trade.get("timestamp", "")
            if symbol and timestamp:
                # Normalize timestamp for comparison (remove microseconds, timezone)
                try:
                    if isinstance(timestamp, str):
                        ts_normalized = timestamp.split('.')[0].replace('Z', '').replace('+00:00', '')
                    else:
                        ts_normalized = str(timestamp)
                    key = (symbol, ts_normalized)
                    if key not in trades_dict:  # XAI logs take precedence
                        trades_dict[key] = trade
                except:
                    # If timestamp parsing fails, use trade_id as fallback
                    trade_id = trade.get("trade_id") or f"{trade.get('type')}_{symbol}_{timestamp}"
                    if trade_id:
                        key = (symbol, trade_id)
                        if key not in trades_dict:
                            trades_dict[key] = trade
        
        # Add attribution trades (only if not already in XAI logs)
        for trade in attribution_trades:
            symbol = str(trade.get("symbol", "")).upper()
            timestamp = trade.get("timestamp", "")
            if symbol and timestamp:
                try:
                    # Normalize timestamp for comparison
                    if isinstance(timestamp, str):
                        ts_normalized = timestamp.split('.')[0].replace('Z', '').replace('+00:00', '')
                    else:
                        ts_normalized = str(timestamp)
                    key = (symbol, ts_normalized)
                    if key not in trades_dict:  # Only add if not already present
                        trades_dict[key] = trade
                except:
                    # If timestamp parsing fails, use trade_id as fallback
                    trade_id = trade.get("trade_id", "")
                    if trade_id:
                        key = (symbol, trade_id)
                        if key not in trades_dict:
                            trades_dict[key] = trade
        
        # Convert back to list and sort by timestamp (newest first)
        trades = list(trades_dict.values())
        try:
            trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        except:
            pass
        
        # Limit to 500 most recent
        trades = trades[:500]
        
        # Normalize regime field for all trades (extract from top-level or context)
        for trade in trades:
            # Regime might be at top level (from XAI logs) or in context.market_regime (from attribution logs)
            regime = trade.get("regime")
            
            # If regime is missing or "unknown", try to get from context
            if not regime or regime == "unknown" or regime == "":
                context = trade.get("context", {})
                if isinstance(context, dict):
                    market_regime = context.get("market_regime")
                    if market_regime and market_regime != "unknown" and market_regime != "":
                        regime = market_regime
                    else:
                        regime = None  # Will default below
                else:
                    regime = None
            
            # Normalize regime value - convert common variations
            if regime:
                regime_upper = str(regime).upper()
                # Map common regime names
                if regime_upper in ["RISK_ON", "BULL", "BULLISH"]:
                    trade["regime"] = "RISK_ON"
                elif regime_upper in ["RISK_OFF", "BEAR", "BEARISH"]:
                    trade["regime"] = "RISK_OFF"
                elif regime_upper in ["NEUTRAL", "MIXED"]:
                    trade["regime"] = "NEUTRAL"
                elif regime_upper in ["PANIC", "HIGH_VOL"]:
                    trade["regime"] = "PANIC"
                else:
                    # Keep original if it's a valid regime name
                    trade["regime"] = regime_upper if regime_upper in ["RISK_ON", "RISK_OFF", "NEUTRAL", "PANIC"] else "NEUTRAL"
            else:
                # Default to NEUTRAL instead of unknown (frontend will show NEUTRAL instead of N/A)
                trade["regime"] = "NEUTRAL"
            
            # Ensure regime is always a string
            if not isinstance(trade.get("regime"), str):
                trade["regime"] = "NEUTRAL"
        
        # Get weights with error handling
        try:
            weights = explainable.get_weight_explanations(limit=100)
        except Exception as e:
            errors.append(f"Failed to get weight explanations: {str(e)}")
            # Fallback: Try reading directly from log file
            try:
                from pathlib import Path
                import json
                log_file = Path("data/explainable_logs.jsonl")
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    rec = json.loads(line)
                                    if rec.get("type") == "weight_adjustment":
                                        weights.append(rec)
                                except:
                                    continue
                    weights = weights[:100]  # Limit
            except Exception as fallback_e:
                errors.append(f"Weight fallback also failed: {str(fallback_e)}")
        
        # Always return 200, even with errors (so frontend can display partial data)
        response = {
            "trades": trades,
            "weights": weights,
            "status": "ok" if not errors else "partial",
            "trade_count": len(trades),
            "weight_count": len(weights)
        }
        
        if errors:
            response["errors"] = errors
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[Dashboard] XAI Auditor error: {error_details}", flush=True)
        
        # Return empty but valid response so frontend doesn't break
        return jsonify({
            "error": str(e),
            "trades": [],
            "weights": [],
            "status": "error",
            "trade_count": 0,
            "weight_count": 0
        }), 200  # Return 200 so frontend can display error message

@app.route("/api/xai/health", methods=["GET"])
def api_xai_health():
    """Health check for XAI system"""
    health = {
        "status": "ok",
        "log_file_exists": False,
        "log_file_size": 0,
        "recent_entries": 0,
        "recent_exits": 0,
        "recent_weights": 0,
        "errors": []
    }
    
    try:
        from pathlib import Path
        import json
        from datetime import datetime, timedelta
        
        log_file = Path("data/explainable_logs.jsonl")
        health["log_file_exists"] = log_file.exists()
        
        if log_file.exists():
            health["log_file_size"] = log_file.stat().st_size
            
            # Count recent entries (last 24 hours)
            cutoff = (datetime.now() - timedelta(days=1)).isoformat()
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            ts = rec.get("timestamp", "")
                            if ts >= cutoff:
                                if rec.get("type") == "trade_entry":
                                    health["recent_entries"] += 1
                                elif rec.get("type") == "trade_exit":
                                    health["recent_exits"] += 1
                                elif rec.get("type") == "weight_adjustment":
                                    health["recent_weights"] += 1
                        except:
                            continue
        
        # Check if XAI logger can be imported
        try:
            from xai.explainable_logger import get_explainable_logger
            explainable = get_explainable_logger()
            health["logger_available"] = True
        except Exception as e:
            health["logger_available"] = False
            health["errors"].append(f"Logger import failed: {str(e)}")
            health["status"] = "degraded"
        
    except Exception as e:
        health["status"] = "error"
        health["errors"].append(str(e))
    
    return jsonify(health), 200

@app.route("/api/xai/export", methods=["GET"])
def api_xai_export():
    """Export all XAI logs as JSON"""
    try:
        from xai.explainable_logger import get_explainable_logger
        from pathlib import Path
        import json
        
        explainable = get_explainable_logger()
        log_file = explainable.log_file
        
        if not log_file.exists():
            return jsonify(
                {
                    "ok": False,
                    "state": "DISABLED",
                    "reason": "No XAI log file on this host.",
                    "logs": [],
                }
            ), 200

        # Read all logs
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except:
                        continue
        
        # Return as JSON download
        return Response(
            json.dumps(logs, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=xai_logs_{datetime.now().strftime("%Y%m%d")}.json'}
        )
    except Exception as e:
        return jsonify(
            {"ok": False, "state": "DISABLED", "reason": str(e)[:400], "logs": []}
        ), 200

@app.route("/api/executive_summary", methods=["GET"])
def api_executive_summary():
    """Get executive summary with trades, P&L, and learning analysis. Query: timeframe=24h|48h|7d|2d|5d (Performance window)."""
    try:
        from executive_summary_generator import generate_executive_summary, SUPPORTED_TIMEFRAMES, DEFAULT_TIMEFRAME
        timeframe = request.args.get("timeframe", DEFAULT_TIMEFRAME)
        if timeframe not in SUPPORTED_TIMEFRAMES:
            timeframe = DEFAULT_TIMEFRAME
        summary = generate_executive_summary(timeframe=timeframe)
        return jsonify(summary), 200
    except ImportError as e:
        return jsonify({"error": f"Module import error: {str(e)}", "trades": [], "total_trades": 0, "pnl_metrics": {}, "signal_analysis": {}, "learning_insights": {}, "written_summary": "Executive summary generator not available."}), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[Dashboard] Executive summary error: {error_details}", flush=True)
        return jsonify({
            "error": f"Failed to generate executive summary: {str(e)}",
            "trades": [],
            "total_trades": 0,
            "pnl_metrics": {"timeframe": "24h", "pnl": 0, "trades": 0, "win_rate": 0},
            "signal_analysis": {"top_signals": {}, "bottom_signals": {}},
            "learning_insights": {},
            "written_summary": f"Error generating summary: {str(e)}"
        }), 200  # Return 200 so frontend can display error


def _rolling_pnl_5d_build():
    path = (_DASHBOARD_ROOT / "reports" / "state" / "rolling_pnl_5d.jsonl").resolve()
    if not path.exists():
        return {
            "points": [],
            "points_total_before_cap": 0,
            "window": "5d",
            "source": "unified_exits",
            "shadow_value": [],
            "rolling_pnl_points_cap": 900,
        }
    points = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            points.append(json.loads(line))
        except Exception:
            continue
    _ROLLING_PNL_MAX_POINTS = 900
    _points_total = len(points) if isinstance(points, list) else 0
    if isinstance(points, list) and len(points) > _ROLLING_PNL_MAX_POINTS:
        points = points[-_ROLLING_PNL_MAX_POINTS:]
    shadow_value = [
        p.get("equity_shadow")
        for p in points
        if isinstance(p, dict) and p.get("equity_shadow") is not None
    ]
    if not shadow_value and points:
        shadow_value = [p.get("equity") for p in points if isinstance(p, dict)]
    return {
        "points": points,
        "points_total_before_cap": _points_total,
        "window": "5d",
        "source": "unified_exits",
        "shadow_value": shadow_value,
        "rolling_pnl_points_cap": _ROLLING_PNL_MAX_POINTS,
    }


@app.route("/api/rolling_pnl_5d", methods=["GET"])
def api_rolling_pnl_5d():
    """Return 5-day rolling PnL series from reports/state/rolling_pnl_5d.jsonl. No smoothing; gaps visible.
    Also returns ``shadow_value``: hypothetic equity if trades entered with ``shadow_chop_block`` (11:30–1:30 ET) were removed."""
    try:
        data = _dash_cache_get("rolling_pnl_5d_v2", _rolling_pnl_5d_build)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"points": [], "window": "5d", "shadow_value": [], "error": str(e)}), 200


def _metrics_payload():
    """Aggregated governance / KPI JSON for the SPA (cached)."""
    root = Path(_DASHBOARD_ROOT)
    out: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "equity_baseline_usd": 10_000.0,
    }
    try:
        from src.governance.canonical_trade_count import compute_canonical_trade_count
        from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

        floor = float(STRICT_EPOCH_START)
        c = compute_canonical_trade_count(root, floor_epoch=floor)
        out["strict_cohort_n"] = c.get("total_trades_post_era")
        out["strict_realized_pnl_sum_usd"] = c.get("realized_pnl_sum_usd")
        out["strict_floor_epoch_utc"] = c.get("floor_epoch_utc")
        out["strict_trades_to_250"] = c.get("trades_to_250")
        out["strict_next_milestone"] = c.get("next_milestone")
    except Exception as e:
        out["strict_cohort_error"] = str(e)

    try:
        reps = root / "reports"
        best: Optional[Path] = None
        best_name = ""
        if reps.is_dir():
            for p in reps.glob("ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md"):
                if p.name > best_name:
                    best_name = p.name
                    best = p
        if best is not None and best.exists():
            txt = best.read_text(encoding="utf-8", errors="replace")[:8000]
            out["data_ready_report"] = best.name
            if "DATA_READY: YES" in txt:
                out["DATA_READY"] = True
            elif "DATA_READY: NO" in txt:
                out["DATA_READY"] = False
            else:
                out["DATA_READY"] = None
        else:
            out["DATA_READY"] = None
            out["data_ready_report"] = None
    except Exception as e:
        out["data_ready_error"] = str(e)

    try:
        roll = _dash_cache_get("rolling_pnl_5d_v2", _rolling_pnl_5d_build)
        pts = roll.get("points") or []
        if isinstance(pts, list) and len(pts) > 40:
            out["rolling_pnl_last_points"] = pts[-40:]
        else:
            out["rolling_pnl_last_points"] = pts
        out["rolling_pnl_point_count"] = len(pts) if isinstance(pts, list) else 0
    except Exception as e:
        out["rolling_pnl_error"] = str(e)

    # ML cohort HUD strip removed (V3 decoupled UI); offline scripts still own strict cohort counts.
    out["ml_epoch_note"] = "HUD decoupled — use reports/Gemini + flattener offline."

    try:
        pos = _dash_cache_get("positions_bundle_v1", _positions_cached_fetch)
        plist = pos.get("positions") or []
        out["open_position_count"] = len(plist) if isinstance(plist, list) else 0
        out["day_pnl_usd"] = pos.get("day_pnl")
        # Same Alpaca REST snapshot as /open_positions (broker truth for KPI strip).
        out["broker_equity_usd"] = pos.get("account_equity")
        out["broker_last_equity_usd"] = pos.get("account_last_equity")
        out["broker_portfolio_value_usd"] = pos.get("total_value")
        out["broker_buying_power_usd"] = pos.get("account_buying_power")
        out["broker_currency"] = pos.get("broker_currency")
        out["broker_day_pnl_usd"] = pos.get("day_pnl")
    except Exception as e:
        out["positions_snapshot_error"] = str(e)

    return out


@app.route("/metrics", methods=["GET"])
def api_metrics():
    """Light aggregated metrics for dashboard polling (TTL-cached)."""
    try:
        payload = _dash_cache_get("metrics_bundle_v1", _metrics_payload)
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e), "timestamp_utc": datetime.now(timezone.utc).isoformat()}), 500


@app.route("/api/health_status", methods=["GET"])
def api_health_status():
    """Health status endpoint for dashboard - provides Last Order and Doctor status"""
    try:
        import time
        import json
        from pathlib import Path
        from datetime import datetime, timezone
        
        # CRITICAL FIX: Query Alpaca API directly for most recent order (most reliable source)
        last_order_ts = None
        last_order_age_sec = None
        
        # Try Alpaca API first (most authoritative source)
        if _alpaca_api is not None:
            try:
                # Get most recent order from Alpaca
                orders = _alpaca_api.list_orders(status='all', limit=1, direction='desc', nested=False)
                if orders and len(orders) > 0:
                    order = orders[0]
                    # Use submitted_at (when order was submitted) or created_at as fallback
                    submitted_at = getattr(order, 'submitted_at', None) or getattr(order, 'created_at', None)
                    if submitted_at:
                        try:
                            # Parse ISO timestamp string to unix timestamp
                            if isinstance(submitted_at, str):
                                # Handle ISO format: '2025-01-05T10:30:00.123456Z' or '2025-01-05T10:30:00.123456-05:00'
                                dt = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                                last_order_ts = dt.timestamp()
                            elif hasattr(submitted_at, "timestamp") and callable(getattr(submitted_at, "timestamp", None)):
                                last_order_ts = float(submitted_at.timestamp())
                            else:
                                last_order_ts = float(submitted_at)
                            
                            if last_order_ts:
                                last_order_age_sec = time.time() - last_order_ts
                        except Exception as e:
                            print(f"[Dashboard] Warning: Failed to parse order timestamp: {e}", flush=True)
            except Exception as e:
                print(f"[Dashboard] Warning: Failed to query Alpaca API for last order: {e}", flush=True)
        
        # Fallback to log files if Alpaca API unavailable or failed (paths resolve against _DASHBOARD_ROOT)
        if last_order_ts is None:
            orders_files = [
                (_DASHBOARD_ROOT / "data" / "live_orders.jsonl").resolve(),
                (_DASHBOARD_ROOT / "logs" / "orders.jsonl").resolve(),
                (_DASHBOARD_ROOT / "logs" / "trading.jsonl").resolve(),
            ]
            
            for orders_file in orders_files:
                if orders_file.exists():
                    try:
                        # CRITICAL FIX: Read only last 500 lines efficiently (don't load entire file)
                        # Use seek to read from end of file to avoid memory issues
                        with orders_file.open("r", encoding='utf-8') as f:
                            # Read last 500 lines efficiently
                            try:
                                # Seek to end, then read backwards in chunks
                                f.seek(0, 2)  # Seek to end
                                file_size = f.tell()
                                if file_size == 0:
                                    continue
                                
                                # Read last ~50KB (enough for ~500 lines)
                                read_size = min(50000, file_size)
                                f.seek(max(0, file_size - read_size))
                                chunk = f.read()
                                
                                # Split into lines and take last 500
                                lines = chunk.splitlines()
                                if len(lines) > 500:
                                    lines = lines[-500:]
                                
                                for line in lines:
                                    if not line.strip():
                                        continue
                                    try:
                                        event = json.loads(line.strip())
                                        event_ts = event.get("_ts", 0)
                                        event_type = event.get("event", "")
                                        if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                                            last_order_ts = event_ts
                                    except:
                                        pass
                            except Exception as read_err:
                                # Fallback: try reading entire file if chunk read fails
                                print(f"[Dashboard] Warning: Chunk read failed for {orders_file}, trying full read: {read_err}", flush=True)
                                f.seek(0)
                                all_lines = f.readlines()
                                for line in all_lines[-500:]:
                                    if not line.strip():
                                        continue
                                    try:
                                        event = json.loads(line.strip())
                                        event_ts = event.get("_ts", 0)
                                        event_type = event.get("event", "")
                                        if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                                            last_order_ts = event_ts
                                    except:
                                        pass
                    except Exception as file_err:
                        print(f"[Dashboard] Warning: Failed to read {orders_file}: {file_err}", flush=True)
                        pass
            
            if last_order_ts:
                last_order_age_sec = time.time() - last_order_ts
        
        # Get Doctor/heartbeat from file (paths resolve against _DASHBOARD_ROOT)
        # CRITICAL: Check bot_heartbeat.json FIRST (main.py writes here)
        heartbeat_age_sec = None
        heartbeat_files = [
            (_DASHBOARD_ROOT / "state" / "bot_heartbeat.json").resolve(),
            (_DASHBOARD_ROOT / "state" / "doctor_state.json").resolve(),
            (_DASHBOARD_ROOT / "state" / "system_heartbeat.json").resolve(),
            (_DASHBOARD_ROOT / "state" / "heartbeat.json").resolve(),
        ]
        
        for hb_file in heartbeat_files:
            if hb_file.exists():
                try:
                    data = json.loads(hb_file.read_text())
                    # CRITICAL FIX: Check last_heartbeat_ts first (the actual field name used by main.py)
                    heartbeat_ts = data.get("last_heartbeat_ts") or data.get("timestamp") or data.get("_ts") or data.get("last_heartbeat") or data.get("last_update")
                    if heartbeat_ts:
                        heartbeat_age_sec = time.time() - float(heartbeat_ts)
                        break
                    else:
                        # Use file modification time as fallback
                        heartbeat_age_sec = time.time() - hb_file.stat().st_mtime
                        break
                except:
                    continue
        
        # Market status (NYSE regular session, America/New_York — matches sre_monitoring)
        from datetime import datetime, timezone
        from zoneinfo import ZoneInfo

        now_utc = datetime.now(timezone.utc)
        now_et = now_utc.astimezone(ZoneInfo("America/New_York"))
        market_open = now_et.weekday() < 5 and (
            now_et.replace(hour=9, minute=30, second=0, microsecond=0)
            <= now_et
            <= now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        )
        market_status = "market_open" if market_open else "market_closed"
        
        return jsonify({
            "last_order": {
                "timestamp": last_order_ts,
                "age_sec": last_order_age_sec,
                "age_hours": last_order_age_sec / 3600 if last_order_age_sec else None,
                "status": "healthy" if last_order_age_sec and last_order_age_sec < 3600 else 
                         "warning" if last_order_age_sec and last_order_age_sec < 10800 else
                         "stale" if last_order_age_sec else "unknown"
            },
            "doctor": {
                "age_sec": heartbeat_age_sec,
                "age_minutes": heartbeat_age_sec / 60 if heartbeat_age_sec else None,
                "status": "healthy" if heartbeat_age_sec and heartbeat_age_sec < 300 else
                         "warning" if heartbeat_age_sec and heartbeat_age_sec < 1800 else
                         "stale" if heartbeat_age_sec else "unknown"
            },
            "market": {
                "open": market_open,
                "status": market_status
            },
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scores/distribution", methods=["GET"])
def api_scores_distribution():
    """
    SCORING PIPELINE FIX (Part 3): Score distribution endpoint
    Returns score distribution statistics for monitoring
    """
    try:
        from telemetry.score_telemetry import get_score_distribution
        import json
        
        symbol = request.args.get("symbol", None)
        lookback_hours = int(request.args.get("lookback_hours", 24))
        
        distribution = get_score_distribution(symbol=symbol, lookback_hours=lookback_hours)
        return jsonify(distribution)
    except ImportError:
        return jsonify({"error": "score_telemetry module not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scores/components", methods=["GET"])
def api_scores_components():
    """
    SCORING PIPELINE FIX (Part 3): Component health endpoint
    Returns component-level contribution statistics
    """
    try:
        from telemetry.score_telemetry import get_component_health
        import json
        
        lookback_hours = int(request.args.get("lookback_hours", 24))
        
        component_health = get_component_health(lookback_hours=lookback_hours)
        return jsonify(component_health)
    except ImportError:
        return jsonify({"error": "score_telemetry module not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scores/telemetry", methods=["GET"])
def api_scores_telemetry():
    """
    SCORING PIPELINE FIX (Part 3): Complete telemetry summary endpoint
    Returns all score telemetry statistics for dashboard
    """
    try:
        from telemetry.score_telemetry import get_telemetry_summary
        import json
        
        summary = get_telemetry_summary()
        return jsonify(summary)
    except ImportError:
        return jsonify({"error": "score_telemetry module not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/failure_points")
def api_failure_points():
    """Get failure point status and trading readiness"""
    try:
        from failure_point_monitor import get_failure_point_monitor
        monitor = get_failure_point_monitor()
        readiness = monitor.get_trading_readiness()
        return jsonify(readiness), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "readiness": "UNKNOWN",
            "critical_count": 0,
            "warning_count": 0
        }), 500

@app.route("/api/signal_history", methods=["GET"])
def api_signal_history():
    """Get the last 50 signal processing events for Signal Review tab. Exposes malformed_line_count when corruption is detected."""
    try:
        from signal_history_storage import get_signal_history_with_meta, get_last_signal_timestamp
        from shadow_tracker import get_shadow_tracker

        signals, malformed_line_count, last_malformed_ts = get_signal_history_with_meta(limit=50)
        last_signal_ts = get_last_signal_timestamp()

        # Update virtual P&L from shadow positions
        try:
            shadow_tracker = get_shadow_tracker()
            for signal in signals:
                symbol = signal.get("symbol")
                if symbol and signal.get("shadow_created"):
                    shadow_pos = shadow_tracker.get_position(symbol)
                    if shadow_pos:
                        signal["virtual_pnl"] = shadow_pos.max_profit_pct
                        if shadow_pos.closed:
                            signal["shadow_closed"] = True
                            signal["shadow_close_reason"] = shadow_pos.close_reason
        except Exception:
            pass

        payload = {
            "signals": signals,
            "last_signal_timestamp": last_signal_ts,
            "count": len(signals),
        }
        if malformed_line_count > 0:
            payload["malformed_line_count"] = malformed_line_count
            payload["last_malformed_ts"] = last_malformed_ts
        return jsonify(payload), 200
    except ImportError:
        return jsonify({
            "signals": [],
            "last_signal_timestamp": "",
            "count": 0,
            "error": "signal_history_storage module not available"
        }), 200
    except Exception as e:
        return jsonify({
            "signals": [],
            "last_signal_timestamp": "",
            "count": 0,
            "error": str(e)
        }), 500


@app.route("/api/regime-and-posture", methods=["GET"])
def api_regime_and_posture():
    """
    Structural upgrade status endpoint:
    - market context (state/market_context_v2.json)
    - regime+posture (state/regime_posture_state.json)
    - composite version + shadow enabled (env/config)
    """
    try:
        from config.registry import StateFiles, read_json
        mc = {}
        rp = {}
        try:
            if hasattr(StateFiles, "MARKET_CONTEXT_V2"):
                p = (_DASHBOARD_ROOT / StateFiles.MARKET_CONTEXT_V2).resolve()
                if p.exists():
                    mc = read_json(p, default={})
        except Exception:
            mc = {}
        try:
            if hasattr(StateFiles, "REGIME_POSTURE_STATE"):
                p = (_DASHBOARD_ROOT / StateFiles.REGIME_POSTURE_STATE).resolve()
                if p.exists():
                    rp = read_json(p, default={})
        except Exception:
            rp = {}

        composite_version = os.getenv("COMPOSITE_VERSION", "v1")
        shadow_enabled_raw = os.getenv("SHADOW_TRADING_ENABLED", "true")
        shadow_enabled = str(shadow_enabled_raw).strip().lower() in ("1", "true", "yes", "y", "on")

        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "market_context_v2": mc if isinstance(mc, dict) else {},
                "regime_posture_v2": rp if isinstance(rp, dict) else {},
                "config": {
                    "COMPOSITE_VERSION": str(composite_version),
                    "SHADOW_TRADING_ENABLED": bool(shadow_enabled),
                },
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.utcnow().isoformat()}), 500


# ============================================================
# Telemetry bundle + computed artifacts (read-only dashboard API)
# ============================================================
def _latest_telemetry_dir():
    """Resolve latest telemetry date folder using absolute path (cwd-independent)."""
    try:
        root = TELEMETRY_ROOT
        if not root.exists():
            return None
        dirs = [p for p in root.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == "-" and p.name[7] == "-"]
        if not dirs:
            return None
        # Lexicographic sort works for YYYY-MM-DD; return latest even if computed/ not yet present.
        return sorted(dirs, key=lambda p: p.name)[-1]
    except Exception:
        return None


_TELEMETRY_COMPUTED_MAP = {
    "live_vs_shadow_pnl": "live_vs_shadow_pnl.json",
    "signal_performance": "signal_performance.json",
    "signal_weight_recommendations": "signal_weight_recommendations.json",
    "blocked_counterfactuals_summary": "blocked_counterfactuals_summary.json",
    "exit_quality_summary": "exit_quality_summary.json",
    "signal_profitability": "signal_profitability.json",
    "gate_profitability": "gate_profitability.json",
    "intelligence_recommendations": "intelligence_recommendations.json",
    # Existing computed artifacts (for index/panels)
    "shadow_vs_live_parity": "shadow_vs_live_parity.json",
    "entry_parity_details": "entry_parity_details.json",
    "score_distribution_curves": "score_distribution_curves.json",
    "regime_timeline": "regime_timeline.json",
    "feature_family_summary": "feature_family_summary.json",
    "replacement_telemetry_expanded": "replacement_telemetry_expanded.json",
    "long_short_analysis": "long_short_analysis.json",
    "exit_intel_completeness": "exit_intel_completeness.json",
    "feature_value_curves": "feature_value_curves.json",
    "regime_sector_feature_matrix": "regime_sector_feature_matrix.json",
    "feature_equalizer_builder": "feature_equalizer_builder.json",
    "bar_health_summary": "bar_health_summary.json",
}


def _freshness_status(age_sec) -> str:
    try:
        if age_sec is None:
            return "unknown"
        a = float(age_sec)
        if a < 6 * 3600:
            return "healthy"
        if a < 24 * 3600:
            return "warning"
        return "stale"
    except Exception:
        return "unknown"


def _build_latest_computed_index(tdir):
    """
    Returns a list of computed artifact status rows for the latest telemetry bundle (best-effort).
    """
    try:
        import time

        comp_dir = tdir / "computed"
        comp_dir.mkdir(parents=True, exist_ok=True)
        out = []
        for key, fn in sorted(_TELEMETRY_COMPUTED_MAP.items(), key=lambda kv: kv[0]):
            fp = comp_dir / fn
            if fp.exists():
                age_sec = float(time.time() - fp.stat().st_mtime)
                out.append(
                    {
                        "name": key,
                        "filename": fn,
                        "path": str(fp),
                        "age_sec": age_sec,
                        "status": _freshness_status(age_sec),
                        "bytes": int(fp.stat().st_size),
                    }
                )
            else:
                out.append({"name": key, "filename": fn, "path": str(fp), "age_sec": None, "status": "missing", "bytes": 0})
        return out
    except Exception:
        return []


@app.route("/api/telemetry/latest/index", methods=["GET"])
def api_telemetry_latest_index():
    try:
        tdir = _latest_telemetry_dir()
        if tdir is None:
            return jsonify({
                "latest_date": None,
                "computed": [],
                "message": "No telemetry bundle found. Run full telemetry extract or bar health check for a date.",
                "telemetry_root": str(TELEMETRY_ROOT),
                "as_of_ts": datetime.now(timezone.utc).isoformat(),
            }), 200

        out = _build_latest_computed_index(tdir)
        return jsonify({"latest_date": tdir.name, "computed": out, "as_of_ts": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        return jsonify({"error": str(e), "latest_date": None, "computed": []}), 500


@app.route("/api/telemetry/latest/computed", methods=["GET"])
def api_telemetry_latest_computed():
    try:
        name = (request.args.get("name") or "").strip()
        if not name:
            return jsonify({"error": "missing query param: name"}), 400

        tdir = _latest_telemetry_dir()
        if tdir is None:
            # 200 + explicit error: UI must not treat missing bundle as silent OK; avoid 404 for tab hydration.
            return jsonify({
                "ok": False,
                "error": "no telemetry bundles found",
                "message": "Run bar health or full telemetry extract to create telemetry/YYYY-MM-DD/computed/",
                "telemetry_root": str(TELEMETRY_ROOT),
                "latest_date": None,
                "name": name,
                "data": None,
                "as_of_ts": datetime.now(timezone.utc).isoformat(),
            }), 200

        comp_dir = tdir / "computed"
        comp_dir.mkdir(parents=True, exist_ok=True)
        fn = _TELEMETRY_COMPUTED_MAP.get(name) or name
        # Allow passing a filename directly (must end with .json).
        if not str(fn).endswith(".json"):
            return jsonify(
                {
                    "ok": False,
                    "error": f"unknown computed artifact: {name}",
                    "latest_date": tdir.name,
                    "name": name,
                    "data": None,
                    "as_of_ts": datetime.now(timezone.utc).isoformat(),
                }
            ), 200
        fp = comp_dir / str(fn)
        if not fp.exists():
            return jsonify(
                {
                    "ok": False,
                    "error": f"computed artifact missing: {fn}",
                    "latest_date": tdir.name,
                    "name": name,
                    "filename": str(fn),
                    "data": None,
                    "as_of_ts": datetime.now(timezone.utc).isoformat(),
                }
            ), 200

        data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
        return jsonify(
            {
                "ok": True,
                "latest_date": tdir.name,
                "name": name,
                "filename": str(fn),
                "data": data,
                "as_of_ts": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper-mode-intel-state", methods=["GET"])
def api_paper_mode_intel_state():
    """Paper-mode intelligence overrides state (telemetry/paper_mode_intel_state.json)."""
    try:
        fp = TELEMETRY_ROOT / "paper_mode_intel_state.json"
        if not fp.exists():
            try:
                from config.paper_mode_config import write_paper_mode_intel_state
                write_paper_mode_intel_state()
            except Exception:
                pass
            if fp.exists():
                data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
                return jsonify(data)
            return jsonify({
                "displacement_relaxation_active": False,
                "min_exec_score_active": False,
                "exit_tuning_active": False,
                "regime_filter_active": False,
                "effective_params": {},
                "trading_mode": "unknown",
                "overrides_version": "",
            })
        data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/telemetry/latest/health", methods=["GET"])
def api_telemetry_latest_health():
    """
    Telemetry Health summary for dashboard panels (best-effort).
    """
    try:
        import time

        tdir = _latest_telemetry_dir()
        if tdir is None:
            return jsonify({
                "latest_date": None,
                "computed_index": {"computed": []},
                "message": "No telemetry bundle yet.",
                "telemetry_root": str(TELEMETRY_ROOT),
                "as_of_ts": datetime.now(timezone.utc).isoformat(),
            }), 200
        idx = {"latest_date": tdir.name, "computed": _build_latest_computed_index(tdir), "as_of_ts": datetime.now(timezone.utc).isoformat()}

        parity = {}
        repl = {}
        try:
            # Pull key signals from computed artifacts (if present)
            if tdir is not None:
                p = (tdir / "computed" / "shadow_vs_live_parity.json")
                if p.exists():
                    parity = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                r = (tdir / "computed" / "replacement_telemetry_expanded.json")
                if r.exists():
                    repl = json.loads(r.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            parity = parity if isinstance(parity, dict) else {}
            repl = repl if isinstance(repl, dict) else {}

        parity_health = {}
        try:
            notes = parity.get("notes") if isinstance(parity, dict) else {}
            agg = parity.get("aggregate_metrics") if isinstance(parity, dict) else {}
            ep = parity.get("entry_parity") if isinstance(parity, dict) else {}
            counts = ep.get("classification_counts") if isinstance(ep, dict) else {}
            parity_health = {
                "parity_available": (notes.get("parity_available") if isinstance(notes, dict) else None),
                "match_rate": (agg.get("match_rate") if isinstance(agg, dict) else None),
                "mean_entry_ts_delta_seconds": (agg.get("mean_entry_ts_delta_seconds") if isinstance(agg, dict) else None),
                "mean_score_delta": (agg.get("mean_score_delta") if isinstance(agg, dict) else None),
                "mean_price_delta_usd": (agg.get("mean_price_delta_usd") if isinstance(agg, dict) else None),
                "classification_counts": counts if isinstance(counts, dict) else {},
            }
        except Exception:
            parity_health = {}

        replacement_health = {}
        try:
            cnts = repl.get("counts") if isinstance(repl, dict) else {}
            replacement_health = {
                "replacement_rate": (cnts.get("replacement_rate") if isinstance(cnts, dict) else None),
                "replacement_anomaly_detected": (repl.get("replacement_anomaly_detected") if isinstance(repl, dict) else None),
            }
        except Exception:
            replacement_health = {}

        # Master trade log status (canonical path per MEMORY_BANK 5.5 / config.registry LogFiles)
        try:
            from config.registry import LogFiles
            mtl = (_DASHBOARD_ROOT / LogFiles.MASTER_TRADE_LOG).resolve()
        except Exception:
            mtl = _DASHBOARD_ROOT / "logs" / "master_trade_log.jsonl"
        mtl_status = {"exists": mtl.exists()}
        try:
            if mtl.exists():
                age_sec = float(time.time() - mtl.stat().st_mtime)
                mtl_status.update({"age_sec": age_sec, "status": _freshness_status(age_sec)})
        except Exception:
            pass

        return jsonify(
            {
                "latest_date": (tdir.name if tdir is not None else None),
                "computed_index": idx,
                "parity_health": parity_health,
                "replacement_health": replacement_health,
                "master_trade_log": mtl_status,
                "as_of_ts": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "as_of_ts": datetime.now(timezone.utc).isoformat()}), 500

if __name__ == "__main__":
    # Fixed bind: external firewall allows 5005 only; do not drift to 5006+.
    port = 5005
    print(f"[Dashboard] Starting on port {port} (hardcoded)...", flush=True)
    print(f"[Dashboard] Instance: {os.getenv('INSTANCE', 'UNKNOWN')}", flush=True)

    # Fail fast if Flask isn't actually available.
    # WHY: If Flask is missing, the dashboard never binds a port, so it appears "down" with no clear error.
    # HOW TO VERIFY: Logs show this message and process exits non-zero; install Flask in the runtime to resolve.
    if not _FLASK_AVAILABLE:
        print("[Dashboard] ERROR: Flask is not installed in this runtime. Install flask and restart the dashboard service.", flush=True)
        raise SystemExit(1)

    # Best-effort load `.env` for manual starts (systemd/supervisor already exports env vars).
    try:
        _load_dotenv_if_available()
    except Exception:
        pass

    # Fail-closed: dashboard must not start without auth credentials.
    try:
        from config.registry import DashboardAuthConfig
        DashboardAuthConfig.validate_or_die()
    except SystemExit:
        raise
    except Exception as e:
        print(f"[DashboardAuth] CONTRACT VIOLATION: Could not validate dashboard auth config: {e}", flush=True)
        raise SystemExit(1)
    
    loader_thread = threading.Thread(target=lazy_load_dependencies, daemon=True)
    loader_thread.start()
    
    print(f"[Dashboard] Server starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
