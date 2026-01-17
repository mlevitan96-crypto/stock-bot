#!/usr/bin/env python3
import re
import sys
from urllib.parse import urljoin

import requests


def main() -> int:
    docs_url = "https://api.unusualwhales.com/docs/"
    html = requests.get(docs_url, timeout=30).text
    print("docs_url:", docs_url)
    print("html_len:", len(html))

    print("\n--- first 2000 chars of HTML ---")
    print(html[:2000])
    print("--- end preview ---\n")

    # Try common swagger-ui patterns
    candidates = set()

    # Swagger UI v3 patterns
    for pat in [
        r'url\s*:\s*"([^"]+)"',
        r"url\s*:\s*'([^']+)'",
        r'urls\s*:\s*\[\s*\{[^\}]*url\s*:\s*"([^"]+)"',
        r'urls\s*:\s*\[\s*\{[^\}]*url\s*:\s*\'([^\']+)\'',
    ]:
        for m in re.finditer(pat, html, flags=re.I):
            candidates.add(m.group(1))

    # Also scrape obvious swagger/openapi filenames
    for pat in [r'[^"\']+swagger[^"\']+\.json', r'[^"\']+openapi[^"\']+\.json']:
        for m in re.finditer(pat, html, flags=re.I):
            candidates.add(m.group(0))

    # Also pull script src/href that might contain config
    for pat in [r'<script[^>]+src="([^"]+)"', r"<script[^>]+src='([^']+)'", r'<link[^>]+href="([^"]+)"']:
        for m in re.finditer(pat, html, flags=re.I):
            candidates.add(m.group(1))

    candidates = {c.strip() for c in candidates if c and c.strip()}
    resolved = sorted({urljoin(docs_url, c) for c in candidates})

    print("found_candidates:", len(resolved))
    for u in resolved[:50]:
        print(" -", u)

    # Probe candidates as JSON
    ok = []
    for u in resolved[:50]:
        try:
            r = requests.get(u, timeout=20)
            ct = (r.headers.get("content-type") or "").lower()
            if r.status_code == 200 and ("json" in ct or r.text.lstrip().startswith("{")):
                ok.append(u)
        except Exception:
            continue

    print("json_like_ok:", len(ok))
    for u in ok[:20]:
        print(" *", u)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

