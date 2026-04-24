#!/usr/bin/env python3
"""Merge a GitHub pull request via REST API. Uses .env GITHUB_TOKEN/GH_TOKEN."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

def _load_dotenv():
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
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN in .env", file=sys.stderr)
        sys.exit(1)
    pr_num = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    repo = os.environ.get("GITHUB_REPO", "mlevitan96-crypto/stock-bot")
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_num}/merge"
    req = urllib.request.Request(url, data=b"{}", method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(data.get("message", "Merged."))
            print(data.get("sha", ""))
            return 0
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else str(e)
        print(f"GitHub API error: {e.code} {e.reason}", file=sys.stderr)
        print(err, file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
