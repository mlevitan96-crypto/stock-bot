# Field addition playbook (evidence copy)

- Copied at UTC `2026-03-30T21:46:23.730020+00:00`.

---

# Field addition playbook (PnL audit lineage)

Use when a **required audit field** is missing, wrong, or not joinable. **No strategy tuning** — only additive telemetry / logging.

## 1. Identify the gap

- Compare failing audit row to `docs/pnl_audit/LINEAGE_MATRIX.json`.
- Run: `python3 scripts/audit/alpaca_pnl_lineage_map_check.py` (see `MEMORY_BANK.md`).

## 2. Choose emitter

| Surface | Typical emitter |
|---------|-----------------|
| Pre-trade intent | `main.py:_emit_trade_intent` or `telemetry/*` helpers it calls |
| Order row | `main.py:log_order` (after merge keys) |
| Attribution | `main.py:log_attribution` |
| Exit / PnL row | `src/exit/exit_attribution.py:append_exit_attribution` / `build_exit_attribution_record` |
| Regime / state | `state/*.json` writers (search callers of `atomic_write_json`) |

**Rule:** Prefer **one canonical persistence** per field; if dual-write, document both in `LINEAGE_MATRIX.json`.

## 3. Persist

- Append-only: `config.registry.LogFiles` paths only (no ad-hoc paths).
- For state: `config.registry.StateFiles`.
- Inject `strategy_id` already handled in `main.py:jsonl_write` — reuse.

## 4. Join

- Prefer **broker `order_id`** for execution truth.
- Prefer **`canonical_trade_id`** / **`trade_key`** for intent ↔ metadata ↔ exit.
- Avoid **ts-only joins** unless documented as fragile fallback.

## 5. Update the contract

1. Edit `docs/pnl_audit/LINEAGE_MATRIX.json` (add/change row).
2. Regenerate human table:  
   `python3 -c "..."`  (same snippet as in `MEMORY_BANK.md` for `LINEAGE_MATRIX.md`)  
   or manually edit `docs/pnl_audit/LINEAGE_MATRIX.md`.
3. Update `docs/pnl_audit/REQUIRED_FIELDS.md` if the canonical field set changed.

## 6. Verify

```bash
cd /root/stock-bot   # or repo root
python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence
python3 scripts/audit/alpaca_forward_collection_readiness.py   # optional cross-check
```

## 7. Evidence artifact

Write under `reports/daily/<ET-date>/evidence/`:

- `ALPACA_PNL_LINEAGE_MAP_CHECK.md` (from map check `--write-evidence`)
- Short note: `ALPACA_PNL_FIELD_<name>_PROOF.md` with sample JSONL line or API snippet.

## 8. Governance

- **MEMORY_BANK.md** must stay aligned: matrix is law; broker vs local sources explicit per row.
