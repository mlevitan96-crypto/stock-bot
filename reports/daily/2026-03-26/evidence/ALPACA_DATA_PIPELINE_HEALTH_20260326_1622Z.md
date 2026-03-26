# PHASE 1 — Live Pipeline Health (SRE)

**Timestamp:** 2026-03-26 ~16:22 UTC  
**Host:** Alpaca droplet (`ubuntu-s-1vcpu-2gb-nyc3-01-alpaca`)  
**Method:** SSH via `DropletClient` — `systemctl`, `journalctl`, `ps`.

---

## 1. Service status (active)

| Unit | State | Role |
|------|-------|------|
| `stock-bot.service` | **active (running)** | Trading loop (`systemd_start.sh` → bot) |
| `uw-flow-daemon.service` | **active (running)** | UW polling daemon |
| `stock-bot-dashboard.service` | **active (running)** | Dashboard Flask :5000 |

**Evidence:** `systemctl list-units --type=service --state=running` filtered — captured during certification run.

---

## 2. Process model

- **Trading:** `/root/stock-bot/venv/bin/python -u main.py` (PID observed ~1557624 at sample time).  
- **Execution “sidecar”:** **No separate systemd unit** named sidecar/supervisor for Alpaca execution. Order/fill logging is **in-process** with the trading stack (writes to `logs/orders.jsonl`). CSA wording “execution sidecar” should be interpreted as **orders.jsonl + broker truth**, not a distinct service, unless CSA revises the contract.

---

## 3. Related timers (integrity / audit)

| Timer | Service | Note |
|-------|---------|------|
| `alpaca-postclose-deepdive.timer` | `alpaca-postclose-deepdive.service` | Post-close job |
| `stock-bot-dashboard-audit.timer` | `stock-bot-dashboard-audit.service` | Dashboard audit |

No unit matching `*integrity*refresh*` beyond generic `fwupd-refresh` (unrelated).

---

## 4. Journal — last 500 lines per unit (excerpt)

Full pulls: `journalctl -u <unit> -n 500` executed for each of the three services. Below: **representative tail** (last ~15 lines each) proving fresh activity at audit time.

### `stock-bot.service` (excerpt)

```
Mar 26 16:22:35 ... DEBUG EXITS: Successfully closed and verified NIO ...
Mar 26 16:22:35 ... DEBUG EXITS: Closing UNH ...
Mar 26 16:22:38 ... DEBUG EXITS: Successfully closed and verified UNH ...
Mar 26 16:22:43 ... [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets
Mar 26 16:22:44 ... DEBUG EXITS: Successfully closed and verified RIVN ...
Mar 26 16:22:47 ... [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets
Mar 26 16:22:48 ... DEBUG EXITS: Closing SLB ...
Mar 26 16:22:50 ... DEBUG EXITS: Successfully closed and verified SLB ...
```

### `uw-flow-daemon.service` (excerpt)

```
Mar 26 16:22:50 ... uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "oi_change:NIO", ...}
... (repeated poll scheduling for NIO endpoints)
```

### `stock-bot-dashboard.service` (excerpt)

```
Mar 26 16:22:01 ... "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 16:22:01 ... [Dashboard] Warning: Failed to parse order timestamp: float() argument must be a string or a real number, not 'Timestamp'
Mar 26 16:22:01 ... "GET /api/health_status HTTP/1.1" 200 -
```

---

## 5. Verdict (Phase 1)

- **Trading + UW + dashboard:** **UP** at sample time.  
- **Gap vs checklist wording:** Dedicated **“execution sidecar”** and **“integrity refresh”** services are **not present as named units**; interpret per §2 and timers above.  
- **Operational noise:** Alpaca API retry warnings in journal; dashboard timestamp parse warnings (non-fatal to file appenders).

**Artifact cross-ref:** `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json` (log line counts on same host).
