#!/usr/bin/env python3
"""
Position Dashboard - Fast Start Version
Binds port 5000 immediately, then lazy-loads heavy dependencies.
"""

import os
import sys
import json
import threading
import base64
import functools
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response, request

print("[Dashboard] Starting Flask app...", flush=True)
app = Flask(__name__)

_alpaca_api = None
_registry_loaded = False

def _auth_enabled() -> bool:
    # Enable auth when DASHBOARD_PASSWORD is set (recommended).
    return bool(os.getenv("DASHBOARD_PASSWORD", "").strip())

def _check_basic_auth(auth_header: str) -> bool:
    try:
        if not auth_header or not auth_header.lower().startswith("basic "):
            return False
        encoded = auth_header.split(" ", 1)[1].strip()
        decoded = base64.b64decode(encoded).decode("utf-8", "ignore")
        user, pwd = decoded.split(":", 1)
        expected_user = os.getenv("DASHBOARD_USER", "admin")
        expected_pwd = os.getenv("DASHBOARD_PASSWORD", "")
        return user == expected_user and pwd == expected_pwd
    except Exception:
        return False

def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Allow unauthenticated health ping
        if request.path == "/health":
            return fn(*args, **kwargs)
        if not _auth_enabled():
            return fn(*args, **kwargs)
        if _check_basic_auth(request.headers.get("Authorization", "")):
            return fn(*args, **kwargs)
        return Response("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="dashboard"'})
    return wrapper

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
        .positions-table {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow-x: auto;
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
        .tabs { display: flex; gap: 10px; margin-top: 15px; }
        .tab-btn { border: 1px solid #e5e7eb; background: #fff; padding: 8px 12px; border-radius: 8px; cursor: pointer; }
        .tab-btn.active { background: #667eea; color: #fff; border-color: #667eea; }
        .tab { display: none; }
        .tab.active { display: block; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Bot Dashboard</h1>
            <p>Live position monitoring with real-time P&L updates</p>
            <p class="update-info">Auto-refresh: 10 seconds | Last update: <span id="last-update">-</span></p>
            <div class="tabs">
                <button class="tab-btn active" onclick="showTab('positions-tab')">Positions</button>
                <button class="tab-btn" onclick="showTab('performance-tab')">Performance</button>
            </div>
        </div>
        
        <div class="tab active" id="positions-tab">
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
        </div>
        
        <div class="positions-table">
            <h2 style="margin-bottom: 15px;">Open Positions</h2>
            <div id="positions-content">
                <p class="loading">Loading positions...</p>
            </div>
        </div>
        </div>

        <div class="tab" id="performance-tab">
            <div class="positions-table" style="margin-top: 20px;">
                <h2 style="margin-bottom: 15px;">Rolling performance (2d / 5d)</h2>
                <div id="perf-content"><p class="loading">Loading performance...</p></div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(id) {
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(id));
            if (btn) btn.classList.add('active');
            if (id === 'performance-tab') updatePerformance();
        }

        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
        }
        
        function formatPercent(value) {
            return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
        }
        
        function updateDashboard() {
            fetch('/api/positions')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    if (data.error) {
                        document.getElementById('positions-content').innerHTML = 
                            '<p class="no-positions">Error: ' + data.error + '</p>';
                        return;
                    }
                    
                    document.getElementById('total-positions').textContent = data.positions.length;
                    document.getElementById('total-value').textContent = formatCurrency(data.total_value || 0);
                    
                    const pnl = data.unrealized_pnl || 0;
                    const pnlEl = document.getElementById('unrealized-pnl');
                    pnlEl.textContent = formatCurrency(pnl);
                    pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'positive' : 'negative');
                    
                    const dayPnl = data.day_pnl || 0;
                    const dayPnlEl = document.getElementById('day-pnl');
                    dayPnlEl.textContent = formatCurrency(dayPnl);
                    dayPnlEl.className = 'stat-value ' + (dayPnl >= 0 ? 'positive' : 'negative');
                    
                    if (data.positions.length === 0) {
                        document.getElementById('positions-content').innerHTML = 
                            '<p class="no-positions">No open positions</p>';
                        return;
                    }
                    
                    let html = '<table><thead><tr>';
                    html += '<th>Symbol</th><th>Side</th><th>Qty</th><th>Entry</th>';
                    html += '<th>Current</th><th>Value</th><th>P&L</th><th>P&L %</th></tr></thead><tbody>';
                    
                    data.positions.forEach(pos => {
                        const pnlClass = pos.unrealized_pnl >= 0 ? 'positive' : 'negative';
                        html += '<tr>';
                        html += '<td class="symbol">' + pos.symbol + '</td>';
                        html += '<td><span class="side ' + pos.side + '">' + pos.side.toUpperCase() + '</span></td>';
                        html += '<td>' + pos.qty + '</td>';
                        html += '<td>' + formatCurrency(pos.avg_entry_price) + '</td>';
                        html += '<td>' + formatCurrency(pos.current_price) + '</td>';
                        html += '<td>' + formatCurrency(pos.market_value) + '</td>';
                        html += '<td class="' + pnlClass + '">' + formatCurrency(pos.unrealized_pnl) + '</td>';
                        html += '<td class="' + pnlClass + '">' + formatPercent(pos.unrealized_pnl_pct) + '</td>';
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('positions-content').innerHTML = html;
                })
                .catch(error => {
                    console.error('Error fetching positions:', error);
                });
        }

        function renderRollup(title, r) {
            const pnl = r.pnl || {};
            const blocks = r.blocks || {};
            const review = (r.executive_review || []).join('\\n- ');
            const topSyms = (r.top_symbols || []).map(s => `${s.symbol}: ${formatCurrency(s.pnl_usd)} (${s.trades})`).join('<br>');
            const topReasons = (blocks.top_reasons || []).map(x => `${x.reason}: ${x.count}`).join('<br>');
            return `
              <div style="margin-bottom: 20px;">
                <h3 style="margin-bottom:8px;">${title}</h3>
                <div><b>PnL</b>: ${formatCurrency(pnl.total_pnl_usd || 0)} | <b>Trades</b>: ${pnl.trades_closed || 0} | <b>Win rate</b>: ${(pnl.win_rate==null?'—':(pnl.win_rate*100).toFixed(1)+'%')}</div>
                <div style="margin-top:8px;"><b>Top symbols</b><br>${topSyms || '—'}</div>
                <div style="margin-top:8px;"><b>Blocked trades</b>: ${blocks.total || 0}</div>
                <div style="margin-top:8px;"><b>Top block reasons</b><br>${topReasons || '—'}</div>
                <div style="margin-top:8px;"><b>Executive review</b><pre>- ${review || '—'}</pre></div>
              </div>
            `;
        }

        function updatePerformance() {
            fetch('/api/rollups')
              .then(r => r.json())
              .then(data => {
                if (data.error) {
                  document.getElementById('perf-content').innerHTML = '<p class="no-positions">Error: ' + data.error + '</p>';
                  return;
                }
                const r2 = data.rollups && data.rollups["2"];
                const r5 = data.rollups && data.rollups["5"];
                let html = '';
                if (r2) html += renderRollup('Last 2 days', r2);
                if (r5) html += renderRollup('Last 5 days', r5);
                document.getElementById('perf-content').innerHTML = html || '<p class="no-positions">No rollup data yet</p>';
              })
              .catch(err => {
                document.getElementById('perf-content').innerHTML = '<p class="no-positions">Error loading performance</p>';
              });
        }
        
        updateDashboard();
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>
"""

@app.route("/")
@require_auth
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies_loaded": _registry_loaded,
        "alpaca_connected": _alpaca_api is not None
    })

@app.route("/api/positions")
@require_auth
def api_positions():
    try:
        if _alpaca_api is None:
            return jsonify({
                "positions": [],
                "total_value": 0,
                "unrealized_pnl": 0,
                "day_pnl": 0,
                "error": "Alpaca API not connected"
            })
        
        positions = _alpaca_api.list_positions()
        account = _alpaca_api.get_account()
        
        pos_list = []
        for p in positions:
            pos_list.append({
                "symbol": p.symbol,
                "side": "long" if float(p.qty) > 0 else "short",
                "qty": abs(float(p.qty)),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": abs(float(p.market_value)),
                "unrealized_pnl": float(p.unrealized_pl),
                "unrealized_pnl_pct": float(p.unrealized_plpc) * 100
            })
        
        return jsonify({
            "positions": pos_list,
            "total_value": float(account.portfolio_value),
            "unrealized_pnl": sum(p["unrealized_pnl"] for p in pos_list),
            "day_pnl": float(account.equity) - float(account.last_equity)
        })
    except Exception as e:
        return jsonify({
            "positions": [],
            "total_value": 0,
            "unrealized_pnl": 0,
            "day_pnl": 0,
            "error": str(e)
        })

@app.route("/api/closed_positions")
@require_auth
def api_closed_positions():
    try:
        from pathlib import Path
        import csv
        from io import StringIO
        
        closed = []
        state_file = Path("state/closed_positions.json")
        if state_file.exists():
            data = json.loads(state_file.read_text())
            closed = data if isinstance(data, list) else data.get("positions", [])
        
        return jsonify({"closed_positions": closed[-50:]})
    except Exception as e:
        return jsonify({"closed_positions": [], "error": str(e)})

@app.route("/api/rollups")
@require_auth
def api_rollups():
    try:
        from pathlib import Path
        from learning_rollup import compute_rollup
        repo = Path(".").resolve()
        now_ts = int(time.time())
        r2 = compute_rollup(repo, 2, now_ts=now_ts)
        r5 = compute_rollup(repo, 5, now_ts=now_ts)
        return jsonify({"rollups": {"2": r2, "5": r5}})
    except Exception as e:
        return jsonify({"error": str(e), "rollups": {}})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"[Dashboard] Binding to 0.0.0.0:{port}...", flush=True)
    
    loader_thread = threading.Thread(target=lazy_load_dependencies, daemon=True)
    loader_thread.start()
    
    print(f"[Dashboard] Server starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
