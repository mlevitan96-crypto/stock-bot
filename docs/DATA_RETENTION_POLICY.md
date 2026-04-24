# Data retention policy (Alpaca bot)

**Scope:** Append-only JSONL logs under `logs/`, state under `state/`, caches under `data/`, and reports under `reports/`.

## Logs (`logs/*.jsonl`)

- **Model:** append-only; no in-place rewrites of historical lines.
- **Rotation:** Operators may archive or truncate **whole files** during maintenance windows when the trading process is stopped; this repo does not auto-rotate by default.
- **Permissions:** service user must be able to append; avoid world-writable permissions on production hosts.

## State (`state/`)

- **Model:** atomic JSON / JSONL updates for recovery (e.g. `position_metadata.json`). Not used as the primary attribution ledger; attribution remains in `logs/`.

## Cache (`data/`)

- **UW / composite caches:** refreshed by daemons; safe to delete to force cold reload (may increase API load).

## Reports (`reports/`)

- **Audit and board outputs:** human-generated artifacts; retain per operational policy (often indefinite until disk pressure).

## Join / attribution keys

- **time_bucket_id:** `300s|<utc_epoch_floor>` (see `telemetry.attribution_emit_keys.time_bucket_id_utc`).
- **Slippage reference:** `decision_slippage_ref_mid` (NBBO mid or ref price at submit) vs fill price in `logs/orders.jsonl`.
