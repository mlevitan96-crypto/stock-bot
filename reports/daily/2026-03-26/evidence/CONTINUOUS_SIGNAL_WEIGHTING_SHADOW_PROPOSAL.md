# Board Proposal — Continuous Signal Weighting & Bulk Shadow Optimization

## Objective

Accelerate profitability by replacing binary signal gating with continuous, weighted signal contributions, enabling safe bulk optimization in a shadow replay environment and faster, higher-confidence promotions to paper.

---

## Problem Statement (Why Change Is Required)

Current signal behavior includes implicit or explicit on/off gating, which:

- Creates brittle cliff effects
- Masks interaction dynamics between signals
- Slows learning by discarding partial information
- Makes bulk testing misleading or unsafe

As the system matures, binary gating is now a bottleneck to profitability.

---

## Proposed Path Forward (Core Idea)

### 1. Move All Alpha Signals to Continuous Weighting

- Every alpha signal contributes continuously to a composite score
- No alpha signal may veto trades outright
- Signals are normalized to a common scale (e.g. [-1, +1])
- Relative weights, not gates, determine influence

**Safety constraints** (max loss, exposure caps, kill switches) remain binary and unchanged.

### 2. Introduce a Shadow Replay Lab for Bulk Optimization

Create a sealed, read-only shadow review area that:

- Replays historical ledgers deterministically
- Sweeps signal weights and interaction modifiers (100–1000+ iterations)
- Never touches live or paper configs
- Produces ranked candidates, not auto-promotions

This lab answers: *"What weight configurations are most likely to improve expectancy and stability?"*

### 3. Promote Only Shortlisted Candidates to the Live Loop

- Bulk results feed into the existing daily promotion quota
- One candidate at a time is promoted to paper
- Guardrails, CSA verdicts, and revert logic remain intact
- Live exposure is used only for confirmation

---

## Expected Benefits

- Faster learning without destabilizing live systems
- Smooth optimization instead of cliff-driven behavior
- Clear visibility into signal interactions
- Higher confidence promotions
- Reduced infra cost spent "waiting to see"

---

## CSA Review & Board Decision Requirements

The Board (CSA, Quant, Risk, SRE, Adversarial) must:

1. **Agree** that alpha signals should be weighted, not gated
2. **Approve** the creation of a shadow replay lab as read-only
3. **Authorize** bulk weight sweeps in shadow only
4. **Confirm** that live promotions remain single-step, guarded, and reversible
5. **Direct** Cursor to proceed with implementation in the shadow review area

- No deferral to "more data."
- No architecture expansion beyond the shadow lab.
- Decision required.

---

## Immediate Next Steps Upon Approval

- Inventory and classify existing signal gates (alpha vs safety)
- Convert alpha gates to weighted contributors
- Define canonical signal schema (normalized output + weight)
- Stand up the shadow replay harness
- Begin bulk weight optimization runs
- Feed top candidates into the daily promotion loop

---

## Success Criteria

- Shadow lab produces ranked signal-weight configurations
- Live promotions become higher-confidence and less volatile
- Profitability convergence accelerates without increased tail risk

---

## Board Action Requested

Review, debate, and reach consensus on this path forward.

Upon agreement, instruct Cursor to proceed immediately in the shadow review area.

*This is the fastest safe path to improving signal quality and profitability without breaking what already works.*
