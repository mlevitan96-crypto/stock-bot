# Wheel hard removal — proof bundle (SRE)

**Timestamp:** 20260325_221500Z (UTC-anchored label; generated in repo on 2026-03-25)  
**Related inventory:** `reports/WHEEL_HARD_REMOVAL_INVENTORY_20260325_193000Z.md`

---

## Stop-gate 0 — plan confirmation (CSA)

**Plan (restated):** Remove the retired options “wheel” sleeve from all **live** surfaces: Flask dashboard routes and UI, trading engine wiring, daily report generators, board EOD artifacts, config/registry paths, verification scripts, and operator-facing docs under `docs/`. Delete implementation modules and wheel-only scripts. Preserve equity/Alpaca execution, learning APIs, and non-wheel HTTP contracts.

**Verdict:** **APPROVE** (execute hard removal; no feature flags).

---

## Stop-gate 1 — inventory verdict (CSA)

**Completeness:** Inventory file lists dashboard, `main.py`, strategies, config, scripts, board EOD, and audit harness touchpoints. Follow-up edits aligned canonical endpoint maps and `docs/` to the post-removal world.

**Risk ranking (residual):** Low for runtime — Python tree contains no `wheel` matches. Medium only for **human process**: droplet must pull and restart dashboard (and trading supervisor if that host still runs an older build).

**Verdict:** **APPROVE**.

---

## Living-code grep proof (exclude historical trees)

**Definition — “living tree”:** All files under the repo with extensions `.py`, `.md`, `.json`, `.yaml`, `.yml`, `.txt`, `.html`, `.js`, `.css`, `.toml`, `.ini`, **excluding** paths matching `reports/` and `board/eod/out/` (captured EOD outputs and audit exports).

**Scan:** case-insensitive substring `wheel`.

**Result:** **0 files** with matches (script: `os.walk` + `re.search`, path filter as above).

**Implication:** No wheel strategy references remain in application code, root-level docs outside `reports/`, configs outside `reports/`, or board Python under the filtered scope.

---

## Python import / syntax proof

```text
python -m py_compile main.py dashboard.py board/eod/run_stock_quant_officer_eod.py
```
**Exit code:** 0

**Additional:** `*.py` ripgrep-style scan (workspace tool) reports **no** `wheel` / `Wheel` / `WHEEL` matches across `*.py`.

---

## Automated tests

```text
python -m pytest tests/ -q
```
**Result:** `37 passed`

---

## Historical / archived strings (explicit exclusion)

The following areas **may still contain** the substring `wheel` in filenames or frozen narrative. They are **not** loaded by the trading engine or dashboard for the retired sleeve:

- `reports/**` (audit PDFs, stockbot snapshots, `*_stock-bot_wheel.json`, root-cause reports, etc.)
- `board/eod/out/**` (dated EOD JSON/MD from February 2026 runs)

**Hygiene (optional):** Archive or delete those paths if a **repo-wide** literal zero match is required; not required for runtime safety.

---

## Dashboard route spot-check (code-level)

`dashboard.py` defines **no** routes containing `wheel`, `wheel_analytics`, `universe_health`, or `strategy/comparison`. Learning & readiness continues to read `reports/{date}_stock-bot_combined.json` server-side for optional `strategy_comparison` metadata.

---

## Deploy / restart (this session)

**Not executed** from this environment (no live droplet restart). Operator checklist after `git pull` on the host:

1. Restart **dashboard** process (e.g. supervisor stanza that runs `dashboard.py`) — **required** if the running binary was built before this removal.
2. Restart **trading / `main.py` supervisor** — **required only** if that host still imports deleted modules (after pull, it should not).

---

## CSA + SRE sign-off (synthetic, per your governance model)

| Gate        | Role | Verdict   |
|------------|------|-----------|
| Plan       | CSA  | APPROVE   |
| Inventory  | CSA  | APPROVE   |
| Execution  | SRE  | Complete in repo |
| Production | SRE  | Pending operator restart + smoke |
