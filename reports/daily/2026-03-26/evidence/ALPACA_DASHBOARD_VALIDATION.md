# Alpaca Dashboard Validation (SRE + CSA)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20  
**Dashboard:** `dashboard.py` (served via Flask)

---

## Panel classification

### DECISION_GRADE (canonical data source)

| Panel | Endpoint | Source | Classification |
|-------|----------|--------|----------------|
| **Closed Trades** | `/api/stockbot/closed_trades` | `logs/exit_attribution.jsonl` (primary), `logs/attribution.jsonl` (fallback) | **DECISION_GRADE** — per MEMORY_BANK §5.5, exit_attribution is canonical closed-trade ledger |
| **Executive Summary (PnL)** | `/api/executive_summary` | `logs/exit_attribution.jsonl`, `logs/attribution.jsonl` | **DECISION_GRADE** — PnL metrics from authoritative sources |
| **SRE Health** | `/api/sre/health` | Process state, broker connectivity | **DECISION_GRADE** — operational status |

---

### INFORMATIONAL_ONLY (derived / computed)

| Panel | Endpoint | Source | Classification |
|-------|----------|--------|----------------|
| **Signal Performance** | `/api/telemetry/latest/computed?name=signal_performance` | `telemetry/YYYY-MM-DD/computed/*.json` | **INFORMATIONAL_ONLY** — computed artifacts; not real-time trade data |
| **Live vs Shadow** | `/api/telemetry/latest/computed?name=live_vs_shadow_pnl` | Telemetry bundles | **INFORMATIONAL_ONLY** — shadow counterfactuals |
| **Signal Review** | `/api/signal_history` | Recent signal processing events | **INFORMATIONAL_ONLY** — diagnostic feed |

---

## Validation against canonical data

### Exit counts

| Dashboard metric | Canonical source | Alignment |
|------------------|------------------|-----------|
| **Closed trades count** | `logs/exit_attribution.jsonl` (unique canonical keys) | **Aligned** — dashboard reads same file via `_load_stock_closed_trades()` |
| **Loss magnitude** | `exit_attribution.pnl` / `pnl_usd` | **Aligned** — dashboard displays PnL from exit records |
| **Exit timing** | `exit_attribution.exit_ts` / `timestamp` | **Aligned** — dashboard shows timestamps from exit file |

---

## Promotion activation timestamp alignment

| Check | Result |
|-------|--------|
| **Dashboard shows trades since activation** | **N/A** — dashboard does not filter by promotion timestamp; shows all closed trades |
| **Promotion state visible** | **N/A** — dashboard does not display diagnostic promotion metadata (expected; promotion is config-level, not UI feature) |

**Note:** Dashboard is **read-only** for trade data; promotion state lives in `state/alpaca_diagnostic_promotion.json` and is not displayed in UI.

---

## CSA classification

| Panel type | Use for decisions |
|------------|-------------------|
| **DECISION_GRADE** | **Yes** — use for PnL attribution, trade counts, exit reason analysis |
| **INFORMATIONAL_ONLY** | **No** — use for diagnostics, signal exploration, shadow comparisons only |

---

*SRE + CSA — dashboard panels classified; DECISION_GRADE panels align with canonical exit_attribution.jsonl.*
