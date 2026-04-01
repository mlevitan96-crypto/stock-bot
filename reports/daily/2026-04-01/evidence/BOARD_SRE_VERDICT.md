# Board — SRE verdict

- **Ops:** `git pull`, `systemctl restart stock-bot`, and one-off backfill are low-risk; backfill only appends `logs/strict_backfill_*`.
- **Env:** Startup banner confirms `strict_runlog_effective` and `run.jsonl` path — reduces “wrong flags” ambiguity.
- **New failure modes:** Minimal. **Observed:** `evaluate_exits` traceback on droplet after deploy; mitigated by skipping non-dict `opens` info (defensive). Monitor `opens_info_not_dict` events.
- **Permissions:** Backfill wrote successfully as the service user on `/root/stock-bot/logs`.
