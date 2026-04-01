# Decision matrix — template (Workstream J)

**Rule:** Every row ends in **KEEP**, **KILL**, **GATE**, or **SIZE**. Use **lever tags** where the primary decision is insufficient:

- **FLIP** — directional policy change  
- **DELAY_ENTRY** — timing / confirmation / staleness  
- **CHANGE_EXIT** — exit path or threshold change  

**DEFER** is allowed only with a **telemetry ID** (data gap owner + artifact).

| Entity | Grain (signal / exit / dir / regime) | Evidence table | Metric (primary) | Root cause (WHY×3) | Decision | Lever tags + detail | Confidence | Owner | Revisit date |
|--------|--------------------------------------|----------------|------------------|---------------------|----------|---------------------|------------|-------|--------------|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |

## Row examples (illustrative only — do not treat as findings)

| Entity | Grain | Decision | Lever detail |
|--------|-------|----------|--------------|
| Example: signal X | long + high vol | GATE | Require second agreeing signal |
| Example: exit Y | all | SIZE | Widen trail only when MFE > k |

---

## Post-board status

| Row id | Board outcome | Committed? | PR / config ref |
|--------|---------------|------------|-----------------|
| | | | |
