# Directional Intelligence — Capture Verification

**Purpose:** Confirm that all new intelligence is captured, stored, and verifiable.

**Scripts:**
- `scripts/verify_intelligence_capture.py` — Checks that intel_snapshot_entry/exit, direction_event, and direction_intel_embed in exit_attribution/exit_event exist and have expected shape.
- `scripts/verify_intelligence_replay_readiness.py` — Checks that canonical direction components and intel_deltas are present for replay.

**Artifacts:**

| Artifact | Path | Verification |
|----------|------|---------------|
| Intel snapshot (entry) | `logs/intel_snapshot_entry.jsonl` | Records have `timestamp`, `event=entry`, and at least `premarket_intel` (or full snapshot keys). |
| Intel snapshot (exit) | `logs/intel_snapshot_exit.jsonl` | Records have `timestamp`, `event=exit`. |
| Direction event | `logs/direction_event.jsonl` | Records have `event_type`, `symbol`, `direction_components` (dict with canonical keys). Exit records have `metadata.intel_deltas`. |
| Exit attribution | `logs/exit_attribution.jsonl` | Recent records may have `direction_intel_embed` with `intel_snapshot_entry`, `intel_snapshot_exit`, `direction_intel_components_exit`, `intel_deltas`, `canonical_direction_components`. |
| Exit event | `logs/exit_event.jsonl` | Recent records may have `direction_intel_embed` (same structure). |
| Entry snapshot state | `state/position_intel_snapshots.json` | Keyed by `SYMBOL:entry_ts`; used for exit deltas. |

**Run:**

```bash
python scripts/verify_intelligence_capture.py --base-dir . --last 50
python scripts/verify_intelligence_replay_readiness.py --base-dir .
```

**Expected:** Both scripts exit 0 and print OK lines when capture has run (e.g. after at least one entry and one exit). If no trades have occurred yet, some ISSUEs are expected (e.g. no exit_attribution with embed).
