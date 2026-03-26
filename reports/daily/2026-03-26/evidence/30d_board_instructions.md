# 30-Day Board Review — Instructions

## Purpose

The Board must do a **comprehensive review** of our current architecture and PnL over the last 30 days, using **real data from the droplet**, and produce **5 agreed recommendations** to stop losing money and improve.

## Inputs (use real droplet data)

1. **30-day comprehensive review bundle**  
   - Primary: `reports/board/30d_comprehensive_review.md` and `reports/board/30d_comprehensive_review.json`.  
   - **To refresh with droplet data:** run  
     `python scripts/run_30d_board_review_on_droplet.py`  
     then re-open this instruction set and the updated bundle.

2. **Architecture**  
   - Described in the bundle (entry: composite score, gates; exit: signal_decay, time/trail stops; universe; execution).  
   - Full organism: `reports/audit/FULL_ORGANISM_DATA_CAPTURE_AND_EXIT_REVIEW_2026-03-02.md`.  
   - Trade designation for replay: `docs/TRADE_DESIGNATION_FOR_REPLAY.md`.

3. **Long/short verification (droplet)**  
   - **Must review:** `reports/board/LONG_SHORT_VERIFICATION_DROPLET_2026-03-03.md` (why all of today's positions are long; LONG_ONLY status; direction from flow sentiment).  
   - Audit: `reports/audit/LONG_SHORT_TRADE_LOGIC_AUDIT.md`.

4. **Realistic backtest**  
   - 30-day replay: `scripts/run_30d_backtest_droplet.py` (run on droplet).  
   - Exit effectiveness: `scripts/run_exit_review_on_droplet.py` → `reports/exit_review/exit_effectiveness_v2.md`, `exit_tuning_recommendations.md`.

## Process

1. **Each persona produces 3 ideas**  
   - **Equity Skeptic** (drawdown, churn, regime mismatch): 3 ideas.  
   - **Wheel Advocate** (premium decay, assignment risk): 3 ideas.  
   - **Risk Officer** (capital efficiency, tail risk): 3 ideas.  
   - **Promotion Judge** (promotion vs demotion): 3 ideas.  
   - **Customer Advocate** (why are we losing money? challenge assumptions; demand expectancy improvement): 3 ideas.  
   - **Innovation Officer** (2–3 testable experiments per day; hypothesis, environment, kill criteria): 3 ideas.  
   - **SRE** (health + opportunity cost; which limits are too conservative?): 3 ideas.  

   Each idea must be **concrete**: entry/exit/universe/backtest/replay or ops, with hypothesis and how we measure success.

2. **Synthesis and agreement**  
   - Board Synthesizer merges all ideas.  
   - Full Board **agrees on the top 5** recommendations that will help us move toward making money.  
   - Consider: trade designation for replay, realistic backtest to tune entry/exit, universe or filters for edge, exit review and hold-time, governance/learning loop.

3. **Output**  
   - **Exactly 5 recommendations**, each with:  
     - **Title**  
     - **Owner** (role or component)  
     - **Metric** (how we measure)  
     - **3/5-day success criteria**  
     - **One-line rationale**  

   Write to: `reports/board/30d_TOP_5_AGREED_RECOMMENDATIONS.md`.

## Constraints

- Customer Advocate must explicitly challenge poor results and demand evidence.  
- Innovation Officer: no idea without a test (hypothesis, data, kill criteria).  
- All recommendations must be actionable (code, config, or process we can execute).
