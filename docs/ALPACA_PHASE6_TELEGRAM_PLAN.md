# Alpaca Phase 6 — Telegram Notifications — Implementation Plan

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Optional Telegram notifications for governance outcomes (Tier 1/2/3 packets, convergence, promotion gate, heartbeat). Failures must NOT block reviews; failures logged to TELEGRAM_NOTIFICATION_LOG.md.  
**Context:** Existing Alpaca Telegram helpers (send_telegram_message.py, notify_governance_experiment_alpaca_*.py). Alpaca-only scope.

---

## 1. Notification Types

| Type | When | Message content (short) |
|------|------|--------------------------|
| Tier 1 packet | After Tier 1 review script succeeds | e.g. "Alpaca Tier1 review: <one_liner or packet dir>" |
| Tier 2 packet | After Tier 2 review script succeeds | e.g. "Alpaca Tier2 review: <one_liner or packet dir>" |
| Tier 3 packet | After Tier 3 review script succeeds | e.g. "Alpaca Tier3 review: <packet dir> scope <scope>" |
| Convergence summary | After convergence check | e.g. "Alpaca Convergence: <convergence_status> — <one_liner>" |
| Promotion gate status | After promotion gate run | e.g. "Alpaca Gate: gate_ready=<bool> — <one_liner>" |
| Heartbeat | After heartbeat run | e.g. "Alpaca Heartbeat: <one_liner>" |

All messages are short (one line or two). No secrets; no execution impact.

---

## 2. Integration

- **Shared helper:** One callable (e.g. `send_governance_telegram(text, log_path)`) that:
  - Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (same as existing scripts).
  - Sends `text` via Telegram API (requests.post).
  - On success: return. On failure (missing env, HTTP error, timeout): append one line to `log_path` with timestamp and error; **do not raise**; do not exit. So callers never see failure as fatal.
- **Log file:** `TELEGRAM_NOTIFICATION_LOG.md` at repo root (or under reports/audit). Format: append lines like `YYYY-MM-DD HH:MM:SS UTC — <script_name> — <error>`.
- **Per-script:** Each of: run_alpaca_board_review_tier1.py, run_alpaca_board_review_tier2.py, run_alpaca_board_review_tier3.py, run_alpaca_convergence_check.py, run_alpaca_promotion_gate.py, run_alpaca_board_review_heartbeat.py:
  - Add optional `--telegram` flag.
  - After successful state/packet write, if `--telegram`: call shared helper with a short message (e.g. one_liner or summary). If helper fails, script still exits 0 (failure already logged by helper).

**Failures do NOT block reviews:** Scripts do not exit non-zero when Telegram send fails. Helper catches and logs only.

---

## 3. Implementation Details

- **Helper location:** `scripts/alpaca_telegram.py` with function `send_governance_telegram(text: str, log_path: Path | None = None) -> bool`. If log_path is None, use REPO / "TELEGRAM_NOTIFICATION_LOG.md". Return True if sent, False if not (env missing or API failure).
- **Optional dependency:** `requests` (already used by existing Telegram scripts). If missing, log and return False.
- **No new cron:** Notifications are best-effort when scripts are run with --telegram (e.g. by existing cron or manual run).

---

## 4. Testing Plan

1. **Dry-run without --telegram:** All scripts run as today; no Telegram call. OK.
2. **With --telegram and env set:** Run one script (e.g. convergence) with TELEGRAM_* set → message sent (or logged on failure). Script exit 0.
3. **With --telegram and env unset:** Run script → no send; log line appended; script exit 0. CSA/SRE confirm no block.

---

## 5. Architecture Fit

- Reuses existing Telegram env vars and API. Single shared helper; minimal changes to each governance script. Fits ARCHITECTURE_AND_OPERATIONS (Telegram documented in §5). Alpaca-only.

---

STOP for CSA + SRE review.
