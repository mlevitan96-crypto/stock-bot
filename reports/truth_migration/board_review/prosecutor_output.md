# Prosecutor — CTR migration edge cases (assume it will break live trading)

**Persona:** Prosecutor. **Intent:** Find every edge case that could break live trading.

## 1. Permissions
- **CTR root** (`/var/lib/stock-bot/truth` or `STOCKBOT_TRUTH_ROOT`): Process may run as non-root; directory must exist and be writable by service user. If created at install time as root, `chown` to run user or service will fail on first write.
- **Legacy paths** under repo (`logs/`, `state/`, `data/`): Today written with process umask/cwd. If CTR is on a different volume (e.g. `/var/lib`), different mount options (noexec, quota) could cause writes to fail or behave differently.
- **systemd** `ReadWritePaths=` or `PrivateTmp=`: If unit restricts filesystem, CTR path must be explicitly allowed or writes will fail.

## 2. Paths and cwd
- **Relative vs absolute:** Legacy code uses both (e.g. `Path("logs/...")`, `_REPO_ROOT / "logs" / ...`). If WorkingDirectory is wrong (e.g. `/root` instead of `/root/stock-bot`), legacy writes go to wrong place; CTR must use absolute path derived from `STOCKBOT_TRUTH_ROOT` so it never depends on cwd.
- **Dashboard/audit scripts** run from repo root on droplet; if they later read from CTR, path must be resolved the same way (env or config), not cwd-relative.

## 3. systemd env
- **TRUTH_ROUTER_ENABLED=0** must be default. If someone sets it in a drop-in and forgets, and CTR is misconfigured, trading could break. Mitigation: router must no-op when disabled (no write to CTR, no exception).
- **TRUTH_ROUTER_MIRROR_LEGACY=1**: When enabled, legacy write must always happen first or in parallel; if CTR write fails, legacy must still succeed. Order of operations: write legacy, then write CTR; catch and log CTR errors only.
- **Missing STOCKBOT_TRUTH_ROOT**: Router should default to `/var/lib/stock-bot/truth` and ensure parent exists; if default path not writable, router should disable itself and log (not crash).

## 4. Stale / partial writes
- **Atomic JSON:** Router must write to `.tmp` then `rename`; if process is killed mid-write, legacy file could be truncated. Legacy callers already use atomic_write in some places; router must not replace legacy write with a non-atomic one.
- **JSONL append:** Append is inherently non-atomic (last line can be partial). Mitigation: don’t use CTR as sole source until mirror period is over; readers validate last line is valid JSON.
- **Heartbeat:** If heartbeat write fails (e.g. disk full), we must not block the main write. Heartbeat update should be best-effort after successful stream write.

## 5. Multiple processes
- **Dashboard + main.py:** Both may write if dashboard ever writes to truth; single heartbeat file could see races. Use single writer (main loop) for heartbeat or use file locking.
- **UW daemon:** Does not write gate/exit truth; no conflict.

## 6. EOD / audit failures
- **“No silent inference”:** If audit reads from CTR and CTR is empty (router was off), audit must FAIL loudly with clear message (“CTR stream X missing or stale; TRUTH_ROUTER_ENABLED?”), not fall back to inferring from logs.
- **Freshness threshold:** If we require “last write &lt; 600s” and market is closed for 24h, legitimately no new writes. EOD should allow “stale but present” when market closed or use “last trading day” semantics.

## 7. Rollback
- **Instant rollback:** Setting `TRUTH_ROUTER_ENABLED=0` and restart must restore exact previous behavior. No code path should require CTR to be present when disabled.
- **Legacy paths:** Must remain the authoritative read source for dashboard/EOD until gates pass; no “prefer CTR if present” in Phase 1 for readers.

## 8. Summary of risks
| Risk | Mitigation |
|------|------------|
| CTR dir not writable | Router checks once at first write; disables self and logs; legacy unchanged |
| Partial JSON write | Atomic write (temp + rename) for JSON; JSONL append last-line validation in readers |
| Wrong cwd | CTR path always from env or default absolute path |
| systemd env typo | Default TRUTH_ROUTER_ENABLED=0; no-op when disabled |
| Mirror order | Always write legacy first; CTR second; catch CTR errors |
| EOD false fail | Document “market closed” vs “stale” policy; optional override for closed days |
