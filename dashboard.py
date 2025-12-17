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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Bot Dashboard</h1>
            <p>Live position monitoring with real-time P&L updates</p>
            <p class="update-info">Auto-refresh: 10 seconds | Last update: <span id="last-update">-</span></p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('positions')">📊 Positions</button>
            <button class="tab" onclick="switchTab('sre')">🔍 SRE Monitoring</button>
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
    </div>
    
    <script>
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Load SRE content if switching to SRE tab
            if (tabName === 'sre') {
                loadSREContent();
            }
        }
        
        function loadSREContent() {
            const sreContent = document.getElementById('sre-content');
            if (sreContent.innerHTML.includes('Loading') || !sreContent.dataset.loaded) {
                fetch('/api/sre/health')
                    .then(response => response.json())
                    .then(data => {
                        sreContent.dataset.loaded = 'true';
                        renderSREContent(data, sreContent);
                    })
                    .catch(error => {
                        sreContent.innerHTML = `<div class="loading" style="color: #ef4444;">Error loading SRE data: ${error.message}</div>`;
                    });
            }
        }
        
        function renderSREContent(data, container) {
            const overallHealth = data.overall_health || 'unknown';
            const healthClass = overallHealth === 'healthy' ? 'healthy' : 
                              overallHealth === 'degraded' ? 'degraded' : 'critical';
            
            let html = `
                <div class="stat-card" style="border: 3px solid ${healthClass === 'healthy' ? '#10b981' : healthClass === 'degraded' ? '#f59e0b' : '#ef4444'}; margin-bottom: 20px;">
                    <h2 style="color: ${healthClass === 'healthy' ? '#10b981' : healthClass === 'degraded' ? '#f59e0b' : '#ef4444'}; margin-bottom: 10px;">
                        Overall Health: ${overallHealth.toUpperCase()}
                    </h2>
                    <p>Market: <span style="padding: 4px 8px; background: ${data.market_open ? '#10b981' : '#64748b'}; color: white; border-radius: 4px;">
                        ${data.market_status || 'unknown'}
                    </span></p>
                    ${data.critical_issues ? '<p style="color: #ef4444; margin-top: 10px;"><strong>Critical:</strong> ' + data.critical_issues.join(', ') + '</p>' : ''}
                    ${data.warnings ? '<p style="color: #f59e0b; margin-top: 10px;"><strong>Warnings:</strong> ' + data.warnings.join(', ') + '</p>' : ''}
                </div>
                
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
                            <div>Last Update: ${formatTimeAgo(health.last_update_age_sec)}</div>
                            ${health.data_freshness_sec !== null && health.data_freshness_sec !== undefined ? 
                                `<div>Freshness: ${formatTimeAgo(health.data_freshness_sec)}</div>` : ''}
                            ${health.error_rate_1h !== undefined ? 
                                `<div>Error Rate: ${(health.error_rate_1h * 100).toFixed(1)}%</div>` : ''}
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
                <div class="positions-table">
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
            `;
            
            container.innerHTML = html;
        }
        
        // Auto-refresh SRE content if on SRE tab
        setInterval(() => {
            if (document.getElementById('sre-tab').classList.contains('active')) {
                loadSREContent();
            }
        }, 10000);
        
        function formatCurrency(value) {
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
            fetch('/api/sre/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    // Update overall health
                    const overallHealth = data.overall_health || 'unknown';
                    const overallEl = document.getElementById('overall-health');
                    overallEl.className = 'overall-health ' + getStatusClass(overallHealth);
                    overallEl.innerHTML = `
                        <h2>${overallHealth.toUpperCase()}</h2>
                        <p>Market: <span class="market-status ${data.market_open ? 'open' : 'closed'}">${data.market_status || 'unknown'}</span></p>
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
                        apiContainer.innerHTML = '<div class="loading">No API endpoints found</div>';
                    } else {
                        apiContainer.innerHTML = Object.entries(apis).map(([name, health]) => {
                            const status = health.status || 'unknown';
                            const statusClass = getStatusClass(status);
                            return `
                                <div class="health-card ${statusClass}">
                                    <div class="health-card-header">
                                        <span class="health-card-name">${name}</span>
                                        <span class="health-status ${statusClass}">${status}</span>
                                    </div>
                                    <div class="health-details">
                                        ${health.avg_latency_ms !== null && health.avg_latency_ms !== undefined ? 
                                            `<div><strong>Avg Latency:</strong> ${health.avg_latency_ms.toFixed(0)}ms</div>` : ''}
                                        ${health.error_rate_1h !== undefined ? 
                                            `<div><strong>Error Rate (1h):</strong> ${(health.error_rate_1h * 100).toFixed(1)}%</div>` : ''}
                                        ${health.rate_limit_remaining !== null && health.rate_limit_remaining !== undefined ? 
                                            `<div><strong>Rate Limit:</strong> ${health.rate_limit_remaining} remaining</div>` : ''}
                                        ${health.last_error ? 
                                            `<div style="color: #ef4444; margin-top: 5px;"><strong>Error:</strong> ${health.last_error}</div>` : ''}
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
        setInterval(updateSREDashboard, 10000);
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

@app.route("/sre")
def sre_dashboard():
    """Comprehensive SRE monitoring dashboard"""
    return render_template_string(SRE_DASHBOARD_HTML)

@app.route("/api/sre/health", methods=["GET"])
def api_sre_health():
    """Get comprehensive SRE health data"""
    try:
        import requests
        # Try to get from main bot API first
        try:
            resp = requests.get("http://localhost:8081/api/sre/health", timeout=2)
            if resp.status_code == 200:
                return jsonify(resp.json()), 200
        except:
            pass
        
        # Fallback to local sre_monitoring
        try:
            from sre_monitoring import get_sre_health
            health = get_sre_health()
            return jsonify(health), 200
        except Exception as e:
            return jsonify({"error": f"Failed to load SRE health: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health_status", methods=["GET"])
def api_health_status():
    """Health status endpoint for dashboard - provides Last Order and Doctor status"""
    try:
        import time
        from pathlib import Path
        
        # Get last order directly from file
        last_order_ts = None
        last_order_age_sec = None
        orders_file = Path("data/live_orders.jsonl")
        if orders_file.exists():
            try:
                with orders_file.open("r") as f:
                    lines = f.readlines()
                    for line in lines[-500:]:
                        try:
                            event = json.loads(line.strip())
                            event_ts = event.get("_ts", 0)
                            event_type = event.get("event", "")
                            if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                                last_order_ts = event_ts
                        except:
                            pass
                if last_order_ts:
                    last_order_age_sec = time.time() - last_order_ts
            except:
                pass
        
        # Get Doctor/heartbeat from file
        heartbeat_age_sec = None
        heartbeat_files = [
            Path("state/doctor_state.json"),
            Path("state/system_heartbeat.json"),
            Path("state/heartbeat.json"),
            Path("state/bot_heartbeat.json")
        ]
        
        for hb_file in heartbeat_files:
            if hb_file.exists():
                try:
                    data = json.loads(hb_file.read_text())
                    heartbeat_ts = data.get("timestamp") or data.get("_ts") or data.get("last_heartbeat") or data.get("last_update")
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"[Dashboard] Binding to 0.0.0.0:{port}...", flush=True)
    
    loader_thread = threading.Thread(target=lazy_load_dependencies, daemon=True)
    loader_thread.start()
    
    print(f"[Dashboard] Server starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
