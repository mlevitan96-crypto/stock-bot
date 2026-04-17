#!/usr/bin/env python3
"""
Off-Leash Alpaca Red Team Hunt (production / droplet).

No prescriptive checklist-only pass: scans journal, process RSS/threads, JSONL health,
and keyword surfaces in run/system_events for friction signals. See MEMORY_BANK_ALPACA.md
for canonical paths (logs/exit_attribution.jsonl, stock-bot.service, etc.).

Usage:
  PYTHONPATH=/root/stock-bot python3 scripts/audit/off_leash_alpaca_hunt.py --root /root/stock-bot
  python3 scripts/audit/off_leash_alpaca_hunt.py --root . --no-journal   # local smoke
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iter_jsonl_lines(path: Path, max_lines: int, from_tail: bool) -> Iterator[Tuple[int, str]]:
    """Yield (1-based line_no_approx, line) for up to max_lines; from_tail reads last chunk only (approx lines)."""
    if not path.is_file():
        return
    if max_lines <= 0:
        return
    if not from_tail:
        n = 0
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if n >= max_lines:
                    break
                s = line.strip()
                if s:
                    yield i, s
                    n += 1
        return

    try:
        size = path.stat().st_size
    except OSError:
        return
    chunk = min(32 * 1024 * 1024, size)
    with path.open("rb") as f:
        f.seek(max(0, size - chunk))
        raw = f.read().decode("utf-8", errors="replace")
    lines = raw.splitlines()
    take = lines[-max_lines:] if len(lines) > max_lines else lines
    base = max(0, len(lines) - len(take))
    for j, line in enumerate(take):
        s = line.strip()
        if s:
            yield base + j + 1, s


def _scan_jsonl_corruption(
    path: Path, max_lines: int, label: str
) -> Dict[str, Any]:
    bad = 0
    ok = 0
    samples: List[str] = []
    for _, s in _iter_jsonl_lines(path, max_lines, from_tail=True):
        try:
            json.loads(s)
            ok += 1
        except json.JSONDecodeError as e:
            bad += 1
            if len(samples) < 5:
                samples.append(f"{e.msg} @ col {e.colno}: {s[:200]!r}")
    return {
        "path": str(path),
        "label": label,
        "lines_attempted_approx": ok + bad,
        "json_ok": ok,
        "json_decode_error": bad,
        "samples": samples,
    }


def _grep_file_keywords(
    path: Path, max_lines: int, patterns: List[Tuple[str, re.Pattern]]
) -> Dict[str, Any]:
    hits: Dict[str, int] = {name: 0 for name, _ in patterns}
    samples: Dict[str, List[str]] = defaultdict(list)
    if not path.is_file():
        return {"path": str(path), "hits": hits, "samples": dict(samples), "missing": True}
    for _, s in _iter_jsonl_lines(path, max_lines, from_tail=True):
        low = s.lower()
        for name, pat in patterns:
            if pat.search(s) or pat.search(low):
                hits[name] += 1
                if len(samples[name]) < 3:
                    samples[name].append(s[:400])
    return {"path": str(path), "hits": hits, "samples": {k: v for k, v in samples.items() if v}}


def _journal_hunt(unit: str, lines: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {"unit": unit, "lines_requested": lines, "ok": False, "stderr": "", "patterns": {}}
    try:
        proc = subprocess.run(
            ["journalctl", f"-u{unit}", f"-n{lines}", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        out["exit_code"] = proc.returncode
        out["stderr"] = (proc.stderr or "")[:2000]
        text = proc.stdout or ""
        out["ok"] = proc.returncode == 0
        out["char_len"] = len(text)
        pats = {
            "ERROR": re.compile(r"\bERROR\b", re.I),
            "WARN": re.compile(r"\bWARN(ING)?\b", re.I),
            "timeout": re.compile(r"timeout|timed out", re.I),
            # Avoid matching sub-second timestamps like ",429 " in log lines.
            "429": re.compile(
                r"(?:\bHTTP\s*/?1\.1\s+429\b|status[^\n]{0,24}\b429\b|"
                r"rate\s*limit|too\s+many\s+requests|uw_rate_limit|http_status[^\n]*429)",
                re.I,
            ),
            "SIP": re.compile(
                r"\bsip\b|wss://stream\.data\.alpaca|market-data.*402|"
                r"CRITICAL_DATA_STALE|stream.*auth\s*fail",
                re.I,
            ),
            "PDT": re.compile(r"\bpdt\b|pattern day", re.I),
            "wash": re.compile(r"wash.?sale|wash sale", re.I),
            "ghost": re.compile(r"close_position.*None|returned None|unhandled", re.I),
            "CRITICAL": re.compile(r"CRITICAL", re.I),
            "JSONDecodeError": re.compile(r"JSONDecodeError", re.I),
            "sqlite": re.compile(r"sqlite|database is locked", re.I),
        }
        counts = Counter()
        samples: Dict[str, List[str]] = defaultdict(list)
        for line in text.splitlines():
            for name, pat in pats.items():
                if pat.search(line):
                    counts[name] += 1
                    if len(samples[name]) < 4:
                        samples[name].append(line[:500])
        out["pattern_counts"] = dict(counts)
        out["pattern_samples"] = {k: v for k, v in samples.items() if v}
        out["tail_preview"] = text[-4000:] if len(text) > 4000 else text
    except FileNotFoundError:
        out["note"] = "journalctl not available (not Linux or not in PATH)"
    except subprocess.TimeoutExpired:
        out["note"] = "journalctl timed out"
    except Exception as e:
        out["note"] = str(e)[:500]
    return out


def _proc_rss_threads() -> Dict[str, Any]:
    info: Dict[str, Any] = {"pids": [], "entries": [], "note": None}
    try:
        proc = subprocess.run(
            ["pgrep", "-f", "python.*main.py"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            info["note"] = "no pgrep match for python.*main.py"
            return info
        pids = [x.strip() for x in proc.stdout.split() if x.strip().isdigit()]
        info["pids"] = pids[:8]
        for pid in info["pids"]:
            status = Path(f"/proc/{pid}/status")
            if not status.is_file():
                continue
            vmrss = None
            threads = None
            name = None
            try:
                for line in status.read_text(errors="replace").splitlines():
                    if line.startswith("Name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("VmRSS:"):
                        vmrss = line.split(":", 1)[1].strip()
                    elif line.startswith("Threads:"):
                        threads = line.split(":", 1)[1].strip()
            except OSError:
                pass
            info["entries"].append(
                {"pid": pid, "name": name, "VmRSS": vmrss, "Threads": threads}
            )
    except FileNotFoundError:
        info["note"] = "pgrep/proc not available"
    except Exception as e:
        info["note"] = str(e)[:400]
    return info


def _sqlite_probe(root: Path) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen: set[Path] = set()
    globs: List[Path] = []
    for base in (root / "state", root / "data"):
        if base.is_dir():
            globs.extend(base.rglob("*.db"))
            globs.extend(base.rglob("*.sqlite"))
    for pp in globs:
        if pp in seen or not pp.is_file():
            continue
        seen.add(pp)
        try:
            rel = str(pp.relative_to(root))
        except ValueError:
            rel = str(pp)
        row: Dict[str, Any] = {"path": rel, "size": pp.stat().st_size}
        try:
            import sqlite3

            conn = sqlite3.connect(f"file:{pp}?mode=ro", uri=True, timeout=1.0)
            try:
                cur = conn.execute("PRAGMA integrity_check")
                row["integrity_check"] = cur.fetchone()[0]
            finally:
                conn.close()
        except Exception as e:
            row["error"] = str(e)[:300]
        results.append(row)
        if len(results) >= 24:
            break
    return results


def run_hunt(root: Path, *, journal_lines: int, jsonl_tail: int, skip_journal: bool) -> Dict[str, Any]:
    root = root.resolve()
    logs = root / "logs"
    findings: Dict[str, Any] = {
        "schema": "off_leash_alpaca_hunt_v1",
        "root": str(root),
        "generated_at_utc": _now_iso(),
        "journalctl": None,
        "process": _proc_rss_threads(),
        "sqlite": _sqlite_probe(root),
        "jsonl_corruption": [],
        "keyword_hunts": [],
    }

    if not skip_journal:
        findings["journalctl"] = _journal_hunt("stock-bot.service", journal_lines)

    for rel, label in (
        ("logs/exit_attribution.jsonl", "exit_attribution"),
        ("logs/entry_snapshots.jsonl", "entry_snapshots"),
        ("logs/run.jsonl", "run"),
        ("logs/system_events.jsonl", "system_events"),
        ("logs/orders.jsonl", "orders"),
        ("logs/signal_context.jsonl", "signal_context"),
    ):
        p = root / rel if not rel.startswith("logs/") else root / rel
        findings["jsonl_corruption"].append(_scan_jsonl_corruption(p, jsonl_tail, label))

    kw_patterns = [
        ("rate_limit", re.compile(r"429|rate.?limit|throttl", re.I)),
        ("sip_stream", re.compile(r"\bsip\b|websocket|wss://stream\.data\.alpaca|CRITICAL_DATA_STALE", re.I)),
        ("pdt", re.compile(r"pdt|pattern day|day trade", re.I)),
        ("wash", re.compile(r"wash", re.I)),
        ("order_none", re.compile(r"returned None|close_position|submit.*fail", re.I)),
        ("polygon", re.compile(r"polygon", re.I)),
        ("alpaca_api", re.compile(r"alpaca.*(4\d\d|5\d\d)|paper-api|api\.alpaca", re.I)),
    ]
    findings["keyword_hunts"] = [
        _grep_file_keywords(root / "logs" / "run.jsonl", jsonl_tail, kw_patterns),
        _grep_file_keywords(root / "logs" / "system_events.jsonl", jsonl_tail, kw_patterns),
    ]

    return findings


def _findings_to_markdown(f: Dict[str, Any]) -> str:
    lines = [
        "# RED_TEAM_REPORT — Off-Leash Alpaca Hunt",
        "",
        f"**Generated (UTC):** `{f.get('generated_at_utc')}`  ",
        f"**Root:** `{f.get('root')}`  ",
        f"**Schema:** `{f.get('schema')}`  ",
        "",
        "## 1. Executive threats (machine-readable summary)",
        "",
        "```json",
        json.dumps(
            {
                "json_decode_errors_total": sum(
                    x.get("json_decode_error", 0) for x in f.get("jsonl_corruption", [])
                ),
                "journal_error_hits": (f.get("journalctl") or {}).get("pattern_counts", {}).get("ERROR", 0),
                "journal_warn_hits": (f.get("journalctl") or {}).get("pattern_counts", {}).get("WARN", 0),
                "journal_429_hits": (f.get("journalctl") or {}).get("pattern_counts", {}).get("429", 0),
            },
            indent=2,
        ),
        "```",
        "",
        "## 2. journalctl — stock-bot.service",
        "",
        "```",
        json.dumps(f.get("journalctl"), indent=2, default=str)[:24000],
        "```",
        "",
        "## 3. Process memory / threads (main.py)",
        "",
        "```json",
        json.dumps(f.get("process"), indent=2),
        "```",
        "",
        "## 4. SQLite probes (read-only)",
        "",
        "```json",
        json.dumps(f.get("sqlite"), indent=2),
        "```",
        "",
        "## 5. JSONL corruption (tail scan)",
        "",
        "```json",
        json.dumps(f.get("jsonl_corruption"), indent=2),
        "```",
        "",
        "## 6. Keyword hunts — run.jsonl + system_events.jsonl (tails)",
        "",
        "```json",
        json.dumps(f.get("keyword_hunts"), indent=2)[:16000],
        "```",
        "",
        "## 7. Board triage prompts (unconstrained)",
        "",
        "- Any non-zero `json_decode_error` in canonical logs is telemetry integrity debt: treat as P0 until explained.",
        "- Journal `ghost` / `close_position` samples: execution path may be losing broker confirmation while UI still shows risk.",
        "- 429 / rate_limit clusters: external API budget or retry storm; correlate with UW and Alpaca REST.",
        "- PDT / wash hits in logs: compliance surfacing; verify operator visibility and block reason propagation.",
        "- SIP / stream / CRITICAL_DATA_STALE: market-data contract breach; session-edge entries are NO-GO per governance.",
        "",
        "---",
        "*End of automated hunt. Human red team: correlate timestamps across journal + run.jsonl + exit_attribution.*",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--journal-lines", type=int, default=4000)
    ap.add_argument("--jsonl-tail", type=int, default=150_000)
    ap.add_argument("--no-journal", action="store_true")
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    if args.out_json is None:
        args.out_json = root / "reports" / "off_leash_hunt_findings.json"
    if args.out_md is None:
        args.out_md = root / "reports" / "RED_TEAM_REPORT.md"

    findings = run_hunt(
        root,
        journal_lines=args.journal_lines,
        jsonl_tail=args.jsonl_tail,
        skip_journal=args.no_journal,
    )
    md = _findings_to_markdown(findings)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    args.out_md.write_text(md, encoding="utf-8")
    print(json.dumps({"ok": True, "json": str(args.out_json), "md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
