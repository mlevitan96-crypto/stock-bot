#!/usr/bin/env python3
"""
Validate known JSON and JSONL artifacts. Exit non-zero if corruption detected.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARTIFACTS = [
    ("state/signal_history.jsonl", "jsonl"),
    ("logs/score_snapshot.jsonl", "jsonl"),
    ("logs/gate.jsonl", "jsonl"),
    ("logs/attribution.jsonl", "jsonl"),
    ("logs/exit_attribution.jsonl", "jsonl"),
]


def check_jsonl(path: Path) -> tuple[int, int]:
    """Return (valid_lines, malformed_lines)."""
    if not path.exists():
        return 0, 0
    valid = 0
    malformed = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                json.loads(line)
                valid += 1
            except json.JSONDecodeError:
                malformed += 1
    return valid, malformed


def check_json(path: Path) -> bool:
    """Return True if valid single JSON."""
    if not path.exists():
        return True
    try:
        path.read_text(encoding="utf-8", errors="replace")
        json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return True
    except json.JSONDecodeError:
        return False


def main() -> int:
    failed = []
    for rel, kind in ARTIFACTS:
        path = REPO / rel
        if kind == "jsonl":
            valid, malformed = check_jsonl(path)
            if malformed > 0:
                failed.append(f"{rel}: {malformed} malformed line(s)")
            print(f"{rel}: {valid} valid, {malformed} malformed")
        else:
            ok = check_json(path)
            if not ok:
                failed.append(f"{rel}: invalid JSON")
            print(f"{rel}: {'OK' if ok else 'INVALID'}")
    if failed:
        print("FAIL:", "; ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
