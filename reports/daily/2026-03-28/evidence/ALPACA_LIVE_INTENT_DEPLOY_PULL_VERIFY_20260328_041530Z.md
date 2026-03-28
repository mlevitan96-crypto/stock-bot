# Alpaca live intent deploy — pull verify

**UTC:** 2026-03-28T04:15:30Z (approx)  
**Host:** Alpaca droplet `/root/stock-bot`

## 1) Git before pull

- **HEAD (pre-pull):** `39d98ac38b72ba33a7194fb51934222de2f1b362`
- **Porcelain:** dirty (modified MEMORY_BANK, data files, untracked artifacts — typical droplet state)

## 2) Pull

- `git pull origin main` — **required** moving aside untracked `scripts/audit/alpaca_learning_invariant_confirmation.py` to `/tmp/` (would have been overwritten).

## 3) HEAD after pull

- **HEAD:** `9acc43d298f64719758c6bf5bbf53fe596b964b7`
- **Ancestor check:** `git merge-base --is-ancestor 54a26a1 HEAD` → **YES** (54a26a1 included)

## 4) Contract file

- `docs/ALPACA_LIVE_ENTRY_INTENT_CONTRACT.md` → **present**

## 5) Emitter LIVE markers (source verify)

- `telemetry/alpaca_entry_decision_made_emit.py` sets `entry_intent_synthetic: False` and `entry_intent_source: live_runtime` on emitted rows (see `build_entry_decision_made_record`).

## Outcome

**PASS** — repo matches `origin/main` at postfix audit tooling commit; contract and emitter markers present in tree.
