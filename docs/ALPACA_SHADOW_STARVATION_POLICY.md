# Alpaca Shadow Starvation Policy

**Authority:** `docs/ALPACA_GOVERNANCE_CONTEXT.md` Section A5 (Shadow Learning Health) and Section C4.  
**Scope:** Alpaca-only. Defines what “shadow starvation” is and how the system responds (WARN vs FAIL).

---

## 1. Definition: shadow starvation

**Shadow starvation** occurs when:

- There is at least one **blocked trade** in a given period (e.g. a calendar day or a run), and
- There is **no** corresponding **shadow candidate** (or equivalent shadow decision) for that same opportunity in the shadow stream.

In other words: the system blocked a live trade (so an “opportunity” existed from scoring’s perspective) but the shadow learning path did not record a hypothetical candidate for that symbol/cycle. That prevents shadow from learning from that missed opportunity and degrades blocked-winner forensics and A/B comparison.

**Not starvation:**

- Zero blocked trades and zero shadow candidates (no opportunity).
- Shadow experiments disabled by config (no shadow stream expected).
- Shadow stream present and has shadow_candidate / shadow_variant_decision for the same symbols that were blocked (learning path is fed).

---

## 2. Policy choice: WARN (no automatic FAIL)

**Decision:** Treat shadow starvation as **WARN** only. Do **not** fail the pipeline or block deployment when starvation is detected.

**Rationale:**

- Shadow rollout may be partial (e.g. SHADOW_EXPERIMENTS_ENABLED off, or only a subset of cycles emitting shadow events). A hard FAIL would block production despite acceptable operation.
- The primary goal is **observability**: surface “blocked but no shadow candidate” so operators and governance can fix config or code (e.g. enable shadow for that path, or add shadow_candidate emission where blocked_trade is logged). Escalation to FAIL can be a future governance decision after shadow is fully rolled out and validated.
- Prefer documentation and diagnostics over hard FAIL unless clearly warranted (per governance constraints).

**Conditional FAIL (optional, not default):**

- If governance later decides that “shadow must learn from every blocked trade,” a **conditional FAIL** could be introduced only when: (1) shadow experiments are enabled, and (2) the run is explicitly marked as shadow-auditable (e.g. an env or runbook flag). That is **not** implemented by default; it would require explicit approval and a code change.

---

## 3. Operational response

- **Daily / EOD:** Run the optional diagnostic (see below). If the report shows “blocked_trades > 0 and shadow_candidates == 0” (or equivalent) for the period, treat as **WARN**: log in daily report, mention in governance review, and consider enabling or fixing shadow emission for that path.
- **Dashboard / reports:** Shadow audit report (`reports/_daily_review_tools/generate_shadow_audit.py`) already compares real vs shadow; a starvation metric or sentence can be added there (e.g. “Shadow starvation: N blocks with no shadow candidate today”) as informational only.

---

## 4. Optional diagnostic

- **Script:** `scripts/diagnose_shadow_starvation.py` (proposed). Reads `state/blocked_trades.jsonl` and `logs/shadow.jsonl` for a given date (or last N hours); counts blocked_trades and shadow_candidate (or shadow_variant_decision) per symbol/interval; prints a short summary and sets exit code 0 (WARN only) or optionally exit code 1 only if `--strict` and starvation detected (for use only after approval).
- **Enforcement:** Do **not** wire this as a mandatory gate in CI or EOD without explicit approval. Default is diagnostic-only (exit 0, report to stdout/file).

---

## 5. References

- Shadow events: `logs/shadow.jsonl`; producers in `telemetry/shadow_experiments.py`, `shadow/shadow_pnl_engine.py`.
- Blocked trades: `state/blocked_trades.jsonl`; `main.log_blocked_trade()`.
- Audit: `reports/_daily_review_tools/generate_shadow_audit.py`.
- Governance: `docs/ALPACA_GOVERNANCE_CONTEXT.md` Section C4.
