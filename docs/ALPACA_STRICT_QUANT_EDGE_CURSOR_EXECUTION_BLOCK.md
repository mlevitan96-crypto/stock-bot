# Actionable strict quant edge analysis — Cursor execution block

**Purpose:** Turn strict-scope data into **decision-grade** output with explicit levers. This doc is the **procedure**; each run produces timestamped artifacts under `reports/`.

---

## Goal

Produce evidence-backed insights from **strict-scope live trades**: WHY wins/losses, HOW to act (**KILL, GATE, FLIP, SIZE, CHANGE_EXIT**, **DELAY_ENTRY**).

---

## Authoritative inputs

- Strict cohort: `telemetry.alpaca_strict_completeness_gate.evaluate_completeness` and `scripts/audit/export_strict_quant_edge_review_cohort.py`.
- Logs: `logs/run.jsonl`, `logs/exit_attribution.jsonl`, `logs/strict_backfill_exit_attribution.jsonl` (if present), `logs/orders.jsonl`, unified events as per gate.
- **Gate state** must appear in every output header.

---

## Step 1 — Ensure cohort visibility

On droplet (or `TRADING_BOT_ROOT`):

```bash
cd /root/stock-bot && git pull origin main
PYTHONPATH=. python3 scripts/audit/run_strict_quant_edge_analysis.py --root /root/stock-bot
```

**Confirm artifacts:**

- `reports/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_<timestamp>.md`
- `reports/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_<timestamp>.json`

**Certification:**

| `LEARNING_STATUS` | Use of this analysis |
|-------------------|----------------------|
| **ARMED** | Learning-grade; safe input to promotion-style decisions (with usual governance). |
| **BLOCKED** | **Review-only, not promotable.** Forensics and planning only until gate re-arms. |

---

## Step 2 — Extract actionable sections

From the generated Markdown/JSON, copy forward explicitly:

1. PnL headline and expectancy (sum, avg, median, win rate).  
2. Long vs short performance.  
3. Exit reason / decay bucket performance.  
4. Entry and exit regime slices.  
5. Best and worst trades (ids + reasons).  
6. `suggested_actions` from the tool (heuristic seeds only).

---

## Step 3 — WHY analysis (mandatory)

For **each** negative or underperforming slice (negative avg PnL with meaningful n, or structural gap):

| Level | Question |
|-------|----------|
| WHY 1 | What happened in the data (symptom)? |
| WHY 2 | What mechanism links that to PnL? |
| WHY 3 | Why does the system allow it (threshold, missing telemetry, regime blind spot)? |
| **HOW** | Exactly one primary lever: **KILL / GATE / FLIP / SIZE / CHANGE_EXIT / DELAY_ENTRY** (+ secondary if needed). |

No slice is “done” without **HOW**.

---

## Step 4 — Directional decision

Using long vs short table:

- Decide: **gate shorts**, **flip** policy, **resize** short book, **remove** (KILL) short path, or **KEEP** with monitoring.  
- Document **decision + rationale** in the board packet.

---

## Step 5 — Exit policy review

- List exit buckets with **negative expectancy** (n ≥ threshold, e.g. 5–8).  
- For each: **KEEP** (monitor), **CHANGE** (threshold / rule change), or **REMOVE** (kill sub-rule).  
- Tie **CHANGE** to measurable thresholds (V2 score bands, time-exit, flow_reversal interaction).

---

## Step 6 — Regime and telemetry gaps

For **unknown** or **underperforming** regime buckets:

| Classification | Meaning |
|----------------|---------|
| **Data gap** | Need new or repaired telemetry (entry/exit regime stamp). |
| **Structural regime blindness** | Model does not distinguish states; need regime feature or gate. |
| **Gating opportunity** | Stand aside or size down when bucket is toxic. |

---

## Step 7 — Decision matrix

Produce a table (Markdown + JSON) with rows at grain:

**signal / composite family · direction · exit type (normalized) · regime bucket → action (KEEP, KILL, GATE, FLIP, SIZE).**

Use `docs/ALPACA_QUANT_EDGE_REVIEW_DECISION_MATRIX_TEMPLATE.md` as the skeleton.

---

## Step 8 — Certification check

If **BLOCKED**:

- **Do not** promote config/strategy changes solely on this packet.  
- List **prerequisites to re-arm**: e.g. strict chain backfill, live `exit_intent`/metadata fixes, integrity cycle green.  
- Re-run Step 1 when **ARMED** and regenerate decision packet.

---

## Step 9 — Next expansions (recommended)

- **Complete-only** cohort filter (`trades_complete` ids only).  
- **Blocked** trade opportunity cost (`blocked_trades.jsonl`).  
- **Bar-based MFE/MAE**.  
- **Signal agreement / interaction** from entry snapshots.  
- **Latency and slippage** from intent vs fill vs mid.

---

## Definition of done

- [ ] Major loss drivers have WHY×3 + HOW.  
- [ ] Directional and exit policy decisions **written**.  
- [ ] Decision matrix committed for the run.  
- [ ] Gate status and **confidence** stated explicitly.  
- [ ] If BLOCKED: promotion path deferred; re-arm steps listed.

---

## Related

- `docs/ALPACA_MASSIVE_QUANT_EDGE_REVIEW_FRAMEWORK.md`  
- `scripts/audit/run_strict_quant_edge_analysis.py`  
- `scripts/audit/export_strict_quant_edge_review_cohort.py`
