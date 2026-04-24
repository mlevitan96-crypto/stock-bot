# PROFIT_V2_RUNTIME_FLAG_ANALYSIS

## systemd-visible environment

From `systemctl show stock-bot -p ExecStart -p Environment -p FragmentPath` (stored in `_PROFIT_V2_DROPLET_RAW.json` → `phase0.show`):

- **ExecStart:** `/root/stock-bot/systemd_start.sh`
- **Environment:** truth router + score logging flags (see `PROFIT_V2_BASELINE_CONTEXT.md`)
- **`ALPACA_SIGNAL_CONTEXT_EMIT`:** **not** present in the inline `Environment=` line

## `ALPACA_SIGNAL_CONTEXT_EMIT` semantics (code)

- `telemetry/signal_context_logger.py`: default **`1`** (emit on) unless value is `0/false/no/off`.
- If `.env` or a drop-in sets emit off, systemd `show` may still **not** list it (loader-dependent). **Droplet `.env` was not exfiltrated** (secrets).

## Empirical outcome

- `logs/signal_context.jsonl`: **0 lines** after file exists on disk (mtime ~2026-03-30).  
- `verify_signal_context_nonempty.py` on droplet: **exit 2** (“zero valid JSONL rows”).

**Plausible classes (non-exclusive):**

1. **`ALPACA_SIGNAL_CONTEXT_EMIT` disabled** in a sourced env file not visible in `systemctl show` snippet.  
2. **Silent failures** inside `log_signal_context` (broad `except: pass` around body).  
3. **Process / deploy skew:** file touched but writer never successfully appended in this environment.

## Alpaca **data** URL (bars fetch)

- `.env` has `ALPACA_BASE_URL=https://paper-api.alpaca.markets` (probed on droplet).  
- Initial fetch implementation mapped “paper” → `https://data.sandbox.alpaca.markets`, producing **zero** bars for all symbols (exit code 4, 0 lines written).  
- **Evidence-based fix:** direct probe to `https://data.alpaca.markets` returned **HTTP 200** with `bars` for `SPY`.  
- `fetch_alpaca_bars_for_counterfactuals.py` was updated to use **`ALPACA_DATA_URL` if set, else `https://data.alpaca.markets`**, decoupling data host from paper **trading** base URL.

## Live stability

- Bars pull and replay scripts run **outside** `main.py`; **no** stock-bot restart required for this evidence.
