# ALPACA unified exit attribution zero — root cause + vacuous ARMED fix (full proof)

**Timestamp (artifact):** 20260325_1702Z  
**Environment:** Alpaca droplet `/root/stock-bot`, repo `main` @ `db0410a` (post-push).

---

## Plan confirmation (requested)

1. **Plan restated:** Establish post-deploy terminal-close facts → if zero, stop valid → else trace emitter, add additive diagnostics, surface silent failures via `learning_blocker`, fix vacuous ARMED when `trades_seen==0`, prove on live logs, write proof artifacts.
2. **Missed failure modes (review):** (a) Confusing validator API (`if validate(): return` on a **list**) obscuring intent — addressed by explicit `issues` + blockers. (b) `_append_jsonl` swallowing IO errors — addressed with `alpaca_jsonl_append_failed`. (c) Wrong `ROOT` in ad-hoc droplet scripts — documented; production uses package-relative `REPO`. (d) `DEPLOY_START` stale after restart — document epoch refresh. (e) ARMED with zero trades — fixed.
3. **PLAN_VERDICT:** **APPROVE** (executed).

---

## Phase 0 — Facts (SRE)

Executed on droplet after `git pull`:

- **UTC:** `Wed Mar 25 17:01:08 UTC 2026` (audit command bundle).
- **Uptime:** `up 30 days, 1 min` (representative).
- **`stock-bot.service`:** `active`; last start before pull: `Wed 2026-03-25 16:30:40 UTC` (`ActiveEnterTimestamp`).
- **Post-deploy terminal closes** (script `scripts/alpaca_post_deploy_terminal_close_audit.py`, `DEPLOY_START=1774456240`):
  - `terminal_closes_since_deploy_count_exit_attribution`: **30**
  - `terminal_closes_since_deploy_count_orders_close_position`: **30**
  - **Examples (≤5):** MS, XLE, LOW, WFC, JPM at times shown in summary JSON (~`16:54:13Z`–`16:54:24Z` on 2026-03-25).

---

## Phase 1 — Terminal closes == 0?

**Not applicable** — count is 30 / 30.

---

## Phase 2–3 — Emitter path and silent failures

### Path

1. `append_exit_attribution` writes `logs/exit_attribution.jsonl`, then calls `emit_exit_attribution` (see `src/exit/exit_attribution.py`).
2. `emit_exit_attribution` validates, appends dedicated exit JSONL, then unified:

```159:228:src/telemetry/alpaca_attribution_emitter.py
def emit_exit_attribution(
    ...
) -> None:
    ...
    exit_issues = validate_exit_attribution(base)
    unified_p = LOG_DIR / "alpaca_unified_events.jsonl"
    if exit_issues:
        ...
        _maybe_diag_unified_exit_emit(str(trade_id), unified_p, False, "validation:" + ";".join(exit_issues[:5]))
        return
    _append_jsonl(_exit_log_path(), base, symbol=str(symbol), purpose="dedicated_exit_attribution")
    if LOG_DIR.exists():
        unified_rec = {"event_type": "alpaca_exit_attribution", **base}
        _append_jsonl(unified_p, unified_rec, symbol=str(symbol), purpose="alpaca_unified_exit")
        _maybe_diag_unified_exit_emit(str(trade_id), unified_p, True, "written")
```

### Live proof

- `grep -c alpaca_exit_attribution /root/stock-bot/logs/alpaca_unified_events.jsonl` ⇒ **31** (includes historical lines; strictly > 0).
- Sample tail line includes real symbol **XLE**, `terminal_close`, `trade_key`, timestamps — not synthetic.

### Visibility (no trading impact)

- Wrapper exceptions → `learning_blocker` `unified_exit_emit_exception` with truncated traceback.
- Validation / append failures → `alpaca_exit_validation_blocked` / `alpaca_jsonl_append_failed`.

---

## Phase 4 — Vacuous ARMED

Strict gate now blocks when **no trades** in window:

```191:220:telemetry/alpaca_strict_completeness_gate.py
    vacuous_zero_trades = len(closed) == 0
    blocked = bool(precheck) or vacuous_zero_trades or (len(closed) - complete) > 0 or structural
    ...
        elif vacuous_zero_trades:
            learning_fail_closed_reason = "NO_POST_DEPLOY_PROOF_YET"
```

CLI: `scripts/alpaca_strict_completeness_gate.py --open-ts-epoch <epoch>` for post-deploy windows.

---

## Phase 5 — Live proof commands

```bash
grep -c alpaca_exit_attribution /root/stock-bot/logs/alpaca_unified_events.jsonl
python3 scripts/alpaca_strict_completeness_gate.py --root /root/stock-bot --open-ts-epoch 1774456240
```

**Observed:** grep **31**; gate `trades_seen=30`, `trades_complete=0`, `trades_incomplete=30`, `LEARNING_STATUS=BLOCKED`, `learning_fail_closed_reason=incomplete_trade_chain`.

**Interpretation:** Unified **exit** events exist; strict **learning chain** (entry attribution, orders `canonical_trade_id`, exit_intent, etc.) is still incomplete for those trades — **fail-closed** preserved.

---

## Phase 6 — Service refresh

`sudo systemctl restart stock-bot.service` at **2026-03-25T17:01:20Z** (epoch **1774458080**) to load new telemetry wrapper code. Trading continues under same strategy/execution semantics (additive telemetry only).

---

## Artifacts

- This file: `reports/ALPACA_UNIFIED_EXIT_ZERO_ROOTCAUSE_PROOF_20260325_1702Z.md`
- Summary: `reports/ALPACA_UNIFIED_EXIT_ZERO_ROOTCAUSE_PROOF_SUMMARY_20260325_1702Z.md`
- Same paths on droplet under `/root/stock-bot/reports/` (uploaded after generation).
