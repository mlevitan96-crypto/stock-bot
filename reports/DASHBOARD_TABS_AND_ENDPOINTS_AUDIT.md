# Dashboard Tabs and Endpoints Audit

## Tab → Loader → Endpoints

| Tab | Content div | Loader | Primary endpoint(s) |
|-----|--------------|--------|----------------------|
| Positions | positions-content | updateDashboard / loadPositions | /api/positions |
| Signal Review | signal-review-content | loadSignalReview | /api/signal_history |
| SRE Monitoring | sre-content | loadSREContent | /api/sre/health, /api/telemetry/latest/computed?name=bar_health_summary, /api/version, /api/versions |
| Executive Summary | executive-content | loadExecutiveSummary | /api/executive_summary |
| Natural Language Auditor (XAI) | xai-content | loadXAIAuditor | /api/xai/auditor |
| Trading Readiness | failure_points-content | loadFailurePoints | /api/failure_points |
| Telemetry | telemetry-content | loadTelemetryContent | /api/telemetry/latest/index, live_vs_shadow_pnl, signal_performance, signal_weight_recommendations, health, blocked_counterfactuals_summary, exit_quality_summary, signal_profitability, gate_profitability, intelligence_recommendations, /api/paper-mode-intel-state |

## Credentials

All fetches use `credentials: 'same-origin'` so the browser sends Basic Auth. If the main script fails to parse, only the first-script minimal loaders run; we now define minimal loaders for every tab in the first script so all tabs work.

## Minimal loaders (first script block) — all tabs work

- loadVersion, loadPositions: version badge and positions (already in first script).
- window.loadSREContent: fetch /api/sre/health, render overall_health and bot status.
- window.loadExecutiveSummary: fetch /api/executive_summary, render total_trades.
- window.loadXAIAuditor: fetch /api/xai/auditor, render trade_count and weight_count.
- window.loadFailurePoints: fetch /api/failure_points, render readiness.
- window.loadSignalReview: fetch /api/signal_history, render signals table (up to 50).
- window.loadTelemetryContent: fetch /api/telemetry/latest/index, render latest_date.

All minimal loaders use credentials: 'same-origin' and show a clear error on HTTP error or network failure. If the main script runs, it overwrites these with full renderers; if not, minimal loaders ensure every tab shows data.
