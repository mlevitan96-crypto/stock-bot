# ALPACA_INTEGRITY_CLOSURE_CONTEXT (Phase 0 — droplet capture)

## Addendum (post-mission)

- **Follow-up:** Untracked `ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_*.json` blocked `git pull`; moved aside, **fast-forward to `e8133504`**, **`/etc/systemd/system/*.service` copied from repo**, `daemon-reload` executed. Evidence in `ALPACA_TELEGRAM_LOCKDOWN_IMPLEMENTATION.md` / `ALPACA_TELEGRAM_PROD_ENABLEMENT_PROOF.md` reflects **live** unit contents.
- **Droplet `HEAD` after pull:** `e813350493ed235261d2092f2c9b7ecb8e66dc53`.

### git_pull (exit 1)

```
From https://github.com/mlevitan96-crypto/stock-bot
 * branch              main       -> FETCH_HEAD
   0d9ec040..e8133504  main       -> origin/main
error: The following untracked working tree files would be overwritten by merge:
	reports/daily/2026-04-01/evidence/ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_20260401_191124Z.json
Please move or remove them before you merge.
Aborting
Updating 0d9ec040..e8133504

```

### git_head_utc_et (exit 0)

```
0d9ec04088ec28cb15d2995df1fcba7b5736f3a7
Wed Apr  1 19:26:17 UTC 2026
2026-04-01

```

### stock_bot_status (exit 0)

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Wed 2026-04-01 18:36:53 UTC; 49min ago
   Main PID: 1847213 (systemd_start.s)
      Tasks: 32 (limit: 9483)
     Memory: 763.1M (peak: 770.9M)
        CPU: 31min 41.872s
     CGroup: /system.slice/stock-bot.service
             ├─1847213 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1847215 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1847221 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1847232 /root/stock-bot/venv/bin/python -u main.py
             └─1847256 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,797 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2190
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,815 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9510
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,839 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.0800
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,858 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.7210
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,877 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.8890
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,895 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2150
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,912 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7600
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,931 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9570
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,956 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.9220
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,981 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.8360

```

### ps_stock_bot (exit 0)

```
root     1751296  7.8  1.2 106340 97632 ?        Ss   Mar30 236:02 /root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py
root     1781963  0.1  2.9 873004 235836 ?       Ssl  Mar31   2:14 /usr/bin/python3 /root/stock-bot/dashboard.py
root     1839160  0.0  0.0   7740  3544 ?        Ss   16:45   0:00 bash -c bash -lc cat /root/stock-bot/reports/daily/2026-04-01/evidence/ALPACA_250_THRESHOLD_FINAL_VERDICT.md; echo ---; head -100 /root/stock-bot/reports/daily/2026-04-01/evidence/ALPACA_250_MILESTONE_NOTIFIER_STATE.md
root     1847213  0.0  0.0   7740  3496 ?        Ss   18:36   0:00 /bin/bash /root/stock-bot/systemd_start.sh
root     1847215  0.1  1.4 588504 121396 ?       Sl   18:36   0:05 /root/stock-bot/venv/bin/python deploy_supervisor.py
root     1847221  0.0  1.2 404188 103068 ?       Sl   18:36   0:01 /root/stock-bot/venv/bin/python -u dashboard.py
root     1847232 63.7  5.9 1619564 480872 ?      Sl   18:37  31:18 /root/stock-bot/venv/bin/python -u main.py
root     1847256  0.4  1.3 393752 109436 ?       Sl   18:37   0:13 /root/stock-bot/venv/bin/python heartbeat_keeper.py

```

### journal_stock_bot (exit 0)

```
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for MSFT
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MSFT: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for GOOGL
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GOOGL: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for AMZN
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: AMZN: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for META
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: META: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for NVDA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NVDA: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for TSLA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: TSLA: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for AMD
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: AMD: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for NFLX
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NFLX: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for INTC
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: INTC: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for SPY
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SPY: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for QQQ
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: QQQ: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for IWM
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: IWM: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for DIA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: DIA: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLF
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLF: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLE
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLE: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLK
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLK: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLV
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLV: 100 normalized, 11 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLI
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLI: 100 normalized, 11 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XLP
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLP: 100 normalized, 11 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for JPM
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: JPM: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for BAC
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BAC: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for GS
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GS: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for MS
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MS: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for C
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: C: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for WFC
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: WFC: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for BLK
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BLK: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for V
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: V: 100 normalized, 12 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for MA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MA: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for COIN
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COIN: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for PLTR
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: PLTR: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for SOFI
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SOFI: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for HOOD
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: HOOD: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for RIVN
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: RIVN: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for LCID
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: LCID: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for F
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: F: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for GM
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GM: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for NIO
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NIO: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for BA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BA: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for CAT
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: CAT: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for XOM
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XOM: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for CVX
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: CVX: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for COP
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COP: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for SLB
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SLB: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for JNJ
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: JNJ: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for PFE
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: PFE: 100 normalized, 14 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for MRNA
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MRNA: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for UNH
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: UNH: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for WMT
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: WMT: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for TGT
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: TGT: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for COST
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COST: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for HD
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: HD: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Found 100 raw trades for LOW
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: LOW: 100 normalized, 13 passed filter
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Cache mode active - composite scoring will run even if flow_trades empty (689 trades from flow, 56 symbols in cache)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Maps built: 53 dark_pool, 53 gamma, 53 net_premium
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Fetched data, clustering 689 trades
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Initial flow_trades clusters=6, use_composite=True
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Running composite scoring for 53 symbols (flow_trades may be empty)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Processing 54 symbols (5 from clusters, 53 from cache)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for LCID (symbol 1/54)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: LCID composite_score=3.944
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to LCID: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to LCID: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for LCID: score=4.74, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: LCID score=4.74
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for COIN (symbol 2/54)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COIN composite_score=3.970
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to COIN: +0.30 (sector=Financial, count=12)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to COIN: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for COIN: score=4.77, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: COIN score=4.77
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for JPM (symbol 3/54)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: JPM composite_score=2.119
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to JPM: +0.30 (sector=Financial, count=12)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to JPM: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for JPM: score=2.92, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: JPM score=2.92
Apr 01 19:23:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for DIA (symbol 4/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: DIA composite_score=2.170
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to DIA: +0.30 (sector=ETF, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to DIA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for DIA: score=2.97, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: DIA score=2.97
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for SLB (symbol 5/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SLB composite_score=3.712
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to SLB: +0.30 (sector=Energy, count=4)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to SLB: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for SLB: score=4.51, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: SLB score=4.51
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for GOOGL (symbol 6/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GOOGL composite_score=3.126
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to GOOGL: +0.30 (sector=Technology, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to GOOGL: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for GOOGL: score=3.93, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: GOOGL score=3.93
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for TGT (symbol 7/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: TGT composite_score=3.601
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to TGT: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to TGT: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for TGT: score=4.40, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: TGT score=4.40
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for UNH (symbol 8/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: UNH composite_score=3.516
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to UNH: +0.30 (sector=Healthcare, count=4)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to UNH: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for UNH: score=4.32, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: UNH score=4.32
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for IWM (symbol 9/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: IWM composite_score=1.713
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to IWM: +0.30 (sector=ETF, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to IWM: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for IWM: score=2.51 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: IWM score=2.51 reason=score=2.51 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for IWM: score=2.51 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for SPY (symbol 10/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SPY composite_score=1.391
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to SPY: +0.30 (sector=ETF, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to SPY: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for SPY: score=2.19 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: SPY score=2.19 reason=score=2.19 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for SPY: score=2.19 < threshold=2.70
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Skipping SPXW - not in UW cache
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for HD (symbol 11/54)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: HD composite_score=3.194
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to HD: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to HD: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for HD: score=3.99, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: HD score=3.99
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLP (symbol 12/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLP composite_score=1.892
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLP: +0.30 (sector=ETF, count=10)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLP: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for XLP: score=2.69 < threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: XLP score=2.69 reason=score=2.69 < threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for XLP: score=2.69 < threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for C (symbol 13/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: C composite_score=2.345
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to C: +0.30 (sector=Financial, count=12)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to C: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for C: score=3.15, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: C score=3.15
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for BLK (symbol 14/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BLK composite_score=2.416
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to BLK: +0.30 (sector=Financial, count=12)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to BLK: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for BLK: score=3.22, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: BLK score=3.22
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for MA (symbol 15/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MA composite_score=3.313
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to MA: +0.30 (sector=Financial, count=12)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to MA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for MA: score=4.11, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: MA score=4.11
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for GS (symbol 16/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GS composite_score=2.111
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to GS: +0.30 (sector=Financial, count=12)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to GS: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for GS: score=2.91, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: GS score=2.91
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for GM (symbol 17/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: GM composite_score=3.242
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to GM: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to GM: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for GM: score=4.04, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: GM score=4.04
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLF (symbol 18/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLF composite_score=2.242
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLF: +0.30 (sector=ETF, count=10)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLF: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for XLF: score=3.04, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: XLF score=3.04
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for AAPL (symbol 19/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: AAPL composite_score=3.265
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to AAPL: +0.30 (sector=Technology, count=10)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to AAPL: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for AAPL: score=4.06, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: AAPL score=4.06
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XOM (symbol 20/54)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XOM composite_score=3.270
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XOM: +0.30 (sector=Energy, count=4)
Apr 01 19:23:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XOM: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for XOM: score=4.07, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: XOM score=4.07
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for LOW (symbol 21/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: LOW composite_score=3.220
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to LOW: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to LOW: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for LOW: score=4.02, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: LOW score=4.02
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for AMD (symbol 22/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: AMD composite_score=2.215
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to AMD: +0.30 (sector=Technology, count=10)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to AMD: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for AMD: score=3.01, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: AMD score=3.01
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for MRNA (symbol 23/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MRNA composite_score=3.630
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to MRNA: +0.30 (sector=Healthcare, count=4)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to MRNA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for MRNA: score=4.43, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: MRNA score=4.43
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for V (symbol 24/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: V composite_score=2.197
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to V: +0.30 (sector=Financial, count=12)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to V: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for V: score=3.00, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: V score=3.00
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLI (symbol 25/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLI composite_score=1.892
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLI: +0.30 (sector=ETF, count=10)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLI: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for XLI: score=2.69 < threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: XLI score=2.69 reason=score=2.69 < threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for XLI: score=2.69 < threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for BA (symbol 26/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BA composite_score=2.773
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to BA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for BA: score=3.27, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: BA score=3.27
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for MS (symbol 27/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MS composite_score=2.213
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to MS: +0.30 (sector=Financial, count=12)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to MS: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for MS: score=3.01, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: MS score=3.01
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for PFE (symbol 28/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: PFE composite_score=3.400
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to PFE: +0.30 (sector=Healthcare, count=4)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to PFE: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for PFE: score=4.20, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: PFE score=4.20
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for INTC (symbol 29/54)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: INTC composite_score=2.061
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to INTC: +0.30 (sector=Technology, count=10)
Apr 01 19:23:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to INTC: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for INTC: score=2.86, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: INTC score=2.86
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for JNJ (symbol 30/54)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: JNJ composite_score=3.116
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to JNJ: +0.30 (sector=Healthcare, count=4)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to JNJ: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for JNJ: score=3.92, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: JNJ score=3.92
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for COP (symbol 31/54)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COP composite_score=3.455
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to COP: +0.30 (sector=Energy, count=4)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to COP: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for COP: score=4.25, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: COP score=4.25
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for COST (symbol 32/54)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: COST composite_score=3.147
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to COST: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to COST: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for COST: score=3.95, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: COST score=3.95
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for META (symbol 33/54)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: META composite_score=2.863
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to META: +0.30 (sector=Technology, count=10)
Apr 01 19:23:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to META: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for META: score=3.66, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: META score=3.66
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for PLTR (symbol 34/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: PLTR composite_score=3.951
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to PLTR: +0.30 (sector=Technology, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to PLTR: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for PLTR: score=4.75, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: PLTR score=4.75
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for NIO (symbol 35/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NIO composite_score=3.226
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to NIO: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to NIO: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for NIO: score=4.03, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: NIO score=4.03
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for CAT (symbol 36/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: CAT composite_score=3.695
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to CAT: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for CAT: score=4.20, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: CAT score=4.20
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for NVDA (symbol 37/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NVDA composite_score=3.137
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to NVDA: +0.30 (sector=Technology, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to NVDA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for NVDA: score=3.94, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: NVDA score=3.94
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for HOOD (symbol 38/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: HOOD composite_score=3.942
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to HOOD: +0.30 (sector=Financial, count=12)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to HOOD: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for HOOD: score=4.74, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: HOOD score=4.74
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for RIVN (symbol 39/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: RIVN composite_score=3.893
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to RIVN: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to RIVN: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for RIVN: score=4.69, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: RIVN score=4.69
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for TSLA (symbol 40/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: TSLA composite_score=2.060
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to TSLA: +0.30 (sector=Technology, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to TSLA: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for TSLA: score=2.86, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: TSLA score=2.86
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLE (symbol 41/54)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLE composite_score=2.261
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLE: +0.30 (sector=ETF, count=10)
Apr 01 19:23:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLE: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for XLE: score=3.06, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: XLE score=3.06
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLV (symbol 42/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLV composite_score=1.908
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLV: +0.30 (sector=ETF, count=10)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLV: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for XLV: score=2.71, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: XLV score=2.71
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for BAC (symbol 43/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: BAC composite_score=1.908
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to BAC: +0.30 (sector=Financial, count=12)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to BAC: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for BAC: score=2.71, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: BAC score=2.71
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for CVX (symbol 44/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: CVX composite_score=3.257
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to CVX: +0.30 (sector=Energy, count=4)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to CVX: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for CVX: score=4.06, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: CVX score=4.06
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for WMT (symbol 45/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: WMT composite_score=3.295
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to WMT: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to WMT: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for WMT: score=4.09, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: WMT score=4.09
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for MSFT (symbol 46/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: MSFT composite_score=3.617
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to MSFT: +0.30 (sector=Technology, count=10)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to MSFT: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for MSFT: score=4.42, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: MSFT score=4.42
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for WFC (symbol 47/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: WFC composite_score=1.906
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to WFC: +0.30 (sector=Financial, count=12)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to WFC: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for WFC: score=2.71, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: WFC score=2.71
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for AMZN (symbol 48/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: AMZN composite_score=3.384
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to AMZN: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for AMZN: score=3.88, sentiment=BEARISH->bearish, threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: AMZN score=3.88
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for NFLX (symbol 49/54)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: NFLX composite_score=1.423
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to NFLX: +0.30 (sector=Technology, count=10)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to NFLX: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for NFLX: score=2.22 < threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: NFLX score=2.22 reason=score=2.22 < threshold=2.70
Apr 01 19:23:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for NFLX: score=2.22 < threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for XLK (symbol 50/54)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: XLK composite_score=2.419
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to XLK: +0.30 (sector=ETF, count=10)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to XLK: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for XLK: score=3.22, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: XLK score=3.22
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for F (symbol 51/54)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: F composite_score=3.280
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to F: +0.30 (sector=Consumer, count=10)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to F: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for F: score=4.08, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: F score=4.08
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for SOFI (symbol 52/54)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: SOFI composite_score=4.121
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to SOFI: +0.30 (sector=Financial, count=12)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to SOFI: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal ACCEPTED for SOFI: score=4.92, sentiment=BULLISH->bullish, threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged accepted signal to history: SOFI score=4.92
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Computing composite score for QQQ (symbol 53/54)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: QQQ composite_score=1.472
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Sector Tide boost applied to QQQ: +0.30 (sector=ETF, count=10)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Persistence boost applied to QQQ: +0.50 (count=9, whale_motif=True)
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for QQQ: score=2.27 < threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Logged rejected signal to history: QQQ score=2.27 reason=score=2.27 < threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite signal REJECTED for QQQ: score=2.27 < threshold=2.70
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Using ONLY composite-scored clusters (47 clusters with scores), discarding 6 unscored flow_clusters
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite scoring complete: 53 symbols processed, 47 passed gate, 47 composite clusters, 6 flow clusters, 47 total clusters
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Composite filter complete, 47 clusters passed gate
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Building confirm_map for 47 clusters
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: About to call decide_and_execute with 47 clusters, regime=mixed
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:3801: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   "time_of_day_min": int(datetime.utcnow().hour * 60 + datetime.utcnow().minute),
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG decide_and_execute: Processing 47 clusters (sorted by strength), stage=bootstrap
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: Processing cluster - direction=bullish, initial_score=5.80, source=composite_v3
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: expectancy=0.4373, should_trade=True, reason=expectancy_passed
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: PASSED expectancy gate, checking other gates...
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:5575: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: Side determined: buy, qty=37, ref_price=15.6056
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:10102: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   tod_min = datetime.utcnow().hour * 60 + datetime.utcnow().minute
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: Expected entry price computed: 15.59
Apr 01 19:23:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: About to call submit_entry with qty=37, side=buy, regime=mixed
Apr 01 19:23:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:23:17,658 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 01 19:23:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:23:17,889 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=12
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: submit_entry returned - order_type=market, entry_status=filled, filled_qty=12, fill_price=15.61
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SOFI: Order IMMEDIATELY FILLED - qty=12, price=15.61
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6456: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   "updated_at": datetime.utcnow().isoformat(),
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: Processing cluster - direction=bullish, initial_score=5.66, source=composite_v3
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: expectancy=0.4170, should_trade=True, reason=expectancy_passed
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: PASSED expectancy gate, checking other gates...
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:5575: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: Side determined: buy, qty=3, ref_price=173.585
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:10102: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   tod_min = datetime.utcnow().hour * 60 + datetime.utcnow().minute
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: Expected entry price computed: 173.41
Apr 01 19:23:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: About to call submit_entry with qty=3, side=buy, regime=mixed
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=3
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: submit_entry returned - order_type=market, entry_status=filled, filled_qty=3, fill_price=173.75
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COIN: Order IMMEDIATELY FILLED - qty=3, price=173.75
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:23:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: Processing cluster - direction=bullish, initial_score=5.64, source=composite_v3
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: expectancy=0.4132, should_trade=True, reason=expectancy_passed
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: PASSED expectancy gate, checking other gates...
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: Side determined: buy, qty=3, ref_price=146.545
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: Expected entry price computed: 146.4
Apr 01 19:23:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: About to call submit_entry with qty=3, side=buy, regime=mixed
Apr 01 19:23:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=1
Apr 01 19:23:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=1, fill_price=146.5
Apr 01 19:23:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PLTR: Order IMMEDIATELY FILLED - qty=1, price=146.5
Apr 01 19:23:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: Processing cluster - direction=bullish, initial_score=5.69, source=composite_v3
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: expectancy=0.4192, should_trade=True, reason=expectancy_passed
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: PASSED expectancy gate, checking other gates...
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: Side determined: buy, qty=61, ref_price=9.61
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: ExecutionRouter selected strategy=limit_offset, spread_bps=20.0
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: Expected entry price computed: 9.6
Apr 01 19:23:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: About to call submit_entry with qty=61, side=buy, regime=mixed
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:23:48,143 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=61
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=61, fill_price=9.61
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG LCID: Order IMMEDIATELY FILLED - qty=61, price=9.61
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: Processing cluster - direction=bullish, initial_score=5.64, source=composite_v3
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:23:48,600 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:23:48,600 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: expectancy=0.4188, should_trade=True, reason=expectancy_passed
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: PASSED expectancy gate, checking other gates...
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:23:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: Side determined: buy, qty=7, ref_price=70.12
Apr 01 19:23:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: ExecutionRouter selected strategy=limit_offset, spread_bps=20.0
Apr 01 19:23:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: Expected entry price computed: 70.04
Apr 01 19:23:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: About to call submit_entry with qty=7, side=buy, regime=mixed
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=7
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: submit_entry returned - order_type=market, entry_status=filled, filled_qty=7, fill_price=70.15
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG HOOD: Order IMMEDIATELY FILLED - qty=7, price=70.15
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: Processing cluster - direction=bullish, initial_score=5.57, source=composite_v3
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: expectancy=0.4090, should_trade=True, reason=expectancy_passed
Apr 01 19:24:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: PASSED expectancy gate, checking other gates...
Apr 01 19:24:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:24:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: Side determined: buy, qty=39, ref_price=15.005
Apr 01 19:24:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: ExecutionRouter selected strategy=limit_offset, spread_bps=20.0
Apr 01 19:24:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: Expected entry price computed: 14.99
Apr 01 19:24:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: About to call submit_entry with qty=39, side=buy, regime=mixed
Apr 01 19:24:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $171,443.58, Equity: $47,249.38
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:10,262 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9570
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:10,280 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.9300
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:10,297 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.9310
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:10,320 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9390
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:10,340 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 4.1080
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0013% (entry=$15.61, current=$15.63)
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7587: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_info = info.get("ts", datetime.utcnow())
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7590: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   position_age_sec = (datetime.utcnow() - entry_ts_info).total_seconds()
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:11,066 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9560
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:11,085 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.9300
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:11,104 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.9310
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:11,122 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9390
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:11,142 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 4.1080
Apr 01 19:24:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0013% (entry=$15.61, current=$15.63)
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:12,362 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9560
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:12,380 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.9300
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:12,398 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.9310
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:12,420 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9390
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:12,445 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 4.1080
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0013% (entry=$15.61, current=$15.63)
Apr 01 19:24:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=1
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: submit_entry returned - order_type=market, entry_status=filled, filled_qty=1, fill_price=15.01
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG RIVN: Order IMMEDIATELY FILLED - qty=1, price=15.01
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: Processing cluster - direction=bullish, initial_score=5.35, source=composite_v3
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: expectancy=0.3424, should_trade=True, reason=expectancy_passed
Apr 01 19:24:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: PASSED expectancy gate, checking other gates...
Apr 01 19:24:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:24:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: Side determined: buy, qty=11, ref_price=50.08
Apr 01 19:24:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:24:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: Expected entry price computed: 50.03
Apr 01 19:24:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: About to call submit_entry with qty=11, side=buy, regime=mixed
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: submit_entry completed - res=True, order_type=market, entry_status=submitted_unfilled, filled_qty=0
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: submit_entry returned - order_type=market, entry_status=submitted_unfilled, filled_qty=0, fill_price=None
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: Order SUBMITTED (not yet filled) - status=submitted_unfilled, will be tracked by reconciliation
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG SLB: Order submitted (status=submitted_unfilled) - reconciliation will track fill
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: Processing cluster - direction=bearish, initial_score=5.28, source=composite_v3
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: expectancy=0.3260, should_trade=True, reason=expectancy_passed
Apr 01 19:24:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: PASSED expectancy gate, checking other gates...
Apr 01 19:24:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:24:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: Side determined: sell, qty=6, ref_price=50.105
Apr 01 19:24:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:24:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: Expected entry price computed: 50.1
Apr 01 19:24:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: About to call submit_entry with qty=6, side=sell, regime=mixed
Apr 01 19:24:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:24:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:24:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=5
Apr 01 19:24:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: submit_entry returned - order_type=market, entry_status=filled, filled_qty=5, fill_price=50.1
Apr 01 19:24:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MRNA: Order IMMEDIATELY FILLED - qty=5, price=50.1
Apr 01 19:24:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: Processing cluster - direction=bearish, initial_score=5.29, source=composite_v3
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: expectancy=0.3234, should_trade=True, reason=expectancy_passed
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: PASSED expectancy gate, checking other gates...
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: Momentum check failed but allowing entry (score=4.42 >= 1.5)
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: Side determined: sell, qty=1, ref_price=369.595
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: Expected entry price computed: 369.54
Apr 01 19:24:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: About to call submit_entry with qty=1, side=sell, regime=mixed
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=1
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=1, fill_price=369.55
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MSFT: Order IMMEDIATELY FILLED - qty=1, price=369.55
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: Processing cluster - direction=bearish, initial_score=5.23, source=composite_v3
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: expectancy=0.3202, should_trade=True, reason=expectancy_passed
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: PASSED expectancy gate, checking other gates...
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: Side determined: sell, qty=2, ref_price=121.24
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: Expected entry price computed: 121.24
Apr 01 19:24:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: About to call submit_entry with qty=2, side=sell, regime=mixed
Apr 01 19:24:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:48,609 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 01 19:24:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:48,905 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 01 19:24:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:48,905 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 01 19:24:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:53,478 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/42db4048-522d-4f16-a3ed-6a170e32d669 3 more time(s)...
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: submit_entry completed - res=True, order_type=market, entry_status=submitted_unfilled, filled_qty=0
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: submit_entry returned - order_type=market, entry_status=submitted_unfilled, filled_qty=0, fill_price=None
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: Order SUBMITTED (not yet filled) - status=submitted_unfilled, will be tracked by reconciliation
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG TGT: Order submitted (status=submitted_unfilled) - reconciliation will track fill
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: Processing cluster - direction=bearish, initial_score=5.14, source=composite_v3
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: expectancy=0.3032, should_trade=True, reason=expectancy_passed
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: PASSED expectancy gate, checking other gates...
Apr 01 19:24:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:24:57,891 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/positions 3 more time(s)...
Apr 01 19:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: Side determined: sell, qty=1, ref_price=273.95
Apr 01 19:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: Expected entry price computed: 273.95
Apr 01 19:25:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: About to call submit_entry with qty=1, side=sell, regime=mixed
Apr 01 19:25:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:07,054 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/ea428c9e-7622-470e-a9ac-99f140120e90 3 more time(s)...
Apr 01 19:25:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:25:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $169,457.02, Equity: $47,247.78
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,800 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9190
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,818 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2790
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,836 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2800
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,855 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9650
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,875 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.5940
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,899 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9030
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,919 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2290
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,939 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7750
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,958 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9700
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:12,976 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.5750
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6921: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts = datetime.utcnow()  # Unknown entry time
Apr 01 19:25:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0003% (entry=$15.61, current=$15.62)
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,718 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9190
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,744 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2790
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,770 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2800
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,798 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9650
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,826 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.5940
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,853 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9030
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,880 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2290
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,907 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7740
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,935 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9700
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:13,960 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.5750
Apr 01 19:25:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0003% (entry=$15.61, current=$15.62)
Apr 01 19:25:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:15,104 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/9e40d525-8e34-4417-a8d4-861860e05f8e 3 more time(s)...
Apr 01 19:25:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:15,110 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/positions 3 more time(s)...
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,229 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9180
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,248 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2780
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,265 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2790
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,284 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9640
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,302 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.5930
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,322 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9020
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,341 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2280
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,365 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7730
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,384 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9690
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:18,409 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.5740
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0006% (entry=$15.61, current=$15.62)
Apr 01 19:25:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:19,166 [CACHE-ENRICH] INFO: 107.189.30.132 - - [01/Apr/2026 19:25:19] "GET http://azenv.net:80/ HTTP/1.0" 200 -
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=1
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: submit_entry returned - order_type=market, entry_status=filled, filled_qty=1, fill_price=273.95
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG UNH: Order IMMEDIATELY FILLED - qty=1, price=273.95
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: Processing cluster - direction=bearish, initial_score=5.08, source=composite_v3
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: expectancy=0.2910, should_trade=True, reason=expectancy_passed
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: PASSED expectancy gate, checking other gates...
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: Momentum check failed but allowing entry (score=4.25 >= 1.5)
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: Side determined: sell, qty=2, ref_price=128.37
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: Expected entry price computed: 128.37
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: About to call submit_entry with qty=2, side=sell, regime=mixed
Apr 01 19:25:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:19,953 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/assets/COP 3 more time(s)...
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=1
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=1, fill_price=128.33
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG COP: Order IMMEDIATELY FILLED - qty=1, price=128.33
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: Processing cluster - direction=bearish, initial_score=5.00, source=composite_v3
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: expectancy=0.2800, should_trade=True, reason=expectancy_passed
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: PASSED expectancy gate, checking other gates...
Apr 01 19:25:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:30,669 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/positions 3 more time(s)...
Apr 01 19:25:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:25:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: Side determined: sell, qty=11, ref_price=28.575
Apr 01 19:25:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:25:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: Expected entry price computed: 28.57
Apr 01 19:25:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: About to call submit_entry with qty=11, side=sell, regime=mixed
Apr 01 19:25:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:35,548 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/6ef77c24-8c27-43e8-b12a-b7b2668952c9 3 more time(s)...
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=11
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=11, fill_price=28.57
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG PFE: Order IMMEDIATELY FILLED - qty=11, price=28.57
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: Processing cluster - direction=bearish, initial_score=4.99, source=composite_v3
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: expectancy=0.2790, should_trade=True, reason=expectancy_passed
Apr 01 19:25:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: PASSED expectancy gate, checking other gates...
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: Side determined: sell, qty=1, ref_price=734.825
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: Expected entry price computed: 734.83
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: About to call submit_entry with qty=1, side=sell, regime=mixed
Apr 01 19:25:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:39,410 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders:by_client_order_id 3 more time(s)...
Apr 01 19:25:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: submit_entry completed - res=False, order_type=error, entry_status=fractional orders cannot be sold short, filled_qty=0
Apr 01 19:25:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG CAT: submit_entry returned None - order submission failed (order_type=error, entry_status=fractional orders cannot be sold short)
Apr 01 19:25:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: Processing cluster - direction=bullish, initial_score=4.87, source=composite_v3
Apr 01 19:25:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:44,662 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/account 3 more time(s)...
Apr 01 19:25:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: expectancy=0.2828, should_trade=True, reason=expectancy_passed
Apr 01 19:25:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: PASSED expectancy gate, checking other gates...
Apr 01 19:25:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:25:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: Side determined: buy, qty=1, ref_price=492.225
Apr 01 19:25:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:25:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: Expected entry price computed: 491.73
Apr 01 19:25:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: About to call submit_entry with qty=1, side=buy, regime=mixed
Apr 01 19:25:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:48,739 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/b40d00a6-deae-4a27-88ac-4692a7d62a55 3 more time(s)...
Apr 01 19:25:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:48,915 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 01 19:25:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:49,240 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 01 19:25:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:49,240 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 01 19:25:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:25:58,521 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/607a3e57-9c5d-4957-9b83-d1334495c0eb 3 more time(s)...
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: submit_entry completed - res=True, order_type=market, entry_status=filled, filled_qty=1
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: submit_entry returned - order_type=market, entry_status=filled, filled_qty=1, fill_price=492.23
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG MA: Order IMMEDIATELY FILLED - qty=1, price=492.23
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: Processing cluster - direction=bearish, initial_score=4.88, source=composite_v3
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: expectancy=0.2590, should_trade=True, reason=expectancy_passed
Apr 01 19:26:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: PASSED expectancy gate, checking other gates...
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: Side determined: sell, qty=2, ref_price=124.915
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: ExecutionRouter selected strategy=twap_slice, spread_bps=20.0
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: Expected entry price computed: 124.92
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: About to call submit_entry with qty=2, side=sell, regime=mixed
Apr 01 19:26:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:03,786 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/1132b8a1-aca2-484e-bb26-e306113dbf7b 3 more time(s)...
Apr 01 19:26:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 19:26:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: submit_entry completed - res=True, order_type=limit, entry_status=filled, filled_qty=1
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: submit_entry returned - order_type=limit, entry_status=filled, filled_qty=1, fill_price=124.91
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WMT: Order IMMEDIATELY FILLED - qty=1, price=124.91
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: Processing cluster - direction=bullish, initial_score=4.91, source=composite_v3
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: expectancy=0.2864, should_trade=True, reason=expectancy_passed
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: PASSED expectancy gate, checking other gates...
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: PASSED ALL GATES! Calling submit_entry...
Apr 01 19:26:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: Side determined: buy, qty=43, ref_price=11.6586
Apr 01 19:26:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: ExecutionRouter selected strategy=limit_offset, spread_bps=20.0
Apr 01 19:26:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: Expected entry price computed: 11.65
Apr 01 19:26:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG F: About to call submit_entry with qty=43, side=buy, regime=mixed
Apr 01 19:26:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:13,345 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/3b2e0c52-08e4-4801-9e8b-c9552b19d2e1 3 more time(s)...
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $167,792.86, Equity: $47,250.32
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,719 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9060
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,738 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.7760
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,756 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2640
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,776 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2650
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,797 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2190
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,815 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9510
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,839 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.0800
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,858 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.7210
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,877 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.8890
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,895 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2150
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,912 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7600
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,931 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9570
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,956 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.9220
Apr 01 19:26:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:18,981 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.8360
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,000 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.6160
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0006% (entry=$15.61, current=$15.62)
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,725 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9060
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,746 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.7760
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,766 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2640
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,784 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2650
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,803 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2190
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,820 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9500
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,840 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.0800
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,859 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.7210
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,879 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.8890
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,898 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2150
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,916 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7600
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,937 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9570
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,955 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.9220
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,974 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.8360
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:19,994 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.6160
Apr 01 19:26:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0006% (entry=$15.61, current=$15.62)
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,236 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9060
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,255 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.7750
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,273 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.2640
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,291 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.2650
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,309 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2190
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,326 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.9500
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,345 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.0800
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,363 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.7210
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,382 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.8890
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,400 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.2140
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,420 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.7600
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,441 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9560
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,461 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.9220
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,480 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.8350
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:21,499 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.6160
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0006% (entry=$15.61, current=$15.62)
Apr 01 19:26:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 01 19:26:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 19:26:23,419 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/orders/a5032c95-c1c3-46d3-8e88-050348d737d0 3 more time(s)...

```

### state_ls (exit 0)

```
total 65M
drwxr-xr-x  5 root root 4.0K Apr  1 19:26 .
drwxr-xr-x 47 root root  48K Apr  1 18:36 ..
-rw-r--r--  1 root root  137 Apr  1 19:20 alpaca_100trade_sent.json
-rw-r--r--  1 root root   87 Apr  1 19:20 alpaca_milestone_250_state.json
-rw-r--r--  1 root root  136 Apr  1 19:20 alpaca_milestone_integrity_arm.json
-rw-r--r--  1 root root  169 Apr  1 19:23 alpaca_positions.json
-rw-r--r--  1 root root  516 Apr  1 19:20 alpaca_telegram_integrity_cycle.json
-rw-r--r--  1 root root  119 Mar 30 17:36 bayes_profiles.json
-rw-r--r--  1 root root  51M Apr  1 19:19 blocked_trades.jsonl
-rw-r--r--  1 root root 1.1K Apr  1 19:23 bot_heartbeat.json
-rw-r--r--  1 root root 3.9M Apr  1 00:12 causal_analysis_state.json
-rw-r--r--  1 root root  130 Mar 30 17:36 champions.json
-rw-r--r--  1 root root   93 Mar 30 17:36 correlation_snapshot.json
-rw-r--r--  1 root root   98 Apr  1 13:30 daily_start_equity.json
-rw-r--r--  1 root root   64 Mar 30 17:36 degraded_mode.json
-rw-r--r--  1 root root  222 Apr  1 18:10 direction_readiness.json
-rw-r--r--  1 root root  110 Mar 31 16:38 direction_replay_status.json
-rw-r--r--  1 root root  699 Mar 30 17:36 eod_rolling_windows_2026-03-30.json
-rw-r--r--  1 root root  13K Apr  1 19:25 execution_failures.jsonl
-rw-r--r--  1 root root   63 Apr  1 19:23 executor_state.json
-rw-r--r--  1 root root   43 Apr  1 19:23 fail_counter.json
-rw-r--r--  1 root root 4.2K Apr  1 02:00 failure_point_monitor.json
-rw-r--r--  1 root root 8.2K Apr  1 00:12 gate_pattern_learning.json
-rw-r--r--  1 root root  402 Mar 30 18:26 governor_freezes.json
-rw-r--r--  1 root root 4.8K Apr  1 13:03 healing_history.jsonl
-rw-r--r--  1 root root 1.7K Apr  1 19:22 health.json
drwxr-xr-x  2 root root 4.0K Mar 30 17:30 heartbeats
-rw-r--r--  1 root root   67 Apr  1 19:23 internal_positions.json
-rw-r--r--  1 root root  119 Mar 31 16:38 last_droplet_analysis.json
-rw-r--r--  1 root root 5.7K Apr  1 19:23 last_scores.json
-rw-r--r--  1 root root  750 Apr  1 00:12 learning_processing_state.json
-rw-r--r--  1 root root  150 Mar 31 20:46 learning_scheduler_state.json
drwxr-xr-x  3 root root 4.0K Mar 30 20:43 legacy
-rw-r--r--  1 root root  202 Apr  1 19:23 logic_stagnation_state.json
-rw-r--r--  1 root root  107 Mar 30 17:43 macro_gate_state.json
-rw-r--r--  1 root root  589 Apr  1 19:23 market_context_v2.json
-rw-------  1 root root  453 Mar 31 19:57 peak_equity.json
-rw-r--r--  1 root root  617 Apr  1 19:24 pending_fill_scores.json
-rw-r--r--  1 root root 7.5M Apr  1 19:23 portfolio_state.jsonl
-rw-r--r--  1 root root 1.4M Apr  1 19:26 position_intel_snapshots.json
-rw-r--r--  1 root root  48K Apr  1 19:26 position_metadata.json
-rw-r--r--  1 root root  12K Mar 30 18:26 position_metadata.pre_liquidation.20260330_182621Z.json
-rw-r--r--  1 root root  86K Mar 30 18:31 position_metadata.pre_liquidation.20260330_183111Z.json
-rw-r--r--  1 root root  11K Mar 30 18:32 position_metadata.pre_liquidation.20260330_183223Z.json
-rw-r--r--  1 root root  220 Mar 31 04:27 postclose_watermark.json
-rw-r--r--  1 root root  107 Apr  1 18:30 regime_detector_state.json
-rw-r--r--  1 root root  637 Apr  1 19:23 regime_posture_state.json
-rw-r--r--  1 root root 4.8K Mar 30 17:43 score_telemetry.json
-rw-r--r--  1 root root  38K Apr  1 19:23 sector_tide_state.json
-rw-r--r--  1 root root  133 Apr  1 19:23 self_healing_threshold.json
-rw-r--r--  1 root root 3.6K Mar 30 17:36 signal_correlation_cache.json
-rw-r--r--  1 root root  134 Apr  1 19:26 signal_funnel_state.json
-rw-r--r--  1 root root  28K Apr  1 19:26 signal_history.jsonl
-rw-r--r--  1 root root  102 Apr  1 00:12 signal_pattern_learning.json
-rw-r--r--  1 root root  17K Apr  1 19:26 signal_strength_cache.json
-rw-r--r--  1 root root   63 Mar 30 17:36 signal_survivorship_2026-03-30.json
-rw-r--r--  1 root root 200K Apr  1 02:00 signal_weights.json
-rw-r--r--  1 root root  30K Apr  1 19:26 smart_poller.json
-rw-r--r--  1 root root  268 Apr  1 19:23 sre_metrics.json
-rw-r--r--  1 root root  124 Mar 30 17:36 survivorship_adjustments.json
-rw-r--r--  1 root root 9.1K Apr  1 13:30 symbol_risk_features.json
-rw-r--r--  1 root root  309 Mar 30 17:36 system_stage.json
-rw-r--r--  1 root root 5.1K Apr  1 19:26 trading_state.json
-rw-r--r--  1 root root 4.7K Apr  1 00:12 uw_blocked_learning.json
drwxr-xr-x  2 root root  68K Apr  1 19:26 uw_cache
-rw-r--r--  1 root root   96 Mar 30 17:36 uw_flow_daemon.lock
-rw-r--r--  1 root root  45K Mar 30 17:31 uw_openapi_catalog.json
-rw-r--r--  1 root root  214 Apr  1 19:26 uw_usage_state.json
-rw-r--r--  1 root root 1.4K Apr  1 18:37 v2_metrics.json
-rw-r--r--  1 root root   97 Apr  1 18:37 v2_promoted.json

```

### timers (exit 0)

```
NEXT                                LEFT LAST                              PASSED UNIT                                ACTIVATES
Wed 2026-04-01 19:27:22 UTC          54s Wed 2026-04-01 19:26:22 UTC       5s ago trading-bot-doctor.timer            trading-bot-doctor.service
Wed 2026-04-01 19:30:00 UTC     3min 31s Wed 2026-04-01 19:15:05 UTC    11min ago alpaca-forward-truth-contract.timer alpaca-forward-truth-contract.service
Wed 2026-04-01 19:30:00 UTC     3min 31s Wed 2026-04-01 19:20:16 UTC     6min ago sysstat-collect.timer               sysstat-collect.service
Wed 2026-04-01 19:30:22 UTC     3min 54s Wed 2026-04-01 19:20:22 UTC     6min ago alpaca-telegram-integrity.timer     alpaca-telegram-integrity.service
Wed 2026-04-01 19:32:13 UTC         5min Wed 2026-04-01 18:28:45 UTC    57min ago fwupd-refresh.timer                 fwupd-refresh.service
Wed 2026-04-01 20:00:39 UTC        34min Wed 2026-04-01 12:27:26 UTC       6h ago apt-daily.timer                     apt-daily.service
Wed 2026-04-01 20:30:00 UTC      1h 3min Tue 2026-03-31 20:30:04 UTC      22h ago alpaca-postclose-deepdive.timer     alpaca-postclose-deepdive.service
Thu 2026-04-02 00:00:00 UTC     4h 33min Wed 2026-04-01 00:00:09 UTC      19h ago dpkg-db-backup.timer                dpkg-db-backup.service
Thu 2026-04-02 00:00:00 UTC     4h 33min Wed 2026-04-01 00:00:09 UTC      19h ago logrotate.timer                     logrotate.service
Thu 2026-04-02 00:03:27 UTC     4h 36min Wed 2026-04-01 12:11:06 UTC       7h ago motd-news.timer                     motd-news.service
Thu 2026-04-02 00:07:00 UTC     4h 40min Wed 2026-04-01 00:07:09 UTC      19h ago sysstat-summary.timer               sysstat-summary.service
Thu 2026-04-02 02:00:00 UTC           6h Wed 2026-04-01 02:00:06 UTC      17h ago stock-bot-dashboard-audit.timer     stock-bot-dashboard-audit.service
Thu 2026-04-02 05:31:13 UTC          10h Wed 2026-04-01 10:14:24 UTC       9h ago man-db.timer                        man-db.service
Thu 2026-04-02 06:04:12 UTC          10h Wed 2026-04-01 06:51:25 UTC      12h ago apt-daily-upgrade.timer             apt-daily-upgrade.service
Thu 2026-04-02 17:07:36 UTC          21h Wed 2026-04-01 17:07:36 UTC 2h 18min ago update-notifier-download.timer      update-notifier-download.service
Thu 2026-04-02 17:17:21 UTC          21h Wed 2026-04-01 17:17:21 UTC  2h 9min ago systemd-tmpfiles-clean.timer        systemd-tmpfiles-clean.service
Sun 2026-04-05 03:10:49 UTC       3 days Sun 2026-03-29 03:10:46 UTC   3 days ago e2scrub_all.timer                   e2scrub_all.service
Mon 2026-04-06 00:21:18 UTC       4 days Mon 2026-03-30 00:56:34 UTC   2 days ago fstrim.timer                        fstrim.service
Thu 2026-04-09 21:28:43 UTC 1 week 1 day Mon 2026-03-30 17:04:29 UTC   2 days ago update-notifier-motd.timer          update-notifier-motd.service
-                                      - -                                      - apport-autoreport.timer             apport-autoreport.service
-                                      - -                                      - snapd.snap-repair.timer             snapd.snap-repair.service
-                                      - -                                      - ua-timer.timer                      ua-timer.service

22 timers listed.

```

### crontab (exit 0)

```

```

### cron_grep (exit 0)

```

```

### deploy_systemd_copy (exit 0)

```
OK

```

### systemd_cat_postclose (exit 0)

**Updated after `e8133504` + `cp` + `daemon-reload` (see addendum).**

```
# /etc/systemd/system/alpaca-postclose-deepdive.service
[Unit]
Description=Alpaca post-close deep dive (reports + Telegram, read-only)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/stock-bot
Environment=TRADING_BOT_ROOT=/root/stock-bot
EnvironmentFile=-/root/stock-bot/.env
# After .env: post-close still writes reports; Telegram API blocked here (integrity allowlist only).
Environment=TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1
ExecStart=/root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/alpaca_postclose_deepdive.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

### systemd_cat_failure_det (exit 0)

**Updated after `e8133504` + `cp` + `daemon-reload` (see addendum).**

```
# /etc/systemd/system/telegram-failure-detector.service
[Unit]
Description=Telegram failure pager (Alpaca post-close / direction / integrity expectations)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/stock-bot
Environment=TRADING_BOT_ROOT=/root/stock-bot
EnvironmentFile=-/root/stock-bot/.env
# Block pager Telegram in prod; alpaca-telegram-integrity.service does not set this (allowlisted script_names still send).
Environment=TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1
ExecStart=/root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/governance/telegram_failure_detector.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

### strict_export (exit 0)

```
{
  "generated_at_utc": "2026-04-01T19:26:34.771043+00:00",
  "root": "/root/stock-bot",
  "open_ts_epoch": 1774458080.0,
  "LEARNING_STATUS": "BLOCKED",
  "trades_seen": 431,
  "trades_complete": 415,
  "trades_incomplete": 16,
  "strict_cohort_trade_id_count": 431,
  "complete_trade_id_count": 415,
  "reconciliation": {
    "strict_cohort_len_equals_trades_seen": true,
    "complete_len_equals_trades_complete": true
  },
  "authoritative_join_key_rule": "Per closed trade: trade_key from unified alpaca_exit_attribution (or derived from open_{SYM}_{entry_ts} trade_id + exit row side). Expand aliases using undirected canonical_trade_id_intent <-> canonical_trade_id_fill edges from run.jsonl so trade_intent(entered) keyed at intent-time still joins to fill-time keys. Do not use a single per-symbol 'latest fill' as the join key (multiple positions per symbol would collide)."
}
strict_cohort_trade_ids: 431 rows (full list in --out-json if set)
complete_trade_ids: 415 rows

```

### warehouse_tail (exit 0)

```
DATA_READY: YES
execution_join_coverage_pct: 100.00
fee_coverage_pct: 100.00
slippage_coverage_pct: 100.00
uw_coverage_pct: 100.00
blocked_candidate_coverage_pct: 51.84
coverage_report: /root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1926.md
pnl_packet: /root/stock-bot/reports/ALPACA_PNL_AUDIT_PACKET_20260401_1926.md
board_packet: /root/stock-bot/reports/ALPACA_BOARD_DECISION_PACKET_20260401_1926.md

```

### coverage_file_head (exit 0)

```
# ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1926

DATA_READY: YES

- execution join coverage: **100.00%**
- fee computable (fills basis): **100.00%**
- slippage computable (exits with context+exit px): **100.00%**
- signal snapshot near exit: **100.00%**
- decision events (snapshots+intents): **2201**
- blocked/near-miss bucket coverage (5m symbol buckets with block detail ∩ eval buckets): **381** / **735** → **51.84%**
- CI reason on blocked intents: **100.00%** (3/3)
- UW coverage on snapshots: **100.00%** (configured=False)

## Join reasons
Counter({'exit_has_order_id': 432})


```

### parse_coverage_smoke_check

```
{
  "coverage_path": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1926.md",
  "data_ready_yes": true,
  "parse_ok": true,
  "execution_join_pct": 100.0
}

```

### integrity_cycle_dry_run

```
{
  "root": "/root/stock-bot",
  "utc": "2026-04-01T19:26:46.006424+00:00",
  "warehouse_run": {
    "skipped": true
  },
  "coverage_file": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1926.md",
  "coverage_age_hours": 0.0,
  "strict_chain_backfill": {
    "ok": true,
    "applied": 16,
    "dry_run": false,
    "exit_attribution_missing": false
  },
  "strict": {
    "LEARNING_STATUS": "ARMED",
    "trades_seen": 200,
    "trades_incomplete": 0
  },
  "exit_probe": {
    "lines_scanned": 400,
    "missing": {
      "symbol": 0,
      "exit_ts": 0,
      "trade_id": 0
    }
  },
  "pager_windows": [
    {
      "key": "alpaca:post_close",
      "state": "PENDING",
      "cause": "before_expect_window"
    },
    {
      "key": "alpaca:direction_readiness",
      "state": "PASS",
      "cause": "freshness_ok"
    }
  ],
  "checkpoint_100_precheck_ok": true,
  "checkpoint_100_precheck_reasons": [],
  "milestone": {
    "session_open_utc_iso": "2026-04-01T13:30:00+00:00",
    "session_anchor_et": "2026-04-01",
    "unique_closed_trades": 16,
    "realized_pnl_sum_usd": -8.43,
    "sample_trade_keys": [
      "SOFI|SHORT|1775069142",
      "JPM|SHORT|1775069352",
      "MRNA|SHORT|1775069251",
      "MS|SHORT|1775069285",
      "RIVN|SHORT|1775069179"
    ],
    "counting_basis": "integrity_armed",
    "count_floor_utc_iso": "2026-04-01T19:20:31.101308+00:00",
    "integrity_armed": true
  },
  "milestone_counting_basis": "integrity_armed",
  "milestone_integrity_arm": {
    "arm_epoch_utc": 1775071231.101308,
    "armed_at_utc_iso": "2026-04-01T19:20:31.101308+00:00",
    "session_anchor_et": "2026-04-01"
  },
  "checkpoint_100_guard_file": "/root/stock-bot/state/alpaca_100trade_sent.json",
  "reasons_evaluated": []
}

```

### alpaca_milestone_integrity_arm.json

```
{
  "arm_epoch_utc": 1775071231.101308,
  "armed_at_utc_iso": "2026-04-01T19:20:31.101308+00:00",
  "session_anchor_et": "2026-04-01"
}

```

### alpaca_milestone_250_state.json

```
{
  "fired_milestone": false,
  "last_count": 16,
  "session_anchor_et": "2026-04-01"
}

```

### rg_send_governance_telegram_sample

```

```

### system_events_tail_grep_ERROR

```
no_ERROR_in_tail
bash: line 1: rg: command not found

```

