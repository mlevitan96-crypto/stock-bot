# Alpaca Telegram — Analysis Completion Alerts (Phase 3)

**Mission:** Alerts when key analysis phases complete.  
**Authority:** CSA, SRE. READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Phases and Triggers

| Phase | Trigger | Artifact paths (examples) | Readiness status |
|-------|---------|---------------------------|------------------|
| **Loss causality analysis completed** | After run_alpaca_loss_causality.py (or pipeline step that writes it) | reports/audit/ALPACA_LOSS_CAUSALITY.md | Ready / Partial (e.g. &lt;500 trades) |
| **Counterfactual analysis completed** | After counterfactual script run; ALPACA_COUNTERFACTUAL_RESULTS.md written | reports/audit/ALPACA_COUNTERFACTUAL_RESULTS.md | Ready / Partial |
| **Profit discovery lab completed** | After run_alpaca_profit_lab.py; RAW_RESULTS and RANKED written | reports/audit/ALPACA_PROFIT_LAB_RAW_RESULTS.json, ALPACA_PROFIT_LAB_RANKED.md | Ready / Partial |
| **Robustness analysis completed** | After robustness run; ALPACA_PROFIT_LAB_ROBUSTNESS.md updated | reports/audit/ALPACA_PROFIT_LAB_ROBUSTNESS.md | Ready / Partial |
| **Board packet finalized** | After QSA/CSA/SRE reviews and board packet written | reports/audit/QSA_REVIEW_ALPACA_PROFIT_LAB.md, CSA_REVIEW_ALPACA_PROFIT_LAB.md, SRE_REVIEW_ALPACA_PROFIT_LAB.md, ALPACA_PROFIT_LAB_BOARD_PACKET.md | Ready |

---

## 2. Message Content (Per Phase)

Each alert includes:

- **Phase name:** As in table (e.g. “Loss causality analysis completed”).
- **Artifact paths:** Relative or absolute paths to primary outputs (comma or newline separated).
- **Readiness status:** “Ready” when artifacts exist and meet minimum (e.g. dataset size); “Partial” when run completed but dataset below target (e.g. &lt;500 trades).

---

## 3. When to Send

- **Option A:** Send at end of pipeline run that produces the artifact (e.g. pipeline step that runs loss causality and then sends Telegram).
- **Option B:** Separate job or manual trigger after operator confirms artifact exists; script reads artifact paths and sends one message per phase (with idempotency key if desired, e.g. date or run id).
- **No spam:** One completion alert per phase per “run” or per day, as defined by operator; avoid duplicate alerts for the same artifact set.

---

## 4. Template (Recap)

See ALPACA_TELEGRAM_MESSAGE_FORMAT.md §3: Phase, Artifacts, Readiness, Timestamp (UTC).
