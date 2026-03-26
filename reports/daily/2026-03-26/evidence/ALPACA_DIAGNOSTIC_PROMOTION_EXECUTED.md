# Alpaca Diagnostic Promotion — Executed (SRE)

**Promotion tag:** `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS`  
**Rule:** `SCORE_DETERIORATION_EMPHASIS`  
**Scope:** Live **paper** only · **No capital risk**

---

## 1. Promotion timestamp

| Event | UTC |
|-------|-----|
| Config + code deployed to droplet | **2026-03-20T00:22:37Z** |
| `stock-bot` service restart (load `exit_score_v2.py`) | **~2026-03-20T00:22:45Z** (restart succeeded; unit **active**) |
| Dropped `state/alpaca_diagnostic_promotion.json` | **2026-03-20T00:22:37Z** |

**Droplet commit at deploy:** `28abc2a33e365caa58736b99a175ae360f9d1447` (runtime picks up **uploaded** `active.json` + `exit_score_v2.py`; **commit git** should be updated on next push from dev machine).

---

## 2. Config bound to paper engine

**File:** `config/tuning/active.json`

- **version:** `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS_2026-03-20`
- **exit_weights (diagnostic):**
  - `score_deterioration`: **0.28** (was **0.25** in code default)
  - `flow_deterioration`: **0.17** (was **0.25** default; prior file had **0.37** single-key overlay that did not affect `compute_exit_score_v2` before wiring fix)
  - Other keys: `darkpool_deterioration` 0.10, `sentiment_deterioration` 0.10, `regime_shift` 0.10, `sector_shift` 0.05, `vol_expansion` 0.10, `thesis_invalidated` 0.10  
  - **Sum = 1.00**

**State marker:** `state/alpaca_diagnostic_promotion.json` — records tag, rule name, `activated_utc`, paths.

---

## 3. Code change (required for promotion to take effect)

**File:** `src/exit/exit_score_v2.py`

- **`compute_exit_score_v2`** now uses **`get_merged_exit_weights`** from `config/tuning/tuning_loader.py` for:
  - the **weighted exit score** (same terms as before, now tunable)
  - **`attribution_components` contributions** (stays consistent with score)

**Before this change:** `config/tuning/active.json` was **not** applied to `compute_exit_score_v2` (weights were hardcoded). **After:** paper diagnostics honor **`exit_weights`** in `active.json`.

**No other logic changes** in this mission (no entry thresholds, no order sizing, no broker routing).

---

## 4. Diff summary (local repo)

See `git diff` for `src/exit/exit_score_v2.py` — structural change: `_DEFAULT_EXIT_WEIGHTS` + `get_merged_exit_weights` for composite score and attribution.

---

## 5. Operational confirmation

| Check | Result |
|-------|--------|
| Files on droplet at `/root/stock-bot/` | **Uploaded** (`active.json`, `exit_score_v2.py`, `alpaca_diagnostic_promotion.json`) |
| `systemctl restart stock-bot` | **Exit 0**, service **active** |

---

## 6. Shadow / other rules

- **No** other overlays activated.
- Fast lane, shadow snapshot profiles, and unrelated experiments remain **SHADOW** / unchanged.

---

*SRE — diagnostic promotion applied; restart required after future `exit_score_v2.py` edits.*
