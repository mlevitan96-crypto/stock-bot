# DISPLACEMENT_GOOD_VS_BAD_SEPARATION
- **Classification horizon:** `pnl_60m` Variant A
- **n:** 5705 (BAD=3256, GOOD=2449)
- **Conclusion:** A) We can separate GOOD vs BAD displacement blocks with decision-time features (see top rules).

## Top rules (univariate impurity reduction)

```json
[
  {
    "feature": "dist_thr",
    "operator": "<=",
    "threshold": 2.3856,
    "impurity_reduction": 0.006496,
    "n_left": 4020,
    "n_right": 1685,
    "bad_rate_left": 0.5338,
    "bad_rate_right": 0.6588
  },
  {
    "feature": "dist_thr",
    "operator": ">",
    "threshold": 2.3856,
    "impurity_reduction": 0.006496,
    "n_left": 1685,
    "n_right": 4020,
    "bad_rate_left": 0.6588,
    "bad_rate_right": 0.5338
  },
  {
    "feature": "hour_utc",
    "operator": "<=",
    "threshold": 15.0,
    "impurity_reduction": 0.002068,
    "n_left": 1320,
    "n_right": 4385,
    "bad_rate_left": 0.5121,
    "bad_rate_right": 0.5884
  },
  {
    "feature": "hour_utc",
    "operator": ">",
    "threshold": 15.0,
    "impurity_reduction": 0.002068,
    "n_left": 4385,
    "n_right": 1320,
    "bad_rate_left": 0.5884,
    "bad_rate_right": 0.5121
  },
  {
    "feature": "snap_joined",
    "operator": "<=",
    "threshold": 0.0,
    "impurity_reduction": 0.000867,
    "n_left": 4773,
    "n_right": 932,
    "bad_rate_left": 0.5799,
    "bad_rate_right": 0.5236
  },
  {
    "feature": "snap_joined",
    "operator": ">",
    "threshold": 0.0,
    "impurity_reduction": 0.000867,
    "n_left": 932,
    "n_right": 4773,
    "bad_rate_left": 0.5236,
    "bad_rate_right": 0.5799
  },
  {
    "feature": "log1p_conc",
    "operator": "<=",
    "threshold": 3.091042,
    "impurity_reduction": 0.000809,
    "n_left": 5507,
    "n_right": 198,
    "bad_rate_left": 0.5669,
    "bad_rate_right": 0.6768
  },
  {
    "feature": "log1p_conc",
    "operator": ">",
    "threshold": 3.091042,
    "impurity_reduction": 0.000809,
    "n_left": 198,
    "n_right": 5507,
    "bad_rate_left": 0.6768,
    "bad_rate_right": 0.5669
  },
  {
    "feature": "dist_thr",
    "operator": "<=",
    "threshold": 1.2488,
    "impurity_reduction": 0.000707,
    "n_left": 1584,
    "n_right": 4121,
    "bad_rate_left": 0.5404,
    "bad_rate_right": 0.5824
  },
  {
    "feature": "dist_thr",
    "operator": ">",
    "threshold": 1.2488,
    "impurity_reduction": 0.000707,
    "n_left": 4121,
    "n_right": 1584,
    "bad_rate_left": 0.5824,
    "bad_rate_right": 0.5404
  }
]
```
