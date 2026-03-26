# Alpaca dashboard — permanentize (Phase 1: working files vs repo)

**Timestamp:** `20260326_2015Z`

## Git (pre-commit)

```text
 M dashboard.py
 M scripts/dashboard_verify_all_tabs.py
```

## Diffstat

```text
 dashboard.py                         | 300 +++++++++++++++++++++++++++++++----
 scripts/dashboard_verify_all_tabs.py |  99 ++++++++++--
 2 files changed, 359 insertions(+), 40 deletions(-)
```

## SHA256 (workspace files before commit)

| File | SHA256 |
|------|--------|
| `dashboard.py` | `b24079d59f43302a5678a1b9e879726b0156c9dbd2d985ba57d9c8736547c518` |
| `scripts/dashboard_verify_all_tabs.py` | `e34725219216cc3892a3a813b53fc38d785343baf7c86dd054d5f74a1e9212b1` |

## Confirmations (no guesswork)

### `dashboard.py`

- **Auth allowlist** includes `"/api/alpaca_operational_activity"` (unauthenticated GET alongside other public panel paths).
- **Route:** `@app.route("/api/alpaca_operational_activity", methods=["GET"])` → `api_alpaca_operational_activity`.
- **Payload:** `_alpaca_operational_activity_payload(...)`; disclaimer includes exact CSA line: *“Trades are executing on Alpaca. Data is NOT certified for learning or attribution.”*
- **UI:** `#alpaca-operational-activity`, `loadAlpacaOperationalActivity`, learning banner / tab state helpers (dashboard-only).

### `scripts/dashboard_verify_all_tabs.py`

- **First path** in `TAB_ENDPOINTS`: `"/api/alpaca_operational_activity?hours=72"`.
- **`argparse`** with `--json-out PATH`; writes structured JSON (`all_pass`, `results[]` with `http_status`, `body_snippet`, etc.).

## Full diff

Captured locally with:

`git diff dashboard.py scripts/dashboard_verify_all_tabs.py`

Too large to inline here in full; after commit, identical tree diff is:

`git show <COMMIT_SHA> --stat` and `git show <COMMIT_SHA> -- dashboard.py scripts/dashboard_verify_all_tabs.py`

(See `ALPACA_DASHBOARD_PERMANENTIZE_COMMIT_20260326_2015Z.md` for SHA.)
