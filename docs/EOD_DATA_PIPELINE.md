# EOD Data Pipeline

End-of-day (EOD) reporting for the stock-bot uses a canonical 8-file bundle under the repo root. This document describes paths, workflow, and scripts. **All paths are relative to the stock-bot repo root.** No references to any other repository.

---

## 1. Canonical bundle paths (do not move/rename)

| # | Relative path | Description |
|---|----------------|-------------|
| 1 | `logs/attribution.jsonl` | One record per closed trade (P&L, context). |
| 2 | `logs/exit_attribution.jsonl` | One record per exit (reason, P&L, components). |
| 3 | `logs/master_trade_log.jsonl` | Trade entries/exits (trade_id, symbol, entry_ts, exit_ts). |
| 4 | `state/blocked_trades.jsonl` | Blocked trade records (reason, score, symbol). |
| 5 | `state/daily_start_equity.json` | Session baseline equity. |
| 6 | `state/peak_equity.json` | Peak equity for drawdown. |
| 7 | `state/signal_weights.json` | Adaptive weights / component state. |
| 8 | `state/daily_universe_v2.json` | Daily universe (symbols). |

On the droplet, repo root is `/root/stock-bot`; the same relative paths apply.

---

## 1.1 Extended canonical (vNext)

These paths are **optional** and do not replace the 8-file canonical list. When present, the EOD runner includes them in the bundle summary and memo.

| Relative path | Description |
|---------------|-------------|
| `state/symbol_risk_snapshot.json` | Daily per-symbol risk/stress snapshot (producer: `scripts/generate_symbol_risk_snapshot.py`; overwritten each day). EOD runner copies to `board/eod/out/symbol_risk_snapshot_<DATE>.json` and writes `symbol_risk_snapshot_<DATE>.md`. If missing/empty, bundle lists it as missing_file. |

---

## 2. EOD runner

- **Script:** `board/eod/run_stock_quant_officer_eod.py`
- **Contract:** `board/quant_officer_contract.md` (fallback: `board/stock_quant_officer_contract.md`)
- **Behavior:**
  - Resolves bundle paths with `(REPO_ROOT / rel).resolve()`.
  - Missing file → `log.error("Bundle file missing: %s", path)`, `data[name] = None`, skip load.
  - Empty file → `log.warning("Bundle file empty: %s", path)`, set `[]` or `None`, skip load.
  - Prepends prompt with: *"Ignore any prior context. Use ONLY the EOD bundle summary below."*
  - Linux: no prompt truncation. Windows: `MAX_PROMPT_LEN` truncation for CLI.
  - Session: `CLAWDBOT_SESSION_ID="stock_quant_eod_$(date -u +%Y-%m-%d)"` (date-scoped).
- **Outputs (on success):**
  - `board/eod/out/quant_officer_eod_<DATE>.json`
  - `board/eod/out/quant_officer_eod_<DATE>.md`
- **On parse failure:** writes raw response to `board/eod/out/<DATE>_raw_response.txt`, exit 1.

---

## 3. Memo content

The generated memo must include:

- Key metrics summary + table
- Regime context
- Sector context
- Parameter recommendations (priority + rationale)
- Risk flags
- Monitoring gaps
- Open questions for Chairman (checklist)

---

## 4. Cron

- **EOD cron:** 21:30 UTC, weekdays (Mon–Fri).
- **Session:** Date-scoped `stock_quant_eod_$(date -u +%Y-%m-%d)`.
- **Installed by:** `board/eod/install_eod_cron_on_droplet.py` (or `scripts/` equivalent if present).
- **Sync cron:** 21:32 UTC weekdays via `scripts/droplet_sync_to_github.sh` (push EOD outputs to GitHub).
- **Symbol risk snapshot (optional):** Run `python3 scripts/generate_symbol_risk_snapshot.py` before EOD (e.g. 21:28 UTC) so `state/symbol_risk_snapshot.json` is present for the EOD bundle. Manual run or future cron hook.

---

## 5. Sync and local fetch

- **Droplet → GitHub:** `scripts/droplet_sync_to_github.sh` (run on droplet). May hit conflicts; align repo with `origin/main` if needed.
- **GitHub → local (repeatable, recommended):** Run **after** droplet sync (e.g. weekdays after 21:35 UTC):
  - **Windows (PowerShell):** `.\scripts\pull_eod_to_local.ps1`
  - **Git Bash / Linux:** `bash scripts/pull_eod_to_local.sh`
  - These scripts fetch, align `board/eod/out/` with `origin/main`, and pull so you always get the latest EOD without conflicts. Optionally schedule (e.g. Windows Task Scheduler) for the same time each weekday.
- **Droplet → local `board/eod/out/` (direct):** `scripts/local_sync_from_droplet.sh` (SCP; needs `DROPLET_IP` or `droplet_config.json`).
- **Droplet → local `EOD--OUT/`:** `scripts/fetch_eod_to_local.py` (SFTP).

---

## 6. Manual run on droplet

```bash
cd /root/stock-bot
export CLAWDBOT_SESSION_ID="stock_quant_eod_$(date -u +%Y-%m-%d)"
python3 board/eod/run_stock_quant_officer_eod.py
```

Dry-run (no Clawdbot call):

```bash
python3 board/eod/run_stock_quant_officer_eod.py --dry-run
```

---

*End of EOD Data Pipeline.*
