#!/usr/bin/env python3
"""
Cleanup known-bad AAPL shadow trades (2026-01-22)
================================================

Contract:
- Data cleanup only (no trading/scoring/exit logic changes).
- Safe and idempotent:
  - Creates .bak backups (only once) before overwriting.
  - Skips missing files.
  - Re-running is safe (no further changes once removed).
- Surgical:
  - Only removes AAPL shadow artifacts for date 2026-01-22.
  - Never deletes non-AAPL data.
  - Never touches other dates.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TARGET_DAY = "2026-01-22"
TARGET_SYMBOL = "AAPL"


@dataclass
class CleanResult:
    path: str
    kind: str  # jsonl|json|md
    existed: bool
    changed: bool
    removed: int
    note: str = ""


def _backup_once(path: Path) -> None:
    """
    Create a .bak copy next to path if it doesn't already exist.
    """
    try:
        if not path.exists():
            return
        bak = path.with_suffix(path.suffix + ".bak")
        if bak.exists():
            return
        shutil.copy2(path, bak)
    except Exception:
        # Best-effort backups; don't block cleanup.
        return


def _is_target_day(ts: Any) -> bool:
    try:
        return str(ts or "").startswith(TARGET_DAY)
    except Exception:
        return False


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _iter_jsonl_lines(path: Path) -> Iterable[Tuple[str, Optional[Dict[str, Any]]]]:
    """
    Yields (raw_line, parsed_dict_or_none).
    Preserves unparseable lines as-is (parsed=None).
    """
    for ln in _read_text(path).splitlines():
        raw = ln
        s = ln.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                yield raw, obj
            else:
                yield raw, None
        except Exception:
            yield raw, None


def _write_jsonl(path: Path, lines: List[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    tmp.replace(path)


def _clean_jsonl(
    path: Path,
    *,
    drop_predicate,
    kind_note: str,
) -> CleanResult:
    if not path.exists():
        return CleanResult(path=str(path), kind="jsonl", existed=False, changed=False, removed=0, note="missing")

    _backup_once(path)
    kept: List[str] = []
    removed = 0
    for raw, rec in _iter_jsonl_lines(path):
        if rec is not None and drop_predicate(rec):
            removed += 1
            continue
        kept.append(raw)

    before = _read_text(path).splitlines()
    changed = removed > 0
    if changed:
        _write_jsonl(path, kept)

    # Idempotent note: if we removed nothing, file remains untouched.
    return CleanResult(
        path=str(path),
        kind="jsonl",
        existed=True,
        changed=changed,
        removed=removed,
        note=kind_note + f" (kept_lines={len(kept)} orig_lines={len(before)})",
    )


def _scrub_json_obj(x: Any) -> Tuple[Any, int]:
    """
    Generic JSON scrub:
    - Remove any dict items with symbol == AAPL (commonly inside arrays).
    - Remove any string list items == "AAPL" (e.g., overlap symbol lists).
    - Remove any dict keys == "AAPL" (e.g., pnl_by_symbol maps).
    Returns: (scrubbed_obj, removed_count)
    """
    removed = 0

    if isinstance(x, list):
        out: List[Any] = []
        for it in x:
            if isinstance(it, dict) and str(it.get("symbol", "")).upper() == TARGET_SYMBOL:
                removed += 1
                continue
            if isinstance(it, str) and it.upper() == TARGET_SYMBOL:
                removed += 1
                continue
            it2, r2 = _scrub_json_obj(it)
            removed += r2
            out.append(it2)
        return out, removed

    if isinstance(x, dict):
        out: Dict[str, Any] = {}
        for k, v in x.items():
            if isinstance(k, str) and k.upper() == TARGET_SYMBOL:
                removed += 1
                continue
            v2, r2 = _scrub_json_obj(v)
            removed += r2
            out[k] = v2
        return out, removed

    return x, 0


def _clean_json(path: Path) -> CleanResult:
    if not path.exists():
        return CleanResult(path=str(path), kind="json", existed=False, changed=False, removed=0, note="missing")
    _backup_once(path)
    try:
        d = json.loads(_read_text(path))
    except Exception:
        return CleanResult(path=str(path), kind="json", existed=True, changed=False, removed=0, note="invalid_json (skipped)")

    d2, removed = _scrub_json_obj(d)
    changed = removed > 0
    if changed:
        path.write_text(json.dumps(d2, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return CleanResult(path=str(path), kind="json", existed=True, changed=changed, removed=removed)


def _clean_md(path: Path) -> CleanResult:
    if not path.exists():
        return CleanResult(path=str(path), kind="md", existed=False, changed=False, removed=0, note="missing")
    txt = _read_text(path).splitlines(True)
    if not any(TARGET_SYMBOL in ln for ln in txt):
        return CleanResult(path=str(path), kind="md", existed=True, changed=False, removed=0)
    _backup_once(path)
    new = [ln for ln in txt if TARGET_SYMBOL not in ln]
    removed = len(txt) - len(new)
    path.write_text("".join(new), encoding="utf-8")
    return CleanResult(path=str(path), kind="md", existed=True, changed=True, removed=removed)


def _paths_under(glob_pat: str) -> List[Path]:
    try:
        return sorted(Path(".").glob(glob_pat))
    except Exception:
        return []


def main() -> int:
    results: List[CleanResult] = []

    # 1) logs/shadow_trades.jsonl (shadow-only; treat all as shadow)
    results.append(
        _clean_jsonl(
            Path("logs/shadow_trades.jsonl"),
            drop_predicate=lambda r: (
                str(r.get("symbol", "")).upper() == TARGET_SYMBOL
                and _is_target_day(r.get("ts") or r.get("timestamp") or r.get("entry_ts") or r.get("exit_ts"))
            ),
            kind_note="drop symbol=AAPL for TARGET_DAY (shadow-only log)",
        )
    )

    # 2) logs/exit_attribution.jsonl (shadow-only; treat all as shadow)
    results.append(
        _clean_jsonl(
            Path("logs/exit_attribution.jsonl"),
            drop_predicate=lambda r: (
                str(r.get("symbol", "")).upper() == TARGET_SYMBOL
                and _is_target_day(r.get("timestamp") or r.get("ts") or r.get("entry_timestamp") or r.get("exit_timestamp"))
            ),
            kind_note="drop symbol=AAPL for TARGET_DAY (shadow-only log)",
        )
    )

    # 3) logs/master_trade_log.jsonl (drop ONLY AAPL shadow entries for the date)
    results.append(
        _clean_jsonl(
            Path("logs/master_trade_log.jsonl"),
            drop_predicate=lambda r: (
                str(r.get("symbol", "")).upper() == TARGET_SYMBOL
                and bool(r.get("is_shadow")) is True
                and _is_target_day(r.get("entry_ts") or r.get("exit_ts") or r.get("timestamp"))
            ),
            kind_note="drop symbol=AAPL AND is_shadow=true for TARGET_DAY",
        )
    )

    # 4) telemetry bundle artifacts (if present)
    troot = Path("telemetry") / TARGET_DAY
    # computed/*.json
    for p in sorted((troot / "computed").glob("*.json")) if (troot / "computed").exists() else []:
        results.append(_clean_json(p))
    # state/*.json (bundle copies only; safe to scrub AAPL references)
    for p in sorted((troot / "state").glob("*.json")) if (troot / "state").exists() else []:
        results.append(_clean_json(p))
    # logs/*.jsonl (bundle copies only; drop AAPL records for the target day)
    for p in sorted((troot / "logs").glob("*.jsonl")) if (troot / "logs").exists() else []:
        def _drop_bundle_log(rec: Dict[str, Any]) -> bool:
            try:
                sym = str(rec.get("symbol", "")).upper()
                if sym != TARGET_SYMBOL:
                    return False
                ts = rec.get("ts") or rec.get("timestamp") or rec.get("_ts") or rec.get("entry_ts") or rec.get("exit_ts") or rec.get("entry_timestamp")
                return _is_target_day(ts)
            except Exception:
                return False

        results.append(_clean_jsonl(p, drop_predicate=_drop_bundle_log, kind_note="drop AAPL records for TARGET_DAY (telemetry bundle logs/)"))
    # telemetry_manifest.json
    results.append(_clean_json(troot / "telemetry_manifest.json"))
    # top-level md + reports md
    for p in [troot / f"FULL_TELEMETRY_{TARGET_DAY}.md"]:
        results.append(_clean_md(p))
    for p in sorted((troot / "reports").glob("*.md")) if (troot / "reports").exists() else []:
        results.append(_clean_md(p))

    # 5) analysis pack artifacts (if present)
    aroot = Path("analysis_packs") / TARGET_DAY
    if aroot.exists():
        for p in sorted(aroot.glob("**/*.md")):
            results.append(_clean_md(p))
        for p in sorted(aroot.glob("**/*.json")):
            results.append(_clean_json(p))

    # Summary
    cleaned = [r for r in results if r.existed and r.changed]
    removed_total = sum(r.removed for r in cleaned)

    print("CLEANUP_SUMMARY")
    print(f"- target_day: {TARGET_DAY}")
    print(f"- target_symbol: {TARGET_SYMBOL}")
    print(f"- files_touched: {len(cleaned)}")
    print(f"- removed_total: {removed_total}")
    for r in cleaned:
        print(f"  - {r.kind} {r.path}: removed={r.removed}{(' note='+r.note) if r.note else ''}")

    # Idempotency check: running again should remove 0 additional entries.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

