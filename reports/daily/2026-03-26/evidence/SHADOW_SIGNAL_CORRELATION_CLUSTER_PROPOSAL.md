# Board Proposal — Shadow Signal Correlation & Cluster Analysis

## Objective

Analyze signal-level correlations at decision time, identify latent signal clusters and conditional dependence, and produce cluster-aware diagnostics and recommendations—**shadow-only, read-only**. No gating, no promotion, no weight changes.

---

## Purpose

- **Correlation at decision time:** Use backfilled ledger artifacts (signal_vectors, normalized_scores) to build per-trade signal matrices and compute correlations between signals.
- **Latent clusters:** Identify groups of signals that move together (e.g. hierarchical clustering with a correlation threshold).
- **Conditional dependence:** Understand which signals matter more conditional on outcome (win/loss) or cluster.
- **Output:** Cluster-aware diagnostics and recommendations for downstream use (e.g. weight sweep design, signal pruning). No automatic promotion or config changes.

---

## Scope & Constraints

- **Shadow-only:** All reads from `reports/shadow/backfill`; all writes under `reports/shadow/correlation` and `reports/shadow/clusters`.
- **Read-only** with respect to live/paper configs and ledgers outside shadow.
- **No gating, no promotion, no weight changes:** Analysis only; decisions remain with the board and daily promotion loop.
- **Prerequisite:** CSA verdict `TRUE_REPLAY_POSSIBLE` (backfilled ledgers with signal_vectors available).

---

## Pipeline (5 Phases)

1. **Extract signal matrices** from backfilled ledgers: one row per trade, columns = signal names (from signal_vectors / normalized_scores), optional outcome column (win/loss).
2. **Compute signal correlation matrices** (optionally conditioned on outcome).
3. **Identify signal clusters** (e.g. hierarchical clustering, threshold 0.7).
4. **Conditional importance analysis** per cluster using signal matrices and outcomes.
5. **Emit cluster-aware recommendations** (shadow-only report; no auto-actions).

---

## Board Review Questions

1. Does this analysis make sense for improving weight and signal decisions without changing behavior?
2. What could go wrong (e.g. overfitting to synthetic backfill, small sample)?
3. What is the best strategy to test moving forward: (A) run once on current backfill and review outputs, (B) run weekly as backfill grows, (C) run only when native emission replaces backfill, (D) other?

---

## Success Criteria

- Correlation and cluster outputs are interpretable and auditable.
- Recommendations are clearly marked as shadow-only and non-binding.
- No impact on live or paper configs.

---

## Board Action Requested

Review, agree on sensibility, and decide the **strategy to test** (A/B/C/D above). Upon agreement, CSA authorizes running the pipeline in shadow.
