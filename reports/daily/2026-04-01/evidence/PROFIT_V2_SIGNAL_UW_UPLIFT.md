# PROFIT_V2_SIGNAL_UW_UPLIFT
- Matched exit↔snapshot pairs: **63**
- Bootstrap: 2.5–97.5 percentile of high-vs-low mean PnL difference (median split on component).

## Per-component summary
### `flow`

```json
{
  "n": 63,
  "median_split_on_component": 2.4,
  "bootstrap": {
    "mean_high": -0.717042,
    "mean_low": 0.015145,
    "delta_mean": -0.732187,
    "bootstrap_p95_low": -1.545211,
    "bootstrap_p95_high": -0.005905,
    "n_high": 32,
    "n_low": 31
  }
}
```
### `dark_pool`

```json
{
  "n": 63,
  "median_split_on_component": 0.186,
  "bootstrap": {
    "mean_high": -0.538125,
    "mean_low": -0.169543,
    "delta_mean": -0.368582,
    "bootstrap_p95_low": -1.105323,
    "bootstrap_p95_high": 0.317079,
    "n_high": 32,
    "n_low": 31
  }
}
```
### `whale`

```json
{
  "n": 63,
  "median_split_on_component": 0.0,
  "bootstrap": {
    "mean_high": -0.538125,
    "mean_low": -0.169543,
    "delta_mean": -0.368582,
    "bootstrap_p95_low": -1.124193,
    "bootstrap_p95_high": 0.278257,
    "n_high": 32,
    "n_low": 31
  }
}
```
### `etf_flow`

```json
{
  "n": 63,
  "median_split_on_component": 0.043,
  "bootstrap": {
    "mean_high": -0.538125,
    "mean_low": -0.169543,
    "delta_mean": -0.368582,
    "bootstrap_p95_low": -1.105323,
    "bootstrap_p95_high": 0.325829,
    "n_high": 32,
    "n_low": 31
  }
}
```
### `greeks_gamma`

```json
{
  "n": 63,
  "median_split_on_component": 0.143,
  "bootstrap": {
    "mean_high": -0.25,
    "mean_low": -0.466962,
    "delta_mean": 0.216962,
    "bootstrap_p95_low": -0.440911,
    "bootstrap_p95_high": 0.983308,
    "n_high": 32,
    "n_low": 31
  }
}
```
