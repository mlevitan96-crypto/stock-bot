# Final governance day closeout — UW (Unusual Whales / flow data path)

**Bot:** UW (flow and enrichment pipeline; **not** a separate stock-trading engine)  
**Closeout generated (UTC):** 2026-03-25T18:12:00Z  
**Policy:** No application code changes; no shared execution or learning logic with Alpaca; no Alpaca trading or learning changes performed as part of this UW closeout.

---

## Phase 0 — Service model (SRE)

| Item | Value |
|------|--------|
| **UW-specific dashboard service** | **None identified** in this repository. UW does not have its own systemd unit parallel to `stock-bot-dashboard.service`. |
| **UW runtime unit (data pipeline)** | `uw-flow-daemon.service` — **enabled** and **active** on the production droplet at verification time (separate from the Flask dashboard). |
| **How UW data reaches operators** | Through the **stock-bot dashboard** and cached artifacts when that dashboard and cache layers are healthy — there is **no independent UW Flask dashboard** to restart under this model. |
| **Hot-reload** | **No** for the daemon under systemd (standard process model). |

---

## Phase 1 — Dashboard restart (required)

| Item | Value |
|------|--------|
| **What was restarted for UW** | **Nothing UW-specific.** UW has **no** dedicated dashboard process. |
| **What was done for the shared operator UI** | The **Alpaca** closeout performed **`systemctl restart stock-bot-dashboard`** once (see `FINAL_GOVERNANCE_DAY_CLOSEOUT_ALPACA_20260325_180743Z.md`). That is the only dashboard restart applicable to UW visibility today. |
| **What was NOT restarted** | **`uw-flow-daemon.service`** — it is **not** the dashboard; restarting it would alter the UW data pipeline (out of scope for “dashboard only”). **Trading and learning** were also not restarted. |

---

## Phase 2 — Post-restart verification (CSA)

All dashboard checks are **shared** with the Alpaca operator surface (same Flask app on port 5000). For UW in isolation:

| Check | Result |
|-------|--------|
| **System Health / `/api/dashboard/data_integrity`** | **Not available on production** (HTTP **404** on droplet) — same finding as Alpaca closeout; UW-specific telemetry merge **cannot** be validated on this host until deploy. |
| **UI: Telemetry merged into System Health** | **Not verified** on production (stale dashboard build). |
| **Trade tables / strict completeness** | **Not applicable** to UW as a separate bot; UW does not own equity closed-trade strict badges. |

---

## Phase 3 — Readiness confirmation (CSA)

| Domain | Status | Notes |
|--------|--------|--------|
| **Trading (UW)** | **N/A** — UW path is not the Alpaca execution engine. |
| **UW pipeline** | **ACTIVE** | `uw-flow-daemon.service` reported **active**; no restart performed here. |
| **Learning (UW-specific)** | **N/A / not dashboard-armed** | No separate UW learning arm via this dashboard; any learning gates remain Alpaca-scope unless separately documented. |

---

## Phase 4 — Summary (mandatory answers)

1. **What was restarted and why**  
   **No UW dashboard restart** (no such service). The **stock-bot dashboard** was restarted once for operator UI activation (shared listener); see Alpaca artifact for timestamp.

2. **What was NOT restarted and why**  
   **`uw-flow-daemon.service`** (pipeline, not dashboard), **Alpaca trading service**, **schedulers/timers**, **learning** — to stay within “dashboard only” and avoid cross-bot execution changes.

3. **Dashboard verification results**  
   **Same production gap as Alpaca:** integrity API **missing** (404); merged System Health / strict trade truthfulness **not** live on droplet `dashboard.py` yet.

4. **Current trading status**  
   **N/A** for UW bot (UW is not the trading executor).

5. **Current learning status**  
   **N/A** for UW-isolated dashboard learning arm; Alpaca learning visibility **BLOCKED** on dashboard until deploy (see Alpaca closeout).

6. **Exact remaining condition (if any)**  
   **Deploy** rationalized `dashboard.py` to production, then re-verify `/api/dashboard/data_integrity` and operator UI; keep **`uw-flow-daemon`** stable unless a separate SRE change window is opened.

7. **No further action required today — or list**  
   **Further action required:** same as Alpaca artifact for the **shared dashboard** (deploy + reconcile duplicate dashboard processes). **No additional UW-only dashboard restart** is possible until a dedicated UW dashboard service exists.

---

*Independence note: this UW closeout did not modify, restart, or reconfigure Alpaca trading or learning logic; it only records UW’s lack of a standalone dashboard service and the shared UI verification outcome.*
