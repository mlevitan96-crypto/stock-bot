#!/usr/bin/env python3
"""
Create a GitHub pull request via REST API.
Uses GITHUB_TOKEN or GH_TOKEN from environment or .env (Cursor–GitHub integration or local).
Usage: python scripts/github_create_pr.py [--head BRANCH] [--base BASE] [--title TITLE] [--body-file PATH]
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

def _load_dotenv():
    """Load .env from repo root (stdlib only)."""
    root = Path(__file__).resolve().parent.parent
    for p in [root / ".env", Path.cwd() / ".env"]:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, _, v = line.partition("=")
                            k, v = k.strip(), v.strip()
                            if k and v and v not in ('""', "''"):
                                os.environ.setdefault(k, v.strip('"').strip("'"))
            except OSError:
                pass
            break

def main():
    _load_dotenv()
    ap = argparse.ArgumentParser(description="Create GitHub PR via API")
    ap.add_argument("--head", default="cursor/repo-cleanup-20260227", help="Head branch")
    ap.add_argument("--base", default="main", help="Base branch")
    ap.add_argument("--title", default="Repo cleanup: archive stale reports, canonical audit docs, Memory Bank 2.5", help="PR title")
    ap.add_argument("--body-file", default=None, help="Path to PR body (markdown file)")
    ap.add_argument("--repo", default="mlevitan96-crypto/stock-bot", help="owner/repo")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        root = Path(__file__).resolve().parent.parent
        env_path = root / ".env"
        print("ERROR: No GITHUB_TOKEN or GH_TOKEN found.", file=sys.stderr)
        print("  1. Create a token: https://github.com/settings/tokens (scope: repo)", file=sys.stderr)
        print(f"  2. Add to {env_path}:  GITHUB_TOKEN=ghp_your_token_here", file=sys.stderr)
        print("  3. Run this script again.", file=sys.stderr)
        sys.exit(1)

    body = ""
    if args.body_file and os.path.isfile(args.body_file):
        with open(args.body_file, "r", encoding="utf-8") as f:
            body = f.read()
    elif args.body_file:
        print(f"Warning: body file not found: {args.body_file}", file=sys.stderr)

    payload = {
        "title": args.title,
        "head": args.head,
        "base": args.base,
        "body": body or None,
    }
    url = f"https://api.github.com/repos/{args.repo}/pulls"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(data.get("html_url", data.get("url", "")))
            return 0
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else str(e)
        print(f"GitHub API error: {e.code} {e.reason}", file=sys.stderr)
        print(err, file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
