# Wheel Strategy — Overview (External)

This document describes the **wheel strategy** as implemented in the system. It is intended for external sharing and does not reference internal code paths or secrets.

---

## What Is the Wheel?

The wheel is a two-phase options strategy:

1. **CSP (cash-secured put) phase:** Sell puts on a defined universe of underlyings. Collect premium. If the put expires worthless, the cycle ends and capital is freed.
2. **CC (covered call) phase:** If a put is assigned at expiration, the position becomes 100 shares per contract. The system then sells covered calls on those shares. When the call is assigned (shares called away), the cycle completes and capital returns to cash.

The goal is to generate premium income while being willing to own (and later sell via calls) the underlying at a chosen strike. The strategy is run automatically on a schedule; regime and market context may inform reporting but do not gate or block wheel entries.

---

## Universe Selection

- **Source:** A configurable universe of liquid underlyings — typically broad and sector ETFs (e.g. SPY, QQQ, DIA, IWM) plus sector ETFs (XLF, XLE, XLV, etc.) and selected high-liquidity names.
- **Diversification:** Certain sectors (e.g. Technology, Communication Services) can be excluded to reduce concentration. The system may rank candidates by liquidity, open interest, and optional intelligence scores, then take the top N (e.g. 10) for each run.
- **Filters:** Minimum average daily volume, minimum open interest on options, and maximum bid-ask spread are applied so that only tradeable, liquid names are considered. Earnings windows can be avoided (e.g. skip names with earnings within a few days).

---

## CSP Phase (Selling Puts)

- **Target DTE:** Puts are chosen in a short-dated window (e.g. 5–10 days to expiration) to collect premium and either expire or assign quickly.
- **Delta:** Puts are selected in a modest OTM range (e.g. delta around -0.20 to -0.30) so they are not deep OTM (low premium) nor too close to ATM (higher assignment risk).
- **Sizing:** A fixed fraction of total account equity is allocated to the wheel (e.g. 25%). Within that budget, each CSP is limited to a fraction of the wheel budget (e.g. 50% per position) so no single trade dominates. There is a cap on total concurrent CSP positions (e.g. 5) and a per-symbol limit (e.g. 2 positions per underlying).
- **Execution:** One contract per order; limit orders at a minimum credit (e.g. $0.05) to avoid crossing the spread. Orders are tagged with strategy and phase for reporting and idempotency.

---

## CC Phase (Covered Calls on Assigned Shares)

- **Trigger:** When a put is assigned, the system records the resulting shares. The CC phase only runs on underlyings that have assigned shares from the wheel.
- **Target DTE:** Calls are chosen in a short-to-mid range (e.g. 7–21 days to expiration).
- **Delta:** Calls are selected in a range (e.g. delta 0.20–0.30) — slightly OTM to collect premium while leaving upside.
- **Strike:** Only calls with strike at or above the cost basis of the assigned shares are considered, so the position is not sold below the effective purchase price.
- **Coverage:** The number of covered call contracts sold does not exceed the number of lots of 100 shares available from assignments.

---

## Risk and Governance

- **Capital:** The wheel uses a dedicated allocation (e.g. 25% of account equity). The rest of the capital is reserved for other strategies (e.g. equity). No strategy may use the other’s allocation.
- **Position limits:** Max concurrent CSP positions, max positions per symbol, and per-position size limits are enforced before sending orders.
- **No auto-exits:** The strategy does not automatically close positions early; it manages the CSP → assignment → CC flow. Early exits or adjustments would be separate processes or manual.
- **Reporting:** All wheel orders and key events (e.g. run start, capital check, contract selected, order submitted/filled, spot resolution) are logged and tagged for dashboards and post-trade analysis.

---

## Summary Table (Representative)

| Item | Typical setting |
|------|------------------|
| Wheel share of account | 25% of equity |
| Max concurrent CSP positions | 5 |
| Max positions per symbol | 2 |
| CSP DTE | 5–10 days |
| CSP delta | -0.30 to -0.20 |
| CC DTE | 7–21 days |
| CC delta | 0.20–0.30 |
| Per-position vs wheel budget | Up to 50% of wheel budget per CSP |

*Exact values are configurable and may differ by environment (e.g. paper vs live).*

---

*This document describes the wheel strategy as implemented for transparency and external sharing. It is not investment advice.*
