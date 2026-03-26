# Alpaca certification run — REPLAY (droplet)

**TS:** `20260327_0200Z`

## Command

```bash
cd /root/stock-bot && PYTHONPATH=/root/stock-bot venv/bin/python \
  scripts/audit/alpaca_replay_lab_strict_gate.py \
  --workspace /tmp/alpaca_replay_lab_ws --source-root /root/stock-bot --init-snapshot \
  --slice-hours 72 --replay-era-auto --audit \
  --json-out /tmp/ALPACA_REPLAY_GATE_20260327_0200Z.json --ts 20260327_0200Z
```

## Headline (from bundle)

See `reports/audit/ALPACA_CERT_RUN_REPLAY_20260327_0200Z.json`:

- **strict_epoch_start:** auto from 72h exit window tail (see `era_selection_meta`)
- **trades_seen:** 89 (non-vacuous strict cohort)
- **LEARNING_STATUS:** BLOCKED (`trades_incomplete` = 6)
- **cert_label:** `CODE_COMPLETE_REPLAY_ERA_AUTO` / replay bundle metadata inside JSON

## Interpretation

Replay produced a **non-empty** strict cohort under explicit auto-era selection. **Final learning-ready certification failed** on incomplete chain count (see closeout).
