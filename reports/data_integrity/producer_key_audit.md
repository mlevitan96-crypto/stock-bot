# Producer Key Audit

Compare each producer's emitted keys to the canonical list in `canonical_signal_keys.md`.

---

## Producer 1: uw_composite_v2._compute_composite_score_core

**Location:** `uw_composite_v2.py` (lines 1186–1259).  
**Emits:** `components` (dict), `group_sums` (dict).

**Component keys emitted:**  
flow, dark_pool, insider, iv_skew, smile, whale, event, motif_bonus, toxicity_penalty, regime, congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score, freshness_factor

**Group-sum keys emitted:**  
uw, regime_macro, other_components

**Comparison to canonical:**

| Check | Result |
|-------|--------|
| All canonical component keys present | **PASS** — 22 keys match. |
| Renamed keys | **NONE** — keys match canonical. |
| Extra keys | **NONE** — no extras. |
| group_sums keys | **PASS** — uw, regime_macro, other_components. |

**Verdict:** **PASS** — Producer emits exactly the canonical keys.

---

## Producer 2: main.py (conduit to snapshot and blocked_trades)

**Role:** Reads `c.get("composite_meta")` and passes `meta.get("components")` and `meta.get("group_sums")` to:
- `append_score_snapshot(weighted_contributions=meta.get("components"), group_sums=meta.get("group_sums"), ...)`
- `log_blocked_trade(..., attribution_snapshot={ "weighted_contributions": meta.get("components"), "group_sums": meta.get("group_sums"), ... })`

**Comparison:**

| Check | Result |
|-------|--------|
| Forwards components without renaming | **PASS** — passed as-is. |
| Forwards group_sums without renaming | **PASS** — passed as-is. |
| Missing keys (if meta is full composite) | **NONE** — full composite has both. |

**Note:** Other code paths (e.g. ENTRY_FILL/EXIT_FILL telemetry at 1714, 1922, 7034) build a minimal `composite_meta` with only `components` and no `group_sums`. Those do **not** feed `score_snapshot.jsonl` or `blocked_trades.jsonl`; the pipeline only consumes snapshot and blocked_trades. So no mismatch for edge analysis.

**Verdict:** **PASS** — Conduit does not rename or drop keys for snapshot/blocked_trades path.

---

## Producer 3: score_snapshot_writer.append_score_snapshot

**Location:** `score_snapshot_writer.py`.  
**Writes:** `rec["weighted_contributions"]`, `rec["group_sums"]` when provided (optional).

**Comparison:**

| Check | Result |
|-------|--------|
| Writes keys as provided | **PASS** — _sanitize() preserves key names. |
| Drops or renames | **NONE** — no key mapping. |

**Verdict:** **PASS** — Writes canonical keys when present.

---

## Producer 4: log_blocked_trade (attribution_snapshot)

**Location:** `main.py` (log_blocked_trade calls with `attribution_snapshot={...}`).  
**Writes:** `attribution_snapshot.weighted_contributions`, `attribution_snapshot.group_sums` into `state/blocked_trades.jsonl`.

**Comparison:**

| Check | Result |
|-------|--------|
| Same keys as composite | **PASS** — values come from meta.get("components") and meta.get("group_sums"). |
| Renaming | **NONE** — keys preserved. |

**Verdict:** **PASS** — No missing or renamed keys.
