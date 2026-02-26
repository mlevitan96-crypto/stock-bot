# Strategic review and path to profitability

**Date:** 2026-02-26  
**Purpose:** Review the full plan through multiple lenses, then recommend a concrete path and alternatives to reach a profitable trading bot.

---

## 1. What the “entire plan” is (current state)

| Layer | What exists | Evidence / status |
|-------|-------------|-------------------|
| **Entry** | Composite score (flow, dark_pool, insider, iv_skew, event, market_tide, greeks, etc.), MIN_EXEC_SCORE gate, expectancy gate | Trading env: 150 trades, entry_score 2.5–4.4; win rate 35.3%; high bucket (≥3.5) still losing on average |
| **Exit** | v2 exit (signal_decay, flow_reversal, etc.), grid search, promotion | First 100 paper trades after promotion: mix of small wins/losses; exit reasons logged |
| **Truth & evidence** | 30d truth, WTD slice, attribution + exit_attribution, effectiveness (blame, signal_effectiveness, exit_effectiveness) | WTD review: best policy **-$8.25** (all 52 with ≥50 trades negative). Blame baseline needed before next lever |
| **UW** | uw_flow_cache, canonicalization, forward-returns stub, UW-conditioned policy hunt | Canonical events ≥100; profit hunt ran 250+ rounds but policy format bug + truth has no price → forward-return join empty; simulator ignores UW gating |
| **Governance** | PATH_TO_PROFITABILITY loop, LOCK/REVERT on 50 trades, change proposals, multi-model board | PROFITABILITY_ACCELERATION: get blame first; gate on trade count; if weak_entry > exit_timing → entry lever |
| **Discovery** | Percent-move intelligence, contextual policies, win finding, big board edge, exit grid | Many pipelines; best backtest bands (e.g. 1.5–2.0) not yet confirmed in live; live still net negative |

**Bottom line:** We have observability, governed tuning, and many discovery scripts. Live paper is still losing (35% win rate, -$6.52 on 150 trades). We have not yet **closed the loop**: one blame baseline → one correct lever (entry vs exit) → one small change → 50-trade paper check → lock or revert.

---

## 2. Review through multiple personas

### Adversarial

- **Risk:** We keep adding *new* pipelines (WTD, UW profit hunt, UW discover) instead of **fixing the one thing that would tell us what to fix** (entry vs exit blame). More discovery with the same entry/exit stack just re-confirms “nothing is profitable yet.”
- **Risk:** WTD and UW hunt both show “best policy still negative.” That’s consistent with “either we’re picking bad trades (entry) or we’re closing them wrong (exit).” Without blame we’re guessing.
- **Risk:** Expectancy gate is blocking heavily (score_floor_breach; ledger shows low scores). If the *only* trades getting through are marginal, we may be selecting for bad expectancy by construction.
- **Do not:** Add another exit overlay or another discovery run before we have **one** effectiveness run from logs that produces `entry_vs_exit_blame.json` with ≥5 (ideally ≥10) losing trades and a clear weak_entry_pct vs exit_timing_pct.

### Quant

- **Evidence needed:** Single effectiveness run from droplet logs: `run_effectiveness_reports.py --start ... --end ... --out-dir reports/effectiveness_baseline_blame`. Require: join works, `joined_count` ≥ 30, `total_losing_trades` ≥ 5. Then `generate_recommendation.py` → decision.
- **Rule:** If `weak_entry_pct > exit_timing_pct` → next lever = **entry** (e.g. down-weight worst signal from signal_effectiveness, or raise MIN_EXEC_SCORE). If `exit_timing_pct ≥ weak_entry_pct` → exit levers remain justified; use exit_effectiveness + giveback to pick one exit tweak.
- **Trade count over calendar:** Gate all LOCK/REVERT on **≥50 closed trades** in the relevant period (paper overlay window or baseline window). No LOCK on &lt;30 trades; early REVERT only if ≥30 and metrics clearly worse (e.g. win_rate &lt; baseline - 3% or giveback &gt; baseline + 0.05).
- **WTD vs 30D:** WTD “all negative” is useful: it says this week no policy beat zero. Compare WTD vs 30D entry_exit_intelligence to see if signals/exhaustion look different; that can justify “pause entries” or “tighten threshold” even before blame, as a **risk brake**, not the main profit lever.

### Product / Operator

- **One canonical baseline:** Designate one effectiveness dir (e.g. `reports/effectiveness_baseline_blame`) as the **source of truth** for “entry vs exit?” and for pre-paper baseline. Update it when we have new logs; don’t fragment into many ad-hoc dirs.
- **Checklist:** (1) Run effectiveness from logs → blame + signal_effectiveness. (2) If weak_entry &gt; exit_timing → one entry overlay (worst signal down-weight or threshold up). (3) If exit_timing ≥ weak_entry → one exit overlay from recommendations. (4) Paper run with that overlay only. (5) When closed trades in overlay period ≥ 50 → run effectiveness on that period → compare to baseline → LOCK or REVERT. (6) Repeat with one lever at a time.
- **Success definition for “path to profitability”:** First, **stop guessing** (blame baseline). Second, **one correct lever** applied and measured. Third, **positive expectancy over 50+ trades** in paper (or clear improvement in win rate / giveback vs baseline).

### Execution / SRE

- **Data integrity:** Ensure droplet logs (attribution, exit_attribution) have join keys (entry_timestamp or trade_id) so effectiveness join succeeds. If join fails, fix logging first; everything else depends on it.
- **Expectancy gate:** Investigate why scores in ledger are so low (0.17–1.05) vs MIN_EXEC_SCORE (e.g. 2.5). If scores are pre-adjust and post-adjust is higher, ensure gate truth and dashboard reflect the same logic. If the universe is genuinely low-score, consider whether the gate is too high (no trades) or the signal pipeline is broken (no good scores).

### Risk

- **Pause vs tighten:** If WTD and recent paper are both negative, a **temporary pause** (no new entries) or **raise MIN_EXEC_SCORE** (fewer, higher-quality entries) can reduce drawdown while we fix the lever. Document as explicit risk brake, not a permanent strategy.
- **UW and “massive profit hunt”:** UW canonical events exist; the hunt proved the loop runs but current simulator doesn’t use UW gating (premium/size/dte). Until we (a) add price to truth or bar-based forward returns and (b) implement UW gating in the simulator, UW-conditioned policies are not actually conditioned. So: **don’t rely on UW hunt for profit yet**; use it as a future path once entry/exit baseline is fixed and we have bar-based or price-series data.

---

## 3. Path forward (recommended)

**Phase A — Unblock the one decision we need (24–48 h)**  
1. On droplet (or with synced logs), run effectiveness from logs for the longest available window:  
   `python scripts/analysis/run_effectiveness_reports.py --start YYYY-MM-DD --end YYYY-MM-DD --out-dir reports/effectiveness_baseline_blame`  
2. Fix join if needed (attribution ↔ exit_attribution); require `joined_count` ≥ 30, `total_losing_trades` ≥ 5.  
3. Run `generate_recommendation.py` on that dir.  
4. **Decision:** If weak_entry_pct &gt; exit_timing_pct → Phase B1 (entry). Else → Phase B2 (exit).

**Phase B1 — One entry lever**  
1. From signal_effectiveness, pick the **single worst** signal (min win_rate, trade_count ≥ 5).  
2. Create **one** tuning overlay: down-weight that signal (e.g. -0.05 or half weight) or slightly raise MIN_EXEC_SCORE.  
3. Enable overlay in paper only. No exit overlay in the same cycle.  
4. When closed trades in overlay period ≥ 50 → effectiveness on that period → compare to baseline → LOCK (if win_rate ≥ baseline - 2%, giveback ≤ baseline + 0.05) or REVERT.

**Phase B2 — One exit lever**  
1. Use exit_effectiveness + recommendation: one exit weight or one rule change (e.g. flow_deterioration or score_deterioration).  
2. Enable in paper only. No entry overlay in the same cycle.  
3. Same 50-trade gate and comparison → LOCK or REVERT.

**Phase C — Repeat and optional brakes**  
1. After first LOCK, repeat: new effectiveness → new recommendation → one lever → 50-trade check.  
2. If paper or WTD stays negative and we’re waiting for data, consider a **temporary** brake: raise MIN_EXEC_SCORE to reduce volume and drawdown, or pause new entries until blame is in and first lever is applied.

---

## 4. Other ideas to make money (alternatives / additions)

- **Tighten first, learn second:** Raise MIN_EXEC_SCORE (e.g. to 3.0 or 3.2) so only the strongest signals trade. Fewer trades, potentially better win rate. Measure over 50 trades; if win rate and expectancy improve, keep; else revert.  
- **Regime filter:** Use structural_intelligence (regime, market_context_v2) to **disable or reduce size** in clearly adverse regimes (e.g. high vol, strong down-trend). Reduces drawdown in bad environments; we still need entry/exit fix for positive expectancy in normal regimes.  
- **Symbol filter:** If signal_effectiveness or blame shows certain symbols or sectors lose more, exclude or down-weight them in the universe until we have a positive baseline.  
- **Cost and size:** Ensure commissions and slippage are in backtest and in paper PnL. If we’re barely negative, reducing size or improving execution can flip sign.  
- **One strategy at a time:** We have equity + wheel. Run profitability loop on **equity only** first; get that to positive 50-trade expectancy, then add or adjust wheel.  
- **UW as an overlay, not a replacement:** Once entry/exit baseline is profitable, use UW (flow, sweeps) as an **extra filter**: e.g. only take composite entries when UW flow agrees (premium/size in range). Don’t let UW replace the need to fix entry/exit first.  
- **Bar-based forward returns:** Add entry_price (or bar-based series) to truth so UW forward-return labels are real. Then re-run UW hunt with actual conditioning and bar-based horizons; that can surface UW-specific edges as a **second** profit layer.  
- **Win-finding and edge discovery as research:** Keep running win finding, contextual edge, percent-move intelligence as **research**. Use their output to propose **candidate** overlays (e.g. new entry_score_min or hold_minutes bands), then validate with the same 50-trade effectiveness loop before promoting.

---

## 5. What to do first (concrete)

1. **This week:** Produce **one** blame baseline (effectiveness from logs, join working). Decide entry vs exit.  
2. **Next:** Apply **one** lever (entry or exit), paper only, and run to 50 closed trades.  
3. **Then:** Compare, LOCK or REVERT, and repeat with the next lever.  
4. **Optional:** If you want to reduce drawdown while waiting, raise MIN_EXEC_SCORE or pause new entries temporarily; document as a risk brake.  
5. **Defer until baseline is profitable:** Relying on UW profit hunt or more discovery pipelines to “find” a winning policy without fixing entry/exit first.  

**Goal:** Win trades and be profitable. The highest-leverage step is **one blame baseline + one correct lever + one 50-trade check**. Everything else (WTD, UW, more discovery) supports that or comes after.
