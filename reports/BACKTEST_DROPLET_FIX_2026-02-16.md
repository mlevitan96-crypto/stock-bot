# Backtest-on-Droplet: Root Cause and Fixes (2026-02-16)

## Why the run never finished

1. **SSH/Paramiko does not enforce long timeouts**  
   `exec_command(command, timeout=7200)` and `channel.recv_exit_status()` do **not** reliably limit runtime. Paramiko’s timeout is for channel open; for long values (e.g. 2 hours) it often does nothing, and `recv_exit_status()` can block indefinitely. So the local script waited forever for the droplet command to “finish,” even when the droplet had already finished or when the droplet side was stuck.

2. **Injection phase could run indefinitely**  
   Phase 2 (`inject_signals_into_backtest_dir.py`) loads bars per (symbol, date) and can do thousands of Alpaca requests. On the droplet, rate limits or slow responses can make this take a very long time or hang. There was no cap on how long injection could run, so the overall script could run for hours and never exit.

3. **No real timeout in DropletClient**  
   The client relied on Paramiko’s timeout and blocking `recv_exit_status()`, so the process never got control back after a fixed time.

---

## Fixes applied

### 1. Real timeout in `droplet_client._execute` (already present)

- Use a **deadline** and poll `channel.exit_status_ready()` in a loop instead of blocking on `recv_exit_status()`.
- Read stdout/stderr in a **background thread** so the channel is drained and the remote process can complete.
- If the deadline is reached before the command exits, **close the channel** and return exit code **124** (same as `timeout(1)`), with whatever output was captured.
- The caller now gets control back after at most `timeout` seconds (e.g. 7200) and can see partial output.

### 2. Cap injection time on the droplet

- In `board/eod/run_30d_backtest_on_droplet.sh`, the Block 3G inject step is wrapped in:
  - `timeout 2700 python3 scripts/inject_signals_into_backtest_dir.py ...`
- **2700 seconds = 45 minutes** max for injection. If it doesn’t finish (e.g. Alpaca slow/rate-limited), the step exits and the script continues with validation and commit/push.
- Phase 1 (backtest with `--no-inject`) already produced all required artifacts; validation only needs those. So the run **always completes**: either with full injection + signal edge report, or with backtest artifacts only (injection can be run later locally if needed).

### 3. Driver handling of timeout (exit 124)

- In `scripts/run_backtest_on_droplet_and_push.py`, when the droplet command returns **124**:
  - Print a clear message that the command timed out after 2 hours.
  - Suggest checking GitHub for the new backtest dir or re-running with `BACKTEST_DAYS=7`.
  - Return 124 to the caller.

---

## How to run and what to expect

- **Full run (30 days):**  
  `python scripts/run_backtest_on_droplet_and_push.py`  
  - Expect: phase 1 (backtest) + phase 2 (inject, max 45 min) + validate + commit/push, all within the 2h SSH timeout. If injection finishes, you get a 3G dir with `SIGNAL_EDGE_ANALYSIS_REPORT.md` and full signal buckets; if injection hits the 45 min cap, you still get the backtest dir and can run injection locally later.

- **Faster check (7 days):**  
  `set BACKTEST_DAYS=7` (Windows) or `export BACKTEST_DAYS=7` (Unix), then run the same script. Fewer events and less injection work, so the run should finish well under 1 hour.

- **If you see exit code 124:**  
  The remote command hit the 2h limit. Inspect the printed stdout/stderr to see how far it got (e.g. phase 1 done, inject in progress). Pull the latest from GitHub; the droplet may have pushed before the client timed out. If not, SSH to the droplet and run the shell script there, or re-run with `BACKTEST_DAYS=7`.

---

## Verification

- **DropletClient:** `_execute` uses a timer, `exit_status_ready()` polling, and returns 124 on timeout.
- **Shell script:** Inject step is `timeout 2700 ... || true` so the script never hangs on injection.
- **Driver:** Handles `rc == 124` and prints guidance.

These changes ensure the backtest-on-droplet flow **always finishes** (either success or timeout with partial output) and no longer blocks for 24+ hours.
