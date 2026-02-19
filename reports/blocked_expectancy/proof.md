# Blocked-expectancy post-fix proof (droplet)

**Fix applied:** MIN_EXEC_SCORE default 3.0 → 2.5 (config/registry.py). Expectancy floor follows MIN_EXEC_SCORE.

**After redeploy:**

1. Run open-orders investigation on droplet (or capture gate cycle_summary):
   ```bash
   python3 scripts/run_open_orders_investigation_on_droplet.py
   ```
   Or on droplet:
   ```bash
   cd /root/stock-bot && tail -100 logs/gate.jsonl | grep -A2 cycle_summary
   ```

2. **Post-fix gate summary (fill after observation):**
   - considered: ___
   - gate_counts: ___
   - orders: ___

3. **Verdict:** TRADES ADMITTED (orders > 0) or STILL BLOCKED (reason: ___).
