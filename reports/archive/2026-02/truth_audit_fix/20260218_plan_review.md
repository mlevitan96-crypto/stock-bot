# Truth Audit Fix — Plan Review (multi-model)

**Date:** 2026-02-18

## Adversarial hypotheses (what could lie?)

1. **Diagnostic blindness:** Diagnostics return sample_size=0 because they read a different cache path, wrong format, or missing file on droplet; we cannot prove score semantics.
2. **Dashboard JSON error:** "No number after minus sign at position 24233" — either (a) a signal dict contains NaN/Inf which serializes to invalid JSON, (b) state/signal_history.jsonl has a malformed line that when parsed and re-serialized produces invalid JSON, or (c) the API response is truncated.
3. **No canonical score truth:** Live scoring does not emit a single append-only artifact that audits can use; gates may use different score semantics without detection.
4. **Signal history trim corruption:** Buffer maintenance (read all, write last N) can leave a truncated file if write is interrupted.

## Quant assumptions challenged

- **Single JSON parse:** Dashboard calls `response.json()` on the whole body; any non-JSON-serializable value in the payload causes parse failure. Python `json.dumps` raises for NaN/Inf; Flask may emit "NaN" in JS which then fails in strict JSON at "-" in "NaN" or similar.
- **Position 24233:** Suggests a sizeable payload; the error is in the serialized string, not in the file per se (unless the dashboard ever loads a raw file).

## Product / minimal fixes

1. **Canonical score snapshot:** Emit `logs/score_snapshot.jsonl` from live scoring (one record per candidate at expectancy gate) with composite_score, gates, optional breakdown. Append-only, line-buffered.
2. **Harden signal history:** (a) Sanitize numbers (no NaN/Inf) before append and before API response; (b) atomic trim (write tmp + rename); (c) get_signal_history returns malformed_line_count and last_malformed_ts; API exposes them so dashboard can show corruption.
3. **Dashboard loader:** API already builds payload from get_signal_history; ensure sanitization and expose malformed counters. No parsing of JSONL as single JSON.
4. **Truth audit Axes 1–3:** Use score_snapshot.jsonl as canonical source when diagnostic is unavailable; PASS if sample_size > 0 from snapshot.

## Reversibility

- Score snapshot: additive; can stop writing and delete file.
- Signal history: behavior change is backward compatible (skip bad lines already done; add counters and sanitization).
- Truth audit: logic change is additive (prefer snapshot when diagnostic empty).

## Verdict

Plan is minimal, auditable, reversible. Proceed with implementation and droplet proof.
