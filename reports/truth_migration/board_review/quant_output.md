# Quant — Data loss and schema validity

**Persona:** Quant. **Intent:** Ensure no data loss for analytics; confirm schemas and joins remain valid.

## 1. No data loss
- **Mirror mode:** Same record written to legacy and CTR. No aggregation or sampling; byte-level parity not required but record count and key fields must match (G5: parity check within tolerance).
- **Append order:** JSONL order should match between legacy and CTR for each stream so time-series and joins (e.g. by trace_id, ts) remain valid.
- **Schema version:** Each stream should emit or be associated with schema_version (e.g. in meta/schema_version.json or per-stream). Analytics scripts that join on schema must still work (e.g. same field names, same types).

## 2. Schemas and joins
- **exit_attribution ↔ attribution:** Existing joins (e.g. by symbol, date, order_id) must work when reading from CTR (exits/exit_attribution.jsonl, execution/attribution.jsonl if we add it). No schema change in Phase 1; only path change for readers in Phase 2.
- **Gate truth ↔ score_snapshot / blocked_trades:** Funnel and expectancy reports join on trace_id / decision_id / ts. CTR streams must preserve these fields so reports built from CTR match those built from legacy.
- **Score telemetry:** state/score_telemetry.json is a single JSON object (not JSONL). CTR telemetry/score_telemetry.json must be same structure so dashboard and analytics that read “last_update”, “scores”, “components” continue to work.

## 3. Producer versions
- **meta/producer_versions.json:** Git SHA, service name, optional version. Allows reproducibility of analytics runs (“which code produced this truth?”).

## 4. Acceptance
- G5: Mirror parity check — CTR vs legacy counts match within tolerance (e.g. same number of lines in JSONL streams, or documented tolerance for in-flight writes).
