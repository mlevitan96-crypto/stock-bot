"""Exit attribution sampling + strict completeness snapshot."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ExitSchemaReport:
    lines_scanned: int
    missing_field_counts: Dict[str, int]
    examples: List[str] = field(default_factory=list)


def probe_exit_attribution_tail(
    path: Path,
    tail_lines: int,
    required_fields: Sequence[str],
) -> ExitSchemaReport:
    missing = {k: 0 for k in required_fields}
    examples: List[str] = []
    if not path.is_file():
        for k in required_fields:
            missing[k] = tail_lines
        return ExitSchemaReport(0, missing, ["file_missing"])

    lines: List[str] = []
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 65536
            buf = b""
            while size > 0 and len(lines) < tail_lines:
                read = min(block, size)
                size -= read
                f.seek(size)
                buf = f.read(read) + buf
                lines = buf.splitlines()[-tail_lines:]
    except OSError:
        return ExitSchemaReport(0, {k: tail_lines for k in required_fields}, ["read_error"])

    decoded = [ln.decode("utf-8", errors="replace").strip() for ln in lines if ln.strip()]
    scanned = 0
    for line in decoded[-tail_lines:]:
        scanned += 1
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            if len(examples) < 3:
                examples.append("json_decode_error")
            continue
        if not isinstance(o, dict):
            continue
        for k in required_fields:
            v = o.get(k)
            if v is None or v == "":
                missing[k] += 1
    return ExitSchemaReport(scanned, missing, examples)


def run_strict_completeness(root: Path) -> Dict[str, Any]:
    """Import gate in-process (same as audits)."""
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    return evaluate_completeness(root, open_ts_epoch=None, audit=False)


def latest_spi_pointer(root: Path) -> Optional[str]:
    reports = root / "reports"
    if not reports.is_dir():
        return None
    best: Optional[tuple[float, Path]] = None
    for pat in ("ALPACA_SPI_SECTION_*.md", "ALPACA_PNL_SIGNAL_PATH_INTELLIGENCE_*.md"):
        for p in reports.glob(pat):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if best is None or m > best[0]:
                best = (m, p)
    if not best:
        for p in (root / "reports" / "daily").rglob("ALPACA_SPI_SECTION_*.md"):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if best is None or m > best[0]:
                best = (m, p)
    return str(best[1].relative_to(root)) if best else None


def cooldown_ok(state: Dict[str, Any], key: str, cooldown_sec: float, now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(timezone.utc)
    last = state.get("cooldowns", {}).get(key)
    if not last:
        return True
    try:
        prev = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        if prev.tzinfo is None:
            prev = prev.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    return (now - prev).total_seconds() >= cooldown_sec


def touch_cooldown(state: Dict[str, Any], key: str, now: Optional[datetime] = None) -> None:
    now = now or datetime.now(timezone.utc)
    state.setdefault("cooldowns", {})[key] = now.isoformat()
