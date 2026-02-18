# Snapshot fix — root cause decision

**Decision:** **B) Hook reached, write fails (path/permission/exception)** — with primary cause **path resolution**.

**Sub-choice:** Path is CWD-relative. The snapshot file is opened with `Path("logs/score_snapshot.jsonl")`, which is resolved against the process CWD. If the paper run is started from a directory other than repo root (e.g. script that `cd`s into `board/eod` or runs from a different cwd), the file is created at `$CWD/logs/score_snapshot.jsonl`. Observers running `tail logs/score_snapshot.jsonl` or `wc -l logs/score_snapshot.jsonl` from repo root then see no file or an empty file at repo root, while the real file may exist elsewhere.

**Evidence (code):**

- `score_snapshot_writer.py` line 12: `SCORE_SNAPSHOT_FILE = Path("logs/score_snapshot.jsonl")` — no resolution against repo root or `__file__`.
- Droplet runbooks and scripts (e.g. `start_live_paper_run.py`) do `cd /root/stock-bot-current || cd /root/stock-bot` then run `python3 main.py`, so CWD is usually repo root; however, any other entry point (e.g. runner that does not `cd`, or test, or future wrapper) would break the assumption.
- Dashboard and other log readers use repo-root–relative paths; canonical place for the file is repo_root/logs/score_snapshot.jsonl. Making the writer CWD-independent aligns with that and removes dependence on how the process is started.

**Why not A/C/D:**

- **A (hook never reached):** Plausible if there are 0 clusters or all blocked earlier; we cannot confirm without droplet logs. The minimal, safe fix that addresses the most likely bug (path) does not depend on A.
- **C (writes succeed but no cycles):** Would require orchestration/schedule change; not a bug in the snapshot writer itself.
- **D (orchestration prevents execution):** Same as C; runbook already starts from repo root.

**Conclusion:** Treat **B — path resolution** as the root cause and apply a minimal fix: resolve `SCORE_SNAPSHOT_FILE` relative to the package root (e.g. `Path(__file__).resolve().parent`) so the file is always written to repo_root/logs/score_snapshot.jsonl regardless of CWD.
