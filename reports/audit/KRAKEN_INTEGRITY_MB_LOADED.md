# Kraken integrity — MEMORY_BANK load (Phase 0)

| Field | Value |
|-------|--------|
| **Artifact** | `MEMORY_BANK.md` |
| **SHA256** | `29D568EF8B232805A2D5CAB2D34B0E7B0E4113B5FBE60AEF4BBC21B9A05C2A70` |
| **Timestamp (UTC)** | 2026-03-18 ~13:55 |

## MB extraction — Kraken-specific

**Finding:** `MEMORY_BANK.md` does **not** define a Kraken live-trading telemetry contract. Kraken appears only as:

- Isolation boundary (“Alpaca remains fully isolated from Kraken”).
- No canonical Kraken log paths, `trade_id` rules, or DATA_READY gates for a Kraken venue bot.

**Governance:** General MB rules apply (droplet as truth, fail-closed, no local-log fiction). **Alpaca canonical paths** (`logs/exit_attribution.jsonl`, etc.) are **Alpaca-only** and MUST NOT be treated as Kraken evidence.

## Truth Gate checklist (Kraken-independent)

1. [ ] **Venue identity:** Every closed-trade record must declare `venue: "kraken"` (or equivalent) and must not be mixed with other venues in the same proof window.
2. [ ] **Canonical `trade_id`:** Single stable id from first open intent through exit (documented rule: e.g. client id + fill id mapping).
3. [ ] **Streams present & append-only:** entry attribution, exit attribution, execution/submit trail, blocked/counterfactual (if used)—each file exists, grows monotonically, last write within SLO.
4. [ ] **Join proof:** Entry ↔ exit join rate ≥ gate (see `KRAKEN_TELEMETRY_CONTRACT.md`); zero orphan exits for certified window.
5. [ ] **Emission trace:** Code paths documented; no silent skip on fill/exit.
6. [ ] **Droplet confirmation:** All of the above verified on the **Kraken runtime host** with live or frozen copy of production logs.

**Current status:** Checklist **not satisfiable** on audited host — see `KRAKEN_TELEMETRY_INVENTORY.md` and verdict.
