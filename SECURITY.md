# SECURITY

This project is a live trading system. Treat **all network-exposed surfaces** as hostile by default.

## Dashboard: HTTP Basic Authentication (temporary, mandatory)

The STOCK-BOT dashboard (`dashboard.py`, port 5000) is protected by **HTTP Basic Authentication**.

- **Credentials** come from environment variables (loaded from `/root/stock-bot/.env` on the droplet):
  - `DASHBOARD_USER`
  - `DASHBOARD_PASS`
- **Scope**: Auth is enforced **globally** (HTML + every API route) before any content is served.
- **Fail-closed**: If `DASHBOARD_USER` or `DASHBOARD_PASS` is missing/empty, the dashboard **refuses to start** with a contract-driven error.

### How it works

- A client must send an `Authorization: Basic ...` header on every request.
- If missing/invalid, the dashboard returns `401 Unauthorized` with `WWW-Authenticate: Basic realm="stock-bot-dashboard"`.

### How to rotate the password

1. Update `/root/stock-bot/.env` on the droplet:
   - Set `DASHBOARD_PASS` to a new strong password.
2. Restart the dashboard (or the supervisor/service).

Rotation is immediate after restart. No code change required.

### How to disable later (when replaced by stronger auth)

This Basic Auth layer is intentionally **small and reversible**.

When you deploy a stronger auth layer (reverse proxy auth, VPN, SSO, etc.), remove the auth gate by reverting the change that introduced:
- the `before_request` Basic Auth enforcement in `dashboard.py`
- the proxy Basic Auth enforcement in `dashboard_proxy.py` (if you are using the proxy)

Do **not** “disable” by leaving credentials blank: the dashboard is designed to **fail closed**.

