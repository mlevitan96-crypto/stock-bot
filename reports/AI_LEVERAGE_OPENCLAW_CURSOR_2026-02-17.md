# AI Leverage: OpenClaw (Clawdbot/Moltbot) and Cursor

**Date:** 2026-02-17  
**Goal:** Use OpenClaw and Cursor as effectively as possible for profitability and resiliency.

---

## Naming

**OpenClaw, Clawdbot, and Moltbot are the same product** — different names for the same AI agent/tool. The CLI is invoked as `clawdbot` (or `moltbot`); e.g. `clawdbot agent --session-id ... --message <prompt>`. This document uses **OpenClaw** as the product name and **Clawdbot** when referring to the executable or code (e.g. `CLAWDBOT_SESSION_ID`, `run_clawdbot_prompt`).

Separately, the **`moltbot/` directory in this repo** is the “Learning & Engineering Governor” *workflow* — in-repo Python code (orchestrator, sentinel, board, etc.) that produces reports. It is *not* the OpenClaw product; it’s a pipeline named after it. It does not call OpenClaw; it’s rule-based. So: **product** = OpenClaw (Clawdbot/Moltbot); **in-repo workflow** = `moltbot/` package.

---

## 1. Current Use

### OpenClaw (product — same as Clawdbot/Moltbot)
- **Where:** `board/eod/run_stock_quant_officer_eod.py` — single call per EOD.
- **What:** Builds one large prompt (EOD bundle summary, wheel state, watchlists, rolling windows, root-cause summary). Calls OpenClaw via `clawdbot agent --session-id stock_quant_eod_<date> --message <prompt>`. Parses JSON for `wheel_actions`, `recommended_fixes`, memo.
- **Output:** `board/eod/out/<date>/eod_board.json`, `eod_board.md`, `reports/wheel_actions_<date>.json`.
- **Cron:** 21:30 UTC weekdays on droplet (EOD confirmation). Requires `clawdbot` (or `moltbot`) in PATH on droplet; otherwise use `--dry-run` (stub output).
- **Gap:** OpenClaw is used only once per day, only in EOD. No pre-market brief, no causal “why” deep-dive, no synthesis of the in-repo Molt workflow reports by OpenClaw.

### In-repo Molt workflow (`moltbot/` package)
- **Where:** `moltbot/` — orchestrator, sentinel, board (signal_advocate, risk_auditor, counterfactual_analyst, governance_chair), promotion_discipline, memory_evolution.
- **What:** Rule-based (no LLM). Reads daily pack (attribution, profitability, blocked trades, regime). Produces LEARNING_STATUS, ENGINEERING_HEALTH, PROMOTION_PROPOSAL or REJECTION, PROMOTION_DISCIPLINE, MEMORY_BANK_CHANGE_PROPOSAL. Does *not* call OpenClaw.
- **Automation:** `scripts/run_molt_workflow.py`; `scripts/run_molt_on_droplet.sh`. Cron 21:35 UTC weekdays (post-EOD).
- **Gap:** Proposals are consumed only when someone (or Cursor) explicitly looks at the reports.

### Cursor
- **Where:** You drive Cursor with MEMORY_BANK, .cursorrules, and repo context. Cursor implements code/config; the Molt workflow and OpenClaw produce artifacts only.
- **Gap:** No explicit “daily AI checklist” tying Cursor to those outputs; MEMORY_BANK_CHANGE_PROPOSAL and PROMOTION_PROPOSAL are easy to leave unapplied.

---

## 2. Recommendations (Profitability & Resiliency)

### 2.1 OpenClaw — Use More Surfaces
- **Pre-market brief (new):** Once per morning, build a short prompt: regime, yesterday P&L, open positions, last blocked reasons, wheel open CSPs. Call OpenClaw (clawdbot); output 3–5 bullet “today’s focus” (e.g. “Watch XLE CSP expiry; avoid new longs in Y sector”). Run locally or on droplet before market open; no need to change trading code.
- **Weekly profitability post-mortem:** Once per week, feed OpenClaw: 5-day attribution, exit reasons, blocked_trades summary, regime history. Ask for “top 3 causes of P&L drag and 3 concrete, testable changes.” Output to `reports/WEEKLY_AI_POSTMORTEM_<date>.md`. Cursor or human can turn recommendations into config/experiments.
- **Molt workflow → OpenClaw synthesis:** After the in-repo Molt workflow runs, call OpenClaw with LEARNING_STATUS + ENGINEERING_HEALTH + PROMOTION_PROPOSAL/REJECTION (or paths). Prompt: “Synthesize into 5 bullet actions for the operator and 1 MEMORY_BANK change to consider.” Write to `reports/MOLT_OPENCLAW_SYNTHESIS_<date>.md`. Ensures Molt workflow output is summarized and actionable.

### 2.2 In-repo Molt workflow — Smarter Without Breaking NO-APPLY
- **Optional OpenClaw referee:** Add a step that calls OpenClaw with the same inputs as the learning board plus the board’s verdict. Prompt: “Do you agree or dissent? One paragraph.” Append to PROMOTION_PROPOSAL or REJECTION as “OpenClaw referee note.” Keeps the Molt workflow rule-based and NO-APPLY; adds a second opinion from the same product (OpenClaw).
- **Memory Bank proposals → one-click for Cursor:** Ensure MEMORY_BANK_CHANGE_PROPOSAL_<date>.md is structured (e.g. “## Proposed addition: …”, “## Proposed deletion: …”). Add a Cursor rule or a small script: “When user says ‘apply memory bank proposal for <date>’, read reports/MEMORY_BANK_CHANGE_PROPOSAL_<date>.md and apply only approved sections to MEMORY_BANK.md.” Cursor does the edit; human still approves.

### 2.3 Cursor — Tighten the Loop
- **Daily AI checklist in MEMORY_BANK or .cursorrules:** Add a short section: “After EOD + Molt workflow run, Cursor should consider: (1) reports/LEARNING_STATUS_<today>.md, (2) reports/ENGINEERING_HEALTH_<today>.md, (3) reports/PROMOTION_PROPOSAL_<today>.md or REJECTION_*, (4) reports/MEMORY_BANK_CHANGE_PROPOSAL_<today>.md. If user asks ‘what should I do next?’, summarize these and suggest applying proposals or running experiments.”
- **Resiliency review trigger:** When user says “resiliency check” or “why did we lose today”, Cursor loads EOD bundle + BLOCKED_TRADE_INTEL + EXIT_JOIN_HEALTH + ENGINEERING_HEALTH and summarizes. Optionally call OpenClaw with the same set for a narrative “why” and append to a small `reports/RESILIENCE_AI_<date>.md`.

### 2.4 Droplet / Cron Resiliency
- **OpenClaw on droplet:** If EOD runs on droplet and should use OpenClaw (not --dry-run), ensure the product’s CLI is in PATH (`clawdbot` or `moltbot` / `npx clawdbot` or `npx moltbot`) and CLAWDBOT_SESSION_ID is set. Document in MEMORY_BANK: “EOD cron uses OpenClaw (clawdbot); if missing, EOD uses stub (--dry-run). Install on droplet for full AI EOD.”
- **Molt workflow run status:** Have `run_molt_on_droplet.sh` write `state/molt_last_run.json` with { "date": "<date>", "exit_code": 0, "timestamp_utc": "..." }. Dashboard or a small “AI status” panel can show “Molt last run: <date>” so you see at a glance if it’s current.

---

## 3. Summary Table

| Component | Current use | Add for profitability / resiliency |
|-----------|-------------|------------------------------------|
| **OpenClaw** (same product as Clawdbot/Moltbot) | 1×/day EOD (Stock Quant) | Pre-market brief; weekly post-mortem; Molt-workflow synthesis |
| **In-repo Molt workflow** (`moltbot/` package) | Rule-based board + proposals | Optional OpenClaw referee; structured MEMORY_BANK proposals for Cursor |
| **Cursor** | Code + config + MEMORY_BANK | Daily checklist tied to Molt workflow + OpenClaw outputs; “apply proposal” flow; resiliency summary |

---

## 4. Next Steps (Pick What Fits First)

1. **Low effort:** Add “Daily AI checklist” to MEMORY_BANK (or .cursorrules) so Cursor considers LEARNING_STATUS, ENGINEERING_HEALTH, PROMOTION_PROPOSAL, MEMORY_BANK_CHANGE_PROPOSAL when user asks “what’s next?”
2. **Medium effort:** Implement “Molt workflow → OpenClaw synthesis” (one extra OpenClaw call after the Molt workflow; write MOLT_OPENCLAW_SYNTHESIS_<date>.md).
3. **Medium effort:** Add `state/molt_last_run.json` in run_molt_on_droplet.sh and (optional) show “Molt last run” on dashboard or in a small status script.
4. **Higher value:** Pre-market brief script (prompt + OpenClaw call + 5 bullets to file or Slack/local).
5. **Document:** In MEMORY_BANK, one short subsection: “OpenClaw (Clawdbot/Moltbot — same product) is used in EOD; for full AI EOD on droplet, clawdbot (or moltbot) must be in PATH. The in-repo Molt workflow runs 21:35 UTC; artifacts are in reports/. Cursor should consider those reports and MEMORY_BANK_CHANGE_PROPOSAL when user asks for next actions.”

---

*Generated for profitability and resiliency. NO-APPLY: this document is advisory; implement changes via Cursor and config.*
