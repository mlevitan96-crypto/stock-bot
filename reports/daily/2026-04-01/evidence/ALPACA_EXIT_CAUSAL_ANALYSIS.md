# ALPACA_EXIT_CAUSAL_ANALYSIS

## By `exit_reason` / code (tail)

- **signal_decay(0.84)**: n=29, sum=16.6955, E=0.575707, win_rate=0.7586
- **signal_decay(0.83)**: n=22, sum=27.23, E=1.237727, win_rate=0.8182
- **signal_decay(0.93)**: n=21, sum=-28.4654, E=-1.355498, win_rate=0.5714
- **signal_decay(0.85)**: n=20, sum=27.61, E=1.3805, win_rate=0.8
- **signal_decay(0.92)**: n=19, sum=13.45, E=0.707895, win_rate=0.6316
- **signal_decay(0.70)**: n=18, sum=2.52, E=0.14, win_rate=0.3889
- **signal_decay(0.69)**: n=17, sum=5.0067, E=0.29451, win_rate=0.5882
- **signal_decay(0.91)**: n=14, sum=11.64, E=0.831429, win_rate=0.7143
- **signal_decay(0.63)**: n=13, sum=-4.3233, E=-0.332564, win_rate=0.3846
- **signal_decay(0.88)**: n=12, sum=-4.56, E=-0.38, win_rate=0.25
- **signal_decay(0.65)+flow_reversal**: n=12, sum=-8.0333, E=-0.669444, win_rate=0.25
- **signal_decay(0.64)**: n=10, sum=-13.9153, E=-1.391533, win_rate=0.2
- **signal_decay(0.89)**: n=9, sum=-7.4, E=-0.822222, win_rate=0.3333
- **signal_decay(0.71)**: n=9, sum=2.1867, E=0.242963, win_rate=0.6667
- **signal_decay(0.90)**: n=8, sum=0.17, E=0.02125, win_rate=0.5
- **signal_decay(0.94)**: n=8, sum=-13.3871, E=-1.673393, win_rate=0.25
- **signal_decay(0.87)**: n=8, sum=3.26, E=0.4075, win_rate=0.5
- **signal_decay(0.64)+flow_reversal**: n=8, sum=-1.1, E=-0.1375, win_rate=0.375
- **signal_decay(0.86)**: n=7, sum=0.5967, E=0.085238, win_rate=0.7143
- **signal_decay(0.62)**: n=7, sum=-2.3068, E=-0.329546, win_rate=0.5714
- **signal_decay(0.89)+flow_reversal**: n=5, sum=-2.1, E=-0.42, win_rate=0.2
- **signal_decay(0.67)**: n=5, sum=4.7583, E=0.951657, win_rate=0.6
- **signal_decay(0.92)+flow_reversal**: n=4, sum=0.23, E=0.0575, win_rate=0.75
- **signal_decay(0.56)**: n=4, sum=2.38, E=0.595, win_rate=0.75
- **signal_decay(0.79)**: n=4, sum=7.64, E=1.91, win_rate=1.0
- **signal_decay(0.60)**: n=4, sum=0.93, E=0.2325, win_rate=0.5
- **signal_decay(0.59)**: n=4, sum=-2.6, E=-0.65, win_rate=0.5
- **signal_decay(0.65)**: n=4, sum=-6.73, E=-1.6825, win_rate=0.25
- **signal_decay(0.62)+flow_reversal**: n=4, sum=-1.03, E=-0.2575, win_rate=0.0
- **signal_decay(0.82)**: n=3, sum=3.62, E=1.206667, win_rate=1.0

## By `winner` / thesis break (when present)


## Dominant `v2_exit_component` (when dict present)

- **score_deterioration**: n=204, sum=-9.4496, E=-0.046321, win_rate=0.5147
- **vol_expansion**: n=176, sum=43.0921, E=0.244841, win_rate=0.5568
- **regime_shift**: n=43, sum=-25.1892, E=-0.585795, win_rate=0.5116
- **flow_deterioration**: n=9, sum=2.95, E=0.327778, win_rate=0.6667

## Time-in-trade buckets

- **15-60m**: n=355, sum=12.8531, E=0.036206, win_rate=0.5296
- **1-4h**: n=70, sum=5.0571, E=0.072244, win_rate=0.6
- **>=4h**: n=7, sum=-6.5069, E=-0.929558, win_rate=0.1429

## Counterfactual note

- **Early vs late exit** full replay requires bar path + `replay_exit_timing_counterfactuals.py`.
- **Loss amplification from delayed exits:** infer only from time bucket expectancy differences above (associational).

