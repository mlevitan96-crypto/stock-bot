# Go Live — Repo Cleanup PR

**Branch `cursor/repo-cleanup-20260227` is pushed to origin.**

## 1. Open the pull request

Create the PR on GitHub (use either method):

- **Browser:** https://github.com/mlevitan96-crypto/stock-bot/pull/new/cursor/repo-cleanup-20260227  
- **CLI (after `gh auth login`):**  
  `gh pr create --base main --head cursor/repo-cleanup-20260227 --title "Repo cleanup: archive stale reports, canonical audit docs, Memory Bank 2.5" --body-file reports/repo_audit/SAFE_TO_APPLY_PR.md`

Use the body from **`reports/repo_audit/SAFE_TO_APPLY_PR.md`** (copy/paste or `--body-file`).

## 2. Merge to main

After review (and optional full pytest run):

- Merge the PR into `main` on GitHub (Merge pull request).
- Then locally: `git checkout main && git pull origin main`
- Droplet: after merge, deploy from `main` as usual (e.g. trigger your normal deploy). No need to checkout the cleanup branch on droplet; once merged, `main` has the cleanup.

## 3. Optional: set upstream for this branch

```bash
git checkout cursor/repo-cleanup-20260227
git branch --set-upstream-to=origin/cursor/repo-cleanup-20260227
```

## Summary

| Step | Status |
|------|--------|
| Cleanup branch created | Done |
| Reports archived to reports/archive/2026-02/ | Done |
| repo_audit artifacts + Memory Bank 2.5 + README_DEPRECATED_SCRIPTS | Done |
| TEST_RESULTS + DROPLET_DRY_RUN + SAFE_TO_APPLY checklist | Done |
| Committed and pushed to origin | Done |
| Open PR | **You:** use link above or `gh pr create` after `gh auth login` |
| Merge to main | **You:** merge PR on GitHub |
| Deploy from main | **You:** use your normal deploy process |
