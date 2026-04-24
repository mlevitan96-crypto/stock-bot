# CSA verdict — Alpaca Signal Path Intelligence (`20260328_190000Z`)

**Authority:** `MEMORY_BANK.md` (SPI purpose, constraints, invariant: SPI does not authorize behavior change).

## Checks

| Check | Result |
|-------|--------|
| SPI output is non-prescriptive (distributions, descriptive archetypes, no trade instructions) | **PASS** |
| SPI uses canonical cohort trade IDs joined to `exit_attribution.jsonl` (same as PnL reconciliation) | **PASS** |
| Window semantics align with truth JSON when cohort mode is used (`OPEN_TS_UTC_EPOCH` / `EXIT_TS_UTC_EPOCH_MAX` passed to review) | **PASS** |
| No strategy, execution, exit, signal, or risk changes in SPI code path | **PASS** |

## Candidates for future study (no action)

- Richer signal taxonomy when `exit_contributions` is sparse (`attribution_unknown` concentration).
- Bar-cache coverage on droplet: path metrics are `null` when 1m cache is absent unless operator sets `ALPACA_SPI_FETCH_BARS=true` (opt-in cache population via existing loader).

## Verdict token

**`CSA_SPI_ACCEPT`**

— SPI is correctly scoped as read-only governance evidence. It does not certify promotion, tuning, or live behavior change.
