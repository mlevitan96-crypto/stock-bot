# Alpaca Diagnostic Promotion — Selected Rule (Quant Officer)

**Source audit:** [ALPACA_FULL_PNL_ATTRIBUTION_AUDIT.md](./ALPACA_FULL_PNL_ATTRIBUTION_AUDIT.md)

---

## Audit signal

- **`hold`** dominated exit-side reason proxy (~94% of rows by `exit_reason_code`).
- **`intel_deterioration`** was the main non-hold bucket (~6%) — the lever that fires when **composite / intel decays** (`score_det` path in `exit_score_v2`).

---

## Selected rule (one)

| Field | Value |
|-------|--------|
| **Name** | **SCORE_DETERIORATION_EMPHASIS** |
| **Type** | **(A) Loss-limiting exit** — earlier / stronger response to **entry vs now composite decay** (same family as `intel_deterioration` in `compute_exit_score_v2`) |
| **Mechanism** | Increase **`score_deterioration`** weight in the **v2 exit composite**; offset by a small reduction in **`flow_deterioration`** so total weight remains normalized |

---

## Hypothesis (concrete)

> Raising **`score_deterioration`** weight increases **`exit_score`** when `entry_v2_score` &gt; `now_v2_score`, which should increase **`intel_deterioration`**-class exits (per existing reason ladder) **vs** passive **`hold`**, potentially **cutting average loss** on decaying setups and making **score decay** more visible in `attribution_components`.

---

## Why this rule

| Criterion | Fit |
|-----------|-----|
| Observable with scoped data | **Yes** — `exit_reason_code`, `v2_exit_score`, components in `exit_attribution.jsonl` |
| Minimal interaction | **Yes** — single overlay vector in `config/tuning/active.json`; no entry gate changes |
| Clear “what should change” | **Yes** — more weight on **composite decay** vs **flow delta** in the same exit function |

---

## Tag

**`PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS`**

---

*Quant Officer — one diagnostic rule only; all other levers remain SHADOW / baseline unless separately promoted.*
