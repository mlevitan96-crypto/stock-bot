# Snapshot fix — adversarial review (after fix)

**Fix applied:** Resolve `SCORE_SNAPSHOT_FILE` from `Path(__file__).resolve().parent` so the snapshot is always written to repo_root/logs/score_snapshot.jsonl (CWD-independent).

---

## Could this still fail silently?

- **Path:** No. The file path is now fixed relative to the package root; no dependence on CWD. If the writer is imported from a different package (e.g. installed elsewhere), `__file__` would point to that install’s location — acceptable and still a single, deterministic path.
- **Exceptions:** When `SCORE_SNAPSHOT_DEBUG` is not set, exceptions in `append_score_snapshot` are still caught and ignored (pass). So serialization or I/O errors can still fail silently. Mitigation: run with DEBUG=1 after deploy to confirm; long-term, consider logging (e.g. single warning) on first failure without breaking trading.
- **Disk full / permission:** Would raise; same as before. No new silent failure mode.

---

## Remaining blind spots

- **Zero candidates:** If no clusters ever reach the expectancy gate, the hook is never called and the file stays empty. That is correct behavior (nothing to snapshot), not a bug in the writer. Diagnostics (gate logs, cluster counts) are separate.
- **Multiple processes:** If two paper runs write to the same file, both use the same resolved path; appends are interleaved but JSONL remains valid. No change from before.

---

## Reversible and safe?

- **Reversible:** Yes. Revert the commit to restore `Path("logs/score_snapshot.jsonl")`. Existing consumers that assume CWD=repo root keep working; only non-repo-root invocations would again see the previous bug.
- **Safe:** Yes. Same file name and schema; only the resolution of the path changed. No tuning, no refactors, no new features.
