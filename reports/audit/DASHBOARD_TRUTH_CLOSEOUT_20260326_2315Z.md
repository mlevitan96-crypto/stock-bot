# Dashboard truth surfaces — closeout (Alpaca + Kraken)

**TS:** `20260326_2315Z`

## Alpaca (`dashboard.py`)

| Requirement | Evidence |
|-------------|----------|
| Never imply learning-ready when not certified | Global banner: **“LEARNING STATUS: NOT CERTIFIED”**; Learning tab banner **PARTIAL**; System Health surfaces `LEARNING_STATUS` from strict eval |
| Operational vs learning separated | Positions API errors explicitly say broker snapshot ≠ learning certification; executive summary notes PnL windows ≠ strict cohort |
| OK / STALE / PARTIAL / DISABLED | `setTabStateLine` + tab-state banners; `alpaca_strict_eval_error` surfaced in profitability/learning payload |
| No silent 500 on learning API | `/api/learning_readiness` documents **NEVER returns 500** — try/except returns safe JSON |

Code references:

```3590:3634:dashboard.py
@app.route("/api/learning_readiness", methods=["GET"])
def api_learning_readiness():
    """
    Learning & Readiness tab API. NEVER returns 500.
    Always 200 JSON with ok/run_ts/deployed_commit/visibility_matrix/error.
    ...
    try:
        payload = _get_learning_readiness_payload(root, run_ts, deployed_commit)
        return jsonify(payload), 200
    except Exception as e:
        ...
```

Strict eval wiring:

```3188:3224:dashboard.py
    alpaca_strict = None
    alpaca_strict_error = None
    try:
        from telemetry.alpaca_strict_completeness_gate import (
            STRICT_EPOCH_START,
            evaluate_completeness,
        )

        alpaca_strict = evaluate_completeness(root, open_ts_epoch=STRICT_EPOCH_START, audit=False)
    except Exception as e:
        alpaca_strict_error = str(e)[:500]
```

## Kraken

Dashboard exposes **Kraken direction readiness** from `state/direction_readiness.json` in the same payload — **not** equivalent to strict tail completeness or Telegram milestone proof. No separate Kraken strict panel found.

## Gaps (honest)

- **Droplet API proof bundle** (curl to `/api/learning_readiness` + `/api/dashboard/data_integrity`) **not attached** in this run — code-level truth surfaces are verified in-repo only.
