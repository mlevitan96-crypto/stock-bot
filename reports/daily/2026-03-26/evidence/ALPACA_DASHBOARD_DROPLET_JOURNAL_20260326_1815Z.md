# Alpaca dashboard — journal (stock-bot-dashboard.service)

**Timestamp:** 20260326_1815Z  
**Source:** `journalctl -u stock-bot-dashboard.service -n 300 --no-pager` on SSH host `alpaca` (2026-03-26 UTC).

```log
Mar 26 17:15:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:15:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:15:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:15:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:16:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:16:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:16:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:16:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:16:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:16:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:17:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:17:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:17:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:17:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:17:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:17:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:18:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:18:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:18:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:18:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:18:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:18:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:19:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:19:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:19:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:19:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:19:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:19:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:20:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:20:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:20:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:20:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:20:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:20:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:21:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:21:05] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:21:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:21:05] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:21:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:21:05] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:22:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:22:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:22:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:22:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:22:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:22:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:23:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:23:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:23:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:23:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:23:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:23:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:24:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:24:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:24:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:25:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:25:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:25:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:26:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:26:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:26:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:26:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:26:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:26:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:27:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:27:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:27:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:27:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:27:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: 75.167.147.249 - - [26/Mar/2026 17:27:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 4.170s CPU time, 138.2M memory peak, 0B memory swap peak.
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Starting Flask app...
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Starting on port 5000...
Mar 26 17:27:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Instance: UNKNOWN
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Loading dependencies...[Dashboard] Server starting on port 5000
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]:  * Serving Flask app 'dashboard'
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]:  * Debug mode: off
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]:  * Running on all addresses (0.0.0.0)
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]:  * Running on http://127.0.0.1:5000
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]:  * Running on http://104.236.102.57:5000
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: Press CTRL+C to quit
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Alpaca API connected
Mar 26 17:27:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: [Dashboard] Dependencies loaded
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 404 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:27:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:48] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:27:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:50] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:27:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:50] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:27:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:51] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:27:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:51] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:27:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:52] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:27:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:52] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:27:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:52] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:27:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:52] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:27:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:52] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:27:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575132]: 127.0.0.1 - - [26/Mar/2026 17:27:53] "GET /api/xai/health HTTP/1.1" 200 -
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 5.764s CPU time, 2.4M memory peak, 0B memory swap peak.
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Starting Flask app...
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Starting on port 5000...
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Instance: UNKNOWN
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Loading dependencies...[Dashboard] Server starting on port 5000
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]:  * Serving Flask app 'dashboard'
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]:  * Debug mode: off
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]:  * Running on all addresses (0.0.0.0)
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]:  * Running on http://127.0.0.1:5000
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]:  * Running on http://104.236.102.57:5000
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: Press CTRL+C to quit
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:02] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:02] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Alpaca API connected
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Dependencies loaded
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:28:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:09] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:28:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:10] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:28:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:10] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:28:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:11] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:28:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:11] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/xai/health HTTP/1.1" 200 -
Mar 26 17:28:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:21] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:28:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:21] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 401 -
Mar 26 17:28:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:28] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:28:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:28] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 7.995s CPU time, 199.4M memory peak, 0B memory swap peak.
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Starting Flask app...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Starting on port 5000...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Instance: UNKNOWN
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Loading dependencies...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Server starting on port 5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Serving Flask app 'dashboard'
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Debug mode: off
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on all addresses (0.0.0.0)
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on http://127.0.0.1:5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on http://104.236.102.57:5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: Press CTRL+C to quit
Mar 26 17:35:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Alpaca API connected
Mar 26 17:35:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Dependencies loaded
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET / HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/positions HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/version HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/health_status HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /favicon.ico HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /favicon.ico HTTP/1.1" 404 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_weight_recommendations HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_performance HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=gate_profitability HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=blocked_counterfactuals_summary HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=exit_quality_summary HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_profitability HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=intelligence_recommendations HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:37:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:09] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 401 -
Mar 26 17:37:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:09] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:37:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:19] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 404 -
Mar 26 17:37:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:23] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 404 -
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 2.699s CPU time, 87.8M memory peak, 0B memory swap peak.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Starting Flask app...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Starting on port 5000...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Instance: UNKNOWN
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Loading dependencies...[Dashboard] Server starting on port 5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Serving Flask app 'dashboard'
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Debug mode: off
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on all addresses (0.0.0.0)
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on http://127.0.0.1:5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on http://104.236.102.57:5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: Press CTRL+C to quit
Mar 26 17:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Alpaca API connected
Mar 26 17:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Dependencies loaded
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:37:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:50] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:37:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:51] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:37:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:51] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/xai/health HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:38:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:03] "GET / HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/version HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/positions HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/health_status HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/signal_history HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /favicon.ico HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /favicon.ico HTTP/1.1" 404 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_performance HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_weight_recommendations HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=blocked_counterfactuals_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=exit_quality_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=gate_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=intelligence_recommendations HTTP/1.1" 200 -
Mar 26 17:38:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:53] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:38:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:53] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:38:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:54] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:38:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:54] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:38:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:54] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:38:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:55] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:38:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:55] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:38:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:55] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:39:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:39:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:39:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:39:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:39:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:39:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:20] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:20] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:20] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:20] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:20] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:39:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:21] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:39:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:21] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:39:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:22] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:39:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:22] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:39:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:23] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:39:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:23] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:24] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:24] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:24] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:24] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:24] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:39:25] "GET /api/xai/health HTTP/1.1" 200 -
```

