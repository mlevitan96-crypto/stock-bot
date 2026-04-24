# BLOCKED_WHY_CONTEXT

Session anchor (ET): **2026-04-01** (droplet `TZ=America/New_York date` in `_BLOCKED_WHY_PHASE0_RAW.json` → `et`).

## 0.1 Runtime context (droplet evidence)

| Capture | Artifact / command output |
|---------|---------------------------|
| `git rev-parse HEAD` | **`e03f25ef06483e6e0157228d6821613aeac4085f`** (`phase0.head`) |
| `systemctl status stock-bot` | First 80 lines in `_BLOCKED_WHY_PHASE0_RAW.json` → `phase0.status` (state **active (running)** at capture) |
| `systemctl cat stock-bot` | `phase0.cat` — unit file + `override.conf`, `paper-overlay.conf`, `truth.conf` |
| `systemctl show … Environment` | `phase0.show`: inline `Environment=` fragment vars + **`EnvironmentFiles=/root/stock-bot/.env`** |
| `journalctl -u stock-bot --since '36 hours ago' \| tail -n 800` | `phase0.journal` in `_BLOCKED_WHY_PHASE0_RAW.json` |

### `systemctl cat` excerpt (verbatim path proof)

See `_BLOCKED_WHY_PHASE0_RAW.json` key `cat`: `ExecStart=/root/stock-bot/systemd_start.sh`, `EnvironmentFile=/root/stock-bot/.env`, `WorkingDirectory=/root/stock-bot`.

## 0.2 Dataset discovery (no path assumptions)

| Search | Droplet result |
|--------|----------------|
| `find . -maxdepth 4 -type f ( *blocked*jsonl OR *blocked*json )` | `./state/blocked_trades.jsonl`, `./state/uw_blocked_learning.json` (`phase0.find_blocked`) |
| `rg -l blocked_trades -S .` | **Empty stdout** on droplet (`phase0.rg_blocked`) — `rg` not relied on; workspace grep: **80+** `.py` files reference `blocked_trades` (local inventory). |
| `find … exit*attribution* / trade*ledger* / *fills* / *orders*` | Includes `logs/exit_attribution.jsonl`, `logs/orders.jsonl`, `data/live_orders.jsonl`, `replay/.../fills.jsonl.gz`, etc. (`phase0.find_exit`) |
| `find artifacts … *bars*jsonl` | `artifacts/market_data/alpaca_bars.jsonl` (`phase0.find_bars`) |
| `find … score_snapshot / signal_context / uw*context*` | `logs/score_snapshot.jsonl`, `logs/signal_context.jsonl`, `score_snapshot_writer.py` (`phase0.find_snap`) |

### Sizes (droplet `stat` / `wc`)

| Path | Lines / bytes | Source |
|------|----------------|--------|
| `state/blocked_trades.jsonl` | **8669** lines, **57067181** bytes | `phase0.stat_blocked` |
| `logs/exit_attribution.jsonl` | **432** lines, **3894749** bytes | `phase0.stat_exit` |
| `artifacts/market_data/alpaca_bars.jsonl` | **53** lines, **8242141** bytes (post re-fetch) | `phase0.stat_bars` |

## Hard gate Phase 0

**PASS:** blocked trades, executed exits, and bars file are all located; see `BLOCKED_WHY_DATASET_MAP.json`.

## Live-trading impact note

- **No** `systemctl restart stock-bot` for this mission.
- Bars re-fetch: separate Python process, read-only HTTP to Alpaca Data API; **0.25s** sleep between day-requests in `scripts/audit/fetch_alpaca_bars_for_counterfactuals.py`.
