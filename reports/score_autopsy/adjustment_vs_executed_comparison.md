# Adjustment vs executed comparison

## Executed trades (attribution entry_score)
- count=1110, min=3.019, max=8.800, median=3.940

## Blocked (ledger post_score)
- count=3037, post min=0.170, max=1.039

## Adjustment log: lines where score_after in blocked band (0, 2.5) vs executed band [2.5, 10]
- signal_quality: blocked_band lines=0, executed_band lines=20466
- uw: blocked_band lines=38069, executed_band lines=1224

- Mean delta (signal_quality) when score_after in [2.5,10]: 0.9369
