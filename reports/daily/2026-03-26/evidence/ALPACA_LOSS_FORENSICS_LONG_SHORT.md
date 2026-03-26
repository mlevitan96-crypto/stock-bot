# Alpaca Loss Forensics — Long vs Short

| Side | Trades | Total PnL |
|---|---:|---:|
| LONG | 1127 | -440.1958 |
| SHORT | 873 | -115.3064 |

**Net long skew on losing days:** On calendar days with negative daily PnL, long exits=1127, short exits=873.

**Asymmetry:** Short leg contributed *less negative* (or more positive) PnL than long in this window.

## MAE/MFE mean by side (%%)

- **LONG** MAE mean: 0.0000  MFE mean: 0.0000
- **SHORT** MAE mean: 0.0000  MFE mean: 0.0000

## Exit reason × side (counts)

### LONG
- signal_decay(0.70): 48
- signal_decay(0.84): 40
- signal_decay(0.69): 38
- signal_decay(0.71): 32
- signal_decay(0.85): 30
- signal_decay(0.77): 26
- signal_decay(0.83): 26
- signal_decay(0.68): 24
- signal_decay(0.82): 24
- signal_decay(0.78): 23
- signal_decay(0.77)+flow_reversal: 23
- signal_decay(0.74): 21
### SHORT
- signal_decay(0.84): 61
- signal_decay(0.83): 51
- signal_decay(0.82): 41
- signal_decay(0.85): 38
- signal_decay(0.75): 24
- signal_decay(0.76): 20
- signal_decay(0.81): 20
- signal_decay(0.92): 19
- signal_decay(0.94): 19
- signal_decay(0.93): 19
- signal_decay(0.78)+flow_reversal: 18
- signal_decay(0.91): 16
