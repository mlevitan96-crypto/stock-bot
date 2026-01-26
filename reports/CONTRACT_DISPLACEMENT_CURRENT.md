# Displacement Contract — Current Behavior

**Document:** `reports/CONTRACT_DISPLACEMENT_CURRENT.md`  
**Purpose:** Establish current truth for displacement logic (no guessing).  
**Source:** `main.py` (AlpacaExecutor).

---

## 1. Where `displaced_by_*` close_reason is generated

- **Function:** `build_composite_close_reason(exit_signals)` in `main.py` (lines 175–259).
- **Trigger:** When `exit_signals["displacement"]` is set to the **new symbol** (challenger) that caused the exit.
- **Output:** `reasons.append(f"displaced_by_{displacement}")` → e.g. `displaced_by_AAPL`.

**When it’s used for displacement exits:**

- **Function:** `execute_displacement(candidate, new_symbol, new_signal_score)` in `main.py` (lines 4608–4776).
- **Flow:** After successfully closing the displaced position, we build:
  ```python
  displacement_signals = {"displacement": new_symbol, "age_hours": ...}
  close_reason = build_composite_close_reason(displacement_signals)
  ```
- **Logging:** `log_exit_attribution(..., close_reason=close_reason, ...)` and `log_event("displacement", "executed", ...)`.

---

## 2. Decision path that triggers displacement

1. **Entry gate:** `run_once()` in main loop. When `can_open_new_position()` is False (portfolio full), we call `find_displacement_candidate(new_signal_score, new_symbol)`.
2. **Candidate selection:** `find_displacement_candidate` returns a dict (position to displace) or `None`.
3. **Execution:** If candidate is not None, we call `execute_displacement(candidate, new_symbol, new_signal_score)`. On success, we proceed to open the new position; on failure, we log `displacement_failed` and block the new entry.

**Criteria used today (priority order):**

| Priority | Mode | Condition | Displacement criteria |
|----------|------|-----------|------------------------|
| 1 | Elite tier | `num_positions >= MAX` and `new_signal_score > 3.6` | Displace any position with `current_score < 3.0` **or** `pnl_pct < -0.5%`. Pick worst by (lowest score, then worst PnL). |
| 2 | Competitive | `num_positions >= MAX` and `new_signal_score > 4.0` | Displace position with **lowest** current score if `score_delta > 1.0` (new_score − lowest). |
| 3 | Force-close | `num_positions == 5` and `new_signal_score > 4.5` | Displace position with lowest (entry) score, regardless of age/PnL. |
| 4 | Legacy (V1) | `num_positions >= MAX`, none of above | Age ≥ `DISPLACEMENT_MIN_AGE_HOURS`, \|PnL\| ≤ `DISPLACEMENT_MAX_PNL_PCT`, `score_advantage ≥ DISPLACEMENT_SCORE_ADVANTAGE`, and symbol not in `DISPLACEMENT_COOLDOWN_HOURS`. Pick best by score advantage. |

**Config (env):**

- `ENABLE_OPPORTUNITY_DISPLACEMENT` (default `true`)
- `DISPLACEMENT_MIN_AGE_HOURS` (default 4)
- `DISPLACEMENT_MAX_PNL_PCT` (default 0.01)
- `DISPLACEMENT_SCORE_ADVANTAGE` (default 2.0)
- `DISPLACEMENT_COOLDOWN_HOURS` (default 6)
- `MAX_CONCURRENT_POSITIONS` (default 16)

---

## 3. What gets logged

- **`logs/displacement.jsonl`:** `log_event("displacement", msg, **kw)` → various events:  
  `elite_tier_displacement_triggered`, `competitive_displacement_triggered`, `force_close_triggered`,  
  `close_position_api_called`, `close_position_verified` / `close_position_still_open` / `close_position_not_verified`,  
  `close_position_success` / `close_position_failed`, `executed`, `failed`, `candidate_found`, `no_candidates_found`, etc.
- **`logs/system_events.jsonl`:** Same events also emitted via `log_event` → `log_system_event` (subsystem `displacement`, event_type = msg).
- **`state/displacement_cooldowns.json`:** `symbol → datetime` for cooldown.
- **Exit attribution:** `log_exit_attribution` with `close_reason` including `displaced_by_<SYMBOL>`.

---

## 4. Interaction with risk limits and exits

- **Risk limits:** Displacement does not bypass position/notional limits. We only close one position and then open one; `MAX_CONCURRENT_POSITIONS` is unchanged.
- **Exits:** Displacement is an **exit reason**. The close is performed via `close_position_with_retries`. Exit logic (e.g. trail, stop, time exit) is separate; we do not re-trigger those when displacing.
- **Cooldown:** After a symbol is displaced, it’s logged in `displacement_cooldowns` and won’t be considered for displacement again for `DISPLACEMENT_COOLDOWN_HOURS`.

---

## 5. Files and symbols

| Item | Location |
|------|----------|
| `build_composite_close_reason` | `main.py` ~175–259 |
| `find_displacement_candidate` | `main.py` ~4153–4606 |
| `execute_displacement` | `main.py` ~4608–4776 |
| Displacement usage in loop | `main.py` ~7026–7066 |
| Config | `main.py` Config class, `config/registry.py` |
| Cooldown state | `state/displacement_cooldowns.json` |
| Logs | `logs/displacement.jsonl`, `logs/system_events.jsonl` |
