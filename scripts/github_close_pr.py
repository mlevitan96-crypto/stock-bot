#!/usr/bin/env python3
"""Close a GitHub pull request (no merge). Uses GITHUB_TOKEN/GH_TOKEN from .env."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

def _load_dotenv():
    root = Path(__file__).resolve().parents[1]
    for p in [root / ".env", Path.cwd() / ".env"]:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and v:
                            os.environ.setdefault(k, v)
            break

def main():
    _load_dotenv()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN or GH_TOKEN", file=sys.stderr)
        sys.exit(1)
    pr_num = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if not pr_num:
        print("Usage: python github_close_pr.py <PR_NUMBER>", file=sys.stderr)
        sys.exit(1)
    repo = os.environ.get("GITHUB_REPO", "mlevitan96-crypto/stock-bot")
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url, data=json.dumps({"state": "closed"}).encode(), method="PATCH")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode())
            print(f"Closed PR #{pr_num}: {d.get('state')}")
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
