# Cursor + GitHub Integration

How to let Cursor (and agents) create pull requests and push directly to GitHub.

## What Cursor’s GitHub integration does

- **Cursor GitHub App** ([docs](https://cursor.com/docs/integrations/github)): lets Cursor clone, push, and **create PRs** when using **Cloud Agents** (e.g. “Launch an Agent” with `autoCreatePr: true`). The app has “Pull requests | Create PRs with agent changes.”
- **In-IDE agent** (this repo): can run `git` and scripts. It does **not** get a GitHub token from Cursor by default. To create a PR from the current branch you either:
  - Use **GitHub CLI** after logging in: `gh auth login` then `gh pr create ...`, or
  - Use **GitHub API** with a token: set `GITHUB_TOKEN` (or `GH_TOKEN`) and run `scripts/github_create_pr.py` (or call the API yourself).

## Creating a PR from Cursor (this repo)

### Option A: GitHub CLI

1. In a terminal (Cursor’s or system): `gh auth login` and complete the flow.
2. From repo root:
   ```bash
   gh pr create --base main --head cursor/repo-cleanup-20260227 \
     --title "Repo cleanup: archive stale reports, canonical audit docs, Memory Bank 2.5" \
     --body-file reports/repo_audit/SAFE_TO_APPLY_PR.md
   ```

### Option B: GitHub API with token (script)

1. Create a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope.
2. Set it where Cursor’s terminal can see it:
   - **Cursor env**: Cursor Settings → search “environment” / “env” and add `GITHUB_TOKEN` if supported, or
   - **Project .env**: add `GITHUB_TOKEN=ghp_...` to `.env` (ensure `.env` is in `.gitignore`), or
   - **Shell**: `$env:GITHUB_TOKEN = "ghp_..."` (PowerShell) or `export GITHUB_TOKEN=ghp_...` (bash).
3. From repo root:
   ```bash
   python scripts/github_create_pr.py --body-file reports/repo_audit/SAFE_TO_APPLY_PR.md
   ```
   Optional: `--head`, `--base`, `--title`, `--repo` (see script help).

### Option C: Browser

- Open: `https://github.com/mlevitan96-crypto/stock-bot/compare/main...cursor/repo-cleanup-20260227?expand=1`
- Add title and paste body from `reports/repo_audit/SAFE_TO_APPLY_PR.md`, then “Create pull request”.

## Direct integration you have

- **Git push**: Cursor (and the GitHub app when using Cloud Agents) can push to `origin` if the repo is connected and you’ve pushed before (credentials / SSH already set).
- **PR creation**: Not automatic from the in-IDE agent unless you use one of the options above (gh, token + script, or browser).

## Troubleshooting: git push fails with HTTP 500

If you see `error: RPC failed; HTTP 500 curl 22` or `The requested URL returned error: 500` when pushing:

1. **Increase HTTP buffer and use HTTP/1.1** (often fixes the issue):
   ```bash
   git config http.postBuffer 524288000
   git config http.version HTTP/1.1
   git push origin main
   ```
   These settings are stored in the repo's `.git/config` and persist.

2. **If it still fails**: Check [GitHub Status](https://www.githubstatus.com/). If GitHub is healthy, try again later or switch the remote to SSH: `git remote set-url origin git@github.com:mlevitan96-crypto/stock-bot.git` (requires SSH key added to GitHub).

## References

- [Cursor – GitHub](https://cursor.com/docs/integrations/github)
- [Cloud Agents API](https://cursor.com/docs/background-agent/api/endpoints) (for `autoCreatePr` when launching agents)
- [GitHub REST API – Create a pull request](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request)
