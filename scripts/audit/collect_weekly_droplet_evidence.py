#!/usr/bin/env python3
"""
Collect weekly evidence from droplet for CSA weekly board audit.
Pulls: executed trades, exit attribution, signal/blocked events, counter-intel,
order validation, governance, SRE, CSA artifacts, shadow/board JSONs.
Writes: reports/audit/WEEKLY_EVIDENCE_MANIFEST_<YYYY-MM-DD>.json
On critical missing source: reports/audit/WEEKLY_EVIDENCE_BLOCKER_<YYYY-MM-DD>.md and exit 1.

Usage:
  python scripts/audit/collect_weekly_droplet_evidence.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


# Remote paths relative to project_dir on droplet. "tail:N" = fetch last N lines only.
# exit_decision_trace + exit_attribution are required for forensic/backfill scenario runs (see docs/TRADE_DATA_FOR_SCENARIOS.md).
EVIDENCE_SPEC = [
    # Critical: trades and exits (7d slice done by ledger script; here we pull raw for manifest + scenario runs)
    ("logs/exit_attribution.jsonl", "tail:10000"),
    ("reports/state/exit_decision_trace.jsonl", "tail:50000"),
    ("state/blocked_trades.jsonl", "tail:2000"),
    ("logs/score_snapshot.jsonl", "tail:2000"),
    ("logs/attribution.jsonl", "tail:1500"),
    # Governance & SRE
    ("reports/audit/GOVERNANCE_AUTOMATION_STATUS.json", "full"),
    ("reports/audit/SRE_STATUS.json", "full"),
    ("reports/audit/SRE_EVENTS.jsonl", "tail:500"),
    # CSA this week (we'll glob CSA_VERDICT_*.json and CSA_FINDINGS_*.md separately)
    ("reports/audit/CSA_VERDICT_LATEST.json", "full"),
    ("reports/state/TRADE_CSA_STATE.json", "full"),
    # Board / shadow
    ("reports/board/last387_comprehensive_review.json", "full"),
    ("reports/board/30d_comprehensive_review.json", "full"),
    ("reports/board/SHADOW_COMPARISON_LAST387.json", "full"),
]

# Optional (do not block if missing)
OPTIONAL_SPEC = [
    ("reports/audit/deploy_runtime_context_data.json", "full"),
    ("reports/board/COMPARATIVE_REVIEW_30D_vs_LAST387.json", "full"),
    ("state/direction_readiness.json", "full"),
    ("logs/options_events.jsonl", "tail:200"),
]


def _b64_read_full(client, remote_path: str, timeout: int = 90) -> tuple[bool, bytes, str]:
    """Read full file on droplet, return (success, data, error)."""
    cmd = (
        "./venv/bin/python -c "
        "\"import base64; "
        f"p='{remote_path}'; "
        "b=open(p,'rb').read(); "
        "print(base64.b64encode(b).decode('ascii'))\""
    )
    r = client.execute_command(cmd, timeout=timeout)
    out = (r.get("stdout") or "").strip()
    err = (r.get("stderr") or "").strip()
    if not r.get("success"):
        return False, b"", err or "exit_code != 0"
    try:
        return True, base64.b64decode(out.encode("ascii")), ""
    except Exception as e:
        return False, b"", str(e)


def _b64_tail(client, remote_path: str, lines: int, timeout: int = 90) -> tuple[bool, bytes, str]:
    """Tail last N lines on droplet, return (success, data, error)."""
    cmd = (
        "./venv/bin/python -c "
        "\"import base64,pathlib; "
        f"p=pathlib.Path('{remote_path}'); "
        f"n={lines}; "
        "b=(p.read_bytes() if p.exists() else b''); "
        "lines=b.splitlines()[-n:]; "
        "out=(b'\\n'.join(lines) + (b'\\n' if lines else b'')); "
        "print(base64.b64encode(out).decode('ascii'))\""
    )
    r = client.execute_command(cmd, timeout=timeout)
    out = (r.get("stdout") or "").strip()
    err = (r.get("stderr") or "").strip()
    if not r.get("success"):
        return False, b"", err or "exit_code != 0"
    try:
        return True, base64.b64decode(out.encode("ascii")), ""
    except Exception as e:
        return False, b"", str(e)


def _fetch_one(client, remote_path: str, spec: str, local_root: Path) -> tuple[bool, int, str | None]:
    """Fetch one file. spec is 'full' or 'tail:N'. Returns (success, size_bytes, error)."""
    local_path = local_root / remote_path
    ensure_dir(local_path.parent)
    if spec == "full":
        ok, data, err = _b64_read_full(client, remote_path)
    else:
        n = 2000
        if spec.startswith("tail:"):
            n = int(spec.split(":")[1])
        ok, data, err = _b64_tail(client, remote_path, n)
    if not ok:
        return False, 0, err
    local_path.write_bytes(data)
    return True, len(data), None


def _glob_csa_artifacts(client) -> list[str]:
    """List CSA_VERDICT_*.json and CSA_FINDINGS_*.md on droplet (paths relative to project_dir)."""
    out: list[str] = []
    for pattern in ["reports/audit/CSA_VERDICT_*.json", "reports/audit/CSA_FINDINGS_*.md"]:
        cmd = f"python3 -c \"import pathlib; d=pathlib.Path('reports/audit'); print('\\n'.join(str(p) for p in d.glob('{pattern.split('/')[-1]}') if p.is_file()))\""
        r = client.execute_command(cmd, timeout=15)
        if r.get("success") and r.get("stdout"):
            for line in (r.get("stdout") or "").strip().splitlines():
                line = line.strip()
                if line and line.startswith("reports/"):
                    out.append(line)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect weekly evidence from droplet")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    args = ap.parse_args()
    if args.date:
        try:
            dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print("Invalid --date; use YYYY-MM-DD", file=sys.stderr)
            return 1
    else:
        dt = datetime.now(timezone.utc)
    date_str = dt.strftime("%Y-%m-%d")
    audit_dir = REPO / "reports" / "audit"
    ensure_dir(audit_dir)
    manifest_path = audit_dir / f"WEEKLY_EVIDENCE_MANIFEST_{date_str}.json"
    blocker_path = audit_dir / f"WEEKLY_EVIDENCE_BLOCKER_{date_str}.md"

    # Local staging dir for pulled files (same layout as repo)
    stage_dir = REPO / "reports" / "audit" / "weekly_evidence_stage"
    ensure_dir(stage_dir)

    manifest = {
        "date": date_str,
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "coverage_window_days": 7,
        "sources": [],
        "critical_missing": [],
        "optional_missing": [],
    }

    try:
        client = DropletClient()
    except Exception as e:
        manifest["critical_missing"].append(f"droplet_connection: {e}")
        blocker_lines = [
            "# Weekly Evidence Blocker — " + date_str,
            "",
            "## Remediation",
            "1. Ensure droplet is reachable (SSH alias from droplet_config.json).",
            "2. Run again: `python scripts/audit/collect_weekly_droplet_evidence.py --date " + date_str + "`",
            "",
            "## Error",
            str(e),
        ]
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        blocker_path.write_text("\n".join(blocker_lines), encoding="utf-8")
        print("BLOCKER: droplet connection failed", file=sys.stderr)
        return 1

    # Critical sources
    for remote_path, spec in EVIDENCE_SPEC:
        local_path = stage_dir / remote_path
        if spec == "full":
            ok, size, err = _fetch_one(client, remote_path, "full", stage_dir)
        else:
            n = int(spec.split(":")[1])
            ok, size, err = _fetch_one(client, remote_path, f"tail:{n}", stage_dir)
        rec = {"path": remote_path, "spec": spec, "size_bytes": size if ok else 0, "pulled": ok}
        if err:
            rec["error"] = err
            if remote_path.startswith("logs/") or remote_path.startswith("state/") or "reports/audit/GOVERNANCE" in remote_path or "SRE_STATUS" in remote_path or "CSA_VERDICT_LATEST" in remote_path or "reports/board/last387" in remote_path or "SHADOW_COMPARISON" in remote_path:
                manifest["critical_missing"].append(f"{remote_path}: {err}")
        manifest["sources"].append(rec)

    # Optional
    for remote_path, spec in OPTIONAL_SPEC:
        ok, size, _ = _fetch_one(client, remote_path, spec, stage_dir)
        rec = {"path": remote_path, "spec": spec, "size_bytes": size if ok else 0, "pulled": ok, "optional": True}
        if not ok:
            manifest["optional_missing"].append(remote_path)
        manifest["sources"].append(rec)

    # CSA glob
    csa_files = _glob_csa_artifacts(client)
    for rel in csa_files:
        ok, size, _ = _fetch_one(client, rel, "full", stage_dir)
        manifest["sources"].append({"path": rel, "spec": "full", "size_bytes": size if ok else 0, "pulled": ok, "csa_artifact": True})

    # Fail closed: if any critical source is missing, write blocker and stop
    if manifest["critical_missing"]:
        blocker_lines = [
            "# Weekly Evidence Blocker — " + date_str,
            "",
            "One or more critical evidence sources could not be pulled from the droplet.",
            "",
            "## Critical missing",
            "",
        ]
        for m in manifest["critical_missing"]:
            blocker_lines.append(f"- {m}")
        blocker_lines.extend([
            "",
            "## Remediation",
            "1. On droplet, ensure files exist and are readable (e.g. logs/exit_attribution.jsonl, state/blocked_trades.jsonl, reports/audit/GOVERNANCE_AUTOMATION_STATUS.json, SRE_STATUS.json, reports/board/last387_comprehensive_review.json, SHADOW_COMPARISON_LAST387.json).",
            "2. If paths differ, update EVIDENCE_SPEC in scripts/audit/collect_weekly_droplet_evidence.py.",
            "3. Re-run: `python scripts/audit/collect_weekly_droplet_evidence.py --date " + date_str + "`",
            "",
        ])
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        blocker_path.write_text("\n".join(blocker_lines), encoding="utf-8")
        print("BLOCKER: critical sources missing. See", blocker_path, file=sys.stderr)
        return 1

    # Add file timestamps where possible (from local staged files)
    for s in manifest["sources"]:
        p = stage_dir / s["path"]
        if p.exists():
            try:
                s["mtime_iso"] = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
            except Exception:
                pass

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Manifest written:", manifest_path)
    print("Staged evidence under:", stage_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
