# ALPACA PnL LINEAGE — FINAL VERDICT

- Required fields documented: **docs/pnl_audit/REQUIRED_FIELDS.md** (+ evidence copy).
- Lineage matrix rows: **38** (`LINEAGE_MATRIX.json`).
- Map check: RESOLVED=38 MOVED=0 MISSING=0.

## Completeness

- **Lineage map:** all matrix rows classified (see `ALPACA_PNL_LINEAGE_MAP_CHECK.md`).
- **Droplet verification:** see `ALPACA_PNL_LINEAGE_DROPLET_VERIFICATION.md` (files, broker sample, dashboard ping).

## Adversarial residual risk

- Top risks: service inactive → no new telemetry; local `order_id` sparse → use broker REST join; paper fees implicit zero.
- **Acceptable for next open** if `stock-bot` is started and Alpaca keys valid (verify context + SRE doc).

## Rerun commands

```bash
cd /root/stock-bot
python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence
python3 scripts/audit/alpaca_forward_collection_readiness.py
python3 scripts/audit/alpaca_pnl_lineage_evidence_bundle.py
```
