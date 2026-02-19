# Root cause and edge

## Pipeline audit
- systemd_audit.md, signal_chain_audit.md, scoring_pipeline_audit.md (see reports/scoring_integrity).

## Bucket analysis summary
- Positive expectancy bucket: see bucket_analysis.md (mean_pnl_pct > 0, win_rate).

## Signal-group edge
- See signal_group_expectancy.md. Delta > 0 suggests group adds edge when strong.

## Decision (A/B/C)
- **A** Pipeline partially broken (missing/zeroed signals, stale caches, mis-weighted).
- **B** Pipeline intact; scores weak but informative; some blocked buckets show positive expectancy.
- **C** Both.

## Signal groups with positive edge
- List groups where mean_pnl_strong > mean_pnl_weak and delta_expectancy > 0.

## Signal groups noise/negative
- List groups where delta <= 0 or sample too small.
