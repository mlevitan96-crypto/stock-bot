#!/usr/bin/env python3
"""
Position Dashboard - Fast Start Version
Binds port 5000 immediately, then lazy-loads heavy dependencies.

IMPORTANT: For project context, common issues, and solutions, see MEMORY_BANK.md
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
            <p class="update-info">Auto-refresh: 60 seconds | Last update: <span id="last-update">-</span> | Last Signal: <span id="last-signal">-</span></p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('positions', event)">📊 Positions</button>
            <button class="tab" onclick="switchTab('signal_review', event)">🔍 Signal Review</button>
            <button class="tab" onclick="switchTab('sre', event)">🔍 SRE Monitoring</button>
            <button class="tab" onclick="switchTab('executive', event)">📈 Executive Summary</button>
            <button class="tab" onclick="switchTab('xai', event)">🧠 Natural Language Auditor</button>
            <button class="tab" onclick="switchTab('failure_points', event)">⚠️ Trading Readiness</button>
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
        
        <div id="failure_points-tab" class="tab-content">
            <div id="failure_points-content">
                <div class="loading">Loading Trading Readiness...</div>
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
        function switchTab(tabName, event) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            if (event && event.target) {
                event.target.classList.add('active');
            } else {
                // Fallback: find button by tab name
                document.querySelectorAll('.tab').forEach(tab => {
                    const tabText = tab.textContent.toLowerCase();
                    if (tabName === 'positions' && tabText.includes('positions')) {
                        tab.classList.add('active');
                    } else if (tabName === 'sre' && tabText.includes('sre')) {
                        tab.classList.add('active');
                    } else if (tabName === 'executive' && tabText.includes('executive')) {
                        tab.classList.add('active');
                    }
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
            } else if (tabName === 'signal_review') {
                loadSignalReview();
            } else if (tabName === 'positions') {
                // Refresh positions when switching back - force fresh data
                updateDashboard();
            }
        }
        
        function loadSREContent() {
            const sreContent = document.getElementById('sre-content');
            // Save scroll position before update
            const scrollTop = sreContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            
            if (sreContent.innerHTML.includes('Loading') || !sreContent.dataset.loaded) {
                fetch('/api/sre/health')
                    .then(response => response.json())
                    .then(data => {
                        sreContent.dataset.loaded = 'true';
                        renderSREContent(data, sreContent);
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
        
        function renderSREContent(data, container) {
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
            
            let html = `
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
        
        function updateLastSignalTimestamp() {
            fetch('/api/signal_history')
                .then(response => response.json())
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
        
        function loadSignalReview() {
            const signalContent = document.getElementById('signal-review-content');
            
            fetch('/api/signal_history')
                .then(response => response.json())
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
            
            fetch('/api/failure_points')
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
            
            fetch('/api/xai/auditor')
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
            fetch('/api/xai/export')
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
        
        function loadExecutiveSummary() {
            const executiveContent = document.getElementById('executive-content');
            // Save scroll position before update
            const scrollTop = executiveContent.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
            // Only show loading if not already loaded
            if (!executiveContent.dataset.loaded) {
                executiveContent.innerHTML = '<div class="loading">Loading executive summary...</div>';
            }
            fetch('/api/executive_summary')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    executiveContent.dataset.loaded = 'true';
                    renderExecutiveSummary(data, executiveContent);
                    // Restore scroll position after render
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
        
        function renderExecutiveSummary(data, container) {
            const pnl2d = data.pnl_metrics?.pnl_2d || 0;
            const pnl5d = data.pnl_metrics?.pnl_5d || 0;
            const pnl2dClass = pnl2d >= 0 ? 'positive' : 'negative';
            const pnl5dClass = pnl5d >= 0 ? 'positive' : 'negative';
            
            let html = `
                <div class="stat-card" style="margin-bottom: 20px; border: 3px solid #667eea;">
                    <h2 style="color: #667eea; margin-bottom: 15px;">📊 Performance Metrics</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <div class="stat-label">Total Trades</div>
                            <div class="stat-value">${data.total_trades || 0}</div>
                        </div>
                        <div>
                            <div class="stat-label">2-Day P&L</div>
                            <div class="stat-value ${pnl2dClass}">${formatCurrency(pnl2d)}</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                                ${data.pnl_metrics?.trades_2d || 0} trades, ${data.pnl_metrics?.win_rate_2d || 0}% win rate
                            </div>
                        </div>
                        <div>
                            <div class="stat-label">5-Day P&L</div>
                            <div class="stat-value ${pnl5dClass}">${formatCurrency(pnl5d)}</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                                ${data.pnl_metrics?.trades_5d || 0} trades, ${data.pnl_metrics?.win_rate_5d || 0}% win rate
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
            
            const topSignals = data.signal_analysis?.top_signals || {};
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
            
            const bottomSignals = data.signal_analysis?.bottom_signals || {};
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
            
            const weightAdjustments = data.learning_insights?.weight_adjustments || {};
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
            
            const counterfactual = data.learning_insights?.counterfactual_insights || {};
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
            
            // Fetch positions - always get fresh data (no browser cache)
            fetch('/api/positions', {
                cache: 'no-store',  // Ensure browser doesn't cache the response
                headers: {
                    'Cache-Control': 'no-cache'
                }
            })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    if (data.error) {
                        document.getElementById('positions-content').innerHTML = 
                            '<p class="no-positions">Error: ' + data.error + '</p>';
                        return;
                    }
                    
                    // Update stats (these don't cause flicker)
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
                    
                    // Update table with minimal DOM manipulation
                    const container = document.getElementById('positions-content');
                    const existingTable = container.querySelector('table');
                    
                    // Check if table structure changed (number of positions)
                    const existingRows = existingTable ? existingTable.querySelectorAll('tbody tr').length : 0;
                    const needsFullRebuild = !existingTable || existingRows !== data.positions.length;
                    
                    if (needsFullRebuild) {
                        // Full rebuild only when structure changes
                        let html = '<table><thead><tr>';
                        html += '<th>Symbol</th><th>Side</th><th>Qty</th><th>Entry</th>';
                        html += '<th>Current</th><th>Value</th><th>P&L</th><th>P&L %</th><th>Entry Score</th><th>Current Score</th></tr></thead><tbody>';
                        
                        data.positions.forEach(pos => {
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
                        // Update existing rows in place (no flicker)
                        const tbody = existingTable.querySelector('tbody');
                        data.positions.forEach((pos, index) => {
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
                    
                    // Restore scroll position
                    if (scrollTop > 0) {
                        requestAnimationFrame(() => {
                            positionsContent.scrollTop = scrollTop;
                            window.scrollTo(0, scrollTop);
                        });
                    }
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
        updateLastSignalTimestamp();  // Initial load
        // Refresh less frequently to reduce flicker and improve UX
        setInterval(updateDashboard, 60000);  // 60 seconds instead of 10
        setInterval(updateLastSignalTimestamp, 30000);  // Update last signal every 30 seconds
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
        # CRITICAL: Always re-read cache file on each request to ensure fresh current_score
        uw_cache = {}
        current_regime = "mixed"
        try:
            from config.registry import CacheFiles, read_json
            import json as json_module
            cache_file = CacheFiles.UW_FLOW_CACHE
            # Force fresh read - re-read file on every API call (no caching)
            if cache_file.exists():
                # Read directly to ensure fresh data (read_json already does this, but being explicit)
                uw_cache = read_json(cache_file, default={})
            
            # Get current regime (also re-read fresh on each request)
            try:
                from config.registry import StateFiles
                regime_file = StateFiles.REGIME_DETECTOR
                if regime_file.exists():
                    # Re-read regime file fresh on each request
                    regime_data = json_module.loads(regime_file.read_text())
                    if isinstance(regime_data, dict):
                        current_regime = regime_data.get("current_regime") or regime_data.get("regime") or "mixed"
            except:
                pass
        except Exception as e:
            print(f"[Dashboard] Warning: Failed to load UW cache for current scores: {e}", flush=True)
        
        pos_list = []
        for p in positions:
            symbol = p.symbol
            # Get entry_score from metadata (default to 0.0 if missing - dashboard will highlight)
            entry_score = metadata.get(symbol, {}).get("entry_score", 0.0) if metadata else 0.0
            
            # Calculate current composite score (same logic as exit evaluation)
            # CRITICAL: Recalculate on every API call to ensure fresh current_score
            current_score = 0.0
            try:
                if uw_cache and symbol in uw_cache:
                    enriched = uw_cache.get(symbol, {})
                    if enriched:
                        import uw_composite_v2 as uw_v2
                        # Always recalculate composite score from fresh cache data
                        composite = uw_v2.compute_composite_score_v3(symbol, enriched, current_regime)
                        if composite:
                            current_score = composite.get("score", 0.0)
            except Exception as e:
                # Fail silently - don't break dashboard if score calculation fails
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
                "entry_score": float(entry_score),  # CRITICAL: Include entry_score from metadata
                "current_score": float(current_score)  # Current composite score
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
                health_data = resp.json()
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
            
            return jsonify(health), 200
        except Exception as e:
            return jsonify({"error": f"Failed to load SRE health: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _calculate_signal_funnel():
    """Calculate Signal Funnel metrics: [UW Alerts] -> [Parsed] -> [Scored > 3.0] -> [Orders]"""
    from pathlib import Path
    import json
    from datetime import datetime, timezone, timedelta
    
    try:
        # Use config.registry for file paths (consistent with rest of codebase)
        from config.registry import LogFiles
        
        # Count UW alerts (from UW logs)
        alerts_count = 0
        parsed_count = 0
        scored_above_3 = 0
        orders_sent = 0
        
        # Get data from last 30 minutes (as per dashboard display requirement)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        # Count UW alerts from multiple possible sources
        from config.registry import CacheFiles
        uw_logs = [
            CacheFiles.UW_ATTRIBUTION if hasattr(CacheFiles, 'UW_ATTRIBUTION') else Path("data/uw_attribution.jsonl"),
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
                                            alerts_count += 1
                                    except:
                                        pass
                            except:
                                continue
                except:
                    pass
        
        # Count parsed signals (from gate logs or attribution)
        gate_logs = [
            Path("logs/gate.jsonl"),
            LogFiles.ATTRIBUTION,
            LogFiles.COMPOSITE_ATTRIBUTION if hasattr(LogFiles, 'COMPOSITE_ATTRIBUTION') else Path("logs/composite_attribution.jsonl")
        ]
        
        for gate_log in gate_logs:
            if isinstance(gate_log, str):
                gate_log = Path(gate_log)
            if gate_log.exists():
                try:
                    with gate_log.open('r', encoding='utf-8') as f:
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
                                            parsed_count += 1
                                            # Check if scored > 3.0
                                            score = rec.get("signal_score") or rec.get("score") or rec.get("entry_score") or 0.0
                                            try:
                                                if float(score) >= 3.0:
                                                    scored_above_3 += 1
                                            except:
                                                pass
                                    except:
                                        pass
                            except:
                                continue
                except:
                    pass
        
        # Count orders sent (from attribution or orders logs)
        orders_logs = [
            LogFiles.ATTRIBUTION,
            LogFiles.ORDERS,
            Path("data/live_orders.jsonl")
        ]
        
        for orders_log in orders_logs:
            if isinstance(orders_log, str):
                orders_log = Path(orders_log)
            if orders_log.exists():
                try:
                    with orders_log.open('r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                rec = json.loads(line.strip())
                                # Check for order submission events
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
                                        except:
                                            pass
                            except:
                                continue
                except:
                    pass
                if orders_sent > 0:
                    break  # Found orders, no need to check other files
        
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
            CacheFiles.UW_ATTRIBUTION if hasattr(CacheFiles, 'UW_ATTRIBUTION') else Path("data/uw_attribution.jsonl"),
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
            
            # CRITICAL: Use standardized path from config/registry.py
            try:
                from config.registry import LogFiles
                attribution_file = LogFiles.ATTRIBUTION
                if not attribution_file.exists():
                    # Fallback to alternative locations if standardized path doesn't exist
                    attribution_files = [
                        Path("logs/attribution.jsonl"),
                        Path("data/attribution.jsonl"),
                    ]
                    for path in attribution_files:
                        if path.exists():
                            attribution_file = path
                            print(f"[Dashboard] WARNING: Using fallback path: {path}", flush=True, file=sys.stderr)
                            break
                    else:
                        attribution_file = None
            except ImportError:
                # Fallback to local paths if registry not available
                attribution_files = [
                    Path("logs/attribution.jsonl"),
                    Path("data/attribution.jsonl"),
                ]
                attribution_file = None
                for path in attribution_files:
                    if path.exists():
                        attribution_file = path
                        break
            
            if attribution_file:
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=90)  # Last 90 days
                with attribution_file.open('r', encoding='utf-8') as f:
                    for line in f:
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
    """Get executive summary with trades, P&L, and learning analysis"""
    try:
        from executive_summary_generator import generate_executive_summary
        summary = generate_executive_summary()
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
            "pnl_metrics": {"pnl_2d": 0, "pnl_5d": 0, "trades_2d": 0, "trades_5d": 0, "win_rate_2d": 0, "win_rate_5d": 0},
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
        
        # Fallback to log files if Alpaca API unavailable or failed
        if last_order_ts is None:
            orders_files = [
                Path("data/live_orders.jsonl"),
                Path("logs/orders.jsonl"),
                Path("logs/trading.jsonl")
            ]
            
            for orders_file in orders_files:
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
                    except:
                        pass
            
            if last_order_ts:
                last_order_age_sec = time.time() - last_order_ts
        
        # Get Doctor/heartbeat from file
        # CRITICAL: Check bot_heartbeat.json FIRST (main.py writes here)
        heartbeat_age_sec = None
        heartbeat_files = [
            Path("state/bot_heartbeat.json"),  # Main bot heartbeat - check FIRST
            Path("state/doctor_state.json"),
            Path("state/system_heartbeat.json"),
            Path("state/heartbeat.json")
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
        
        signals = get_signal_history(limit=50)
        last_signal_ts = get_last_signal_timestamp()
        
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"[Dashboard] Starting on port {port}...", flush=True)
    print(f"[Dashboard] Instance: {os.getenv('INSTANCE', 'UNKNOWN')}", flush=True)
    
    loader_thread = threading.Thread(target=lazy_load_dependencies, daemon=True)
    loader_thread.start()
    
    print(f"[Dashboard] Server starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
