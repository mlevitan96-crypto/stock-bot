# Cleanup and Branch Policy

**Goal:** Less clutter (unused/old files and reports), no hunting through many branches. Operate from `main`; use at most one secondary branch for implementations. Last updated: 2026-02-26.

---

## 1. Branch policy

### Preferred model

- **Primary:** All normal work and history lives on **`main`**.
- **Secondary (optional):** One branch only—e.g. **`staging`** or **`deploy`**—for:
  - Droplet/CI pushes that you later merge into `main`, or
  - Short-lived implementation work that you merge and then delete.
- **No long-lived feature branches.** No `feature/xyz`, `fix/abc`, or timestamped branches like `export-20251223-*`. Merge to `main` (or to the single staging branch, then to `main`) and delete the branch.

### What to do

1. **Delete old branches** (see §3 below)—local and remote.
2. **Default workflow:** Commit and push to `main`. Use one other branch only when you explicitly want a staging/deploy branch; when done, merge into `main` and delete the branch.
3. **Scripts that create branches:** The Cursor/promotion scripts (`cursor_one_shot_runall.sh`, `cursor_final_one_shot_run.sh`, `cursor_full_automated_orchestrator*.sh`, `run_promotion_candidate_1_single_run_on_droplet.sh`, etc.) currently create PR/promotion branches. To align with this policy you can:
   - **Option A:** Change them to push to `main` (no PR branch).
   - **Option B:** Use a single branch name (e.g. `staging`) instead of a new branch per run; overwrite it each time and merge to `main` when ready.

---

## 2. File and report cleanup

### 2.1 What to ignore (stop tracking or adding)

Add or tighten `.gitignore` so generated/run artifacts are not committed:

- **Backtest run outputs:** `backtests/30d_*/`, `reports/backtests/`
- **Bars/droplet run artifacts:** `reports/bars/`, `reports/bars_droplet_*/`
- **Timestamped run dirs** under reports (optional): e.g. `reports/*/*_20260*Z/` (Cursor/board run outputs with timestamps)

Keeping these out of git reduces noise and avoids hunting through hundreds of one-off files. Essential reports (e.g. governance indexes, EOD verification, strategic reviews) stay tracked.

### 2.2 What to archive (move, don’t delete)

- **Old one-off reports** you might still want for reference: move into a single archive, e.g. `reports/archive/` or `archive/reports_YYYY/`, then commit once. After that, add `reports/archive/` to `.gitignore` if you don’t want future archive content in git.
- **Already-archived code:** The repo has an `archive/` folder for old scripts; leave it as-is or consolidate further later.

### 2.3 What to delete (optional)

- **Purely generated artifacts** that can be recreated (e.g. run logs, timestamped Cursor run dirs, duplicate backtest outputs). Prefer deleting only after you’ve added the right `.gitignore` rules so they don’t come back as untracked clutter.
- **Duplicate or obsolete docs** in `reports/` or `docs/`: after a quick scan, remove only what you’re sure is redundant; keep governance, EOD, and strategic summaries.

### 2.4 Safe cleanup order

1. Update `.gitignore` (see §4).
2. Delete or archive only what you’re comfortable with; leave core reports and docs in place.
3. Run a cleanup (e.g. `git status` and remove/archive the listed untracked dirs), then commit the `.gitignore` and any one-time archive move.

---

## 3. Branch cleanup (exact steps)

**Current branches (as of 2026-02-26):**

- **Local (candidates to delete):** `audit-fixes-deployment`, `data-integrity/high-water-giveback`, `export-20251223-214834`, `export-20251223-215324`, `export-20251223-215748`, `fix-all-issues-20251224-135727`
- **Remote (candidates to delete):** `origin/cursor/stock-trading-bot-review-2377`, `origin/data-integrity/high-water-giveback`, `origin/export-20251223-195855`, `origin/export-20251223-204922`, `origin/export-20251223-214834`, `origin/export-20251223-215324`, `origin/export-20251223-215748`
- **Keep:** `main`, `origin/main`

**Assumption:** Anything important from those branches is already merged into `main` or you’ve confirmed you don’t need it.

### 3.1 Delete local branches (from `main`)

```powershell
cd c:\Dev\stock-bot
git checkout main
git branch -D audit-fixes-deployment
git branch -D data-integrity/high-water-giveback
git branch -D export-20251223-214834
git branch -D export-20251223-215324
git branch -D export-20251223-215748
git branch -D fix-all-issues-20251224-135727
```

### 3.2 Delete remote branches

```powershell
git push origin --delete cursor/stock-trading-bot-review-2377
git push origin --delete data-integrity/high-water-giveback
git push origin --delete export-20251223-195855
git push origin --delete export-20251223-204922
git push origin --delete export-20251223-214834
git push origin --delete export-20251223-215324
git push origin --delete export-20251223-215748
```

### 3.3 Prune remote-tracking refs

```powershell
git fetch --prune
git branch -a
```

You should see only `main` and `origin/main` (and optionally one staging branch if you create it).

---

## 4. .gitignore additions (recommended)

Add these so generated outputs and run artifacts stay untracked and don’t clutter `git status`:

```gitignore
# Backtest run outputs (regeneratable)
backtests/30d_*/
reports/backtests/

# Bars / droplet run artifacts
reports/bars/
reports/bars_droplet_*/

# Optional: timestamped Cursor/board run dirs under reports (uncomment if you want to ignore all)
# reports/*/*_202*Z/
```

The last line is optional; use it only if you’re sure you don’t want to track any of those timestamped run directories.

---

## 5. Summary

| Action | Purpose |
|--------|---------|
| **Branch policy** | Work and push on `main`; at most one other branch (e.g. `staging`) for implementations; merge then delete. |
| **Delete old branches** | Stop hunting through many branches; keep only `main` (and optional `staging`). |
| **.gitignore** | Stop committing backtest/bars and optional run artifacts; keep repo focused. |
| **Archive old reports** | Move one-off/old reports to `reports/archive/` (or similar) if you want to keep them but not in the main tree. |
| **Scripts** | Optionally change Cursor/promotion scripts to push to `main` or to a single `staging` branch. |

Yes, we should do the cleanup: it makes the repo easier to work in and aligns with “everything operates out of main, one secondary branch for implementations, no hunting through branches.”
