# SRE review — Alpaca operational hardening (failure-mode focus)

**Mission:** Non-mutating operational hardening  
**TS:** `20260327_180500Z`  
**Mode:** READ-ONLY; no changes applied.

---

## Evaluation criteria

1. New **runtime dependencies** (services, network, order-critical path)?  
2. **Blast radius** on failure (cascade, crash loop, stale trading)?  
3. **Paging noise** / alert fatigue?  
4. **Droplet-sourced**, **idempotent** artifacts?

---

## Item-by-item SRE analysis

| # | Item | New runtime deps? | Blast radius on failure? | Alert / noise risk? | Droplet-sourced + idempotent? |
|---|------|-------------------|--------------------------|---------------------|-------------------------------|
| 1 | Config labeling + hash artifacts | **Low** — file reads, crypto hash (stdlib), optional git call. **Avoid** new network deps in hot loop. | **Low** if **emit-only**. **High** *if* mis-implemented as **fatal** preflight on every tick without timeout. | **Low** unless “hash mismatch” pages **every** cycle; use **daily** or **on-change** paging. | **Yes** if artifacts written under `reports/` or `state/` with deterministic inputs; reruns overwrite or version by date. |
| 2 | Daily strict-completeness certificate | **Medium** — reads large JSONL; CPU/IO. Should run **off critical path** (cron/timer), not inside order loop. | **Low** if batch job **fails closed** to “cert missing” not “trading stopped” (unless explicitly designed). | **Medium** — daily FAIL should page **once** per day with **dedupe** (see existing telegram failure pager patterns). | **Yes** — droplet logs/state; idempotent per **session date** output file. |
| 3 | Zero-fee declaration in artifacts | **None** — string field in markdown/json. | **None** | **None** | **Yes** |
| 4 | Meta-labeling scaffold (shadow) | **Low** — extra writes to shadow store. | **Low** if **separate** path; **Medium** if shared lock with hot writers → **contention**. | **Low** if shadow excluded from primary paging. | **Yes** with append-only or daily partition; avoid unbounded single file growth without rotation policy. |
| 5 | Exit A/B shadow eval | **Medium** — replay CPU, reads `exit_attribution`. | **Low** offline. **High** *only if* run on same host **starves** `main.py` — mitigate with **nice**, **cgroups**, or **off-peak** schedule. | **Low** for shadow; **high** if each A/B run pages. | **Yes** if inputs droplet logs and outputs dated artifacts. |

---

## Failure modes explicitly out of scope (but noted)

- Certificate job **OOM** on huge JSONL → mitigate with streaming / limits (implementation detail).  
- Hash computation **blocks** startup → run **async** or **post-start** label emission.

---

## SRE verdict

**SRE_APPROVE_NON_MUTATING** for items **1–5** as **proposed**, subject to:

- Heavy work (**2, 5**) runs **outside** the order hot path (scheduled batch).  
- **No** fatal coupling: trading engine **must not** depend on certificate freshness for each order.  
- Paging uses **dedupe** and **severity** (FAIL cert ≠ same as “broker down”).  
- Shadow/meta-label outputs use **separate** paths from locks read by `main.py`.

**SRE_BLOCK** if:

- Certificate or hash step is placed in **`run_once`** critical section without SLA bounds, or  
- Hash mismatch **stops** the process manager in a way that **leaves positions unmanaged**, or  
- Meta-labeling writes to **shared** state files the engine reads every cycle without versioning.

---

## Note

This review **did not** deploy or modify any service; it assesses **proposed** hardening only.
