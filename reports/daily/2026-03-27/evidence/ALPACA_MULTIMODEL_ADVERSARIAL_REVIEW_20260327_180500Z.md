# Multi-model adversarial review — Alpaca operational hardening

**Mission:** Non-mutating operational hardening — adversarial pass  
**TS:** `20260327_180500Z`  
**Mode:** READ-ONLY; no repository mutations.

---

## Persona A — Quant adversary

**Thesis:** “Observability always leaks into optimization.”

| Item | Indirect bias to learning or PnL interpretation? | Mutation path? |
|------|--------------------------------------------------|----------------|
| 1 Config hash labels | Analysts may **only** run backtests on “certified” hashes → **selection bias** in which days get studied. **Does not change** realized PnL or model weights. | **No live mutation.** **Interpretation bias** possible if humans discard “non-certified” days without protocol. |
| 2 Strict-completeness daily cert | If cert **defines** “official” PnL for board slides, **incomplete** days might be **under-reported** or delayed — affects **narrative**, not fills. | **No live mutation** if cert is parallel. **Risk:** cert becomes sole **decision** input for capital (governance, not quant math). |
| 3 Zero-fee declaration | If readers **forget** regulatory/exchange fees or non-stock products, **expectancy** looks better than cash. | **No live mutation.** **Mis-labeling** if scope wrong (e.g. options). |
| 4 Meta-labeling shadow | Shadow features could **correlate** with future promoted features — **no causal** effect until wired. | **No mutation** while scaffold is read-isolated. |
| 5 Exit A/B shadow | Counterfactual exits can **cherry-pick** a policy that **would have** won in-sample → **overfitting** if later promoted without OOS. | **No live mutation** while shadow-only. **Mutation path exists only if** outputs drive live exits later. |

**Verdict:** **No trading or learning **experiment** mutation** under strict shadow + non-gating rules. **Interpretation and promotion hygiene** remain human/CSA responsibilities.

---

## Persona B — Ops adversary

**Thesis:** “Green certificates hide red reality.”

| Item | False confidence / masked failure? | Mutation path? |
|------|--------------------------------------|----------------|
| 1 Hashes | “Config OK” **≠** “markets OK” or “API OK.” | **None** to execution; **ops** could misread hash as end-to-end proof. |
| 2 Strict cert | PASS might **lag** bad data by one day; FAIL without paging could hide incidents if no runbook. | **None** to trading if no auto-halt; **masking** if alerts not tied to cert failures. |
| 3 Zero-fee | Declared zero fees **must** match product; otherwise **PnL reconciliation** disagrees with broker cash. | **None** to orders; **confidence** risk only. |
| 4 Meta-labels | Extra fields can **dilute** on-call attention if dashboards get noisy. | **None** if shadow bucket is filtered from prod alerts. |
| 5 Exit A/B | “Policy B won” in shadow **≠** safe live switch. | **None** while offline. |

**Verdict:** Operational **risk is epistemic**, not execution. Mitigation: runbooks + separate health checks (out of scope).

---

## Persona C — Governance adversary

**Thesis:** “Certification artifacts become implicit policy.”

| Item | Misuse to justify unsafe promotion? | Mutation path? |
|------|-------------------------------------|----------------|
| 1 | “Hash matched → promote.” | **Mutation path** if promotion checklist **replaces** strict gate with hash check. **Blocked** by CSA guardrails. |
| 2 | “Cert PASS → skip manual review.” | **Mutation path** if board treats cert as **only** gate. |
| 3 | “Zero fees → raise size.” | **Mutation path** if **risk** uses artifact text instead of `POSITION_SIZE_USD` / registry. |
| 4 | Meta-labels **leak** into `MIN_EXEC_SCORE` tuning. | **Mutation path** if wired without new CSA. |
| 5 | A/B winner **auto-merges** to exit weights. | **Mutation path** explicit; **forbidden** under this mission. |

**Verdict:** **Abuse is process-level**, not automatic from the items as **labeled-only**. **CSA_BLOCK** variants already capture auto-promotion and auto-gating.

---

## Reconciliation

| Question | Consensus |
|----------|-----------|
| Does any item **inherently** mutate the live experiment? | **NO**, when scoped as labeling / shadow / certification **without** feedback into hot path. |
| Is there a **credible mutation path**? | **YES** only via **future** wiring (hash-gated deploy, cert-driven halt, A/B → live weights). Those are **implementation anti-patterns** relative to this mission. |
| Disagreement | Quant stresses **selection bias** in analysis; Ops stresses **alert/certificate lag**; Governance stresses **checklist capture**. All agree: **no mandatory live mutation** from the five items **as specified**. |

---

## Adversarial conclusion

**No reviewer identified a necessary live mutation** from items **1–5** under the stated constraints. **Conditional:** implementation must preserve **read-path isolation** for shadow/meta-labels and **non-authoritative** status for certificates relative to existing strict gates and broker truth.
