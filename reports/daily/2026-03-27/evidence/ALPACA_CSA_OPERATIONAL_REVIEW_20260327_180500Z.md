# CSA review — Alpaca operational hardening (non-mutating)

**Mission:** ALPACA OPERATIONAL HARDENING REVIEW — CSA + MULTI-MODEL + SRE (NON-MUTATING)  
**Mode:** READ-ONLY conceptual review of **proposed** items. **No code, config, or engine changes** were made in producing this document.  
**TS:** `20260327_180500Z`  
**CSA authority:** Primary gate for mutation vs labeling/certification.

---

## Scope (strict)

Items reviewed **only**:

1. Enforce “droplet config is truth” via **runtime labeling + hash artifacts**.  
2. **Daily strict-completeness certificate** for decision-grade PnL.  
3. **Explicit zero-fee declaration** in PnL artifacts (Alpaca stock trading).  
4. **Meta-labeling scaffold** (shadow-only, no gating).  
5. **Exit-policy A/B evaluation in shadow** using existing v2 exit attribution.

---

## Definitions (CSA)

- **Trading behavior:** Any change to whether, when, or how orders are placed, modified, or canceled; or to live/shadow execution choice.  
- **Execution / sizing / exits:** Order type, quantity, timing, exit triggers, or displacement logic **in the live path**.  
- **Weaken a gate:** Lower thresholds, skip checks, or treat a certification artifact as a bypass for existing promotion or safety gates.  
- **New assumptions:** Assertions baked into **live** logic (e.g. “fees are always zero” used to size risk) without remaining overridable by ground truth.  
- **Labeling / certification / observability only:** Artifacts, hashes, certificates, declarations, and shadow-only analytics that **do not** feed live decisions unless a **separate** governed promotion step exists (out of scope here).

---

## Item-by-item CSA matrix

| # | Item | Trading behavior? | Execution / sizing / exits? | Weakens gate? | New assumptions (live)? | Labeling / cert / obs only? |
|---|------|-------------------|-----------------------------|---------------|---------------------------|-----------------------------|
| 1 | Droplet config truth: labels + hashes | **NO** *if* implementation only **emits** config identity (path, git SHA, file hashes) on each run or in sidecar artifacts; **YES** *if* “enforce” means **loading** a different config than today or **rewriting** runtime thresholds from artifacts. | **NO** *if* no order path reads the label for decisions. **YES** *if* engine branches on “approved hash.” | **NO** *if* hashes are not promotion inputs. **YES** *if* any script treats “hash match” as **auto-pass** for learning or live. | **NO** *if* purely documentary. **YES** *if* live code asserts single source without reconciliation to broker. | **YES** *when scoped to emitted metadata + stored artifacts only.* |
| 2 | Daily strict-completeness certificate | **NO** *if* output is **read-only** report (PASS/FAIL + counts) and **does not** block or alter `main.py`. **YES** *if* certificate is wired to **halt trading** or auto-mute entries without human/CSA process.* | **NO** *if* not consulted by executor.* | **NO** *if* strict gate semantics unchanged and cert is **parallel** to existing gates. **YES** *if* cert **replaces** or **short-circuits** `evaluate_completeness` or dashboard gate.* | **NO** *if* clearly labeled “certification snapshot,” not “ground truth for sizing.”* | **YES** *for decision-grade **labeling** of PnL cohorts; not a substitute for broker reconciliation.* |
| 3 | Zero-fee declaration in PnL artifacts | **NO** *if* text/field in **reports only** (e.g. “Alpaca US stock commissions assumed $0 for this artifact”).* **YES** *if* PnL **math** drops fee terms that actually exist in API for the same scope.* | **NO** | **NO** *if* does not change `MIN_EXEC_SCORE`, risk, or promotion.* | **YES** *as a **declared convention** for artifact readers* — acceptable **if** scope is **explicit** (e.g. stock vs options, regulatory fees, borrow). Mis-scoping = false certainty. | **YES** *as declaration; must stay consistent with Alpaca product facts for the traded instruments.* |
| 4 | Meta-labeling scaffold (shadow, no gating) | **NO** *if* labels written only to shadow paths / separate JSONL / telemetry buckets **never read** by `decide_and_execute` or exit submitters.* | **NO** | **NO** *if* no gating.* **YES** *if* any future wire promotes meta-labels into gates without new CSA review.* | **NO** *in live path today.* | **YES** *by definition if shadow-only and no gating.* |
| 5 | Exit-policy A/B in shadow (v2 exit attribution) | **NO** *if* purely **offline** or **parallel simulation** on stored `exit_attribution` / replay; no change to `exit_score_v2` weights or live thresholds.* **YES** *if* outputs **feed** live exit code or auto-tune exits without promotion.* | **NO** *if* live exit path unchanged.* | **NO** *if* shadow. **YES** *if* “winner” auto-applied.* | **NO** *if* clearly counterfactual.* | **YES** *as evaluation; implementation must not write into paths the engine reads on the next tick.* |

---

## CSA verdict

**CSA_APPROVE_AS_NON_MUTATING** — for all **five** items **as specified in scope**, **provided** implementation adheres to the italicized guardrails above:

- **Item 1:** Labels + hashes only; **no** alternate config load or “hash-gated” live branching.  
- **Item 2:** Certificate is **observability / certification** for PnL reporting; **no** automatic trading halt or gate replacement unless that is a **separate**, explicitly governed change (out of this hardening list).  
- **Item 3:** Declaration is **artifact metadata**, not a hidden fee model inside live risk. Scope must name **instrument class** (e.g. US equities) and residual fees if any.  
- **Item 4:** Shadow paths only; **zero** reads from hot path.  
- **Item 5:** Shadow / offline A/B only; **no** feedback into live `exit_score_v2` or order submission without a new promotion design.

**CSA_BLOCK** — for any implementation variant that:

- Loads config from artifacts in a way that **differs** from current droplet truth **without** a normal deploy process, or  
- Uses certificates or meta-labels as **automatic** promotion or **live** gate bypass, or  
- Rewrites exit or entry logic from A/B “winners” **inside** this initiative.

---

## Explicit statement

This CSA review **did not modify** code, config, thresholds, promotion, tuning, shadow/live routing, or any experiment. It **only** classifies the **proposed** items under non-mutation constraints.
