#!/usr/bin/env python3
"""
Position Dashboard - Fast Start Version
Binds port 5000 immediately, then lazy-loads heavy dependencies.

IMPORTANT: For project context, common issues, and solutions, see MEMORY_BANK.md
"""

import os
import sys
import json
import subprocess
import threading
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure repo root is on path so health/config import when cwd differs (e.g. systemd)
_DASHBOARD_ROOT = Path(__file__).resolve().parent
TELEMETRY_ROOT = _DASHBOARD_ROOT / "telemetry"
if str(_DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_ROOT))

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
    from flask import Flask, render_template_string, jsonify, Response, request
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
    app = Flask(__name__)

    def _load_dotenv_if_available() -> None:
        """
        Best-effort: load `/root/stock-bot/.env` so manual dashboard starts inherit secrets.

        WHY:
        - MEMORY_BANK.md allows manual `nohup python3 dashboard.py ...` starts.
        - The dashboard auth contract requires DASHBOARD_USER/PASS, which are stored in `/root/stock-bot/.env`.
        """
        try:
            from dotenv import load_dotenv  # type: ignore
        except Exception:
            return
        try:
            env_path = Path("/root/stock-bot/.env")
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

_alpaca_api = None
_registry_loaded = False

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

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Bot - Live Positions Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { color: #667eea; font-size: 2em; margin-bottom: 10px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-label { font-size: 0.9em; color: #666; margin-bottom: 5px; }
        .stat-value { font-size: 1.8em; font-weight: bold; color: #333; }
        .stat-value.positive { color: #10b981; }
        .stat-value.negative { color: #ef4444; }
        .stat-value.warning { color: #f59e0b; }
        .stat-value.healthy { color: #10b981; }
        .stat-value.degraded { color: #f59e0b; }
        .stat-value.critical { color: #ef4444; }
        .positions-table {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        /* Smooth transitions to reduce flicker perception */
        table tr {
            transition: background-color 0.2s ease;
        }
        .stat-value {
            transition: color 0.3s ease;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }
        td { padding: 12px; border-bottom: 1px solid #e5e7eb; }
        tr:hover { background: #f9fafb; }
        .symbol { font-weight: bold; color: #667eea; }
        .side { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 600; }
        .side.long { background: #d1fae5; color: #065f46; }
        .side.short { background: #fee2e2; color: #991b1b; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .update-info { font-size: 0.85em; color: #666; margin-top: 10px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .no-positions { text-align: center; padding: 40px; color: #666; }
        .health-ok { color: #10b981; }
        /* Version badge - fixed top-right */
        .version-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.75em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .version-badge.ok { background: #d1fae5; color: #065f46; border-color: #10b981; }
        .version-badge.mismatch { background: #fee2e2; color: #991b1b; border-color: #ef4444; }
        .version-badge.unknown { background: #f3f4f6; color: #6b7280; border-color: #9ca3af; }
        .version-badge:hover { opacity: 0.85; transform: scale(1.02); }
        .header { position: relative; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
        }
        .tab {
            padding: 12px 24px;
            background: #f3f4f6;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            color: #6b7280;
            transition: all 0.2s;
            margin-bottom: -2px;
        }
        .tab:hover {
            background: #e5e7eb;
            color: #374151;
        }
        .tab.active {
            background: white;
            color: #667eea;
            border-bottom: 2px solid white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        /* Ensure tabs are clickable (above any overlay) */
        .tabs { position: relative; z-index: 2; }
        .tab { pointer-events: auto; }
        .version-badge { pointer-events: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Bot Dashboard</h1>
            <p>Live position monitoring with real-time P&L updates</p>
            <p class="update-info">Auto-refresh: 60 seconds | Last update: <span id="last-update">-</span> | Last Signal: <span id="last-signal">-</span></p>
            <p id="dashboard-diagnostic" style="font-size:0.75em;color:#6b7280;margin-top:4px;display:none;">If version and data stay loading: open DevTools (F12) → Console and Network; refresh page and log in again.</p>
            <div id="version-badge" class="version-badge unknown" onclick="switchTab('sre', event); setTimeout(function(){var p=document.getElementById('dashboard-version-panel');if(p)p.scrollIntoView({behavior:'smooth'});}, 300);" title="Loading version...">
                Dashboard v...
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" data-tab="positions" onclick="switchTab('positions', event)">📊 Positions</button>
            <button class="tab" data-tab="signal_review" onclick="switchTab('signal_review', event)">🔍 Signal Review</button>
            <button class="tab" data-tab="sre" onclick="switchTab('sre', event)">🔍 SRE Monitoring</button>
            <button class="tab" data-tab="executive" onclick="switchTab('executive', event)">📈 Executive Summary</button>
            <button class="tab" data-tab="xai" onclick="switchTab('xai', event)">🧠 Natural Language Auditor</button>
            <button class="tab" data-tab="failure_points" onclick="switchTab('failure_points', event)">⚠️ Trading Readiness</button>
            <button class="tab" data-tab="wheel_universe" onclick="switchTab('wheel_universe', event)">🔄 Wheel Universe Health</button>
            <button class="tab" data-tab="strategy_comparison" onclick="switchTab('strategy_comparison', event)">⚖️ Strategy Comparison</button>
            <button class="tab" data-tab="closed_trades" onclick="switchTab('closed_trades', event)">📋 Closed Trades</button>
            <button class="tab" data-tab="wheel_strategy" onclick="switchTab('wheel_strategy', event)">🛞 Wheel Strategy</button>
            <button class="tab" data-tab="telemetry" onclick="switchTab('telemetry', event)">📦 Telemetry</button>
        </div>
        
        <div id="positions-tab" class="tab-content active">
        <div class="stats" id="stats-container">
            <div class="stat-card">
                <div class="stat-label">Total Positions</div>
                <div class="stat-value" id="total-positions">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Value</div>
                <div class="stat-value" id="total-value">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unrealized P&L</div>
                <div class="stat-value" id="unrealized-pnl">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Day P&L</div>
                <div class="stat-value" id="day-pnl">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last Order</div>
                <div class="stat-value" id="last-order">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Doctor</div>
                <div class="stat-value" id="doctor">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Missed Alpha (USD)</div>
                <div class="stat-value" id="missed-alpha">-</div>
            </div>
        </div>
        
        <div class="positions-table">
            <h2 style="margin-bottom: 15px;">Open Positions</h2>
            <div id="positions-content">
                <p class="loading">Loading positions...</p>
            </div>
        </div>
        </div>
        
        <div id="sre-tab" class="tab-content">
            <div id="sre-content">
                <div class="loading">Loading SRE monitoring data...</div>
            </div>
        </div>
        
        <div id="executive-tab" class="tab-content">
            <div id="executive-content">
                <div class="loading">Loading executive summary...</div>
            </div>
        </div>
        
        <div id="xai-tab" class="tab-content">
            <div id="xai-content">
                <div class="loading">Loading Natural Language Auditor...</div>
            </div>
        </div>
        
        <div id="wheel_universe-tab" class="tab-content">
            <div id="wheel_universe-content"></div>
        </div>
        <div id="strategy_comparison-tab" class="tab-content">
            <div id="strategy_comparison-content"></div>
        </div>
        <div id="closed_trades-tab" class="tab-content">
            <div id="closed_trades-content">
                <div class="loading">Loading closed trades...</div>
            </div>
        </div>
        <div id="wheel_strategy-tab" class="tab-content">
            <div id="wheel_strategy-content">
                <div class="loading">Loading Wheel Strategy analytics...</div>
            </div>
        </div>
        <div id="failure_points-tab" class="tab-content">
            <div id="failure_points-content">
                <div class="loading">Loading Trading Readiness...</div>
            </div>
        </div>

        <div id="telemetry-tab" class="tab-content">
            <div id="telemetry-content">
                <div class="loading">Loading telemetry...</div>
            </div>
        </div>
        
        <div id="signal_review-tab" class="tab-content">
            <div class="positions-table">
                <h2 style="margin-bottom: 15px;">Signal Review - Last 50 Processing Events</h2>
                <div id="signal-review-content">
                    <p class="loading">Loading signal history...</p>
                </div>
            </div>
        </div>
    </div>
    <script>
    (function(){/* Minimal: tabs + version + positions so data loads even if main script fails */
    var creds={credentials:'same-origin'};
    window.switchTab=function(tabName,event){
    var t=document.querySelectorAll('.tab');for(var i=0;i<t.length;i++)t[i].classList.remove('active');
    var btn=event&&(event.currentTarget||event.target);if(btn&&btn.classList)btn.classList.add('active');
    var c=document.querySelectorAll('.tab-content');for(var i=0;i<c.length;i++)c[i].classList.remove('active');
    var el=document.getElementById(tabName+'-tab');if(el)el.classList.add('active');
    if(typeof loadSREContent==='function'&&tabName==='sre')loadSREContent();
    else if(typeof loadExecutiveSummary==='function'&&tabName==='executive')loadExecutiveSummary();
    else if(typeof loadXAIAuditor==='function'&&tabName==='xai')loadXAIAuditor();
    else if(typeof loadFailurePoints==='function'&&tabName==='failure_points')loadFailurePoints();
    else if(typeof loadWheelUniverseHealth==='function'&&tabName==='wheel_universe')loadWheelUniverseHealth();
    else if(typeof loadStrategyComparison==='function'&&tabName==='strategy_comparison')loadStrategyComparison();
    else if(typeof loadClosedTrades==='function'&&tabName==='closed_trades')loadClosedTrades();
    else if(typeof loadWheelAnalytics==='function'&&tabName==='wheel_strategy')loadWheelAnalytics();
    else if(typeof loadSignalReview==='function'&&tabName==='signal_review')loadSignalReview();
    else if(typeof loadTelemetryContent==='function'&&tabName==='telemetry')loadTelemetryContent();
    else if(typeof updateDashboard==='function'&&tabName==='positions')updateDashboard();
    };
    function fmt(v){if(v==null||v===undefined)return '0.00';var n=Number(v);return isFinite(n)?n.toFixed(2):'0.00';}
    function loadVersion(){fetch('/api/version',creds).then(function(r){if(!r.ok){var b=document.getElementById('version-badge');if(b){b.textContent='Dashboard v??? ('+r.status+')';b.title='HTTP '+r.status;}}return r.ok?r.json():null;}).then(function(d){var b=document.getElementById('version-badge');if(!b||!d)return;var s=(d.git_commit_short||(d.git_commit||'').substring(0,7))||'???';b.textContent='Dashboard v'+s;b.title='Commit '+s;}).catch(function(){var b=document.getElementById('version-badge');if(b){b.textContent='Dashboard v???';b.title='Version fetch failed';}});}
    function loadPositions(){fetch('/api/positions',creds).then(function(r){if(!r.ok){var el=document.getElementById('positions-content');if(el)el.innerHTML='<p class="no-positions">Server '+r.status+'. Refresh and log in again.</p>';return null;}return r.json();}).then(function(d){if(!d){return;}var el=document.getElementById('positions-content');if(!el)return;if(d.error){el.innerHTML='<p class="no-positions">'+d.error+'</p>';return;}var pos=Array.isArray(d.positions)?d.positions:[];var tp=document.getElementById('total-positions');if(tp)tp.textContent=pos.length;var tv=document.getElementById('total-value');if(tv)tv.textContent='$'+fmt(d.total_value);var up=document.getElementById('unrealized-pnl');if(up){up.textContent='$'+fmt(d.unrealized_pnl);up.className='stat-value '+(Number(d.unrealized_pnl)>=0?'positive':'negative');}var dp=document.getElementById('day-pnl');if(dp){dp.textContent='$'+fmt(d.day_pnl);dp.className='stat-value '+(Number(d.day_pnl)>=0?'positive':'negative');}if(pos.length===0){el.innerHTML='<p class="no-positions">No open positions</p>';return;}var h='<table><thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>Value</th><th>P&L</th><th>P&L %</th></tr></thead><tbody>';for(var i=0;i<pos.length;i++){var p=pos[i];var side=p.side||'long';var qty=p.qty!=null?p.qty:0;var entry=p.avg_entry_price!=null?fmt(p.avg_entry_price):'-';var cur=p.current_price!=null?fmt(p.current_price):'-';var val=p.market_value!=null?fmt(p.market_value):'-';var pl=p.unrealized_pnl!=null?fmt(p.unrealized_pnl):'-';var plp=(p.unrealized_pnl_pct!=null?fmt(p.unrealized_pnl_pct):'-')+'%';var cls=Number(p.unrealized_pnl)>=0?'positive':'negative';h+='<tr><td>'+p.symbol+'</td><td>'+side+'</td><td>'+qty+'</td><td>'+entry+'</td><td>'+cur+'</td><td>'+val+'</td><td class="'+cls+'">'+pl+'</td><td class="'+cls+'">'+plp+'</td></tr>';}h+='</tbody></table>';el.innerHTML=h;}).catch(function(e){var el=document.getElementById('positions-content');if(el)el.innerHTML='<p class="no-positions">Positions failed: '+(e&&e.message?e.message:'network error')+'. Refresh and log in.</p>';});}
    function err(el,msg){if(el)el.innerHTML='<div class="loading" style="color:#ef4444;">'+msg+'</div>';}
    function cur(v){if(v==null||v===undefined)return '';var n=Number(v);return isFinite(n)?'$'+n.toFixed(2):String(v);}
    window.loadSREContent=function(){var el=document.getElementById('sre-content');if(!el)return;el.innerHTML='<div class="loading">Loading SRE...</div>';fetch('/api/sre/health',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var m=d.sre_metrics||{};var f=d.signal_funnel||{};var h='<div class="stat-card" style="margin-bottom:16px;"><h3>SRE Health</h3><p><strong>Overall:</strong> '+(d.overall_health||'—')+'</p><p><strong>Bot:</strong> '+(d.bot_process&&d.bot_process.running?'Running':'—')+'</p><p><strong>Market:</strong> '+(d.market_status||'—')+' '+(d.market_open?'(open)':'')+'</p></div>';
    h+='<div class="stat-card" style="margin-bottom:16px;"><h3>Metrics</h3><p>Logic heartbeat: '+(m.logic_heartbeat?new Date(m.logic_heartbeat*1000).toLocaleString():'—')+'</p><p>Mock signal success: '+(m.mock_signal_success_pct!=null?m.mock_signal_success_pct.toFixed(1):'—')+'%</p><p>Parser health: '+(m.parser_health_index!=null?m.parser_health_index.toFixed(1):'—')+'%</p><p>Auto-fix count: '+(m.auto_fix_count!=null?m.auto_fix_count:'—')+'</p></div>';
    if(f.alerts!==undefined){h+='<div class="stat-card" style="margin-bottom:16px;"><h3>Signal Funnel (30m)</h3><p>Alerts: '+(f.alerts||0)+' → Parsed: '+(f.parsed||0)+' ('+(f.parsed_rate_pct!=null?f.parsed_rate_pct.toFixed(0):'—')+'%)</p><p>Scored &gt; threshold: '+(f.scored_above_threshold!=null?f.scored_above_threshold:'—')+' ('+(f.scored_rate_pct!=null?f.scored_rate_pct.toFixed(0):'—')+'%)</p></div>';}
    if(d.warnings&&d.warnings.length){h+='<div class="stat-card" style="margin-bottom:16px;"><h3>Warnings</h3><p>'+d.warnings.join(', ')+'</p></div>';}
    if(d.critical_issues&&d.critical_issues.length){h+='<div class="stat-card" style="margin-bottom:16px; border-color:#ef4444;"><h3>Critical</h3><p>'+d.critical_issues.join(', ')+'</p></div>';}
    var fixes=d.recent_rca_fixes||[];if(fixes.length){h+='<div class="stat-card"><h3>Recent RCA Fixes</h3>';for(var i=0;i<Math.min(fixes.length,5);i++){var x=fixes[i];h+='<p>'+(x.check_name||x.reason_code||'')+' — '+(x.reason_code||'')+'</p>';}h+='</div>';}
    el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'SRE failed: '+(e&&e.message?e.message:'network'));});};
    window.loadExecutiveSummary=function(){var el=document.getElementById('executive-content');if(!el)return;el.innerHTML='<div class="loading">Loading Executive...</div>';fetch('/api/executive_summary',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var t=d.total_trades!=null?d.total_trades:0;var pm=d.pnl_metrics||{};var h='<div class="stat-card" style="margin-bottom:16px;"><h3>Executive Summary</h3><p><strong>Total trades:</strong> '+t+'</p>';
    h+='<p><strong>2d P&L:</strong> '+cur(pm.pnl_2d)+' ('+(pm.trades_2d!=null?pm.trades_2d:'—')+' trades, '+(pm.win_rate_2d!=null?pm.win_rate_2d:'—')+'% win)</p>';
    h+='<p><strong>5d P&L:</strong> '+cur(pm.pnl_5d)+' ('+(pm.trades_5d!=null?pm.trades_5d:'—')+' trades, '+(pm.win_rate_5d!=null?pm.win_rate_5d:'—')+'% win)</p></div>';
    var tr=d.trades||[];if(tr.length){h+='<div class="stat-card" style="margin-bottom:16px;"><h3>Recent Trades</h3><table style="width:100%"><thead><tr><th>Time</th><th>Symbol</th><th>P&L</th><th>Close</th></tr></thead><tbody>';for(var i=0;i<Math.min(tr.length,15);i++){var x=tr[i];var ts=x.timestamp?new Date(x.timestamp).toLocaleString():'—';h+='<tr><td>'+ts+'</td><td>'+(x.symbol||'—')+'</td><td>'+cur(x.pnl_usd)+'</td><td>'+(x.close_reason||'—')+'</td></tr>';}h+='</tbody></table></div>';}
    if(d.written_summary){h+='<div class="stat-card"><h3>Summary</h3><pre style="white-space:pre-wrap;font-size:0.9em;">'+String(d.written_summary).substring(0,2000)+(d.written_summary.length>2000?'…':'')+'</pre></div>';}
    el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Executive failed: '+(e&&e.message?e.message:'network'));});};
    window.loadXAIAuditor=function(){var el=document.getElementById('xai-content');if(!el)return;el.innerHTML='<div class="loading">Loading XAI...</div>';fetch('/api/xai/auditor',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var tc=d.trade_count!=null?d.trade_count:0;var wc=d.weight_count!=null?d.weight_count:0;var h='<div class="stat-card" style="margin-bottom:16px;"><h3>Natural Language Auditor</h3><p><strong>Trades:</strong> '+tc+'</p><p><strong>Weights:</strong> '+wc+'</p></div>';
    var tr=d.trades||[];if(tr.length){h+='<div class="stat-card" style="margin-bottom:16px;"><h3>Trade explanations</h3><table style="width:100%"><thead><tr><th>Symbol</th><th>Type</th><th>Why / Summary</th></tr></thead><tbody>';for(var i=0;i<Math.min(tr.length,20);i++){var x=tr[i];var sum=String(x.why||x.summary||x.reason||'').substring(0,80);h+='<tr><td>'+(x.symbol||'—')+'</td><td>'+(x.type||x.event_type||'—')+'</td><td>'+sum+'</td></tr>';}h+='</tbody></table></div>';}
    var wt=d.weights||[];if(wt.length){h+='<div class="stat-card"><h3>Weight entries</h3><table style="width:100%"><thead><tr><th>Component</th><th>Change</th></tr></thead><tbody>';for(var j=0;j<Math.min(wt.length,15);j++){var w=wt[j];h+='<tr><td>'+(w.component||w.name||'—')+'</td><td>'+(w.change!=null?w.change:(w.multiplier!=null?w.multiplier:'—'))+'</td></tr>';}h+='</tbody></table></div>';}
    if(d.errors&&d.errors.length){h+='<div class="stat-card" style="border-color:#ef4444;"><h3>Errors</h3><p>'+d.errors.join('; ')+'</p></div>';}
    el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'XAI failed: '+(e&&e.message?e.message:'network'));});};
    window.loadFailurePoints=function(){var el=document.getElementById('failure_points-content');if(!el)return;el.innerHTML='<div class="loading">Loading Trading Readiness...</div>';fetch('/api/failure_points',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var rdy=d.readiness||'—';var crit=d.critical_count!=null?d.critical_count:0;var warn=d.warning_count!=null?d.warning_count:0;var h='<div class="stat-card" style="margin-bottom:16px;"><h3>Trading Readiness</h3><p><strong>Status:</strong> '+rdy+'</p><p><strong>Critical:</strong> '+crit+'</p><p><strong>Warnings:</strong> '+warn+'</p></div>';
    var fpObj=d.failure_points||d.checks||{};var fpKeys=Object.keys(fpObj);if(fpKeys.length){h+='<div class="stat-card"><h3>Checks</h3><table style="width:100%"><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>';for(var i=0;i<fpKeys.length;i++){var k=fpKeys[i];var x=fpObj[k];var nm=typeof x==='object'&&x?(x.name||x.check_name||x.id||k):k;var st=typeof x==='object'&&x?(x.status||(x.passing===true?'OK':(x.passing===false?'FAIL':'—'))):'—';h+='<tr><td>'+nm+'</td><td>'+st+'</td></tr>';}h+='</tbody></table></div>';}
    if(d.error){h+='<div class="stat-card" style="border-color:#ef4444;"><p>'+d.error+'</p></div>';}
    el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Readiness failed: '+(e&&e.message?e.message:'network'));});};
    window.loadWheelUniverseHealth=function(){var el=document.getElementById('wheel_universe-content');if(!el)return;el.innerHTML='<div class="loading">Loading Wheel Universe Health...</div>';fetch('/api/wheel/universe_health',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var h='';if(d.message){h+='<div class="stat-card"><p>'+d.message+'</p><p>Run: <code>python scripts/generate_wheel_universe_health.py</code></p></div>';}else{h+='<div class="stat-card"><h3>Wheel Universe Health</h3><p><strong>Date:</strong> '+(d.date||'—')+'</p><p><strong>Current universe:</strong> '+(Array.isArray(d.current_universe)?d.current_universe.join(', '):'—')+'</p><p><strong>Selected candidates:</strong> '+(Array.isArray(d.selected_candidates)?d.selected_candidates.join(', '):'—')+'</p></div>';h+='<div class="stat-card"><h3>Sector distribution</h3><pre>'+JSON.stringify(d.sector_distribution||{},null,2)+'</pre></div>';if(d.assignment_count!=null)h+='<div class="stat-card"><p><strong>Assignments:</strong> '+d.assignment_count+' | <strong>Called away:</strong> '+d.call_away_count+'</p></div>';if(d.ai_recommendations&&d.ai_recommendations.length){h+='<div class="stat-card"><h3>AI recommendations</h3><ul>';for(var i=0;i<d.ai_recommendations.length;i++)h+='<li>'+JSON.stringify(d.ai_recommendations[i])+'</li>';h+='</ul></div>';}}el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Wheel Universe Health failed: '+(e&&e.message?e.message:'network'));});};
    window.loadStrategyComparison=function(){var el=document.getElementById('strategy_comparison-content');if(!el)return;el.innerHTML='<div class="loading">Loading Strategy Comparison...</div>';fetch('/api/strategy/comparison',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var sc=d.strategy_comparison||{};var rec=d.recommendation||'WAIT';var score=d.promotion_readiness_score;var badge='<span style="padding:4px 12px;border-radius:6px;font-weight:bold;background:'+(rec==='PROMOTE'?'#10b981':rec==='DO NOT PROMOTE'?'#ef4444':'#f59e0b')+';color:#fff">'+rec+'</span>';var h='<div class="stat-card"><h3>Strategy Comparison</h3><p><strong>Date:</strong> '+(d.date||'—')+'</p><p><strong>Promotion Readiness Score:</strong> '+(score!=null?score:'—')+' / 100</p><p><strong>Recommendation:</strong> '+badge+'</p></div>';h+='<div class="stat-card"><h3>Equity vs Wheel</h3><p>Equity Realized: $'+(sc.equity_realized_pnl!=null?fmt(sc.equity_realized_pnl):'—')+' | Wheel Realized: $'+(sc.wheel_realized_pnl!=null?fmt(sc.wheel_realized_pnl):'—')+'</p><p>Equity Unrealized: $'+(sc.equity_unrealized_pnl!=null?fmt(sc.equity_unrealized_pnl):'—')+' | Wheel Unrealized: $'+(sc.wheel_unrealized_pnl!=null?fmt(sc.wheel_unrealized_pnl):'—')+'</p><p>Equity Drawdown: '+(sc.equity_drawdown!=null?sc.equity_drawdown:'—')+' | Wheel Drawdown: '+(sc.wheel_drawdown!=null?sc.wheel_drawdown:'—')+'</p><p>Equity Sharpe: '+(sc.equity_sharpe_proxy!=null?sc.equity_sharpe_proxy:'—')+' | Wheel Sharpe: '+(sc.wheel_sharpe_proxy!=null?sc.wheel_sharpe_proxy:'—')+'</p><p>Wheel Yield: '+(sc.wheel_yield_per_period!=null?sc.wheel_yield_per_period:'—')+' | Capital Eff Equity: '+(sc.capital_efficiency_equity!=null?sc.capital_efficiency_equity:'—')+' | Wheel: '+(sc.capital_efficiency_wheel!=null?sc.capital_efficiency_wheel:'—')+'</p></div>';if(d.weekly_report&&d.weekly_report.reasoning){var wr=d.weekly_report.reasoning;h+='<div class="stat-card"><h3>Weekly Reasoning</h3><pre>'+JSON.stringify(wr,null,2)+'</pre></div>';}if(d.historical_comparison&&d.historical_comparison.length){h+='<div class="stat-card"><h3>Historical (last 30 days)</h3><table><thead><tr><th>Date</th><th>Equity</th><th>Wheel</th><th>Score</th></tr></thead><tbody>';for(var i=0;i<Math.min(d.historical_comparison.length,15);i++){var x=d.historical_comparison[i];h+='<tr><td>'+(x.date||'—')+'</td><td>$'+(x.equity_realized!=null?fmt(x.equity_realized):'—')+'</td><td>$'+(x.wheel_realized!=null?fmt(x.wheel_realized):'—')+'</td><td>'+(x.promotion_score!=null?x.promotion_score:'—')+'</td></tr>';}h+='</tbody></table></div>';}el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Strategy Comparison failed: '+(e&&e.message?e.message:'network'));});};
    window.loadSignalReview=function(){var el=document.getElementById('signal-review-content');if(!el)return;el.innerHTML='<div class="loading">Loading Signal Review...</div>';fetch('/api/signal_history',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var sig=Array.isArray(d.signals)?d.signals:[];if(sig.length===0){el.innerHTML='<p class="no-positions">No signal history</p>';return;}var h='<table><thead><tr><th>Symbol</th><th>Direction</th><th>Score</th><th>Decision</th></tr></thead><tbody>';for(var i=0;i<Math.min(sig.length,50);i++){var s=sig[i];h+='<tr><td>'+(s.symbol||'—')+'</td><td>'+(s.direction||'—')+'</td><td>'+(s.final_score!=null?fmt(s.final_score):'—')+'</td><td>'+(s.decision||'—')+'</td></tr>';}h+='</tbody></table>';el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Signal review failed: '+(e&&e.message?e.message:'network'));});};
    window.loadTelemetryContent=function(){var el=document.getElementById('telemetry-content');if(!el)return;el.innerHTML='<div class="loading">Loading Telemetry...</div>';fetch('/api/telemetry/latest/index',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var dt=d.latest_date||'—';var list=d.computed||[];var h='<div class="stat-card" style="margin-bottom:16px;"><h3>Telemetry</h3><p><strong>Latest bundle:</strong> '+dt+'</p>';
    if(d.message){h+='<p>'+d.message+'</p>';}
    if(list.length){h+='<p><strong>Computed artifacts:</strong></p><ul>';for(var i=0;i<list.length;i++){var c=list[i];var name=typeof c==='string'?c:(c.name||c.id||'');if(name)h+='<li>'+name+'</li>';}h+='</ul>';}
    h+='</div>';el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Telemetry failed: '+(e&&e.message?e.message:'network'));});};
    window.loadClosedTrades=function(){var el=document.getElementById('closed_trades-content');if(!el)return;el.innerHTML='<div class="loading">Loading closed trades...</div>';fetch('/api/stockbot/closed_trades',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var filter=document.getElementById('closed_trades_filter');var raw=Array.isArray(d.closed_trades)?d.closed_trades:[];var strategyFilter=(filter&&filter.value)||'all';var list=raw;if(strategyFilter==='equity')list=raw.filter(function(t){return (t.strategy_id||'equity')==='equity';});if(strategyFilter==='wheel')list=raw.filter(function(t){return (t.strategy_id||'')==='wheel';});var h='<div class="stat-card" style="margin-bottom:12px;"><label>Filter: </label><select id="closed_trades_filter" onchange="if(typeof loadClosedTrades===\'function\')loadClosedTrades();"><option value="all"'+(strategyFilter==='all'?' selected':'')+'>All trades</option><option value="equity"'+(strategyFilter==='equity'?' selected':'')+'>Equity only</option><option value="wheel"'+(strategyFilter==='wheel'?' selected':'')+'>Wheel only</option></select></div>';
    h+='<div class="stat-card"><h3>Closed Trades ('+list.length+')</h3><table style="width:100%;font-size:12px;"><thead><tr><th>Strategy</th><th>Symbol</th><th>Time</th><th>P&L</th><th>Close</th><th>Phase</th><th>Type</th><th>Strike</th><th>Expiry</th><th>DTE</th><th>Premium</th><th>Assigned</th><th>Called</th></tr></thead><tbody>';
    for(var i=0;i<list.length;i++){var t=list[i];var sid=t.strategy_id||'equity';var stratLabel=sid==='wheel'?'Wheel':'Equity';var ts=t.timestamp?new Date(t.timestamp).toLocaleString():'—';var pnl=t.pnl_usd!=null?'$'+Number(t.pnl_usd).toFixed(2):'—';var close=t.close_reason||'—';var ph=t.wheel_phase||'—';var ot=t.option_type||'—';var st=t.strike!=null?t.strike:'—';var ex=t.expiry||'—';var dte=t.dte!=null?t.dte:'—';var pr=t.premium!=null?'$'+Number(t.premium).toFixed(2):'—';var asn=t.assigned===true?'Y':(t.assigned===false?'N':'—');var ca=t.called_away===true?'Y':(t.called_away===false?'N':'—');h+='<tr><td>'+stratLabel+'</td><td>'+(t.symbol||'—')+'</td><td>'+ts+'</td><td>'+pnl+'</td><td>'+close+'</td><td>'+ph+'</td><td>'+ot+'</td><td>'+st+'</td><td>'+ex+'</td><td>'+dte+'</td><td>'+pr+'</td><td>'+asn+'</td><td>'+ca+'</td></tr>';}
    h+='</tbody></table></div>';el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Closed trades failed: '+(e&&e.message?e.message:'network'));});};
    window.loadWheelAnalytics=function(){var el=document.getElementById('wheel_strategy-content');if(!el)return;el.innerHTML='<div class="loading">Loading Wheel Strategy...</div>';fetch('/api/stockbot/wheel_analytics',creds).then(function(r){if(!r.ok){err(el,'Server '+r.status+'. Refresh and log in.');return null;}return r.json();}).then(function(d){if(!d)return;var h='<div class="stat-card"><h3>Wheel Strategy Analytics</h3><p><strong>Total wheel trades:</strong> '+(d.total_trades!=null?d.total_trades:0)+'</p><p><strong>Premium collected:</strong> $'+(d.premium_collected!=null?Number(d.premium_collected).toFixed(2):'0.00')+'</p><p><strong>Assignment count:</strong> '+(d.assignment_count!=null?d.assignment_count:0)+' | <strong>Call-away count:</strong> '+(d.call_away_count!=null?d.call_away_count:0)+'</p><p><strong>Assignment rate:</strong> '+(d.assignment_rate_pct!=null?d.assignment_rate_pct.toFixed(1):'—')+'% | <strong>Call-away rate:</strong> '+(d.call_away_rate_pct!=null?d.call_away_rate_pct.toFixed(1):'—')+'%</p><p><strong>Expectancy per trade (USD):</strong> '+(d.expectancy_per_trade_usd!=null?'$'+Number(d.expectancy_per_trade_usd).toFixed(2):'—')+'</p><p><strong>Realized P&L sum:</strong> '+(d.realized_pnl_sum!=null?'$'+Number(d.realized_pnl_sum).toFixed(2):'—')+'</p></div>';if(d.error){h+='<div class="stat-card" style="border-color:#f59e0b;"><p>'+d.error+'</p></div>';}el.innerHTML=h;el.dataset.loaded='1';}).catch(function(e){err(el,'Wheel analytics failed: '+(e&&e.message?e.message:'network'));});};
    try{document.body.setAttribute('data-js','1');}catch(e){}
    setTimeout(function(){loadVersion();loadPositions();},0);
    })();
    </script>
    <script>
        function switchTab(tabName, event) {
            // Update tab buttons - use currentTarget so clicking emoji/text still works
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            var btn = event && (event.currentTarget || event.target);
            if (btn && btn.classList) {
                btn.classList.add('active');
            } else {
                var match = document.querySelector('.tab[data-tab="' + tabName + '"]');
                if (match) match.classList.add('active');
                else document.querySelectorAll('.tab').forEach(function(tab) {
                    if (tab.getAttribute('data-tab') === tabName) tab.classList.add('active');
                });
            }
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {
                targetTab.classList.add('active');
            }
            
            // Load content based on tab
            if (tabName === 'sre') {
                loadSREContent();
            } else if (tabName === 'executive') {
                loadExecutiveSummary();
            } else if (tabName === 'xai') {
                loadXAIAuditor();
            } else if (tabName === 'failure_points') {
                loadFailurePoints();
            } else if (tabName === 'wheel_universe') {
                loadWheelUniverseHealth();
            } else if (tabName === 'strategy_comparison') {
                loadStrategyComparison();
            } else if (tabName === 'closed_trades' && typeof loadClosedTrades === 'function') {
                loadClosedTrades();
            } else if (tabName === 'wheel_strategy') {
                loadWheelAnalytics();
            } else if (tabName === 'signal_review') {
                loadSignalReview();
            } else if (tabName === 'telemetry') {
                loadTelemetryContent();
            } else if (tabName === 'positions') {
                // Refresh positions when switching back - force fresh data
                updateDashboard();
            }
        }
        
        function loadSREContent() {
            const sreContent = document.getElementById('sre-content');
            if (!sreContent) return;
            const scrollTop = sreContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            
            if (sreContent.innerHTML.includes('Loading') || !sreContent.dataset.loaded) {
                fetch('/api/sre/health', { credentials: 'same-origin' })
                    .then(function(response) {
                        if (!response.ok) {
                            sreContent.innerHTML = '<div class="loading" style="color:#ef4444;">Server ' + response.status + '. Refresh and log in again.</div>';
                            return Promise.reject(new Error('HTTP ' + response.status));
                        }
                        return response.json();
                    })
                    .then(function(data) {
                        return Promise.all([
                            Promise.resolve(data),
                            fetch('/api/telemetry/latest/computed?name=bar_health_summary', { credentials: 'same-origin' }).then(r => r.ok ? r.json() : {}).catch(() => ({}))
                        ]);
                    })
                    .then(([data, barHealthResp]) => {
                        const barHealth = (barHealthResp && barHealthResp.data) ? barHealthResp.data : null;
                        sreContent.dataset.loaded = 'true';
                        renderSREContent(data, sreContent, barHealth);
                        fetch('/api/version', { credentials: 'same-origin' }).then(r => r.ok ? r.json() : null).then(versionData => {
                            renderVersionPanel(versionData, sreContent);
                        }).catch(() => renderVersionPanel(null, sreContent));
                        fetch('/api/versions', { credentials: 'same-origin' }).then(r => r.ok ? r.json() : {}).then(versionsData => {
                            renderVersionParityPanel(versionsData, sreContent);
                        }).catch(() => renderVersionParityPanel({}, sreContent));
                        // Restore scroll position after render
                        if (scrollTop > 0) {
                            requestAnimationFrame(() => {
                                sreContent.scrollTop = scrollTop;
                                window.scrollTo(0, scrollTop);
                            });
                        }
                    })
                    .catch(error => {
                        sreContent.innerHTML = `<div class="loading" style="color: #ef4444;">Error loading SRE data: ${error.message}</div>`;
                    });
            }
        }
        
        function renderVersionPanel(versionData, container) {
            let existing = document.getElementById('dashboard-version-panel');
            if (existing) existing.remove();
            const div = document.createElement('div');
            div.id = 'dashboard-version-panel';
            div.className = 'stat-card';
            div.style.marginTop = '20px';
            div.style.padding = '12px 16px';
            if (!versionData) {
                div.innerHTML = '<div style="font-weight: 600;">Dashboard Version</div><div style="color: #ef4444; font-size: 0.9em;">Version unavailable</div>';
                div.style.borderLeft = '4px solid #ef4444';
            } else {
                const shortSha = versionData.git_commit_short || versionData.git_commit || '—';
                const startTime = versionData.process_start_time_utc || '—';
                const match = versionData.matches_expected === true;
                const color = match ? '#10b981' : (versionData.matches_expected === false ? '#ef4444' : '#6b7280');
                div.innerHTML = '<div style="font-weight: 600;">Dashboard Version</div><div style="font-size: 0.9em;">Commit: <code>' + shortSha + '</code></div><div style="font-size: 0.85em; color: #666;">Process start: ' + startTime + '</div>';
                div.style.borderLeft = '4px solid ' + color;
            }
            container.appendChild(div);
        }
        
        function renderVersionParityPanel(versionsData, container) {
            let existing = document.getElementById('version-parity-panel');
            if (existing) existing.remove();
            const div = document.createElement('div');
            div.id = 'version-parity-panel';
            div.className = 'stat-card';
            div.style.marginTop = '20px';
            div.style.padding = '12px 16px';
            div.style.borderLeft = '4px solid #6b7280';
            const live = versionsData.live || {};
            const paper = versionsData.paper || {};
            const shadow = versionsData.shadow || {};
            const lv = live.version || '—';
            const lc = (live.commit && live.commit.substring(0, 7)) || '—';
            const pv = paper.version || '—';
            const pc = (paper.commit && paper.commit.substring(0, 7)) || '—';
            const sv = shadow.version || '—';
            const sc = (shadow.commit && shadow.commit.substring(0, 7)) || '—';
            const sameCommit = lc !== '—' && lc === pc && pc === sc;
            const sameVersion = lv === pv && pv === sv && lv !== '—';
            const parity = sameCommit || sameVersion;
            if (parity) {
                div.style.borderLeftColor = '#10b981';
            }
            let html = '<div style="font-weight: 600;">Version Parity</div>';
            html += '<table style="width:100%; font-size: 0.9em; margin-top: 8px;"><tr><th>Mode</th><th>Version</th><th>Commit</th></tr>';
            html += '<tr><td>live</td><td><code>' + lv + '</code></td><td><code>' + lc + '</code></td></tr>';
            html += '<tr><td>paper</td><td><code>' + pv + '</code></td><td><code>' + pc + '</code></td></tr>';
            html += '<tr><td>shadow</td><td><code>' + sv + '</code></td><td><code>' + sc + '</code></td></tr></table>';
            if (parity) {
                html += '<div style="margin-top: 10px; color: #065f46; font-weight: 600;">PROMOTED TO LATEST</div>';
            } else if (lc !== '—' || pc !== '—' || sc !== '—') {
                html += '<div style="margin-top: 10px; color: #92400e; font-size: 0.9em;">Mismatch — run promote_all_to_latest.py to align</div>';
            }
            div.innerHTML = html;
            container.appendChild(div);
        }
        
        function renderSREContent(data, container, barHealth) {
            // NEVER show 'unknown' - default to 'degraded' if not set
            const overallHealth = (data.overall_health && data.overall_health !== 'unknown') ? data.overall_health : 'degraded';
            const healthClass = overallHealth === 'healthy' ? 'healthy' : 
                              overallHealth === 'degraded' ? 'degraded' : 'critical';
            
            // Check for stagnation alert
            const stagnationAlert = data.stagnation_alert || {};
            const isStagnating = stagnationAlert.status === 'STAGNATION';
            
            // Extract SRE metrics
            const sreMetrics = data.sre_metrics || {};
            const logicHeartbeat = sreMetrics.logic_heartbeat || 0;
            const mockSignalSuccessPct = sreMetrics.mock_signal_success_pct || 100.0;
            const parserHealthIndex = sreMetrics.parser_health_index || 100.0;
            const autoFixCount = sreMetrics.auto_fix_count || 0;
            
            // Extract funnel metrics
            const funnelMetrics = data.signal_funnel || {};
            
            // Determine health color for metrics (GREEN > 95%, YELLOW 80-95%, RED < 80%)
            function getMetricHealthColor(value) {
                if (value >= 95) return '#10b981';  // GREEN
                if (value >= 80) return '#f59e0b';  // YELLOW
                return '#ef4444';  // RED
            }
            
            const mockSignalHealthColor = getMetricHealthColor(mockSignalSuccessPct);
            const parserHealthColor = getMetricHealthColor(parserHealthIndex);
            
            // Format timestamp - show relative time if recent
            let heartbeatTime = 'Never';
            if (logicHeartbeat > 0) {
                const heartbeatDate = new Date(logicHeartbeat * 1000);
                const now = new Date();
                const ageSeconds = (now - heartbeatDate) / 1000;
                if (ageSeconds < 60) {
                    heartbeatTime = `${Math.floor(ageSeconds)}s ago`;
                } else if (ageSeconds < 3600) {
                    heartbeatTime = `${Math.floor(ageSeconds / 60)}m ago`;
                } else {
                    heartbeatTime = heartbeatDate.toLocaleString();
                }
            }
            
            // Recent RCA fixes
            const recentFixes = data.recent_rca_fixes || [];
            const healthSub = data.health_subsystem || {};
            const bannerLevel = healthSub.banner_level || 'none';
            const safeModeActive = healthSub.health_safe_mode_active;
            const escalationsActive = healthSub.escalations_active || [];
            const showCriticalBanner = bannerLevel === 'critical' && (safeModeActive || escalationsActive.length > 0);

            let html = '';
            if (showCriticalBanner) {
                const firstEsc = escalationsActive[0] || {};
                const title = safeModeActive ? 'Safe mode active' : 'Operational incident: self-healing escalated';
                const reason = safeModeActive ? (healthSub.self_heal_reason_codes && healthSub.self_heal_reason_codes[0]) || 'decision_integrity' : (firstEsc.check_name + ' :: ' + firstEsc.reason_code);
                const counts = firstEsc.count_6h != null ? firstEsc.count_6h + ' in 6h, ' + (firstEsc.count_24h || 0) + ' in 24h' : '';
                const cooldownUntil = firstEsc.cooldown_until_ts ? new Date(firstEsc.cooldown_until_ts).toLocaleString() : '';
                html += `
                <div id="sre-critical-banner" style="width: 100%; margin: -10px -15px 20px -15px; padding: 20px 20px; background: #7f1d1d; color: #fef2f2; border-bottom: 4px solid #dc2626; font-size: 1.1em; box-sizing: border-box;">
                    <div style="font-weight: bold; font-size: 1.3em; margin-bottom: 10px;">🛑 ${title}</div>
                    <div style="margin-bottom: 8px;"><strong>Reason:</strong> ${reason}</div>
                    ${counts ? '<div style="margin-bottom: 8px;"><strong>Counts:</strong> ' + counts + '</div>' : ''}
                    ${cooldownUntil ? '<div style="margin-bottom: 8px;"><strong>Cooldown until:</strong> ' + cooldownUntil + '</div>' : ''}
                    <div style="margin-top: 12px; display: flex; gap: 12px; flex-wrap: wrap;">
                        <a href="#self-heal-ledger" style="padding: 8px 16px; background: #dc2626; color: white; border-radius: 6px; text-decoration: none;">Open Self-Healing Ledger</a>
                        <a href="#self-heal-patterns" style="padding: 8px 16px; background: #b91c1c; color: white; border-radius: 6px; text-decoration: none;">Open Pattern Report</a>
                    </div>
                </div>
                `;
            }

            html += `
                <div class="stat-card" style="border: 3px solid ${healthClass === 'healthy' ? '#10b981' : healthClass === 'degraded' ? '#f59e0b' : '#ef4444'}; margin-bottom: 20px;">
                    <h2 style="color: ${healthClass === 'healthy' ? '#10b981' : healthClass === 'degraded' ? '#f59e0b' : '#ef4444'}; margin-bottom: 10px;">
                        Overall Health: ${overallHealth.toUpperCase()}
                    </h2>
                    <p>Market: <span style="padding: 4px 8px; background: ${data.market_open ? '#10b981' : '#64748b'}; color: white; border-radius: 4px;">
                        ${data.market_status || 'unknown'}
                    </span></p>
                    ${isStagnating ? '<p style="color: #ef4444; margin-top: 10px; font-weight: bold; font-size: 1.1em;"><strong>⚠️ STAGNATION DETECTED:</strong> ' + stagnationAlert.alerts_30m + ' alerts but ' + stagnationAlert.orders_30m + ' trades in 30min</p>' : ''}
                    ${data.critical_issues ? '<p style="color: #ef4444; margin-top: 10px;"><strong>Critical:</strong> ' + data.critical_issues.join(', ') + '</p>' : ''}
                    ${data.warnings ? '<p style="color: #f59e0b; margin-top: 10px;"><strong>Warnings:</strong> ' + data.warnings.join(', ') + '</p>' : ''}
                    ${(data.health_subsystem && data.health_subsystem.self_heal_required) ? `
                    <div style="margin-top: 15px; padding: 12px; background: ${data.health_subsystem.health_safe_mode_active ? '#fef2f2' : '#fffbeb'}; border: 2px solid ${data.health_subsystem.health_safe_mode_active ? '#ef4444' : '#f59e0b'}; border-radius: 8px;">
                        <strong>${data.health_subsystem.health_safe_mode_active ? '🛑 Self-healing blocked (manual action required)' : '🔧 Self-healing invoked'}</strong>
                        ${(data.health_subsystem.self_heal_reason_codes && data.health_subsystem.self_heal_reason_codes.length) ? '<br/><span style="font-size: 0.9em;">Reasons: ' + data.health_subsystem.self_heal_reason_codes.join(', ') + '</span>' : ''}
                        <br/><a href="#self-heal-ledger" data-active-ids="${(data.health_subsystem.active_heal_ids || []).join(',')}" class="self-heal-ledger-link" style="font-size: 0.9em;">View Self-Healing Ledger</a>
                    </div>
                    ` : ''}
                </div>
                
                ${funnelMetrics.alerts !== undefined ? `
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📊 Signal-to-Trade Funnel (Last 30 Minutes)</h2>
                    <div style="display: flex; flex-direction: column; gap: 15px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
                            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">Incoming UW Alerts</div>
                            <div style="font-size: 2.5em; font-weight: bold;">${funnelMetrics.alerts || 0}</div>
                        </div>
                        <div style="text-align: center; font-size: 2em; color: #667eea;">↓</div>
                        <div style="background: ${funnelMetrics.parsed > 0 ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'}; padding: 20px; border-radius: 10px; color: white;">
                            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">Parsed Signals</div>
                            <div style="font-size: 2.5em; font-weight: bold;">${funnelMetrics.parsed || 0}</div>
                            <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">${funnelMetrics.parsed_rate_pct || 0}% conversion</div>
                        </div>
                        <div style="text-align: center; font-size: 2em; color: #667eea;">↓</div>
                        <div style="background: ${funnelMetrics.scored_above_threshold > 0 ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'}; padding: 20px; border-radius: 10px; color: white;">
                            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">Scored Signals > 2.7</div>
                            <div style="font-size: 2.5em; font-weight: bold;">${funnelMetrics.scored_above_threshold || 0}</div>
                            <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">${funnelMetrics.scored_rate_pct || 0}% conversion</div>
                        </div>
                        <div style="text-align: center; font-size: 2em; color: #667eea;">↓</div>
                        <div style="background: ${funnelMetrics.orders_sent > 0 ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'}; padding: 20px; border-radius: 10px; color: white;">
                            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">Orders Sent</div>
                            <div style="font-size: 2.5em; font-weight: bold;">${funnelMetrics.orders_sent || 0}</div>
                            <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">${funnelMetrics.order_rate_pct || 0}% conversion</div>
                        </div>
                        ${funnelMetrics.alerts > 0 ? `
                        <div style="margin-top: 15px; padding: 15px; background: #f3f4f6; border-radius: 8px;">
                            <div style="font-weight: bold; margin-bottom: 10px;">Overall Conversion Rate</div>
                            <div style="font-size: 1.5em; color: ${funnelMetrics.overall_conversion_pct > 5 ? '#10b981' : funnelMetrics.overall_conversion_pct > 0 ? '#f59e0b' : '#ef4444'};">
                                ${funnelMetrics.overall_conversion_pct || 0}%
                            </div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                                ${funnelMetrics.orders_sent || 0} orders from ${funnelMetrics.alerts || 0} alerts
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                ` : ''}
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">🔍 SRE System Health Panel</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div class="stat-card">
                            <div class="stat-label">Logic Heartbeat</div>
                            <div class="stat-value" style="font-size: 1.2em;">${heartbeatTime}</div>
                        </div>
                        <div class="stat-card" style="border-left: 4px solid ${mockSignalHealthColor};">
                            <div class="stat-label">Mock Signal Success %</div>
                            <div class="stat-value" style="color: ${mockSignalHealthColor}; font-size: 1.8em;">${mockSignalSuccessPct.toFixed(1)}%</div>
                            ${sreMetrics.last_mock_signal_score !== undefined ? 
                                `<div style="font-size: 0.85em; color: #666; margin-top: 5px;">Last score: ${sreMetrics.last_mock_signal_score.toFixed(2)}</div>` : ''}
                        </div>
                        <div class="stat-card" style="border-left: 4px solid ${parserHealthColor};">
                            <div class="stat-label">Parser Health Index</div>
                            <div class="stat-value" style="color: ${parserHealthColor}; font-size: 1.8em;">${parserHealthIndex.toFixed(1)}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Auto-Fix Count</div>
                            <div class="stat-value" style="font-size: 1.8em;">${autoFixCount}</div>
                        </div>
                        ${data.stagnation_watchdog ? `
                        <div class="stat-card" style="border-left: 4px solid ${data.stagnation_watchdog.status === 'STAGNATION' ? '#ef4444' : '#10b981'};">
                            <div class="stat-label">Stagnation Watchdog</div>
                            <div class="stat-value" style="color: ${data.stagnation_watchdog.status === 'STAGNATION' ? '#ef4444' : '#10b981'}; font-size: 1.8em;">
                                ${data.stagnation_watchdog.status || 'OK'}
                            </div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                                Alerts: ${data.stagnation_watchdog.alerts_received || 0} | Trades: ${data.stagnation_watchdog.trades_executed || 0}
                            </div>
                            ${data.stagnation_watchdog.parser_reload_triggered ? 
                                `<div style="font-size: 0.85em; color: #f59e0b; margin-top: 5px;">⚠️ Parser Warm Reload Triggered</div>` : ''}
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                ${barHealth && (barHealth.total_symbols !== undefined || barHealth.missing_list) ? (function() {
                    const total = barHealth.total_symbols || 0;
                    const withBars = barHealth.symbols_with_bars || 0;
                    const missingBars = barHealth.symbols_missing_bars || 0;
                    const pctMissing = barHealth.percent_missing || (total ? (missingBars / total * 100) : 0);
                    const missingList = barHealth.missing_list || [];
                    const details = barHealth.details || {};
                    const warnHighMissing = total > 0 && pctMissing > 20;
                    let rows = '';
                    const symbols = Object.keys(details).length ? Object.keys(details).sort() : missingList.slice();
                    symbols.forEach(sym => {
                        const d = details[sym] || {};
                        const status = d.status || (missingList.indexOf(sym) >= 0 ? 'MISSING' : 'OK');
                        const count = d.count != null ? d.count : (status === 'OK' ? '—' : '0');
                        const color = status === 'OK' ? '#10b981' : '#ef4444';
                        rows += '<tr><td>' + sym + '</td><td style="color:' + color + '; font-weight: bold;">' + status + '</td><td>' + count + '</td></tr>';
                    });
                    if (!rows && missingList.length) missingList.forEach(sym => { rows += '<tr><td>' + sym + '</td><td style="color:#ef4444; font-weight: bold;">MISSING</td><td>0</td></tr>'; });
                    return `
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📊 Bar Health (Alpaca 1m bars)</h2>
                    ${warnHighMissing ? '<div style="padding: 12px; background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; margin-bottom: 12px; color: #991b1b;"><strong>⚠️ &gt;20% symbols missing bars.</strong> Counterfactuals and exit attribution may be incomplete.</div>' : ''}
                    <div style="margin-bottom: 10px;">${withBars} / ${total} symbols have 1m bars · ${missingBars} missing (${pctMissing.toFixed(1)}%)</div>
                    <div style="overflow-x: auto;">
                        <table style="width:100%; font-size: 0.9em;">
                            <thead><tr><th>Symbol</th><th>Status</th><th>Count</th></tr></thead>
                            <tbody>${rows || '<tr><td colspan="3">No symbol data</td></tr>'}</tbody>
                        </table>
                    </div>
                </div>
                    `;
                })() : ''}
                
                ${recentFixes.length > 0 ? `
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">🔧 Real-Time Diagnostic Feed (Recent RCA Fixes)</h2>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Trigger</th>
                                    <th>Status</th>
                                    <th>Fixes Applied</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                ` + recentFixes.map(fix => {
                    const timeStr = fix.time ? new Date(fix.time).toLocaleString() : (fix.timestamp ? new Date(fix.timestamp * 1000).toLocaleString() : 'N/A');
                    const statusColor = fix.overall_status === 'OK' ? '#10b981' : fix.overall_status === 'WARNING' ? '#f59e0b' : '#ef4444';
                    const fixesApplied = fix.fixes_applied && fix.fixes_applied.length > 0 ? fix.fixes_applied.join(', ') : 'None';
                    return `
                        <tr>
                            <td>${timeStr}</td>
                            <td>${fix.trigger || 'N/A'}</td>
                            <td style="color: ${statusColor}; font-weight: bold;">${fix.overall_status || 'N/A'}</td>
                            <td>${fixesApplied}</td>
                            <td style="font-size: 0.9em; color: #666;">
                                ${fix.checks && fix.checks.length > 0 ? 
                                    fix.checks.map(c => `${c.check_name}: ${c.status}`).join(', ') : 'N/A'}
                            </td>
                        </tr>
                    `;
                }).join('') + `
                            </tbody>
                        </table>
                    </div>
                </div>
                ` : ''}
                
                <div class="positions-table" style="margin-bottom: 20px;" id="self-heal-ledger">
                    <h2 style="margin-bottom: 15px;" id="self-heal-patterns">📋 Self-Healing Ledger</h2>
                    <div style="margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                        <label>Check: <select id="ledger-filter-check"><option value="">All</option></select></label>
                        <label>Severity: <select id="ledger-filter-severity"><option value="">All</option><option value="FAIL">FAIL</option><option value="WARN">WARN</option><option value="INFO">INFO</option></select></label>
                        <label>Auto-healed: <select id="ledger-filter-auto"><option value="">All</option><option value="true">Y</option><option value="false">N</option></select></label>
                        <label>Window: <select id="ledger-filter-window"><option value="">All</option><option value="24h">24h</option><option value="7d">7d</option></select></label>
                        <button type="button" id="ledger-refresh" style="padding: 6px 12px;">Refresh</button>
                    </div>
                    <div id="ledger-summary" style="margin-bottom: 10px; padding: 10px; background: #f3f4f6; border-radius: 6px; font-size: 0.9em;"></div>
                    <div style="overflow-x: auto;">
                        <table id="ledger-table">
                            <thead>
                                <tr>
                                    <th>Heal ID</th>
                                    <th>Time detected</th>
                                    <th>Check name</th>
                                    <th>Severity</th>
                                    <th>Issue summary</th>
                                    <th>Remediation</th>
                                    <th>Auto-healed</th>
                                    <th>Verification</th>
                                    <th>Duration</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="ledger-tbody"></tbody>
                        </table>
                    </div>
                </div>
                <scr` + `ipt>
                (function() {
                    function loadLedger() {
                        const check = document.getElementById('ledger-filter-check') && document.getElementById('ledger-filter-check').value;
                        const severity = document.getElementById('ledger-filter-severity') && document.getElementById('ledger-filter-severity').value;
                        const auto = document.getElementById('ledger-filter-auto') && document.getElementById('ledger-filter-auto').value;
                        const window_ = document.getElementById('ledger-filter-window') && document.getElementById('ledger-filter-window').value;
                        let url = '/api/sre/self_heal_events?limit=200';
                        if (check) url += '&check_name=' + encodeURIComponent(check);
                        if (severity) url += '&severity=' + encodeURIComponent(severity);
                        if (auto !== '') url += '&auto_healed=' + (auto === 'true');
                        if (window_) url += '&since=' + encodeURIComponent(window_);
                        fetch(url).then(r => r.json()).then(data => {
                            const events = data.events || [];
                            const tbody = document.getElementById('ledger-tbody');
                            if (!tbody) return;
                            tbody.innerHTML = events.map(e => {
                                const detected = e.ts_detected ? new Date(e.ts_detected).toLocaleString() : '-';
                                const completed = e.ts_action_completed ? new Date(e.ts_action_completed) : null;
                                const start = e.ts_detected ? new Date(e.ts_detected) : null;
                                let duration = '-';
                                if (completed && start) { const s = (completed - start) / 1000; duration = s < 60 ? s.toFixed(1) + 's' : (s / 60).toFixed(1) + 'm'; }
                                const status = e.required_human_ack ? 'Escalated' : (e.verification_result === 'PASS' ? 'Resolved' : (e.verification_result === 'FAIL' ? 'Failed' : 'Pending'));
                                return '<tr><td style="font-size:0.8em;">' + (e.heal_id || '').slice(0,8) + '</td><td>' + detected + '</td><td>' + (e.check_name || '') + '</td><td>' + (e.severity || '') + '</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;" title="' + (e.issue_summary || '') + '">' + (e.issue_summary || '').slice(0, 60) + '</td><td>' + (e.remediation_action || '') + '</td><td>' + (e.auto_healed ? 'Y' : 'N') + '</td><td>' + (e.verification_result || '-') + '</td><td>' + duration + '</td><td>' + status + '</td></tr>';
                            }).join('') || '<tr><td colspan="10">No events</td></tr>';
                            const summary = document.getElementById('ledger-summary');
                            if (summary && events.length) {
                                const byCheck = {};
                                events.forEach(ev => { byCheck[ev.check_name] = (byCheck[ev.check_name] || 0) + 1; });
                                const top = Object.entries(byCheck).sort((a,b) => b[1] - a[1]).slice(0, 5);
                                summary.innerHTML = '<strong>Top recurring (this window):</strong> ' + top.map(([k,v]) => k + ': ' + v).join(', ');
                            } else if (summary) summary.innerHTML = '';
                            const sel = document.getElementById('ledger-filter-check');
                            if (sel && sel.options.length <= 1) {
                                const names = [...new Set((events || []).map(e => e.check_name).filter(Boolean))].sort();
                                names.forEach(n => { const o = document.createElement('option'); o.value = n; o.textContent = n; sel.appendChild(o); });
                            }
                        }).catch(() => { const tbody = document.getElementById('ledger-tbody'); if (tbody) tbody.innerHTML = '<tr><td colspan="10">Error loading ledger</td></tr>'; });
                    }
                    const refresh = document.getElementById('ledger-refresh');
                    if (refresh) refresh.addEventListener('click', loadLedger);
                    ['ledger-filter-check','ledger-filter-severity','ledger-filter-auto','ledger-filter-window'].forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.addEventListener('change', loadLedger);
                    });
                    loadLedger();
                })();
                </scr` + `ipt>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📊 Signal Components</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px;">
            `;
            
            const signals = data.signal_components || {};
            Object.entries(signals).forEach(([name, health]) => {
                const status = health.status || 'unknown';
                const statusColor = status === 'healthy' ? '#10b981' : 
                                  status === 'degraded' ? '#f59e0b' : 
                                  status === 'critical' ? '#ef4444' : '#64748b';
                html += `
                    <div class="stat-card" style="border-left: 4px solid ${statusColor};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>${name}</strong>
                            <span style="padding: 2px 8px; background: ${statusColor}; color: white; border-radius: 4px; font-size: 0.85em;">
                                ${status}
                            </span>
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            ${health.last_update_age_sec !== null && health.last_update_age_sec !== undefined ? 
                                `<div>Last Update: ${formatTimeAgo(health.last_update_age_sec)}</div>` : 
                                '<div>Last Update: N/A</div>'}
                            ${health.data_freshness_sec !== null && health.data_freshness_sec !== undefined ? 
                                `<div>Freshness: ${formatTimeAgo(health.data_freshness_sec)}</div>` : ''}
                            ${health.signals_generated_1h !== undefined && health.signals_generated_1h > 0 ? 
                                `<div>Generated (1h): ${health.signals_generated_1h}</div>` : ''}
                            ${health.found_in_symbols && health.found_in_symbols.length > 0 ? 
                                `<div>Found in: ${health.found_in_symbols.slice(0, 3).join(', ')}${health.found_in_symbols.length > 3 ? '...' : ''}</div>` : ''}
                            ${health.signal_type ? 
                                `<div>Type: ${health.signal_type}</div>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += `</div></div>
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">🌐 UW API Endpoints</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px;">
            `;
            
            const apis = data.uw_api_endpoints || {};
            Object.entries(apis).forEach(([name, health]) => {
                const status = health.status || 'unknown';
                const statusColor = status === 'healthy' ? '#10b981' : 
                                  status === 'degraded' ? '#f59e0b' : 
                                  status === 'critical' || status === 'no_api_key' ? '#ef4444' : '#64748b';
                html += `
                    <div class="stat-card" style="border-left: 4px solid ${statusColor};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>${name}</strong>
                            <span style="padding: 2px 8px; background: ${statusColor}; color: white; border-radius: 4px; font-size: 0.85em;">
                                ${status}
                            </span>
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            ${health.avg_latency_ms !== null && health.avg_latency_ms !== undefined ? 
                                `<div>Latency: ${health.avg_latency_ms.toFixed(0)}ms</div>` : ''}
                            ${health.error_rate_1h !== undefined ? 
                                `<div>Error Rate: ${(health.error_rate_1h * 100).toFixed(1)}%</div>` : ''}
                            ${health.last_error ? 
                                `<div style="color: #ef4444; margin-top: 5px;">${health.last_error.substring(0, 50)}</div>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += `</div></div>
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">⚙️ Trade Engine & Execution</h2>
                    <div class="stat-card">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            ${data.order_execution ? `
                                <div><strong>Status:</strong> <span style="color: ${healthClass === 'healthy' ? '#10b981' : healthClass === 'degraded' ? '#f59e0b' : '#ef4444'}">${data.order_execution.status || 'unknown'}</span></div>
                                ${data.order_execution.last_order_age_sec !== null && data.order_execution.last_order_age_sec !== undefined ? 
                                    `<div><strong>Last Order:</strong> ${formatTimeAgo(data.order_execution.last_order_age_sec)}</div>` : 
                                    '<div><strong>Last Order:</strong> N/A</div>'}
                                <div><strong>Orders (1h):</strong> ${data.order_execution.orders_1h || 0}</div>
                                <div><strong>Orders (3h):</strong> ${data.order_execution.orders_3h || 0}</div>
                                <div><strong>Orders (24h):</strong> ${data.order_execution.orders_24h || 0}</div>
                                ${data.order_execution.fill_rate !== undefined ? 
                                    `<div><strong>Fill Rate:</strong> ${(data.order_execution.fill_rate * 100).toFixed(1)}%</div>` : ''}
                                ${data.order_execution.errors_1h !== undefined ? 
                                    `<div><strong>Errors (1h):</strong> ${data.order_execution.errors_1h}</div>` : ''}
                            ` : '<div>No execution data available</div>'}
                        </div>
                    </div>
                </div>
                
                ${data.comprehensive_learning ? `
                <div class="positions-table">
                    <h2 style="margin-bottom: 15px;">🧠 Learning Engine</h2>
                    <div class="stat-card">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div><strong>Status:</strong> <span style="color: ${data.comprehensive_learning.running ? '#10b981' : '#64748b'}">${data.comprehensive_learning.running ? 'Running' : 'Idle'}</span></div>
                            ${data.comprehensive_learning.last_run_age_sec !== null && data.comprehensive_learning.last_run_age_sec !== undefined ? 
                                `<div><strong>Last Run:</strong> ${formatTimeAgo(data.comprehensive_learning.last_run_age_sec)}</div>` : 
                                '<div><strong>Last Run:</strong> N/A</div>'}
                            <div><strong>Success Count:</strong> ${data.comprehensive_learning.success_count || 0}</div>
                            <div><strong>Error Count:</strong> ${data.comprehensive_learning.error_count || 0}</div>
                            ${data.comprehensive_learning.components_available ? `
                                <div><strong>Components:</strong> ${Object.keys(data.comprehensive_learning.components_available).filter(k => data.comprehensive_learning.components_available[k]).join(', ') || 'None'}</div>
                            ` : ''}
                            ${data.comprehensive_learning.error ? `
                                <div style="color: #ef4444;"><strong>Error:</strong> ${data.comprehensive_learning.error}</div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                ` : ''}
            `;
            
            container.innerHTML = html;
        }
        
        // Auto-refresh SRE content if on SRE tab (less frequent)
        setInterval(() => {
            if (document.getElementById('sre-tab').classList.contains('active')) {
                loadSREContent();
            }
        }, 60000);  // Refresh every 60 seconds (reduced from 10s)
        
        // Auto-refresh Executive Summary if on executive tab
        setInterval(() => {
            const executiveTab = document.getElementById('executive-tab');
            if (executiveTab && executiveTab.classList.contains('active')) {
                loadExecutiveSummary();
            }
        }, 60000);  // Refresh every 60 seconds (reduced from 30s)
        
        // Auto-refresh XAI Auditor if on xai tab
        setInterval(() => {
            const xaiTab = document.getElementById('xai-tab');
            if (xaiTab && xaiTab.classList.contains('active')) {
                loadXAIAuditor();
            }
        }, 60000);  // Refresh every 60 seconds
        
        // Auto-refresh Failure Points if on failure_points tab
        setInterval(() => {
            const fpTab = document.getElementById('failure_points-tab');
            if (fpTab && fpTab.classList.contains('active')) {
                loadFailurePoints();
            }
        }, 30000);  // Refresh every 30 seconds
        
        // Auto-refresh Signal Review if on signal_review tab
        setInterval(() => {
            const signalTab = document.getElementById('signal_review-tab');
            if (signalTab && signalTab.classList.contains('active')) {
                loadSignalReview();
            }
        }, 30000);  // Refresh every 30 seconds

        // Auto-refresh Telemetry if on telemetry tab
        setInterval(() => {
            const tTab = document.getElementById('telemetry-tab');
            if (tTab && tTab.classList.contains('active')) {
                loadTelemetryContent();
            }
        }, 60000);  // Refresh every 60 seconds
        
        function updateLastSignalTimestamp() {
            fetch('/api/signal_history', { credentials: 'same-origin' })
                .then(function(response) { if (!response.ok) return Promise.reject(new Error('HTTP ' + response.status)); return response.json(); })
                .then(data => {
                    const lastSignalEl = document.getElementById('last-signal');
                    if (data.last_signal_timestamp) {
                        try {
                            const signalDate = new Date(data.last_signal_timestamp);
                            const now = new Date();
                            const ageSeconds = Math.floor((now - signalDate) / 1000);
                            if (ageSeconds < 60) {
                                lastSignalEl.textContent = `${ageSeconds}s ago`;
                                lastSignalEl.style.color = '#10b981';
                            } else if (ageSeconds < 300) {
                                lastSignalEl.textContent = `${Math.floor(ageSeconds / 60)}m ago`;
                                lastSignalEl.style.color = '#f59e0b';
                            } else {
                                lastSignalEl.textContent = `${Math.floor(ageSeconds / 3600)}h ago`;
                                lastSignalEl.style.color = '#ef4444';
                            }
                        } catch (e) {
                            lastSignalEl.textContent = 'Unknown';
                        }
                    } else {
                        lastSignalEl.textContent = 'Never';
                        lastSignalEl.style.color = '#ef4444';
                    }
                })
                .catch(error => {
                    document.getElementById('last-signal').textContent = 'Error';
                });
        }

        async function loadTelemetryContent() {
            const container = document.getElementById('telemetry-content');
            if (!container) return;

            var creds = { credentials: 'same-origin' };
            try {
                const [idx, lvs, sp, swr, health, blockedCf, exitQual, sigProf, gateProf, intelRec, paperIntel] = await Promise.all([
                    fetch('/api/telemetry/latest/index', creds).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
                    fetch('/api/telemetry/latest/computed?name=live_vs_shadow_pnl', creds).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
                    fetch('/api/telemetry/latest/computed?name=signal_performance', creds).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
                    fetch('/api/telemetry/latest/computed?name=signal_weight_recommendations', creds).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
                    fetch('/api/telemetry/latest/health', creds).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
                    fetch('/api/telemetry/latest/computed?name=blocked_counterfactuals_summary', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                    fetch('/api/telemetry/latest/computed?name=exit_quality_summary', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                    fetch('/api/telemetry/latest/computed?name=signal_profitability', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                    fetch('/api/telemetry/latest/computed?name=gate_profitability', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                    fetch('/api/telemetry/latest/computed?name=intelligence_recommendations', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                    fetch('/api/paper-mode-intel-state', creds).then(r => r.ok ? r.json() : {}).catch(() => ({})),
                ]);

                if (idx && idx.error) {
                    container.innerHTML = `<div class="loading" style="color: #ef4444;">Telemetry unavailable: ${idx.error}</div>`;
                    return;
                }

                const latestDate = (idx && idx.latest_date) ? idx.latest_date : (health && health.latest_date) ? health.latest_date : '-';
                const computedIndex = (idx && idx.computed) ? idx.computed : (health && health.computed_index && health.computed_index.computed) ? health.computed_index.computed : [];
                const noBundleMessage = (idx && idx.message) ? idx.message : (health && health.message) ? health.message : null;

                const lvsData = (lvs && lvs.data) ? lvs.data : {};
                const spData = (sp && sp.data) ? sp.data : {};
                const swrData = (swr && swr.data) ? swr.data : {};
                const blockedCfData = (blockedCf && blockedCf.data) ? blockedCf.data : {};
                const exitQualData = (exitQual && exitQual.data) ? exitQual.data : {};
                const sigProfData = (sigProf && sigProf.data) ? sigProf.data : {};
                const gateProfData = (gateProf && gateProf.data) ? gateProf.data : {};
                const intelRecData = (intelRec && intelRec.data) ? intelRec.data : {};
                const paperIntelData = paperIntel && !paperIntel.error ? paperIntel : {};

                const parity = (health && health.parity_health) ? health.parity_health : {};
                const repl = (health && health.replacement_health) ? health.replacement_health : {};
                const mtl = (health && health.master_trade_log) ? health.master_trade_log : {};

                const fmtUsd = (x) => {
                    const v = Number(x || 0);
                    return (v >= 0 ? '$' : '-$') + Math.abs(v).toFixed(2);
                };
                const fmtPct = (x) => {
                    const v = Number(x || 0);
                    return (v * 100).toFixed(1) + '%';
                };
                const fmtAge = (ageSec) => {
                    if (ageSec === null || ageSec === undefined) return 'N/A';
                    const a = Number(ageSec);
                    if (!isFinite(a)) return 'N/A';
                    if (a < 60) return `${Math.floor(a)}s`;
                    if (a < 3600) return `${Math.floor(a / 60)}m`;
                    return `${Math.floor(a / 3600)}h`;
                };

                const windows = (lvsData && lvsData.windows) ? lvsData.windows : {};
                const w24 = windows['24h'] || {};
                const w48 = windows['48h'] || {};
                const w5d = windows['5d'] || {};

                const delta24 = (w24.delta && w24.delta.pnl_usd !== undefined) ? Number(w24.delta.pnl_usd) : 0;
                const delta48 = (w48.delta && w48.delta.pnl_usd !== undefined) ? Number(w48.delta.pnl_usd) : 0;
                const delta5d = (w5d.delta && w5d.delta.pnl_usd !== undefined) ? Number(w5d.delta.pnl_usd) : 0;
                const live24 = (w24.pnl_usd !== undefined) ? Number(w24.pnl_usd) : null;
                const live48 = (w48.pnl_usd !== undefined) ? Number(w48.pnl_usd) : null;
                const live5d = (w5d.pnl_usd !== undefined) ? Number(w5d.pnl_usd) : null;
                const hasLive = live24 !== null || live48 !== null || live5d !== null;
                const comparisonAvailable = !!(lvsData && lvsData.comparison_available === true);

                const cls = (v) => v > 0 ? 'positive' : (v < 0 ? 'negative' : '');

                let html = `
                    <div class="positions-table" style="margin-bottom: 20px;">
                        <h2 style="margin-bottom: 15px;">📦 Telemetry (latest bundle: ${latestDate})</h2>
                        ${noBundleMessage ? `<div style="padding: 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; margin-bottom: 12px; color: #92400e;">${noBundleMessage}</div>` : ''}
                        <div style="color:#666;">These panels read from telemetry/${latestDate}/computed/*.json (read-only).</div>
                    </div>

                    <div class="positions-table" style="margin-bottom: 20px;">
                        <h2 style="margin-bottom: 15px;">Live vs Shadow (PnL delta)</h2>
                        ${!comparisonAvailable && (lvsData && lvsData.note) ? `<div style="color:#64748b; font-size: 0.9em; margin-bottom: 10px;">${lvsData.note}</div>` : ''}
                        <div class="stats">
                            <div class="stat-card">
                                <div class="stat-label">24h Δ (shadow − live)</div>
                                <div class="stat-value ${cls(delta24)}">${fmtUsd(delta24)}</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-label">48h Δ (shadow − live)</div>
                                <div class="stat-value ${cls(delta48)}">${fmtUsd(delta48)}</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-label">5d Δ (shadow − live)</div>
                                <div class="stat-value ${cls(delta5d)}">${fmtUsd(delta5d)}</div>
                            </div>
                        </div>
                        ${hasLive ? `
                        <div style="margin-top: 15px;"><h3 style="margin-bottom: 10px;">Live PnL (from pnl_windows)</h3>
                        <div class="stats">
                            <div class="stat-card"><div class="stat-label">24h live</div><div class="stat-value ${cls(live24 || 0)}">${fmtUsd(live24 != null ? live24 : 0)}</div></div>
                            <div class="stat-card"><div class="stat-label">48h live</div><div class="stat-value ${cls(live48 || 0)}">${fmtUsd(live48 != null ? live48 : 0)}</div></div>
                            <div class="stat-card"><div class="stat-label">5d live</div><div class="stat-value ${cls(live5d || 0)}">${fmtUsd(live5d != null ? live5d : 0)}</div></div>
                        </div></div>
                        ` : ''}
                `;

                // Per-symbol table
                const rows = (lvsData && Array.isArray(lvsData.per_symbol)) ? lvsData.per_symbol : [];
                if (rows.length) {
                    const sorted = rows.slice().sort((a, b) => Math.abs(Number(b.delta_pnl_usd || 0)) - Math.abs(Number(a.delta_pnl_usd || 0)));
                    html += `<div class="positions-table" style="margin-top: 15px;"><h3 style="margin-bottom: 10px;">Per-symbol deltas</h3>`;
                    html += `<table><thead><tr>
                        <th>Symbol</th><th>Window</th><th>Live PnL</th><th>Shadow PnL</th><th>Delta</th><th>Live Trades</th><th>Shadow Trades</th>
                    </tr></thead><tbody>`;
                    for (const r of sorted.slice(0, 200)) {
                        const d = Number(r.delta_pnl_usd || 0);
                        html += `<tr>
                            <td class="symbol">${r.symbol || ''}</td>
                            <td>${r.window || ''}</td>
                            <td>${fmtUsd(r.live_pnl_usd)}</td>
                            <td>${fmtUsd(r.shadow_pnl_usd)}</td>
                            <td class="${cls(d)}"><strong>${fmtUsd(d)}</strong></td>
                            <td>${Number(r.live_trade_count || 0)}</td>
                            <td>${Number(r.shadow_trade_count || 0)}</td>
                        </tr>`;
                    }
                    html += `</tbody></table></div>`;
                } else {
                    html += `<div style="color:#666;margin-top:10px;">No per-symbol rows available.</div>`;
                }
                html += `</div>`;

                // Blocked Opportunity panel (read-only)
                const perReason = (blockedCfData && blockedCfData.per_blocked_reason) ? blockedCfData.per_blocked_reason : {};
                const topSymbolsCf = (blockedCfData && Array.isArray(blockedCfData.top_symbols_by_counterfactual_pnl_30m)) ? blockedCfData.top_symbols_by_counterfactual_pnl_30m : [];
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Blocked Opportunity</h2>
                    <div style="color:#666;">Blocked trade_intent counterfactuals (read-only; does not change behavior).</div>`;
                if (!Object.keys(perReason).length) {
                    html += `<div class="loading">No blocked counterfactuals summary available. Run blocked_counterfactuals_build_today.py.</div>`;
                } else {
                    html += `<table><thead><tr><th>Blocked reason</th><th>Count</th><th>Avg CF PnL (30m)</th><th>% would win (30m)</th></tr></thead><tbody>`;
                    for (const [reason, v] of Object.entries(perReason)) {
                        const avg = (v && v.avg_counterfactual_pnl_30m != null) ? v.avg_counterfactual_pnl_30m : null;
                        const pct = (v && v.pct_would_win_30m != null) ? v.pct_would_win_30m : null;
                        html += `<tr><td class="symbol">${reason}</td><td>${(v && v.count) != null ? v.count : ''}</td><td class="${cls(avg)}">${avg != null ? fmtUsd(avg) : 'N/A'}</td><td>${pct != null ? pct + '%' : 'N/A'}</td></tr>`;
                    }
                    html += `</tbody></table>`;
                    if (topSymbolsCf.length) {
                        html += `<h3 style="margin-top: 12px;">Top symbols by counterfactual PnL (30m)</h3><table><thead><tr><th>Symbol</th><th>Count</th><th>CF PnL sum (30m)</th></tr></thead><tbody>`;
                        for (const r of topSymbolsCf.slice(0, 15)) {
                            const pnl = Number(r.pnl_sum_30m || 0);
                            html += `<tr><td class="symbol">${r.symbol || ''}</td><td>${Number(r.count || 0)}</td><td class="${cls(pnl)}">${fmtUsd(pnl)}</td></tr>`;
                        }
                        html += `</tbody></table>`;
                    }
                }
                html += `</div>`;

                // Exit Quality panel
                const perExitReason = (exitQualData && exitQualData.per_exit_reason) ? exitQualData.per_exit_reason : {};
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Exit Quality</h2>
                    <div style="color:#666;">Exit reason performance and left-on-table (read-only).</div>`;
                if (!Object.keys(perExitReason).length) {
                    html += `<div class="loading">No exit quality summary available. Run exit_attribution_build_today.py.</div>`;
                } else {
                    html += `<table><thead><tr><th>Exit reason</th><th>Count</th><th>Avg PnL</th><th>Left on table (avg)</th><th>Avg time in trade (min)</th></tr></thead><tbody>`;
                    for (const [reason, v] of Object.entries(perExitReason)) {
                        const avgPnl = (v && v.avg_pnl != null) ? v.avg_pnl : null;
                        const left = (v && v.left_on_table_avg != null) ? v.left_on_table_avg : null;
                        const timeMin = (v && v.avg_time_in_trade_minutes != null) ? v.avg_time_in_trade_minutes : null;
                        html += `<tr><td class="symbol">${reason}</td><td>${(v && v.count) != null ? v.count : ''}</td><td class="${cls(avgPnl)}">${avgPnl != null ? fmtUsd(avgPnl) : 'N/A'}</td><td>${left != null ? fmtUsd(left) : 'N/A'}</td><td>${timeMin != null ? timeMin : 'N/A'}</td></tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                // Signal Profitability (per family; read-only)
                const sigProfSignals = (sigProfData && Array.isArray(sigProfData.signals)) ? sigProfData.signals : [];
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Signal Profitability</h2>
                    <div style="color:#666;">Per signal_family contribution (read-only; does not change weights).</div>`;
                if (!sigProfSignals.length) {
                    html += `<div class="loading">No signal profitability. Run build_intelligence_profitability_today.py.</div>`;
                } else {
                    html += `<table><thead><tr><th>Signal family</th><th>Count</th><th>Avg PnL/trade</th><th>Contribution %</th><th>Alignment</th><th>Action</th></tr></thead><tbody>`;
                    for (const r of sigProfSignals.slice(0, 30)) {
                        const pnl = Number(r.avg_pnl_per_trade || 0);
                        const align = Number(r.profitability_alignment_score || 0);
                        const alignCls = align > 0 ? 'positive' : (align < 0 ? 'negative' : '');
                        html += `<tr><td class="symbol">${r.signal_family || ''}</td><td>${Number(r.count || 0)}</td><td class="${cls(pnl)}">${fmtUsd(pnl)}</td><td>${Number(r.contribution_to_total_pnl_pct || 0).toFixed(1)}%</td><td class="${alignCls}">${align > 0 ? '+' : ''}${align}</td><td>${r.suggested_action || 'monitor_only'}</td></tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                // Gate Profitability (read-only) + profitability alignment
                const disp = (gateProfData && gateProfData.displacement) ? gateProfData.displacement : {};
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Gate Profitability</h2>
                    <div style="color:#666;">PnL of passed trades and counterfactual of blocked (read-only). Profitability alignment indicators.</div>`;
                if (!Object.keys(disp).length && !(gateProfData && gateProfData.directional_gate)) {
                    html += `<div class="loading">No gate profitability. Run build_intelligence_profitability_today.py.</div>`;
                } else {
                    const dispAlign = Number(disp.profitability_alignment_score || 0);
                    const dispCls = dispAlign > 0 ? 'positive' : (dispAlign < 0 ? 'negative' : '');
                    html += `<div class="stat-card"><div><strong>Displacement:</strong> allowed=${disp.allowed_count || 0}, blocked=${disp.blocked_count || 0}, counterfactual PnL (blocked 30m)=${fmtUsd(disp.counterfactual_pnl_blocked_30m)}</div>`;
                    html += `<div><strong>Alignment:</strong> <span class="${dispCls}">${dispAlign > 0 ? '+' : ''}${dispAlign}</span> &nbsp; <strong>Suggested:</strong> ${disp.suggested_action || 'monitor_only'}</div>`;
                    const dg = (gateProfData && gateProfData.directional_gate) ? gateProfData.directional_gate : {};
                    html += `<div><strong>Directional gate:</strong> events=${dg.events || 0}, blocked≈${dg.blocked_approx || 0}</div></div>`;
                }
                html += `</div>`;

                // Intelligence recommendations (display only; no auto-tuning) + profitability alignment
                const intelRecs = (intelRecData && Array.isArray(intelRecData.recommendations)) ? intelRecData.recommendations : [];
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Intelligence Recommendations</h2>
                    <div style="color:#666;">Suggested actions (display only; no weights or gates changed). Alignment: +1 support, -1 hurt, 0 neutral.</div>`;
                if (!intelRecs.length) {
                    html += `<div class="loading">No recommendations. Run build_intelligence_profitability_today.py.</div>`;
                } else {
                    html += `<table><thead><tr><th>Type</th><th>Entity</th><th>Status</th><th>Confidence</th><th>Alignment</th><th>Suggested action</th></tr></thead><tbody>`;
                    for (const r of intelRecs.slice(0, 30)) {
                        const align = Number(r.profitability_alignment_score || 0);
                        const alignCls = align > 0 ? 'positive' : (align < 0 ? 'negative' : '');
                        html += `<tr><td>${r.entity_type || ''}</td><td class="symbol">${r.entity || ''}</td><td>${r.status || ''}</td><td>${r.confidence || ''}</td><td class="${alignCls}">${align > 0 ? '+' : ''}${align}</td><td>${r.suggested_action || ''}</td></tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                // Paper Intelligence State (SRE / Intelligence)
                const dispOn = !!paperIntelData.displacement_relaxation_active;
                const scoreOn = !!paperIntelData.min_exec_score_active;
                const exitOn = !!paperIntelData.exit_tuning_active;
                const regimeOn = !!paperIntelData.regime_filter_active;
                const eff = paperIntelData.effective_params || {};
                const mode = paperIntelData.trading_mode || 'unknown';
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Paper Intelligence State</h2>
                    <div style="color:#666;">Paper-mode overrides (CONFIG-ONLY, reversible). Active only when TRADING_MODE=paper.</div>
                    <div class="stat-card" style="margin-top: 10px;">
                        <div><strong>Mode:</strong> ${mode}</div>
                        <div><strong>Displacement relaxation:</strong> ${dispOn ? 'ON' : 'OFF'} ${dispOn && eff.displacement_score_advantage != null ? ' (score_advantage=' + eff.displacement_score_advantage + ', max_pnl_pct=' + eff.displacement_max_pnl_pct + ')' : ''}</div>
                        <div><strong>Min exec score:</strong> ${scoreOn ? 'ON' : 'OFF'} ${scoreOn && eff.min_exec_score != null ? ' (' + eff.min_exec_score + ')' : ''}</div>
                        <div><strong>Exit tuning:</strong> ${exitOn ? 'ON' : 'OFF'} ${exitOn && (eff.time_exit_minutes != null || eff.trailing_stop_pct != null) ? ' (time_exit=' + (eff.time_exit_minutes || '') + ' min, trailing=' + (eff.trailing_stop_pct != null ? eff.trailing_stop_pct : '') + ')' : ''}</div>
                        <div><strong>Regime filter:</strong> ${regimeOn ? 'ON' : 'OFF'} ${regimeOn && eff.size_multiplier_neutral != null ? ' (size_mult_neutral=' + eff.size_multiplier_neutral + ')' : ''}</div>
                    </div>
                </div>`;

                // Signal performance
                const sigs = (spData && Array.isArray(spData.signals)) ? spData.signals : [];
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Signal Performance</h2>`;
                if (!sigs.length) {
                    html += `<div class="loading">No signal performance rows (no realized trades or no signal-family snapshots yet).</div>`;
                } else {
                    const sigSorted = sigs.slice().sort((a, b) => Number(b.expectancy_usd || 0) - Number(a.expectancy_usd || 0));
                    html += `<table><thead><tr>
                        <th>Signal</th><th>Win Rate</th><th>Expectancy (USD)</th><th>Trades</th><th>Contribution</th>
                    </tr></thead><tbody>`;
                    for (const r of sigSorted.slice(0, 200)) {
                        const exp = Number(r.expectancy_usd || 0);
                        html += `<tr>
                            <td class="symbol">${r.name || ''}</td>
                            <td>${fmtPct(r.win_rate || 0)}</td>
                            <td class="${cls(exp)}"><strong>${fmtUsd(exp)}</strong></td>
                            <td>${Number(r.trade_count || 0)}</td>
                            <td>${(Number(r.contribution_to_total_pnl || 0) * 100).toFixed(1)}%</td>
                        </tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                // Recommendations
                const swrRecs = (swrData && Array.isArray(swrData.recommendations)) ? swrData.recommendations : [];
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Signal Weight Recommendations (advisory)</h2>`;
                if (!swrRecs.length) {
                    html += `<div class="loading">No recommendations available.</div>`;
                } else {
                    html += `<table><thead><tr>
                        <th>Signal</th><th>Δ Weight</th><th>Confidence</th><th>Rationale</th>
                    </tr></thead><tbody>`;
                    for (const r of swrRecs.slice(0, 200)) {
                        const dw = Number(r.suggested_delta_weight || 0);
                        html += `<tr>
                            <td class="symbol">${r.signal || ''}</td>
                            <td class="${cls(dw)}"><strong>${dw.toFixed(3)}</strong></td>
                            <td>${r.confidence || ''}</td>
                            <td style="color:#555;">${r.rationale || ''}</td>
                        </tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                // Computed artifacts index + Telemetry health summary
                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Computed Artifacts</h2>
                    <div style="color:#666; margin-bottom: 10px; font-size: 0.9em;">Built by the <strong>daily telemetry extract</strong> (e.g. 20:30 UTC). Age = time since last run. &quot;Missing&quot; = not produced for this bundle (some come from shadow/parity scripts). Live trading data (orders, positions, signals) is separate and updates in real time.</div>`;
                if (!computedIndex || !computedIndex.length) {
                    html += `<div class="loading">No computed index available.</div>`;
                } else {
                    html += `<table><thead><tr>
                        <th>Artifact</th><th>Status</th><th>Age</th><th>Size</th>
                    </tr></thead><tbody>`;
                    for (const r of computedIndex) {
                        const st = r.status || 'unknown';
                        const c = st === 'healthy' ? 'positive' : (st === 'warning' ? 'warning' : (st === 'stale' || st === 'missing') ? 'negative' : '');
                        html += `<tr>
                            <td class="symbol">${r.name || ''}</td>
                            <td class="${c}"><strong>${st}</strong></td>
                            <td>${fmtAge(r.age_sec)}</td>
                            <td>${Number(r.bytes || 0)}</td>
                        </tr>`;
                    }
                    html += `</tbody></table>`;
                }
                html += `</div>`;

                html += `<div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">Telemetry Health</h2>
                    <div class="stat-card">
                        <div><strong>Parity available:</strong> ${(parity.parity_available === true) ? 'true' : (parity.parity_available === false ? 'false' : 'unknown')}</div>
                        <div><strong>Parity match_rate:</strong> ${parity.match_rate !== null && parity.match_rate !== undefined ? parity.match_rate : 'N/A'}</div>
                        <div><strong>Parity mean score delta:</strong> ${parity.mean_score_delta !== null && parity.mean_score_delta !== undefined ? parity.mean_score_delta : 'N/A'}</div>
                        <div><strong>Replacement rate:</strong> ${repl.replacement_rate !== null && repl.replacement_rate !== undefined ? repl.replacement_rate : 'N/A'}</div>
                        <div><strong>Replacement anomaly:</strong> ${(repl.replacement_anomaly_detected === true) ? 'true' : (repl.replacement_anomaly_detected === false ? 'false' : 'unknown')}</div>
                        <div><strong>Master trade log:</strong> ${mtl.exists ? 'present' : 'missing'} ${mtl.status ? '(' + mtl.status + ')' : ''}</div>
                    </div>
                </div>`;

                container.innerHTML = html;
            } catch (e) {
                var msg = (e && e.message) ? e.message : String(e);
                if (msg.indexOf('401') !== -1) msg = 'Login required (401). Refresh the page and log in again.';
                container.innerHTML = '<div class="loading" style="color:#ef4444;">' + msg + '</div>';
            }
        }
        
        function loadSignalReview() {
            const signalContent = document.getElementById('signal-review-content');
            
            fetch('/api/signal_history', { credentials: 'same-origin' })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    // Check if response is actually JSON
                    const contentType = response.headers.get('content-type');
                    if (!contentType || !contentType.includes('application/json')) {
                        return response.text().then(text => {
                            throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        signalContent.innerHTML = `<p class="loading" style="color: #ef4444;">Error: ${data.error}</p>`;
                        return;
                    }
                    
                    const signals = data.signals || [];
                    
                    if (signals.length === 0) {
                        signalContent.innerHTML = '<p class="no-positions">No signal history available</p>';
                        return;
                    }
                    
                    // Build table HTML
                    let html = '<table><thead><tr>';
                    html += '<th>Ticker</th>';
                    html += '<th>Direction</th>';
                    html += '<th>Raw Score</th>';
                    html += '<th>Whale Boost</th>';
                    html += '<th>Final Score</th>';
                    html += '<th>Sector</th>';
                    html += '<th>Persistence</th>';
                    html += '<th>Virtual P&L</th>';
                    html += '<th>ATR Mult</th>';
                    html += '<th>Momentum %</th>';
                    html += '<th>Momentum Req %</th>';
                    html += '<th>Decision</th>';
                    html += '</tr></thead><tbody>';
                    
                    signals.forEach(signal => {
                        const symbol = signal.symbol || 'N/A';
                        const direction = signal.direction || 'unknown';
                        const rawScore = (signal.raw_score !== undefined && signal.raw_score !== null) ? signal.raw_score.toFixed(2) : '0.00';
                        const whaleBoost = (signal.whale_boost !== undefined && signal.whale_boost !== null) ? signal.whale_boost.toFixed(2) : '0.00';
                        const finalScore = (signal.final_score !== undefined && signal.final_score !== null) ? signal.final_score.toFixed(2) : '0.00';
                        const sector = signal.sector || 'Unknown';
                        const persistenceCount = signal.persistence_count || 0;
                        const sectorTideCount = signal.sector_tide_count || 0;
                        const virtualPnl = (signal.virtual_pnl !== undefined && signal.virtual_pnl !== null) ? signal.virtual_pnl : null;
                        const shadowCreated = signal.shadow_created || false;
                        const atrMult = (signal.atr_multiplier !== undefined && signal.atr_multiplier !== null) ? signal.atr_multiplier.toFixed(2) : 'N/A';
                        const momentumPct = (signal.momentum_pct !== undefined && signal.momentum_pct !== null) ? signal.momentum_pct.toFixed(4) : '0.0000';
                        const momentumReqPct = (signal.momentum_required_pct !== undefined && signal.momentum_required_pct !== null) ? signal.momentum_required_pct.toFixed(4) : '0.0000';
                        const decision = signal.decision || 'Unknown';
                        
                        // Format sector with tide indicator
                        let sectorDisplay = sector;
                        if (sectorTideCount >= 3) {
                            sectorDisplay = `${sector} (${sectorTideCount})`;
                        }
                        
                        // Format persistence with indicator
                        let persistenceDisplay = persistenceCount.toString();
                        if (persistenceCount >= 5) {
                            persistenceDisplay = `<strong style="color: #10b981;">${persistenceCount} ⚡</strong>`;
                        }
                        
                        // Format Virtual P&L
                        let virtualPnlDisplay = 'N/A';
                        if (shadowCreated && virtualPnl !== null) {
                            const pnlValue = parseFloat(virtualPnl);
                            const pnlColor = pnlValue > 0 ? '#10b981' : pnlValue < 0 ? '#ef4444' : '#666';
                            const fontWeight = Math.abs(pnlValue) > 1 ? 'bold' : 'normal';
                            const pnlSign = pnlValue >= 0 ? '+' : '';
                            virtualPnlDisplay = '<span style="color: ' + pnlColor + '; font-weight: ' + fontWeight + '">' + pnlSign + pnlValue.toFixed(2) + '%</span>';
                        } else if (shadowCreated) {
                            virtualPnlDisplay = '<span style="color: #666;">Tracking...</span>';
                        }
                        
                        // Color code decision
                        let decisionClass = '';
                        let decisionStyle = '';
                        if (decision === 'Ordered') {
                            decisionClass = 'positive';
                            decisionStyle = 'color: #10b981; font-weight: bold;';
                        } else if (decision.startsWith('Blocked:')) {
                            decisionClass = 'warning';
                            decisionStyle = 'color: #f59e0b;';
                            // Check for specific rejection reasons
                            if (decision.includes('Sector_Tide_Missing')) {
                                decisionStyle = 'color: #f59e0b; font-style: italic;';
                            } else if (decision.includes('Persistence')) {
                                decisionStyle = 'color: #f59e0b;';
                            }
                        } else if (decision.startsWith('Rejected:')) {
                            decisionClass = 'negative';
                            decisionStyle = 'color: #ef4444;';
                        }
                        
                        html += '<tr>';
                        html += `<td class="symbol">${symbol}</td>`;
                        html += `<td><span class="side ${direction === 'bullish' ? 'long' : 'short'}">${direction}</span></td>`;
                        html += `<td>${rawScore}</td>`;
                        html += `<td>${whaleBoost !== '0.00' ? '+' + whaleBoost : whaleBoost}</td>`;
                        html += `<td>${finalScore}</td>`;
                        html += `<td>${sectorDisplay}</td>`;
                        html += `<td>${persistenceDisplay}</td>`;
                        html += `<td>${virtualPnlDisplay}</td>`;
                        html += `<td>${atrMult}</td>`;
                        html += `<td>${momentumPct}%</td>`;
                        html += `<td>${momentumReqPct}%</td>`;
                        html += `<td class="${decisionClass}" style="${decisionStyle}">${decision}</td>`;
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                    signalContent.innerHTML = html;
                })
                .catch(error => {
                    signalContent.innerHTML = `<p class="loading" style="color: #ef4444;">Error loading signal history: ${error.message}</p>`;
                });
        }
        
        function loadFailurePoints() {
            const fpContent = document.getElementById('failure_points-content');
            const scrollTop = fpContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            
            if (!fpContent.dataset.loaded) {
                fpContent.innerHTML = '<div class="loading">Loading Trading Readiness...</div>';
            }
            
            fetch('/api/failure_points', { credentials: 'same-origin' })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    fpContent.dataset.loaded = 'true';
                    renderFailurePoints(data, fpContent);
                    if (scrollTop > 0) {
                        requestAnimationFrame(() => {
                            fpContent.scrollTop = scrollTop;
                            window.scrollTo(0, scrollTop);
                        });
                    }
                })
                .catch(error => {
                    console.error('Failure Points error:', error);
                    fpContent.innerHTML = `<div class="loading" style="color: #ef4444;">Error loading Trading Readiness: ${error.message}</div>`;
                });
        }
        
        function loadWheelUniverseHealth() {
            const el = document.getElementById('wheel_universe-content');
            if (!el) return;
            el.innerHTML = '<div class="loading">Loading Wheel Universe Health...</div>';
            fetch('/api/wheel/universe_health', { credentials: 'same-origin' })
                .then(function(r) {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(function(d) {
                    if (!d) return;
                    let h = '';
                    if (d.message) {
                        h += '<div class="stat-card"><p>' + (d.message || '') + '</p><p>Run: <code>python scripts/generate_wheel_universe_health.py</code></p></div>';
                    } else {
                        h += '<div class="stat-card"><h3>Wheel Universe Health</h3><p><strong>Date:</strong> ' + (d.date || '—') + '</p><p><strong>Current universe:</strong> ' + (Array.isArray(d.current_universe) ? d.current_universe.join(', ') : '—') + '</p><p><strong>Selected candidates:</strong> ' + (Array.isArray(d.selected_candidates) ? d.selected_candidates.join(', ') : '—') + '</p></div>';
                        h += '<div class="stat-card"><h3>Sector distribution</h3><pre>' + JSON.stringify(d.sector_distribution || {}, null, 2) + '</pre></div>';
                        if (d.assignment_count != null) h += '<div class="stat-card"><p><strong>Assignments:</strong> ' + d.assignment_count + ' | <strong>Called away:</strong> ' + (d.call_away_count != null ? d.call_away_count : '—') + '</p></div>';
                        if (d.ai_recommendations && d.ai_recommendations.length) {
                            h += '<div class="stat-card"><h3>AI recommendations</h3><ul>';
                            for (let i = 0; i < d.ai_recommendations.length; i++) h += '<li>' + JSON.stringify(d.ai_recommendations[i]) + '</li>';
                            h += '</ul></div>';
                        }
                    }
                    el.innerHTML = h;
                    el.dataset.loaded = '1';
                })
                .catch(function(e) {
                    el.innerHTML = '<div class="loading" style="color:#ef4444;">Wheel Universe Health failed: ' + (e && e.message ? e.message : 'network') + '</div>';
                });
        }
        
        function loadStrategyComparison() {
            const el = document.getElementById('strategy_comparison-content');
            if (!el) return;
            el.innerHTML = '<div class="loading">Loading Strategy Comparison...</div>';
            fetch('/api/strategy/comparison', { credentials: 'same-origin' })
                .then(function(r) {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(function(d) {
                    if (!d) return;
                    const sc = d.strategy_comparison || {};
                    const rec = d.recommendation || 'WAIT';
                    const score = d.promotion_readiness_score;
                    const badgeClr = rec === 'PROMOTE' ? '#10b981' : (rec === 'DO NOT PROMOTE' ? '#ef4444' : '#f59e0b');
                    const badge = '<span style="padding:4px 12px;border-radius:6px;font-weight:bold;background:' + badgeClr + ';color:#fff">' + rec + '</span>';
                    let h = '<div class="stat-card"><h3>Strategy Comparison</h3><p><strong>Date:</strong> ' + (d.date || '—') + '</p><p><strong>Promotion Readiness Score:</strong> ' + (score != null ? score : '—') + ' / 100</p><p><strong>Recommendation:</strong> ' + badge + '</p></div>';
                    const fmt = function(v) { const n = Number(v); return (v == null || v === undefined) ? '0.00' : (isFinite(n) ? n.toFixed(2) : '0.00'); };
                    h += '<div class="stat-card"><h3>Equity vs Wheel</h3><p>Equity Realized: $' + (sc.equity_realized_pnl != null ? fmt(sc.equity_realized_pnl) : '—') + ' | Wheel Realized: $' + (sc.wheel_realized_pnl != null ? fmt(sc.wheel_realized_pnl) : '—') + '</p><p>Equity Unrealized: $' + (sc.equity_unrealized_pnl != null ? fmt(sc.equity_unrealized_pnl) : '—') + ' | Wheel Unrealized: $' + (sc.wheel_unrealized_pnl != null ? fmt(sc.wheel_unrealized_pnl) : '—') + '</p><p>Equity Drawdown: ' + (sc.equity_drawdown != null ? sc.equity_drawdown : '—') + ' | Wheel Drawdown: ' + (sc.wheel_drawdown != null ? sc.wheel_drawdown : '—') + '</p><p>Equity Sharpe: ' + (sc.equity_sharpe_proxy != null ? sc.equity_sharpe_proxy : '—') + ' | Wheel Sharpe: ' + (sc.wheel_sharpe_proxy != null ? sc.wheel_sharpe_proxy : '—') + '</p><p>Wheel Yield: ' + (sc.wheel_yield_per_period != null ? sc.wheel_yield_per_period : '—') + ' | Capital Eff Equity: ' + (sc.capital_efficiency_equity != null ? sc.capital_efficiency_equity : '—') + ' | Wheel: ' + (sc.capital_efficiency_wheel != null ? sc.capital_efficiency_wheel : '—') + '</p></div>';
                    if (d.weekly_report && d.weekly_report.reasoning) h += '<div class="stat-card"><h3>Weekly Reasoning</h3><pre>' + JSON.stringify(d.weekly_report.reasoning, null, 2) + '</pre></div>';
                    if (d.historical_comparison && d.historical_comparison.length) {
                        h += '<div class="stat-card"><h3>Historical (last 30 days)</h3><table><thead><tr><th>Date</th><th>Equity</th><th>Wheel</th><th>Score</th></tr></thead><tbody>';
                        for (let i = 0; i < Math.min(d.historical_comparison.length, 15); i++) {
                            const x = d.historical_comparison[i];
                            h += '<tr><td>' + (x.date || '—') + '</td><td>$' + (x.equity_realized != null ? fmt(x.equity_realized) : '—') + '</td><td>$' + (x.wheel_realized != null ? fmt(x.wheel_realized) : '—') + '</td><td>' + (x.promotion_score != null ? x.promotion_score : '—') + '</td></tr>';
                        }
                        h += '</tbody></table></div>';
                    }
                    el.innerHTML = h;
                    el.dataset.loaded = '1';
                })
                .catch(function(e) {
                    el.innerHTML = '<div class="loading" style="color:#ef4444;">Strategy Comparison failed: ' + (e && e.message ? e.message : 'network') + '</div>';
                });
        }
        
        function loadWheelAnalytics() {
            const el = document.getElementById('wheel_strategy-content');
            if (!el) return;
            el.innerHTML = '<div class="loading">Loading Wheel Strategy...</div>';
            fetch('/api/stockbot/wheel_analytics', { credentials: 'same-origin' })
                .then(function(r) {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(function(d) {
                    if (!d) return;
                    const totalTrades = d.total_trades != null ? d.total_trades : 0;
                    const premium = d.premium_collected != null ? Number(d.premium_collected).toFixed(2) : '0.00';
                    const allZero = totalTrades === 0 && parseFloat(premium) === 0 && (d.assignment_count || 0) === 0 && (d.call_away_count || 0) === 0;
                    let h = '<div class="stat-card"><h3>Wheel Strategy Analytics</h3><p><strong>Total wheel trades:</strong> ' + totalTrades + '</p><p><strong>Premium collected:</strong> $' + premium + '</p><p><strong>Assignment count:</strong> ' + (d.assignment_count != null ? d.assignment_count : '0') + ' | <strong>Call-away count:</strong> ' + (d.call_away_count != null ? d.call_away_count : '0') + '</p><p><strong>Assignment rate:</strong> ' + (d.assignment_rate_pct != null ? d.assignment_rate_pct.toFixed(1) : '0.0') + '% | <strong>Call-away rate:</strong> ' + (d.call_away_rate_pct != null ? d.call_away_rate_pct.toFixed(1) : '0.0') + '%</p><p><strong>Expectancy per trade (USD):</strong> ' + (d.expectancy_per_trade_usd != null ? '$' + Number(d.expectancy_per_trade_usd).toFixed(2) : '—') + '</p><p><strong>Realized P&L sum:</strong> $' + (d.realized_pnl_sum != null ? Number(d.realized_pnl_sum).toFixed(2) : '0.00') + '</p></div>';
                    if (allZero) h += '<div class="stat-card" style="border-left:4px solid #64748b;"><p style="color:#64748b;font-size:0.9em;"><strong>Data sources:</strong> logs/attribution.jsonl, logs/telemetry.jsonl (strategy_id=wheel), reports/*_stock-bot_wheel.json, state/wheel_state.json. Run <code>python3 scripts/generate_daily_strategy_reports.py</code> to refresh reports. Wheel data appears when the wheel strategy executes trades.</p></div>';
                    if (d.error) h += '<div class="stat-card" style="border-color:#f59e0b;"><p>' + (d.error || '') + '</p></div>';
                    el.innerHTML = h;
                    el.dataset.loaded = '1';
                })
                .catch(function(e) {
                    el.innerHTML = '<div class="loading" style="color:#ef4444;">Wheel analytics failed: ' + (e && e.message ? e.message : 'network') + '</div>';
                });
        }
        
        function renderFailurePoints(data, container) {
            const readiness = data.readiness || 'UNKNOWN';
            const color = data.color || 'gray';
            const criticalCount = data.critical_count || 0;
            const warningCount = data.warning_count || 0;
            const totalChecked = data.total_checked || 0;
            const failurePoints = data.failure_points || {};
            
            let html = `
                <div class="stat-card" style="border: 3px solid ${color === 'green' ? '#10b981' : color === 'yellow' ? '#f59e0b' : '#ef4444'}; margin-bottom: 20px;">
                    <h2 style="color: ${color === 'green' ? '#10b981' : color === 'yellow' ? '#f59e0b' : '#ef4444'}; margin-bottom: 15px;">
                        Trading Readiness: ${readiness}
                    </h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <div class="stat-label">Status</div>
                            <div class="stat-value" style="color: ${color === 'green' ? '#10b981' : color === 'yellow' ? '#f59e0b' : '#ef4444'};">${readiness}</div>
                        </div>
                        <div>
                            <div class="stat-label">Critical Issues</div>
                            <div class="stat-value" style="color: ${criticalCount > 0 ? '#ef4444' : '#10b981'};">${criticalCount}</div>
                        </div>
                        <div>
                            <div class="stat-label">Warnings</div>
                            <div class="stat-value" style="color: ${warningCount > 0 ? '#f59e0b' : '#10b981'};">${warningCount}</div>
                        </div>
                        <div>
                            <div class="stat-label">Total Checked</div>
                            <div class="stat-value">${totalChecked}</div>
                        </div>
                    </div>
                    ${data.critical_fps && data.critical_fps.length > 0 ? `
                        <div style="margin-top: 15px; padding: 10px; background: #fee2e2; border-radius: 5px;">
                            <strong style="color: #ef4444;">Critical Failure Points:</strong> ${data.critical_fps.join(', ')}
                        </div>
                    ` : ''}
                    ${data.warning_fps && data.warning_fps.length > 0 ? `
                        <div style="margin-top: 10px; padding: 10px; background: #fef3c7; border-radius: 5px;">
                            <strong style="color: #f59e0b;">Warning Failure Points:</strong> ${data.warning_fps.join(', ')}
                        </div>
                    ` : ''}
                    ${data.blockers && data.blockers.blocked ? `
                        <div style="margin-top: 15px; padding: 15px; background: #fef2f2; border: 2px solid #ef4444; border-radius: 5px;">
                            <h3 style="color: #ef4444; margin-top: 0;">🚫 Why Am I Not Trading?</h3>
                            <p style="font-weight: bold; margin-bottom: 10px;">${data.blockers.summary}</p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                ${data.blockers.blockers.map(b => `
                                    <li style="margin: 5px 0;">
                                        <strong>${b.type.replace('_', ' ').toUpperCase()}:</strong> ${b.reason}
                                        ${b.requires_manual_action ? ' <span style="color: #ef4444;">(Requires manual action)</span>' : ''}
                                        ${b.can_self_heal ? ' <span style="color: #10b981;">(Self-healing attempted)</span>' : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📋 Failure Point Details</h2>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Category</th>
                                    <th>Status</th>
                                    <th>Last Check</th>
                                    <th>Error</th>
                                    <th>Self-Healing</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            Object.entries(failurePoints).forEach(([fp_id, fp]) => {
                const statusColor = fp.status === 'OK' ? '#10b981' : fp.status === 'WARN' ? '#f59e0b' : '#ef4444';
                const lastCheck = fp.last_check ? new Date(fp.last_check * 1000).toLocaleString() : 'N/A';
                const selfHealing = fp.self_healing_attempted ? (fp.self_healing_success ? '✓ Success' : '✗ Failed') : '-';
                
                html += `
                    <tr>
                        <td><strong>${fp_id}</strong></td>
                        <td>${fp.name}</td>
                        <td>${fp.category}</td>
                        <td style="color: ${statusColor}; font-weight: bold;">${fp.status}</td>
                        <td>${lastCheck}</td>
                        <td style="color: ${fp.last_error ? '#ef4444' : '#666'}; max-width: 300px; word-wrap: break-word;">${fp.last_error || '-'}</td>
                        <td>${selfHealing}</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        function loadXAIAuditor() {
            const xaiContent = document.getElementById('xai-content');
            const scrollTop = xaiContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            
            if (!xaiContent.dataset.loaded) {
                xaiContent.innerHTML = '<div class="loading">Loading Natural Language Auditor...</div>';
            }
            
            fetch('/api/xai/auditor', { credentials: 'same-origin' })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    xaiContent.dataset.loaded = 'true';
                    renderXAIAuditor(data, xaiContent);
                    if (scrollTop > 0) {
                        requestAnimationFrame(() => {
                            xaiContent.scrollTop = scrollTop;
                            window.scrollTo(0, scrollTop);
                        });
                    }
                })
                .catch(error => {
                    console.error('XAI Auditor error:', error);
                    xaiContent.innerHTML = `
                        <div class="loading" style="color: #ef4444; padding: 20px;">
                            <h3>⚠️ Error loading Natural Language Auditor</h3>
                            <p>${error.message}</p>
                            <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                                The system will retry automatically. If this persists, check the dashboard logs.
                            </p>
                            <button onclick="loadXAIAuditor()" style="margin-top: 10px; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                🔄 Retry
                            </button>
                        </div>`;
                });
        }
        
        function renderXAIAuditor(data, container) {
            // Handle errors gracefully
            if (data.error) {
                container.innerHTML = `
                    <div class="loading" style="color: #ef4444; padding: 20px;">
                        <h3>⚠️ Error loading data</h3>
                        <p>${data.error}</p>
                        <button onclick="loadXAIAuditor()" style="margin-top: 10px; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            🔄 Retry
                        </button>
                    </div>`;
                return;
            }
            
            // Show status if partial
            let statusHtml = '';
            if (data.status === 'partial' && data.errors) {
                statusHtml = `<div style="background: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                    <strong>⚠️ Partial data loaded:</strong> Some data may be missing. Errors: ${data.errors.join(', ')}
                </div>`;
            }
            
            let html = `
                <div class="stat-card" style="margin-bottom: 20px; border: 3px solid #667eea;">
                    <h2 style="color: #667eea; margin-bottom: 15px;">🧠 Natural Language Auditor</h2>
                    <p style="color: #666; margin-bottom: 15px;">Explainable AI (XAI) logs showing natural language "Why" sentences for every trade and weight adjustment.</p>
                    ${statusHtml}
                    <div style="margin-bottom: 10px;">
                        <span style="color: #666;">Trades: ${data.trade_count || 0} | Weights: ${data.weight_count || 0}</span>
                    </div>
                    <button onclick="exportXAI()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: 600;">
                        📥 Export All Logs
                    </button>
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📊 Trade Explanations</h2>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Symbol</th>
                                    <th>Type</th>
                                    <th>Why (Natural Language)</th>
                                    <th>Regime</th>
                                    <th>P&L %</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            // Filter out TEST symbols
            const trades = (data.trades || []).filter(t => {
                const symbol = String(t.symbol || '').toUpperCase();
                return symbol && !symbol.includes('TEST');
            });
            
            if (trades.length === 0) {
                html += '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No trade explanations yet</td></tr>';
            } else {
                trades.forEach(trade => {
                    const timeStr = trade.timestamp ? new Date(trade.timestamp).toLocaleString() : 'N/A';
                    const pnl = trade.pnl_pct || (trade.type === 'trade_exit' ? trade.pnl_pct : null);
                    const pnlClass = pnl !== null && pnl !== undefined && pnl >= 0 ? 'positive' : 'negative';
                    html += `
                        <tr>
                            <td>${timeStr}</td>
                            <td class="symbol">${trade.symbol}</td>
                            <td>${trade.type || 'N/A'}</td>
                            <td style="max-width: 400px; word-wrap: break-word;">${trade.why || 'N/A'}</td>
                            <td>${trade.regime && trade.regime !== 'unknown' && trade.regime !== '' ? trade.regime.toUpperCase() : 'NEUTRAL'}</td>
                            <td class="${pnlClass}">${pnl !== null && pnl !== undefined ? (pnl >= 0 ? '+' : '') + pnl.toFixed(2) + '%' : 'N/A'}</td>
                        </tr>
                    `;
                });
            }
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">⚙️ Weight Adjustment Explanations</h2>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Component</th>
                                    <th>Old Weight</th>
                                    <th>New Weight</th>
                                    <th>Why (Natural Language)</th>
                                    <th>Samples</th>
                                    <th>Win Rate</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            // Filter out TEST symbols from weights (if any)
            const weights = (data.weights || []).filter(w => {
                const component = String(w.component || '').toUpperCase();
                return component && !component.includes('TEST');
            });
            
            if (weights.length === 0) {
                html += '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #666;">No weight adjustments yet</td></tr>';
            } else {
                weights.forEach(weight => {
                    const timeStr = weight.timestamp ? new Date(weight.timestamp).toLocaleString() : 'N/A';
                    html += `
                        <tr>
                            <td>${timeStr}</td>
                            <td class="symbol">${weight.component}</td>
                            <td>${weight.old_weight !== undefined ? weight.old_weight.toFixed(2) : 'N/A'}</td>
                            <td>${weight.new_weight !== undefined ? weight.new_weight.toFixed(2) : 'N/A'}</td>
                            <td style="max-width: 400px; word-wrap: break-word;">${weight.why || 'N/A'}</td>
                            <td>${weight.sample_count || 0}</td>
                            <td>${weight.win_rate !== undefined ? (weight.win_rate * 100).toFixed(1) + '%' : 'N/A'}</td>
                        </tr>
                    `;
                });
            }
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        function exportXAI() {
            fetch('/api/xai/export', { credentials: 'same-origin' })
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `xai_logs_${new Date().toISOString().split('T')[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    alert('Export failed: ' + error.message);
                });
        }
        
        function loadExecutiveSummary(timeframe) {
            timeframe = timeframe || document.getElementById('executive-timeframe')?.value || '24h';
            const executiveContent = document.getElementById('executive-content');
            const scrollTop = executiveContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            if (!executiveContent.dataset.loaded) {
                executiveContent.innerHTML = '<div class="loading">Loading executive summary...</div>';
            }
            fetch('/api/executive_summary?timeframe=' + encodeURIComponent(timeframe), { credentials: 'same-origin' })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    return response.json();
                })
                .then(data => {
                    executiveContent.dataset.loaded = 'true';
                    renderExecutiveSummary(data, executiveContent, timeframe);
                    if (scrollTop > 0) {
                        requestAnimationFrame(() => {
                            executiveContent.scrollTop = scrollTop;
                            window.scrollTo(0, scrollTop);
                        });
                    }
                })
                .catch(error => {
                    console.error('Executive summary error:', error);
                    executiveContent.innerHTML = `<div class="loading" style="color: #ef4444;">Error loading executive summary: ${error.message}<br/>Check browser console for details.</div>`;
                });
        }
        
        function renderExecutiveSummary(data, container, currentTimeframe) {
            const pm = data.pnl_metrics || {};
            const tf = pm.timeframe || currentTimeframe || '24h';
            const pnl = pm.pnl != null ? pm.pnl : (pm.pnl_2d != null ? pm.pnl_2d : (pm.pnl_5d != null ? pm.pnl_5d : 0));
            const tradesCount = pm.trades != null ? pm.trades : (pm.trades_2d != null ? pm.trades_2d : (pm.trades_5d != null ? pm.trades_5d : 0));
            const winRate = pm.win_rate != null ? pm.win_rate : (pm.win_rate_2d != null ? pm.win_rate_2d : (pm.win_rate_5d != null ? pm.win_rate_5d : 0));
            const pnlClass = pnl >= 0 ? 'positive' : 'negative';
            const timeframeOptions = ['24h', '48h', '7d', '2d', '5d'];
            let html = `
                <div class="stat-card" style="margin-bottom: 20px; border: 3px solid #667eea;">
                    <h2 style="color: #667eea; margin-bottom: 15px;">📊 Performance Metrics</h2>
                    <div style="margin-bottom: 12px;">
                        <label style="margin-right: 8px;">Timeframe:</label>
                        <select id="executive-timeframe" onchange="loadExecutiveSummary(this.value)" style="padding: 6px 10px; border-radius: 6px; border: 1px solid #ccc;">
                            ${timeframeOptions.map(t => `<option value="${t}" ${t === tf ? 'selected' : ''}>${t}</option>`).join('')}
                        </select>
                        <span style="margin-left: 8px; color: #666; font-size: 0.9em;">Data from canonical logs (MEMORY_BANK 5.5)</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <div class="stat-label">Total Trades (all time)</div>
                            <div class="stat-value">${data.total_trades || 0}</div>
                        </div>
                        <div>
                            <div class="stat-label">P&L (${tf})</div>
                            <div class="stat-value ${pnlClass}">${formatCurrency(pnl)}</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                                ${tradesCount} trades, ${winRate}% win rate
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">📋 Recent Trades</h2>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Symbol</th>
                                    <th>P&L (USD)</th>
                                    <th>P&L (%)</th>
                                    <th>Hold Time</th>
                                    <th>Entry Score</th>
                                    <th>Close Reason</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            const trades = data.trades || [];
            if (trades.length === 0) {
                html += '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #666;">No trades found</td></tr>';
            } else {
                trades.forEach(trade => {
                    const pnlClass = trade.pnl_usd >= 0 ? 'positive' : 'negative';
                    const timeStr = trade.timestamp ? new Date(trade.timestamp).toLocaleString() : 'N/A';
                    // Defensive: Handle missing entry_score (should never happen, but safe)
                    const entryScore = trade.entry_score !== undefined && trade.entry_score !== null ? trade.entry_score.toFixed(2) : '0.00';
                    html += `
                        <tr>
                            <td>${timeStr}</td>
                            <td class="symbol">${trade.symbol}</td>
                            <td class="${pnlClass}">${formatCurrency(trade.pnl_usd)}</td>
                            <td class="${pnlClass}">${trade.pnl_pct >= 0 ? '+' : ''}${trade.pnl_pct.toFixed(2)}%</td>
                            <td>${Math.round(trade.hold_minutes)}m</td>
                            <td>${entryScore}</td>
                            <td>${trade.close_reason}</td>
                        </tr>
                    `;
                });
            }
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">🎯 Signal Performance Analysis</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="color: #10b981; margin-bottom: 10px;">Top Performing Signals</h3>
            `;
            
            const topSignals = (data.signal_analysis && data.signal_analysis.top_signals) || {};
            if (Object.keys(topSignals).length === 0) {
                html += '<p style="color: #666;">No signal data available</p>';
            } else {
                Object.entries(topSignals).forEach(([signal, info]) => {
                    html += `
                        <div class="stat-card" style="margin-bottom: 10px; padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>${signal}</strong>
                                <span class="${info.avg_pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(info.total_pnl)}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                                Avg: ${formatCurrency(info.avg_pnl)} | Win Rate: ${info.win_rate}% | Trades: ${info.count}
                            </div>
                        </div>
                    `;
                });
            }
            
            html += `
                        </div>
                        <div>
                            <h3 style="color: #ef4444; margin-bottom: 10px;">Underperforming Signals</h3>
            `;
            
            const bottomSignals = (data.signal_analysis && data.signal_analysis.bottom_signals) || {};
            if (Object.keys(bottomSignals).length === 0) {
                html += '<p style="color: #666;">No signal data available</p>';
            } else {
                Object.entries(bottomSignals).forEach(([signal, info]) => {
                    html += `
                        <div class="stat-card" style="margin-bottom: 10px; padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>${signal}</strong>
                                <span class="${info.avg_pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(info.total_pnl)}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                                Avg: ${formatCurrency(info.avg_pnl)} | Win Rate: ${info.win_rate}% | Trades: ${info.count}
                            </div>
                        </div>
                    `;
                });
            }
            
            html += `
                        </div>
                    </div>
                </div>
                
                <div class="positions-table" style="margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">🧠 Learning Analysis</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="color: #667eea; margin-bottom: 10px;">Weight Adjustments</h3>
            `;
            
            const weightAdjustments = (data.learning_insights && data.learning_insights.weight_adjustments) || {};
            if (Object.keys(weightAdjustments).length === 0) {
                html += '<p style="color: #666;">No weight adjustments yet</p>';
            } else {
                Object.entries(weightAdjustments).forEach(([component, adj]) => {
                    const mult = adj.current_multiplier;
                    const direction = mult > 1.0 ? '↑' : mult < 1.0 ? '↓' : '→';
                    const color = mult > 1.0 ? '#10b981' : mult < 1.0 ? '#ef4444' : '#666';
                    html += `
                        <div class="stat-card" style="margin-bottom: 10px; padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>${component}</strong>
                                <span style="color: ${color}; font-weight: bold;">${direction} ${mult.toFixed(2)}x</span>
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                                ${adj.sample_count} samples, ${adj.win_rate}% win rate
                            </div>
                        </div>
                    `;
                });
            }
            
            html += `
                        </div>
                        <div>
                            <h3 style="color: #667eea; margin-bottom: 10px;">Counterfactual Insights</h3>
            `;
            
            const counterfactual = (data.learning_insights && data.learning_insights.counterfactual_insights) || {};
            if (counterfactual.missed_opportunities !== undefined) {
                html += `
                    <div class="stat-card" style="margin-bottom: 10px; padding: 15px;">
                        <div><strong>Missed Opportunities:</strong> ${counterfactual.missed_opportunities}</div>
                        <div style="margin-top: 5px;"><strong>Avoided Losses:</strong> ${counterfactual.avoided_losses || 0}</div>
                        <div style="margin-top: 5px;"><strong>Theoretical P&L:</strong> ${formatCurrency(counterfactual.theoretical_pnl || 0)}</div>
                    </div>
                `;
            } else {
                html += '<p style="color: #666;">No counterfactual data available</p>';
            }
            
            html += `
                        </div>
                    </div>
                </div>
                
                <div class="positions-table">
                    <h2 style="margin-bottom: 15px;">📝 Executive Summary</h2>
                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-family: 'Courier New', monospace; line-height: 1.6;">
                        ${data.written_summary || 'No summary available'}
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
        }
        
        function formatPercent(value) {
            return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
        }
        
        function formatTimeAgo(seconds) {
            if (!seconds) return 'N/A';
            if (seconds < 60) return Math.floor(seconds) + 's';
            if (seconds < 3600) return Math.floor(seconds / 60) + 'm';
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return hours + 'h ' + minutes + 'm';
        }
        
        function updateDashboard() {
            // Only update if positions tab is active
            const positionsTab = document.getElementById('positions-tab');
            if (!positionsTab || !positionsTab.classList.contains('active')) {
                return;
            }
            
            // Save scroll position before update
            const positionsContent = document.getElementById('positions-content');
            const scrollTop = positionsContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            
            // Timeout so slow/blocked positions load doesn't freeze the UI or block tab switching
            let controller = null;
            let timeoutId = null;
            if (typeof AbortController !== 'undefined') {
                controller = new AbortController();
                timeoutId = setTimeout(function() { controller.abort(); }, 15000);
            }
            const opts = {
                cache: 'no-store',
                credentials: 'same-origin',
                headers: { 'Cache-Control': 'no-cache' }
            };
            if (controller && controller.signal) opts.signal = controller.signal;
            
            fetch('/api/positions', opts)
                .then(function(response) {
                    if (timeoutId) clearTimeout(timeoutId);
                    if (!response.ok) {
                        var msg = response.status === 401
                            ? 'Not logged in (401). Refresh the page and log in again.'
                            : 'Server error (' + response.status + '). Try another tab or refresh.';
                        var el = document.getElementById('positions-content');
                        if (el) el.innerHTML = '<p class="no-positions">' + msg + '</p>';
                        return Promise.reject(new Error(msg));
                    }
                    return response.text().then(function(text) {
                        try { return JSON.parse(text); } catch (e) { throw new Error('Invalid JSON'); }
                    });
                })
                .then(function(data) {
                    if (!data || typeof data !== 'object') {
                        var el = document.getElementById('positions-content');
                        if (el) el.innerHTML = '<p class="no-positions">Invalid response. Try another tab or refresh.</p>';
                        return;
                    }
                    var lastUpdate = document.getElementById('last-update');
                    if (lastUpdate) lastUpdate.textContent = new Date().toLocaleTimeString();
                    
                    if (data.error) {
                        var posContent = document.getElementById('positions-content');
                        if (posContent) posContent.innerHTML = '<p class="no-positions">Error: ' + (data.error || 'Unknown') + '</p>';
                        return;
                    }
                    
                    var positions = Array.isArray(data.positions) ? data.positions : [];
                    var totalVal = document.getElementById('total-positions');
                    if (totalVal) totalVal.textContent = positions.length;
                    var totalValueEl = document.getElementById('total-value');
                    if (totalValueEl) totalValueEl.textContent = formatCurrency(data.total_value || 0);
                    
                    var pnl = data.unrealized_pnl || 0;
                    var pnlEl = document.getElementById('unrealized-pnl');
                    if (pnlEl) { pnlEl.textContent = formatCurrency(pnl); pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'positive' : 'negative'); }
                    
                    var dayPnl = data.day_pnl || 0;
                    var dayPnlEl = document.getElementById('day-pnl');
                    if (dayPnlEl) { dayPnlEl.textContent = formatCurrency(dayPnl); dayPnlEl.className = 'stat-value ' + (dayPnl >= 0 ? 'positive' : 'negative'); }
                    
                    var missedAlpha = data.missed_alpha_usd || 0;
                    var missedAlphaEl = document.getElementById('missed-alpha');
                    if (missedAlphaEl) {
                        missedAlphaEl.textContent = formatCurrency(missedAlpha);
                        missedAlphaEl.className = 'stat-value ' + (missedAlpha > 0 ? 'negative' : (missedAlpha < 0 ? 'positive' : ''));
                        missedAlphaEl.style.color = missedAlpha > 0 ? '#ef4444' : (missedAlpha < 0 ? '#10b981' : '');
                    }
                    
                    if (positions.length === 0) {
                        var posContent0 = document.getElementById('positions-content');
                        if (posContent0) posContent0.innerHTML = '<p class="no-positions">No open positions</p>';
                        return;
                    }
                    
                    var container = document.getElementById('positions-content');
                    if (!container) return;
                    var existingTable = container.querySelector('table');
                    var existingRows = existingTable ? existingTable.querySelectorAll('tbody tr').length : 0;
                    var needsFullRebuild = !existingTable || existingRows !== positions.length;
                    
                    if (needsFullRebuild) {
                        var html = '<table><thead><tr>';
                        html += '<th>Symbol</th><th>Side</th><th>Qty</th><th>Entry</th>';
                        html += '<th>Current</th><th>Value</th><th>P&L</th><th>P&L %</th><th>Entry Score</th><th>Current Score</th></tr></thead><tbody>';
                        
                        positions.forEach(function(pos) {
                            const pnlClass = pos.unrealized_pnl >= 0 ? 'positive' : 'negative';
                            const entryScore = pos.entry_score !== undefined && pos.entry_score !== null ? pos.entry_score.toFixed(2) : '0.00';
                            const currentScore = pos.current_score !== undefined && pos.current_score !== null ? pos.current_score.toFixed(2) : '0.00';
                            const scoreClass = pos.entry_score > 0 ? '' : 'warning';
                            
                            // Calculate signal decay for visual indicator
                            let currentScoreClass = '';
                            let currentScoreStyle = '';
                            if (pos.entry_score > 0 && pos.current_score !== undefined && pos.current_score !== null) {
                                const decayRatio = pos.current_score / pos.entry_score;
                                if (decayRatio < 0.6) {
                                    currentScoreClass = 'warning';
                                    currentScoreStyle = 'color: #ef4444; font-weight: bold;';
                                } else if (decayRatio < 0.8) {
                                    currentScoreClass = 'warning';
                                    currentScoreStyle = 'color: #f59e0b;';
                                }
                            }
                            
                            html += '<tr data-symbol="' + pos.symbol + '">';
                            html += '<td class="symbol">' + pos.symbol + '</td>';
                            html += '<td><span class="side ' + pos.side + '">' + pos.side.toUpperCase() + '</span></td>';
                            html += '<td>' + pos.qty + '</td>';
                            html += '<td>' + formatCurrency(pos.avg_entry_price) + '</td>';
                            html += '<td>' + formatCurrency(pos.current_price) + '</td>';
                            html += '<td>' + formatCurrency(pos.market_value) + '</td>';
                            html += '<td class="' + pnlClass + '">' + formatCurrency(pos.unrealized_pnl) + '</td>';
                            html += '<td class="' + pnlClass + '">' + formatPercent(pos.unrealized_pnl_pct) + '</td>';
                            html += '<td class="' + scoreClass + '" style="' + (pos.entry_score === 0 ? 'color: #ef4444; font-weight: bold;' : '') + '">' + entryScore + '</td>';
                            html += '<td class="' + currentScoreClass + '" style="' + currentScoreStyle + '">' + currentScore + '</td>';
                            html += '</tr>';
                        });
                        
                        html += '</tbody></table>';
                        container.innerHTML = html;
                    } else {
                        var tbody = existingTable ? existingTable.querySelector('tbody') : null;
                        if (tbody) positions.forEach(function(pos, index) {
                            const row = tbody.children[index];
                            if (!row) return;
                            
                            const pnlClass = pos.unrealized_pnl >= 0 ? 'positive' : 'negative';
                            const cells = row.querySelectorAll('td');
                            
                            // Only update cells that changed (skip symbol, side as they don't change)
                            if (cells.length >= 10) {
                                cells[2].textContent = pos.qty;
                                cells[3].textContent = formatCurrency(pos.avg_entry_price);
                                cells[4].textContent = formatCurrency(pos.current_price);
                                cells[5].textContent = formatCurrency(pos.market_value);
                                cells[6].textContent = formatCurrency(pos.unrealized_pnl);
                                cells[6].className = pnlClass;
                                cells[7].textContent = formatPercent(pos.unrealized_pnl_pct);
                                cells[7].className = pnlClass;
                                const entryScore = pos.entry_score !== undefined && pos.entry_score !== null ? pos.entry_score.toFixed(2) : '0.00';
                                cells[8].textContent = entryScore;
                                if (pos.entry_score === 0) {
                                    cells[8].style.color = '#ef4444';
                                    cells[8].style.fontWeight = 'bold';
                                } else {
                                    cells[8].style.color = '';
                                    cells[8].style.fontWeight = '';
                                }
                                // Update current score
                                const currentScore = pos.current_score !== undefined && pos.current_score !== null ? pos.current_score.toFixed(2) : '0.00';
                                cells[9].textContent = currentScore;
                                // Color code based on signal decay
                                if (pos.entry_score > 0 && pos.current_score !== undefined && pos.current_score !== null) {
                                    const decayRatio = pos.current_score / pos.entry_score;
                                    if (decayRatio < 0.6) {
                                        cells[9].style.color = '#ef4444';
                                        cells[9].style.fontWeight = 'bold';
                                    } else if (decayRatio < 0.8) {
                                        cells[9].style.color = '#f59e0b';
                                        cells[9].style.fontWeight = '';
                                    } else {
                                        cells[9].style.color = '';
                                        cells[9].style.fontWeight = '';
                                    }
                                } else {
                                    cells[9].style.color = '';
                                    cells[9].style.fontWeight = '';
                                }
                            }
                        });
                    }
                    
                    if (scrollTop > 0 && positionsContent) {
                        requestAnimationFrame(function() {
                            positionsContent.scrollTop = scrollTop;
                            window.scrollTo(0, scrollTop);
                        });
                    }
                })
                .catch(function(error) {
                    if (timeoutId) clearTimeout(timeoutId);
                    console.error('Error fetching positions:', error);
                    var content = document.getElementById('positions-content');
                    if (content) {
                        var msg = error.name === 'AbortError'
                            ? 'Positions load timed out. You can switch tabs.'
                            : ('Positions load failed: ' + (error.message || 'network error'));
                        content.innerHTML = '<p class="no-positions">' + msg + '</p>';
                    }
                });
            
            // Fetch health status for Last Order and Doctor (credentials so auth is sent)
            Promise.all([
                fetch('/api/health_status', { credentials: 'same-origin' }).catch(() => null),
                fetch('http://localhost:8081/api/cockpit').catch(() => null),
                fetch('http://localhost:8081/health').catch(() => null)
            ]).then(([healthStatusRes, cockpitRes, healthRes]) => {
                // Try health_status endpoint first (most accurate)
                if (healthStatusRes && healthStatusRes.ok) {
                    healthStatusRes.json().then(data => {
                        // Last Order
                        const lastOrder = data.last_order || {};
                        const lastOrderAgeSec = lastOrder.age_sec;
                        const lastOrderEl = document.getElementById('last-order');
                        if (lastOrderAgeSec !== null && lastOrderAgeSec !== undefined) {
                            lastOrderEl.textContent = formatTimeAgo(lastOrderAgeSec);
                            // Color coding: < 1h = green, 1-3h = yellow, > 3h = red
                            if (lastOrderAgeSec < 3600) {
                                lastOrderEl.className = 'stat-value healthy';
                            } else if (lastOrderAgeSec < 10800) {
                                lastOrderEl.className = 'stat-value warning';
                            } else {
                                lastOrderEl.className = 'stat-value critical';
                            }
                        } else {
                            lastOrderEl.textContent = 'N/A';
                            lastOrderEl.className = 'stat-value';
                        }
                        
                        // Doctor
                        const doctor = data.doctor || {};
                        const doctorAgeSec = doctor.age_sec;
                        const doctorEl = document.getElementById('doctor');
                        if (doctorAgeSec !== null && doctorAgeSec !== undefined) {
                            doctorEl.textContent = formatTimeAgo(doctorAgeSec);
                            // Color coding: < 5m = green, 5-30m = yellow, > 30m = red
                            if (doctorAgeSec < 300) {
                                doctorEl.className = 'stat-value healthy';
                            } else if (doctorAgeSec < 1800) {
                                doctorEl.className = 'stat-value warning';
                            } else {
                                doctorEl.className = 'stat-value critical';
                            }
                        } else {
                            doctorEl.textContent = 'N/A';
                            doctorEl.className = 'stat-value';
                        }
                    });
                } else if (cockpitRes && cockpitRes.ok && healthRes && healthRes.ok) {
                    // Fallback to separate endpoints
                    cockpitRes.json().then(cockpitData => {
                        const lastOrder = cockpitData.last_order || {};
                        const lastOrderAgeSec = lastOrder.age_sec;
                        const lastOrderEl = document.getElementById('last-order');
                        if (lastOrderAgeSec !== null && lastOrderAgeSec !== undefined) {
                            lastOrderEl.textContent = formatTimeAgo(lastOrderAgeSec);
                            if (lastOrderAgeSec < 3600) {
                                lastOrderEl.className = 'stat-value healthy';
                            } else if (lastOrderAgeSec < 10800) {
                                lastOrderEl.className = 'stat-value warning';
                            } else {
                                lastOrderEl.className = 'stat-value critical';
                            }
                        }
                    });
                    
                    healthRes.json().then(healthData => {
                        const heartbeatAge = healthData.last_heartbeat_age_sec;
                        const doctorEl = document.getElementById('doctor');
                        if (heartbeatAge !== null && heartbeatAge !== undefined) {
                            doctorEl.textContent = formatTimeAgo(heartbeatAge);
                            if (heartbeatAge < 300) {
                                doctorEl.className = 'stat-value healthy';
                            } else if (heartbeatAge < 1800) {
                                doctorEl.className = 'stat-value warning';
                            } else {
                                doctorEl.className = 'stat-value critical';
                            }
                        }
                    });
                }
            }).catch(error => {
                console.error('Error fetching health status:', error);
            });
        }
        
        // Fetch version badge once on page load (no polling); timeout so we never hang
        function loadVersionBadge() {
            var badge = document.getElementById('version-badge');
            if (!badge) return;
            var ac = null;
            var tid = null;
            if (typeof AbortController !== 'undefined') {
                ac = new AbortController();
                tid = setTimeout(function() { ac.abort(); }, 10000);
            }
            var opts = { credentials: 'same-origin' };
            if (ac && ac.signal) opts.signal = ac.signal;
            fetch('/api/version', opts)
                .then(function(response) {
                    if (tid) clearTimeout(tid);
                    if (!response.ok) {
                        badge.textContent = 'Dashboard v??? (' + response.status + ')';
                        badge.className = 'version-badge mismatch';
                        badge.title = 'HTTP ' + response.status + ' – refresh and log in again';
                        response.text().catch(function() {});
                        return Promise.reject(new Error('HTTP ' + response.status));
                    }
                    return response.json();
                })
                .then(function(data) {
                    if (!badge) return;
                    if (!data) {
                        badge.textContent = 'Dashboard v???';
                        badge.className = 'version-badge mismatch';
                        badge.title = 'Version unavailable';
                        return;
                    }
                    var shortSha = (data.git_commit_short || (data.git_commit || '').substring(0, 7) || '???');
                    badge.textContent = 'Dashboard v' + shortSha;
                    if (data.matches_expected === true) {
                        badge.className = 'version-badge ok';
                    } else if (data.matches_expected === false) {
                        badge.className = 'version-badge mismatch';
                    } else {
                        badge.className = 'version-badge unknown';
                    }
                    var lines = [
                        'Full SHA: ' + (data.git_commit || 'unknown'),
                        'Process start: ' + (data.process_start_time_utc || 'unknown'),
                        'Build time: ' + (data.build_time_utc || 'unknown'),
                    ];
                    if (data.matches_expected === true) lines.push('Status: OK (matches expected)');
                    else if (data.matches_expected === false) lines.push('Status: MISMATCH (process drift)');
                    badge.title = lines.join('\\n');
                })
                .catch(function(err) {
                    if (tid) clearTimeout(tid);
                    var b = document.getElementById('version-badge');
                    if (b) {
                        b.textContent = 'Dashboard v???';
                        b.className = 'version-badge mismatch';
                        b.title = (err && err.name === 'AbortError') ? 'Version fetch timed out (10s)' : ('Version fetch failed: ' + (err && err.message ? err.message : 'network error'));
                    }
                });
        }
        try { document.body.setAttribute('data-dashboard-js', 'ok'); } catch (e) {}
        setTimeout(function() {
            try { loadVersionBadge(); } catch (e) {
                var b = document.getElementById('version-badge');
                if (b) { b.textContent = 'Dashboard v???'; b.title = 'JS error: ' + (e.message || e); }
            }
            try { updateDashboard(); } catch (e) {
                var pc = document.getElementById('positions-content');
                if (pc) pc.innerHTML = '<p class="no-positions">Startup error: ' + (e.message || e) + '. Check console (F12).</p>';
            }
            try { updateLastSignalTimestamp(); } catch (e) {}
        }, 0);
        setTimeout(function() {
            var vb = document.getElementById('version-badge');
            if (vb && vb.textContent === 'Dashboard v...') {
                var d = document.getElementById('dashboard-diagnostic');
                if (d) d.style.display = 'block';
            }
        }, 12000);
        setInterval(function() { try { updateDashboard(); } catch (e) {} }, 60000);
        setInterval(function() { try { updateLastSignalTimestamp(); } catch (e) {} }, 30000);
    </script>
</body>
</html>
"""

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

@app.route("/api/ping", methods=["GET"])
def api_ping():
    """Lightweight connectivity check; returns immediately (no heavy deps)."""
    return jsonify({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route("/health")
def health():
    """Health check endpoint - checks actual system health"""
    try:
        # Get real health status from SRE monitoring
        from sre_monitoring import get_sre_health
        sre_health = get_sre_health()
        overall_health = sre_health.get("overall_health", "unknown")
        
        # Check if bot process is running
        import subprocess
        bot_running = False
        try:
            result = subprocess.run(
                ["pgrep", "-f", "python.*main.py"],
                capture_output=True,
                timeout=2
            )
            bot_running = result.returncode == 0
        except:
            pass
        
        return jsonify({
            "status": "healthy" if overall_health == "healthy" and bot_running else "degraded",
            "overall_health": overall_health,
            "bot_running": bot_running,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies_loaded": _registry_loaded,
            "alpaca_connected": _alpaca_api is not None,
            "sre_health": {
                "market_open": sre_health.get("market_open", False),
                "last_order": sre_health.get("last_order", {}),
            }
        })
    except Exception as e:
        # Fallback if SRE monitoring fails
        return jsonify({
            "status": "unknown",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies_loaded": _registry_loaded,
            "alpaca_connected": _alpaca_api is not None
        }), 500


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
        }
    positions = _alpaca_api.list_positions()
    account = _alpaca_api.get_account()

    # CRITICAL FIX: Load entry scores from position metadata
    metadata = {}
    try:
        from config.registry import StateFiles, read_json
        metadata_path = StateFiles.POSITION_METADATA
        if metadata_path.exists():
            metadata = read_json(metadata_path, default={})
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load position metadata: {e}", flush=True)

    # Load UW cache for current score calculation (same way as main.py)
    uw_cache = {}
    current_regime = "mixed"
    try:
        from config.registry import CacheFiles, read_json
        import json as json_module
        cache_file = CacheFiles.UW_FLOW_CACHE
        if cache_file.exists():
            uw_cache = read_json(cache_file, default={})
        try:
            from config.registry import StateFiles
            for regime_file in [getattr(StateFiles, "REGIME_DETECTOR_STATE", None), StateFiles.REGIME_DETECTOR]:
                if not regime_file:
                    continue
                if regime_file.exists():
                    regime_data = json_module.loads(regime_file.read_text())
                    if isinstance(regime_data, dict):
                        current_regime = regime_data.get("current_regime") or regime_data.get("regime") or "mixed"
                        break
        except Exception:
            pass
    except Exception as e:
        print(f"[Dashboard] Warning: Failed to load UW cache for current scores: {e}", flush=True)

    pos_list = []
    for p in positions:
        symbol = p.symbol
        entry_score = metadata.get(symbol, {}).get("entry_score", 0.0) if metadata else 0.0
        current_score = 0.0
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
                    composite = uw_v2.compute_composite_score_v3(symbol, enriched_live, current_regime)
                    if composite:
                        current_score = composite.get("score", 0.0)
        except Exception as e:
            print(f"[Dashboard] Warning: Failed to compute current score for {symbol}: {e}", flush=True)
        pos_list.append({
            "symbol": symbol,
            "side": "long" if float(p.qty) > 0 else "short",
            "qty": abs(float(p.qty)),
            "avg_entry_price": float(p.avg_entry_price),
            "current_price": float(p.current_price),
            "market_value": abs(float(p.market_value)),
            "unrealized_pnl": float(p.unrealized_pl),
            "unrealized_pnl_pct": float(p.unrealized_plpc) * 100,
            "entry_score": float(entry_score),
            "current_score": float(current_score),
        })

    missed_alpha_usd = 0.0
    try:
        from shadow_tracker import get_shadow_tracker
        from signal_history_storage import get_signal_history
        signal_history = get_signal_history(limit=500)
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
        
    return {
        "positions": pos_list,
        "total_value": float(account.portfolio_value),
        "unrealized_pnl": sum(p["unrealized_pnl"] for p in pos_list),
        "day_pnl": float(account.equity) - float(account.last_equity),
        "missed_alpha_usd": round(missed_alpha_usd, 2),
    }


@app.route("/api/positions")
def api_positions():
    """Positions endpoint with 8s timeout so dashboard never blocks other tabs."""
    import concurrent.futures
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_api_positions_impl)
            result = future.result(timeout=8)
        return jsonify(result)
    except concurrent.futures.TimeoutError:
        return jsonify({
            "positions": [],
            "total_value": 0,
            "unrealized_pnl": 0,
            "day_pnl": 0,
            "missed_alpha_usd": 0,
            "error": "Request timed out (8s). You can switch tabs.",
        })
    except Exception as e:
        return jsonify({
            "positions": [],
            "total_value": 0,
            "unrealized_pnl": 0,
            "day_pnl": 0,
            "missed_alpha_usd": 0,
            "error": str(e),
        })


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

def _load_stock_closed_trades(max_days=90, max_attribution_lines=10000, max_telemetry_lines=500):
    """
    Load closed stock trades from attribution.jsonl, exit_attribution.jsonl (v2 equity exits),
    and wheel events from telemetry.jsonl.
    Returns list of records with strategy_id and wheel fields (nullable for equity).
    Canonical field names per MEMORY_BANK / wheel_strategy: strategy_id, phase, option_type,
    strike, expiry, dte, delta_at_entry, premium, assigned, called_away.
    Data sources (per MEMORY_BANK 5.5, 7.12): logs/attribution.jsonl, logs/exit_attribution.jsonl,
    logs/telemetry.jsonl. Paths resolved via _DASHBOARD_ROOT for cwd-independence.
    """
    from pathlib import Path
    from datetime import datetime, timezone, timedelta
    try:
        from config.registry import LogFiles
        attr_path = (_DASHBOARD_ROOT / LogFiles.ATTRIBUTION).resolve()
        exit_attr_path = (_DASHBOARD_ROOT / LogFiles.EXIT_ATTRIBUTION).resolve()
        telem_path = (_DASHBOARD_ROOT / LogFiles.TELEMETRY).resolve()
    except ImportError:
        attr_path = (_DASHBOARD_ROOT / "logs" / "attribution.jsonl").resolve()
        exit_attr_path = (_DASHBOARD_ROOT / "logs" / "exit_attribution.jsonl").resolve()
        telem_path = (_DASHBOARD_ROOT / "logs" / "telemetry.jsonl").resolve()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_days)).isoformat()[:10]
    out = []
    seen_keys = set()  # (symbol, ts_precision) for deduplication
    # 1) Attribution: closed trades (strategy_id injected by engine; wheel fields from context if present)
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
                row = {
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "timestamp": ts_str,
                    "pnl_usd": round(pnl_usd, 2),
                    "close_reason": close_reason,
                    "wheel_phase": context.get("phase"),
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
                row = {
                    "strategy_id": "equity",
                    "symbol": symbol,
                    "timestamp": ts_str,
                    "pnl_usd": round(pnl_usd, 2) if pnl_usd is not None else None,
                    "close_reason": rec.get("exit_reason") or "",
                    "wheel_phase": None,
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
    # 3) Telemetry: wheel events (strategy_id=wheel) as trade-like rows with full wheel fields
    if telem_path.exists():
        lines = telem_path.read_text(encoding="utf-8", errors="replace").splitlines()
        lines = lines[-max_telemetry_lines:] if len(lines) > max_telemetry_lines else lines
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("strategy_id") != "wheel":
                continue
            ts_str = rec.get("timestamp") or rec.get("ts") or ""
            if ts_str and str(ts_str)[:10] < cutoff:
                continue
            symbol = str(rec.get("symbol", "")).upper()
            if not symbol:
                continue
            row = {
                "strategy_id": "wheel",
                "symbol": symbol,
                "timestamp": ts_str,
                "pnl_usd": None,
                "close_reason": None,
                "wheel_phase": rec.get("phase"),
                "option_type": rec.get("option_type"),
                "strike": rec.get("strike"),
                "expiry": rec.get("expiry"),
                "dte": rec.get("dte"),
                "delta_at_entry": rec.get("delta_at_entry"),
                "premium": rec.get("premium"),
                "assigned": rec.get("assigned"),
                "called_away": rec.get("called_away"),
            }
            out.append(row)
    out.sort(key=lambda x: (x.get("timestamp") or ""), reverse=True)
    return out[:500]


@app.route("/api/stockbot/closed_trades", methods=["GET"])
def api_stockbot_closed_trades():
    """
    Stock-bot closed trades: strategy_id, wheel fields (wheel_phase, option_type, strike, expiry, dte,
    delta_at_entry, premium, assigned, called_away). Additive; nullable for legacy/equity rows.
    """
    try:
        trades = _load_stock_closed_trades()
        return jsonify({"closed_trades": trades, "count": len(trades)}), 200
    except Exception as e:
        return jsonify({"closed_trades": [], "count": 0, "error": str(e)}), 200


def _aggregate_wheel_reports(reports_dir: Path, max_days: int = 90) -> dict:
    """Aggregate wheel metrics from reports/YYYY-MM-DD_stock-bot_wheel.json (fallback when attribution/telemetry empty)."""
    out = {"premium_collected": 0.0, "assignment_count": 0, "call_away_count": 0, "realized_pnl": 0.0, "trade_count_estimate": 0}
    try:
        from datetime import timedelta
        end_d = datetime.now(timezone.utc).date()
        for i in range(max_days):
            dk = (end_d - timedelta(days=i)).strftime("%Y-%m-%d")
            p = reports_dir / f"{dk}_stock-bot_wheel.json"
            if not p.exists():
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            if data.get("strategy_id") != "wheel":
                continue
            out["premium_collected"] += float(data.get("premium_collected") or 0)
            out["assignment_count"] += int(data.get("assignment_count") or 0)
            out["call_away_count"] += int(data.get("call_away_count") or 0)
            out["realized_pnl"] += float(data.get("realized_pnl") or 0)
            if data.get("positions_by_symbol"):
                out["trade_count_estimate"] += len(data.get("positions_by_symbol", {}))
    except Exception:
        pass
    return out


@app.route("/api/stockbot/wheel_analytics", methods=["GET"])
def api_stockbot_wheel_analytics():
    """
    Wheel-only analytics: premium collected, assignment rate, call-away rate, expectancy, duration, MAE/MFE if available.
    Data sources (in order): logs/attribution.jsonl + logs/telemetry.jsonl (strategy_id=wheel);
    fallback: reports/*_stock-bot_wheel.json; supplement: state/wheel_state.json for assignments.
    """
    try:
        trades = _load_stock_closed_trades()
        wheel = [t for t in trades if t.get("strategy_id") == "wheel"]
        total = len(wheel)
        premium_sum = sum(float(t.get("premium") or 0) for t in wheel)
        assigned_count = sum(1 for t in wheel if t.get("assigned") is True)
        called_away_count = sum(1 for t in wheel if t.get("called_away") is True)
        pnl_sum = sum(float(t.get("pnl_usd") or 0) for t in wheel if t.get("pnl_usd") is not None)

        # Fallback: aggregate from reports + wheel_state when no wheel trades in attribution/telemetry
        if total == 0:
            reports_dir = Path(_DASHBOARD_ROOT) / "reports"
            if reports_dir.exists():
                agg = _aggregate_wheel_reports(reports_dir, max_days=90)
                premium_sum = agg["premium_collected"]
                assigned_count = agg["assignment_count"]
                called_away_count = agg["call_away_count"]
                pnl_sum = agg["realized_pnl"]
                total = max(1, agg["trade_count_estimate"]) if (premium_sum or assigned_count or called_away_count or pnl_sum) else 0

            # Supplement from state/wheel_state.json (assignments/call-aways)
            try:
                wheel_state_path = Path(_DASHBOARD_ROOT) / "state" / "wheel_state.json"
                if wheel_state_path.exists():
                    ws = json.loads(wheel_state_path.read_text(encoding="utf-8", errors="replace"))
                    csp_history = ws.get("csp_history") or []
                    cc_history = ws.get("cc_history") or []
                    for h in csp_history if isinstance(csp_history, list) else []:
                        if isinstance(h, dict) and h.get("assigned") is True:
                            assigned_count += 1
                    for h in cc_history if isinstance(cc_history, list) else []:
                        if isinstance(h, dict) and h.get("called_away") is True:
                            called_away_count += 1
                    if assigned_count or called_away_count:
                        total = max(total, assigned_count + called_away_count)
            except Exception:
                pass

        assignment_rate = (assigned_count / total * 100) if total else 0
        call_away_rate = (called_away_count / total * 100) if total else 0
        expectancy = (pnl_sum / total) if total else None
        return jsonify({
            "strategy_id": "wheel",
            "total_trades": total,
            "premium_collected": round(premium_sum, 2),
            "assignment_count": assigned_count,
            "call_away_count": called_away_count,
            "assignment_rate_pct": round(assignment_rate, 2),
            "call_away_rate_pct": round(call_away_rate, 2),
            "expectancy_per_trade_usd": round(expectancy, 2) if expectancy is not None else None,
            "realized_pnl_sum": round(pnl_sum, 2),
        }), 200
    except Exception as e:
        return jsonify({"strategy_id": "wheel", "total_trades": 0, "error": str(e)}), 200


@app.route("/api/closed_positions")
def api_closed_positions():
    try:
        from pathlib import Path
        import csv
        from io import StringIO
        
        closed = []
        state_file = (_DASHBOARD_ROOT / "state" / "closed_positions.json").resolve()
        if state_file.exists():
            data = json.loads(state_file.read_text())
            closed = data if isinstance(data, list) else data.get("positions", [])
        
        return jsonify({"closed_positions": closed[-50:]})
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
        limit = 500
        try:
            limit = min(500, max(1, int(request.args.get("limit", "500"))))
        except Exception:
            limit = 500
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
  <h2>System Events (last 500)</h2>
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
                    metrics = get_sre_metrics()
                    health_data["sre_metrics"] = metrics
                    
                    diag = SREDiagnostics()
                    recent_fixes = diag.get_recent_fixes(limit=5)
                    health_data["recent_rca_fixes"] = recent_fixes
                except:
                    pass
                return jsonify(health_data), 200
        except:
            pass
        
        # Fallback to local sre_monitoring
        try:
            from sre_monitoring import get_sre_health
            health = get_sre_health()
            
            # Add supervisor health (Risk #9 - Aggregated Health)
            supervisor_health = _get_supervisor_health()
            if supervisor_health:
                health["supervisor_health"] = supervisor_health
                # Override overall_health with supervisor's aggregated health if available
                if supervisor_health.get("overall_status"):
                    supervisor_status = supervisor_health["overall_status"].lower()
                    if supervisor_status == "failed":
                        health["overall_health"] = "critical"
                    elif supervisor_status == "degraded":
                        health["overall_health"] = "degraded"
                    # OK maps to existing health
            
            # Enhance with SRE metrics and RCA fixes
            try:
                from sre_diagnostics import get_sre_metrics, SREDiagnostics
                metrics = get_sre_metrics()
                health["sre_metrics"] = metrics
                
                diag = SREDiagnostics()
                recent_fixes = diag.get_recent_fixes(limit=5)
                health["recent_rca_fixes"] = recent_fixes
                
                # V3.0: Add Signal Funnel metrics and Stagnation Watchdog
                try:
                    funnel_data = _calculate_signal_funnel()
                    health["signal_funnel"] = funnel_data
                except:
                    pass
                
                try:
                    stagnation_data = _calculate_stagnation_watchdog()
                    health["stagnation_watchdog"] = stagnation_data
                except Exception as e:
                    print(f"[Dashboard] Warning: Failed to calculate stagnation watchdog: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    # Still add a default structure so frontend doesn't break
                    health["stagnation_watchdog"] = {
                        "status": "OK",
                        "alerts_received": 0,
                        "trades_executed": 0,
                        "stagnation_detected": False
                    }
            except Exception as outer_e:
                print(f"[Dashboard] Warning: Error in SRE health enhancement: {outer_e}", flush=True)
                # Ensure stagnation watchdog is added even if other enhancements fail
                try:
                    stagnation_data = _calculate_stagnation_watchdog()
                    health["stagnation_watchdog"] = stagnation_data
                except:
                    health["stagnation_watchdog"] = {
                        "status": "OK",
                        "alerts_received": 0,
                        "trades_executed": 0,
                        "stagnation_detected": False
                    }
            
            _merge_health_subsystem(health)
            return jsonify(health), 200
        except Exception as e:
            return jsonify({"error": f"Failed to load SRE health: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            return Response("No logs available", mimetype='text/plain'), 404
        
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
        return Response(f"Export failed: {str(e)}", mimetype='text/plain'), 500

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
        
        # Market status
        from datetime import datetime, timezone, timedelta
        now_utc = datetime.now(timezone.utc)
        now_et = now_utc.astimezone(timezone(timedelta(hours=-5)))
        market_open = (now_et.weekday() < 5 and 
                      now_et.replace(hour=9, minute=30) <= now_et <= now_et.replace(hour=16, minute=0))
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
    """Get the last 50 signal processing events for Signal Review tab"""
    try:
        from signal_history_storage import get_signal_history, get_last_signal_timestamp
        from shadow_tracker import get_shadow_tracker
        
        signals = get_signal_history(limit=50)
        last_signal_ts = get_last_signal_timestamp()
        
        # Update virtual P&L from shadow positions
        try:
            shadow_tracker = get_shadow_tracker()
            for signal in signals:
                symbol = signal.get("symbol")
                if symbol and signal.get("shadow_created"):
                    shadow_pos = shadow_tracker.get_position(symbol)
                    if shadow_pos:
                        # Update virtual P&L with current max profit
                        signal["virtual_pnl"] = shadow_pos.max_profit_pct
                        if shadow_pos.closed:
                            signal["shadow_closed"] = True
                            signal["shadow_close_reason"] = shadow_pos.close_reason
        except Exception:
            pass  # Fail silently if shadow tracker unavailable
        
        return jsonify({
            "signals": signals,
            "last_signal_timestamp": last_signal_ts,
            "count": len(signals)
        }), 200
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


@app.route("/api/wheel/universe_health", methods=["GET"])
def api_wheel_universe_health():
    """
    Wheel Universe Health: universe, candidates, sector distribution, metrics, outcomes.
    Primary: state/wheel_universe_health.json. Fallback: derive from config/universe_wheel.yaml
    and state/daily_universe_v2.json when primary file does not exist.
    """
    try:
        from config.registry import Directories, StateFiles, read_json
        path = (_DASHBOARD_ROOT / Directories.STATE / "wheel_universe_health.json").resolve()
        if path.exists():
            data = read_json(path, default={})
            return jsonify(data), 200
        # Fallback: derive from existing config/state (no external script required)
        today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        current_universe = []
        selected_candidates = []
        sector_distribution = {}
        # From config/universe_wheel.yaml
        wheel_config = (_DASHBOARD_ROOT / "config" / "universe_wheel.yaml").resolve()
        if wheel_config.exists():
            try:
                import yaml
                cfg = yaml.safe_load(wheel_config.read_text(encoding="utf-8", errors="replace")) or {}
                tickers = cfg.get("universe", {}).get("tickers", [])
                current_universe = list(tickers) if isinstance(tickers, list) else []
                selected_candidates = current_universe[:10]
            except Exception:
                # Fallback: parse simple YAML list (e.g. "  - SPY")
                try:
                    import re
                    text = wheel_config.read_text(encoding="utf-8", errors="replace")
                    current_universe = re.findall(r"^\s*-\s+([A-Z0-9]+)\s*$", text, re.MULTILINE)
                    selected_candidates = current_universe[:10]
                except Exception:
                    pass
        # From state/daily_universe_v2.json (may have symbols + sector info)
        du_path = (_DASHBOARD_ROOT / Directories.STATE / "daily_universe_v2.json").resolve()
        if du_path.exists():
            try:
                du = read_json(du_path, default={})
                symbols = du.get("symbols", [])
                if symbols and not current_universe:
                    current_universe = [s.get("symbol") for s in symbols[:20] if isinstance(s, dict) and s.get("symbol")]
                sectors = {}
                for s in symbols if isinstance(symbols, list) else []:
                    if isinstance(s, dict):
                        sec = (s.get("context") or {}).get("sector", "UNKNOWN")
                        sectors[sec] = sectors.get(sec, 0) + 1
                sector_distribution = sectors
            except Exception:
                pass
        return jsonify({
            "date": today,
            "message": "Derived from config/universe_wheel.yaml and state/daily_universe_v2.json (state/wheel_universe_health.json not present)",
            "current_universe": current_universe or [],
            "selected_candidates": selected_candidates or current_universe[:10],
            "sector_distribution": sector_distribution,
            "liquidity_metrics": {},
            "iv_metrics": {},
            "spread_metrics": {},
            "assignment_outcomes_by_ticker": {},
            "yield_by_ticker": {},
            "ai_recommendations": None,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/strategy/comparison", methods=["GET"])
def api_strategy_comparison():
    """
    Strategy comparison: equity vs wheel metrics, promotion readiness, recommendation, last 30 days.
    Data source: reports/{date}_stock-bot_combined.json (from scripts/generate_daily_strategy_reports.py).
    """
    try:
        from pathlib import Path
        from datetime import datetime, timedelta
        reports_dir = (_DASHBOARD_ROOT / "reports").resolve()
        today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")

        def _load_json(p):
            if not p.exists():
                return None
            try:
                return json.loads(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None

        comb_path = reports_dir / f"{today}_stock-bot_combined.json"
        comparison = {}
        recommendation = "WAIT"
        promotion_score = None
        if comb_path.exists():
            comb = _load_json(comb_path)
            if comb and isinstance(comb.get("strategy_comparison"), dict):
                comparison = comb["strategy_comparison"]
                recommendation = comparison.get("recommendation", "WAIT")
                promotion_score = comparison.get("promotion_readiness_score")

        historical = []
        try:
            end_d = datetime.strptime(today[:10], "%Y-%m-%d").date()
            for i in range(29, -1, -1):
                dk = (end_d - timedelta(days=i)).strftime("%Y-%m-%d")
                cp = reports_dir / f"{dk}_stock-bot_combined.json"
                if cp.exists():
                    c = _load_json(cp)
                    if c:
                        sc = c.get("strategy_comparison") or {}
                        historical.append({
                            "date": dk,
                            "equity_realized": c.get("equity_strategy_pnl") or sc.get("equity_realized_pnl"),
                            "wheel_realized": c.get("wheel_strategy_pnl") or sc.get("wheel_realized_pnl"),
                            "promotion_score": sc.get("promotion_readiness_score"),
                        })
        except Exception:
            pass

        weekly_path = reports_dir / f"{today}_weekly_promotion_report.json"
        weekly = _load_json(weekly_path) if weekly_path.exists() else None

        return jsonify({
            "date": today,
            "strategy_comparison": comparison,
            "recommendation": recommendation,
            "promotion_readiness_score": promotion_score,
            "historical_comparison": historical[-30:],
            "weekly_report": weekly,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            return jsonify({
                "error": "no telemetry bundles found",
                "message": "Run bar health or full telemetry extract to create telemetry/YYYY-MM-DD/computed/",
                "telemetry_root": str(TELEMETRY_ROOT),
            }), 404

        comp_dir = tdir / "computed"
        comp_dir.mkdir(parents=True, exist_ok=True)
        fn = _TELEMETRY_COMPUTED_MAP.get(name) or name
        # Allow passing a filename directly (must end with .json).
        if not str(fn).endswith(".json"):
            return jsonify({"error": f"unknown computed artifact: {name}"}), 404
        fp = comp_dir / str(fn)
        if not fp.exists():
            return jsonify({"error": f"computed artifact missing: {fn}", "latest_date": tdir.name}), 404

        data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
        return jsonify({"latest_date": tdir.name, "name": name, "filename": str(fn), "data": data})
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
    port = int(os.getenv("PORT", "5000"))
    print(f"[Dashboard] Starting on port {port}...", flush=True)
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
