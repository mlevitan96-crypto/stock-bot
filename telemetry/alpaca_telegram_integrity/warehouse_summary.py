"""Parse latest truth warehouse coverage artifact; optional subprocess run."""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CoverageSummary:
    path: Optional[Path]
    execution_join_pct: Optional[float]
    fee_pct: Optional[float]
    slippage_pct: Optional[float]
    signal_snap_pct: Optional[float]
    data_ready_yes: Optional[bool]
    raw_lines: List[str] = field(default_factory=list)
    age_hours: Optional[float] = None


_PCT_RE = re.compile(
    r"(execution join coverage|fee computable|slippage computable|signal snapshot)[^*]*\*\*([0-9.]+)%",
    re.I,
)
_DATA_READY_RE = re.compile(r"DATA_READY:\s*(YES|NO)", re.I)


def _latest_coverage_file(reports: Path) -> Optional[Path]:
    if not reports.is_dir():
        return None
    best: Optional[Tuple[float, Path]] = None
    for p in reports.glob("ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md"):
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if best is None or m > best[0]:
            best = (m, p)
    return best[1] if best else None


def parse_coverage_markdown(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for m in _PCT_RE.finditer(text):
        label, val = m.group(1).lower(), m.group(2)
        try:
            v = float(val)
        except ValueError:
            continue
        if "execution" in label:
            out["execution_join_pct"] = v
        elif "fee" in label:
            out["fee_pct"] = v
        elif "slippage" in label:
            out["slippage_pct"] = v
        elif "signal" in label:
            out["signal_snap_pct"] = v
    dm = _DATA_READY_RE.search(text)
    if dm:
        out["data_ready_yes"] = dm.group(1).upper() == "YES"
    return out


def load_latest_coverage(root: Path) -> CoverageSummary:
    reports = root / "reports"
    path = _latest_coverage_file(reports)
    if not path:
        return CoverageSummary(None, None, None, None, None, None, [], None)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        age_h = (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600.0
    except OSError:
        return CoverageSummary(path, None, None, None, None, None, [], None)
    d = parse_coverage_markdown(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:25]
    return CoverageSummary(
        path=path,
        execution_join_pct=d.get("execution_join_pct"),
        fee_pct=d.get("fee_pct"),
        slippage_pct=d.get("slippage_pct"),
        signal_snap_pct=d.get("signal_snap_pct"),
        data_ready_yes=d.get("data_ready_yes"),
        raw_lines=lines,
        age_hours=round(age_h, 2),
    )


def run_warehouse_mission(root: Path, days: int, timeout_sec: int = 240) -> Tuple[int, str]:
    script = root / "scripts" / "alpaca_full_truth_warehouse_and_pnl_audit_mission.py"
    if not script.is_file():
        return 127, "mission_script_missing"
    cmd = [
        sys.executable,
        str(script),
        "--root",
        str(root),
        "--days",
        str(days),
        "--max-compute",
    ]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(root)},
        )
        tail = (r.stdout or "")[-4000:] + "\n" + (r.stderr or "")[-2000:]
        return r.returncode, tail
    except subprocess.TimeoutExpired:
        return 124, "warehouse_timeout"
    except OSError as e:
        return 125, str(e)
