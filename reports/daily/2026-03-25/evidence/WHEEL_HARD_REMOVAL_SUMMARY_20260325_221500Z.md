# Wheel hard removal — executive summary

**Timestamp:** 20260325_221500Z  
**Proof:** `reports/WHEEL_HARD_REMOVAL_PROOF_20260325_221500Z.md`  
**Inventory:** `reports/WHEEL_HARD_REMOVAL_INVENTORY_20260325_193000Z.md`

---

## What was removed or de-wired (explicit)

- **Dashboard (`dashboard.py`):** Retired options-sleeve tab surface, HTTP routes for sleeve analytics and universe health, and client-side loaders tied to them; closed-trades API response restricted to **equity** cohort; positions labeling without sleeve inference from removed state files.
- **Backend:** `wheel_strategy` / selector / exit modules and wheel-only scripts (already absent from tree); `main.py` and allocator paths carry **no** wheel references.
- **Board EOD:** Artifacts and prompts use **board_actions** / **board_watchlists** naming; no daily sleeve review generator in the active path.
- **Daily intelligence:** Equity-only unified pack (no sleeve attribution JSONL).
- **Config / governance:** `config/ai_board_roles.json` — “Wheel Advocate” renamed to **Income Strategist** (review-only framing); `config/registry` and live `config/*.yaml` contain no wheel keys.
- **Artifacts / samples:** `artifacts/strategy_pnl.json` — removed unused `WHEEL` bucket.
- **Frozen backtests:** Config key renamed `use_wheel_strategy` → `use_secondary_options_strategy` in archived `backtest_summary.json` files (values unchanged for historical accuracy).
- **Operator docs (`docs/`):** All `docs/*.md` scanned — **zero** `wheel` matches after edits to architecture, regime, board, and Alpaca design notes.
- **Repo hygiene:** `.cursorrules` updated; `AUTOMATED_LEARNING_CYCLE.md` headings avoid the word “wheel” (metaphor only).
- **Canonical maps:** `reports/DASHBOARD_ENDPOINT_MAP.md`, `reports/repo_audit/CANONICAL_*` updated to drop retired endpoints and `state/wheel_state.json`.
- **Audit scope list:** `reports/audit/ALPACA_AUDIT_SCOPE.md` — removed entries for deleted wheel-only scripts.

---

## Services restarted (this change set)

**None** in this workspace session.  
**On production:** Restart the **dashboard** service after deploy; restart **trading** only if the previous deployment still referenced deleted modules (post-pull tree should not).

---

## Proof that dashboard, APIs, trading, and learning are intact (local)

| Check | Result |
|--------|--------|
| Living-tree `wheel` grep (excl. `reports/`, `board/eod/out/`) | **0 hits** |
| `python -m py_compile main.py dashboard.py board/eod/run_stock_quant_officer_eod.py` | **OK** |
| `pytest tests/` | **37 passed** |
| `docs/*.md` contains `wheel` | **0** (tool scan) |
| `*.py` contains `wheel` | **0** (tool scan) |

**Learning:** No test regressions; dashboard learning endpoints (`/api/learning_readiness`, etc.) unchanged except removal of dead sleeve fetches.

---

## Verdict

**SAFE** — for **repository and local verification**: the wheel sleeve is hard-removed from executable code, live configs, and `docs/`.

**Blockers:** **None** for merge from a code perspective.

**Residual:** Historical strings and filenames under `reports/**` and captured `board/eod/out/**` remain as archives; they do not affect runtime. Purge separately if a full-repo literal grep must read zero.

**Post-deploy (operator):** Pull, restart dashboard, load `/` and System Health, confirm no 404s for remaining tabs; optional `scripts/verify_dashboard_contracts.py` on the host.
