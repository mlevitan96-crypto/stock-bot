# Alpaca dashboard adversarial review (multi-role simulation)

**Artifact ID:** `ALPACA_DASHBOARD_ADVERSARIAL_REVIEW_20260326_1900Z`  
**Note:** Single model session; roles are **simulated** for structured challenge (not separate LLM runs).

---

## CSA

- **Challenge:** “All tabs truthful” cannot be claimed until **droplet** evidence exists with production env, keys, and telemetry cadence.
- **Verdict:** Repo-side wiring fixes are **conditionally approved**; final **DASHBOARD_TRUTH_RESTORED** requires droplet proof artifact.

## SRE

- **Challenge:** `dashboard_verify_all_tabs.py` still does not hit every auxiliary SRE sub-fetch (`bar_health_summary`, full `xai/export`, etc.). **Blind spot:** secondary fetches inside a tab can 404 while primaries pass.
- **Challenge:** Basic auth + `fetch` behavior varies by browser; ledger and strip must be verified under **real** login, not only `test_client`.

## Quant

- **Challenge:** Executive PnL and telemetry windows can diverge; disclaimer exists but **no STALE banner** when executive data is old.
- **Challenge:** `LEARNING_STATUS` may be **BLOCKED** while UI elsewhere looks green — operator must read System Health, not the top strip alone.

## Board

- **Challenge:** Governance reports linked from banner depend on `/reports/board/...` route and file presence; broken link feels “fixed” if banner text shows RESULTS but file 404 (must click link in proof).

## Adversarial persona (mandatory)

**I do not accept “complete” or “fixed.”**

What could still be wrong?

1. **Droplet never ran** `git pull` / restart — you have only **local** `truth_probe` JSON.
2. **Alpaca keys missing** on any runtime → positions permanently **BLOCKED**; that is truthful but not “restored” for operators expecting fills.
3. **Telemetry bundle** may be months old — STALE is honest but **not** “fresh.”
4. **Secondary pages** (`/sre` standalone) not audited here.
5. **`direction_banner` import** may throw in some deployments — API returns “unavailable” **200**; easy to mistake for healthy “waiting” unless `detail` is read.
6. **No automated browser test** — only HTTP probes; JS syntax errors on specific branches could still break a tab.
7. **Kraken block** still shown inside System Health — Alpaca-only **intent** is violated in copy unless scoped as “legacy join readiness” (documented as known cross-venue row).

**Required before claiming restoration:** Droplet `dashboard_verify_all_tabs.py` log + manual tab checklist + screenshot or HAR for Telemetry STALE banner when LVS JSON missing.
