# SECOND_CHANCE_IMPLEMENTATION

## Components

- `src/paper/second_chance_displacement.py` — env-gated scheduler; appends `scheduled` rows + queue entries.
- `main.py` — hook immediately after `log_blocked_trade(..., displacement_blocked)`; **does not** change gate outcome or call the executor for orders.
- `scripts/paper_second_chance_reeval_worker.py` — `--seed-from-blocked-trades N` (paper replay), `--process-queue` (read-only Alpaca + `evaluate_displacement`).
- `logs/second_chance_displacement.jsonl` — audit log (`scheduled` and `reeval_result`).
- `state/paper_second_chance_queue.jsonl` — pending work queue.

## Live order path audit

- **PASS:** `submit_order` **not** present in paper second-chance modules (static string check).

## Env

- `PAPER_SECOND_CHANCE_DISPLACEMENT=1` — enable scheduling from live engine.
- `PAPER_SECOND_CHANCE_DELAY_SECONDS` — re-eval delay (default 60).
