# Adjustment delta attribution (droplet)

## Join strategy
Ledger events have pre_score = signal_raw.score, post_score = score_final. Adjustment logs have no timestamps; join by symbol + score_before within tolerance 0.08. For each event we pick from each log the line with same symbol and score_before closest to expected (pre, after_sq, after_uw). Best-effort; document exact logic in script.

## Distribution of deltas per stage (joined)
- delta_signal_quality: median=0.7497, mean=0.7868, n=3037
- delta_uw: median=0.0000, mean=-0.0065
- delta_survivorship: median=0.0000, mean=-0.0004

## % of total drop attributable to each stage (sum of joined deltas)
- signal_quality: 21.6%
- uw: -0.2%
- survivorship: -0.0%

## Kill counts (raw log: score_before>=2.5 and score_after<2.5)
- signal_quality: 0
- uw: 38069
- survivorship: 19

## Dominant killer
- Stage: **uw**
- Rule/reason: **rejected_low_quality** (kill count from raw log: 38069)

## Top 10 punitive rules per stage (count)
### signal_quality (delta bucket)
### uw
- rejected_low_quality: 38069
### survivorship (action)
- penalize_strong: 19