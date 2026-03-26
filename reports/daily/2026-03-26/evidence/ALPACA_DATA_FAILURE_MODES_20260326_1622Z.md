# PHASE 5 — Failure Mode Search (SRE)

**Timestamp:** 2026-03-26 ~16:23 UTC  
**Sources:** `journalctl` (trading + dashboard), tail of `logs/cache_enrichment.log` on droplet, grep patterns for failures.

---

## 1. Observed patterns (evidence-backed)

| Symptom | Source | Severity |
|---------|--------|----------|
| **Alpaca API retry / backoff** | `stock-bot` journal: `[CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets` | **Medium** — transient broker latency; not a silent drop by itself. |
| **UW cache atomic rename failure** | `cache_enrichment.log`: `No such file or directory: 'data/uw_flow_cache.json.tmp' -> 'data/uw_flow_cache.json'` | **Medium** — can cause stale UW cache / race; **not** Alpaca fill logging directly but affects signal path. |
| **Scanner / TLS garbage on dashboard port** | `cache_enrichment.log`: `code 400, message Bad request version` | **Low** — internet noise hitting Flask. |
| **State vs broker drift warning** | `cache_enrichment.log`: `Positions in Alpaca but not in local state: {'LCID', 'HOOD', 'META'}` | **High for reconciliation** — indicates **partial desync** between broker and local state (risk for order/position attribution if prolonged). |
| **Dashboard order timestamp parse** | `stock-bot-dashboard` journal: `Failed to parse order timestamp ... not 'Timestamp'` | **Low for JSONL appenders** — **UI / API path** quality issue; may hide freshness in dashboard. |

---

## 2. Not evidenced in sampled logs

- Explicit “dropped event” counters  
- Kafka/stream backpressure (no such stack in this deployment)  
- Alpaca HTTP **429** in the captured tail (still possible outside window)

---

## 3. Silent exception risk (code-level note, not runtime proof)

- Telemetry emitters use defensive patterns in places; **absence of errors in tail does not prove absence of swallowed exceptions** elsewhere. Adversarial review expands this.

---

## 4. Phase 5 verdict

**FAIL soft:** No smoking gun of JSONL writer crash in sample, but **broker retries**, **UW cache rename errors**, and **position reconciliation warnings** show the system is **not “quietly perfect.”** Pair with Phase 2–3 quantitative gaps.
