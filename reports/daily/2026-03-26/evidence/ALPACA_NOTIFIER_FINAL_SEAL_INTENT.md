# Alpaca Notifier Final Seal — Intent (CSA)

**UTC:** 2026-03-20

---

## Governance declaration

**CSA intent:** Notifier must be sealed against premature alerts with explicit baseline confirmation and two-phase execution.

**Requirements:**
1. **Two-phase execution:** Notifier must never emit notifications in the same run that mutates state
2. **0-trade baseline confirmation:** A governance-grade Telegram message confirming 0 trades counted is required
3. **CSA + SRE verification:** Both personas must explicitly verify the baseline before hands-off operation
4. **Controlled test:** A test notification must prove correctness without triggering real milestones
5. **Final seal:** Notifier must be sealed against future premature alerts

---

## Problem statement

**Current risk:**
- State mutations (watermark init, baseline confirmation) could occur in same run as threshold evaluation
- No explicit confirmation that 0-trade baseline is accurate
- No governance-grade verification before hands-off operation
- Risk of premature milestone notifications if state is reset or reinitialized

---

## Solution: Two-phase execution + baseline confirmation

**Two-phase execution:**
- **Phase 1:** State mutation (watermark init, baseline confirmation)
- **Phase 2:** Threshold evaluation (milestone notifications)
- **Invariant:** If state is mutated in this run, exit immediately without evaluating thresholds

**0-trade baseline confirmation:**
- After `counting_started_utc` is set and stable
- If `last_count == 0` AND `baseline_confirmed == false`:
  - Send governance-grade Telegram message
  - Set `baseline_confirmed = true`
  - Exit immediately (no threshold evaluation)

**CSA + SRE verification:**
- Both personas verify baseline accuracy
- Co-sign verification artifact
- Only then proceed to hands-off operation

---

## Benefits

1. **Prevents premature alerts:** State mutations never trigger notifications in same run
2. **Explicit baseline:** Governance-grade confirmation of 0-trade starting point
3. **Verification gate:** CSA + SRE must explicitly approve before hands-off
4. **Controlled testing:** Test notifications don't trigger real milestones
5. **Final seal:** Notifier is sealed against future premature alerts

---

*CSA — final seal intent declared; two-phase execution and baseline confirmation required.*
