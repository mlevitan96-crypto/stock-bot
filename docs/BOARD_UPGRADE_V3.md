# Board Upgrade V3 — Multi-Day Intelligence

## Overview
Board Upgrade V3 extends the AI Board with multi-day intelligence, multi-day regime review, multi-day commitments tracking, and multi-day promotion logic. This is a surgical upgrade on top of V2 that does not remove or overwrite existing functionality.

## Key Components

### 1. Multi-Day Analysis Module
- **Script:** `scripts/run_multi_day_analysis.py`
- **Execution:** Runs automatically after daily EOD pipeline
- **Windows:** Computes rolling 3-day, 5-day, 7-day windows
- **Outputs:** `board/eod/out/YYYY-MM-DD/multi_day_analysis.json` and `.md`

**Metrics Computed:**
- Regime persistence and regime transition probability
- Volatility trend
- Sector rotation trend
- Attribution vs exit attribution trend
- Churn trend
- Hold-time trend
- Exit-reason distribution trend
- Blocked trade trend (displacement, max positions, capacity)
- Displacement sensitivity trend
- Capacity utilization trend
- Expectancy trend
- MAE/MFE trend

### 2. Regime Review Officer (New Agent)
- **Location:** `.cursor/agents/regime_review_officer.json`
- **Responsibilities:**
  - Analyze 3/5/7-day regime behavior
  - Detect regime continuation, transition, or reversal
  - Compare multi-day regime to daily regime
  - Identify misalignment between strategy and regime
  - Produce 2–3 regime-aware options with evidence and trade-offs
- **Inputs:** Multi-day analysis module outputs (`multi_day_analysis.json`)

### 3. Updated Agents
All existing agents now:
- Read and incorporate multi-day analysis outputs
- Include multi-day trends in reasoning
- Produce multi-day options when relevant
- Reference multi-day evidence in recommendations
- Track multi-day commitments (1-day, 3-day, 5-day)

**Specific Updates:**
- **Board Review Orchestrator:** Runs Regime Review Officer in every Board Review
- **Board Synthesizer:** Integrates multi-day evidence, includes multi-day sections
- **Exit Specialist:** Incorporates multi-day hold-time, churn, exit-reason trends
- **Performance Auditor:** Incorporates rolling attribution, exit attribution, expectancy
- **Market Context Analyst:** Incorporates multi-day regime, volatility, sector rotation
- **Innovation Officer:** Produces 3–5 multi-day ideas
- **Promotion Officer:** Evaluates multi-day promotion readiness
- **SRE Audit Officer:** Ensures multi-day analysis pipeline health
- **Customer Profit Advocate:** Tracks multi-day commitments, requires multi-day evidence

### 4. Multi-Day Sections in Daily Board Review
The daily Board Review template now includes:

**4.1 Multi-Day Regime Summary**
- 3/5/7-day dominant regime
- Regime stability score
- Regime transition probability

**4.2 Multi-Day P&L & Risk**
- Rolling attribution
- Rolling exit attribution
- Rolling drawdown
- Rolling expectancy

**4.3 Multi-Day Exit & Churn**
- Exit-reason drift
- Churn trend
- Hold-time trend

**4.4 Multi-Day Blocked Trades**
- Displacement trend
- Max-positions trend
- Capacity trend

**4.5 Multi-Day Innovation Opportunities**
Innovation Officer produces 3–5 multi-day ideas with:
- Hypothesis
- Required data
- Test design
- Potential impact

**4.6 Multi-Day Promotion Review**
Promotion Officer evaluates:
- Multi-day sample size
- Multi-day expectancy
- Multi-day volatility
- Multi-day stability
- Multi-day promotion blockers

### 5. Multi-Day Commitments Tracking
Extended from yesterday's commitments to include:
- **1-day commitments** (yesterday)
- **3-day commitments**
- **5-day commitments**

Board reports:
- Completed
- Not completed
- Blocked
- Needs escalation

Customer Profit Advocate challenges any incomplete commitments.

### 6. Board Review Packager Updates
- `scripts/board_daily_packager.py` now includes `multi_day_analysis.json` and `.md` in the combined outputs
- Multi-day analysis is automatically appended to `daily_board_review.md` and included in `daily_board_review.json`

## Cron Integration

After the daily EOD pipeline:
1. Run multi-day analysis module (`scripts/run_multi_day_analysis.py`)
2. Run the full V3 Board Review (including multi-day sections)
3. Package outputs into the dated folder (`board/eod/out/YYYY-MM-DD/`)
4. Commit and push to GitHub
5. Deploy to droplet

## Governance Rules (.cursorrules)

V3 mandates appended to `.cursorrules`:
- Multi-day analysis is required for all Board Reviews
- Regime Review Officer must participate in every Board Review
- Board Synthesizer must integrate multi-day evidence
- All agents must incorporate multi-day trends
- Multi-day commitments must be tracked and escalated
- Innovation Officer must produce multi-day ideas
- Promotion Officer must evaluate multi-day promotion readiness
- Multi-day scenario replay must be used when exit timing is discussed
- Multi-day evidence is required for any recommendation that affects LIVE or PAPER behavior

## Documentation Updates
- `docs/BOARD_REVIEW.md` — Updated with multi-day analysis workflow
- `docs/BOARD_UPGRADE_V2.md` — References V3 changes
- `docs/BOARD_UPGRADE_V3.md` — This document (full V3 architecture)
- `MEMORY_BANK.md` — Updated with multi-day entry

## Testing
To test V3 Board Review:
1. Ensure EOD artifacts exist in `board/eod/out/`
2. Run: `python scripts/run_multi_day_analysis.py --date YYYY-MM-DD`
3. Run: `python scripts/board_daily_packager.py --date YYYY-MM-DD`
4. Verify `board/eod/out/YYYY-MM-DD/multi_day_analysis.json` and `.md` exist
5. Verify `daily_board_review.md` includes multi-day sections
6. In Cursor, run Board Review and verify Regime Review Officer participation

## Deployment
To deploy V3 to droplet:
1. Push code to GitHub: `git push origin main`
2. Run deployment script: `python scripts/deploy_v3_to_droplet.py`
3. Script will: pull latest code → run multi-day analysis → run board packager → commit results → push to GitHub
4. Pull results locally: `git pull origin main`
5. Review: `board/eod/out/YYYY-MM-DD/daily_board_review.md` and `multi_day_analysis.md`

**Verified:** V3 successfully deployed and tested on 2026-02-08. See `board/eod/out/2026-02-08/V3_BOARD_REVIEW_SUMMARY.md` for example output.

## Migration Notes
- V3 is additive; no existing functionality is removed
- Existing Board Reviews continue to work
- Multi-day analysis is optional if historical data is insufficient
- All agents gracefully handle missing multi-day data
