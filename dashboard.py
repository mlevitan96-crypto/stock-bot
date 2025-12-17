#!/usr/bin/env python3
"""
Position Dashboard - Fast Start Version
Binds port 5000 immediately, then lazy-loads heavy dependencies.
"""

import os
import sys
import json
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response

print("[Dashboard] Starting Flask app...", flush=True)
app = Flask(__name__)

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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Bot Dashboard</h1>
            <p>Live position monitoring with real-time P&L updates</p>
            <p class="update-info">Auto-refresh: 10 seconds | Last update: <span id="last-update">-</span></p>
        </div>
        
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
        </div>
        
        <div class="positions-table">
            <h2 style="margin-bottom: 15px;">Open Positions</h2>
            <div id="positions-content">
                <p class="loading">Loading positions...</p>
            </div>
        </div>
    </div>
    
    <script>
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
            // Fetch positions
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
            
            // Fetch health status for Last Order and Doctor
            // Try main bot API first, fallback to health_status endpoint
            Promise.all([
                fetch('/api/health_status').catch(() => null),
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
        
        updateDashboard();
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>
"""

@app.route("/")
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

@app.route("/api/health_status", methods=["GET"])
def api_health_status():
    """Health status endpoint for dashboard - provides Last Order and Doctor status"""
    try:
        from sre_monitoring import SREMonitoringEngine
        engine = SREMonitoringEngine()
        
        # Get last order
        last_order_ts = engine.get_last_order_timestamp()
        last_order_age_sec = time.time() - last_order_ts if last_order_ts else None
        
        # Get Doctor/heartbeat from main health endpoint
        try:
            import requests
            health_response = requests.get("http://localhost:8081/health", timeout=2)
            if health_response.status_code == 200:
                health_data = health_response.json()
                heartbeat_age_sec = health_data.get("last_heartbeat_age_sec")
            else:
                heartbeat_age_sec = None
        except:
            heartbeat_age_sec = None
        
        # Market status
        market_open, market_status = engine.is_market_open()
        
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"[Dashboard] Binding to 0.0.0.0:{port}...", flush=True)
    
    loader_thread = threading.Thread(target=lazy_load_dependencies, daemon=True)
    loader_thread.start()
    
    print(f"[Dashboard] Server starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
