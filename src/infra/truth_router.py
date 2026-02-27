"""
Canonical Truth Root (CTR) — Truth Router.

Single authoritative write/read surface for truth streams. Phase 1: mirror mode only
(write to CTR and legacy when TRUTH_ROUTER_ENABLED=1 and TRUTH_ROUTER_MIRROR_LEGACY=1).
Callers remain responsible for legacy writes; router only adds CTR write when enabled.

Env:
  TRUTH_ROUTER_ENABLED: 1 to write to CTR (default 0).
  TRUTH_ROUTER_MIRROR_LEGACY: 1 to keep mirroring legacy (default 1 when enabled).
  STOCKBOT_TRUTH_ROOT: CTR root directory (default /var/lib/stock-bot/truth).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

_DEFAULT_ROOT = "/var/lib/stock-bot/truth"


def _root() -> Path:
    return Path(os.environ.get("STOCKBOT_TRUTH_ROOT", _DEFAULT_ROOT))


def _enabled() -> bool:
    return os.environ.get("TRUTH_ROUTER_ENABLED", "0").strip() in ("1", "true", "yes")


def _mirror_legacy() -> bool:
    return os.environ.get("TRUTH_ROUTER_MIRROR_LEGACY", "1").strip() in ("1", "true", "yes")


def truth_path(rel: str) -> str:
    """Return absolute path for a relative truth stream (e.g. 'gates/expectancy.jsonl')."""
    root = _root()
    # Normalize: no leading slash, use forward slashes
    r = rel.lstrip("/").replace("\\", "/")
    return str((root / r).resolve())


def _ensure_parents(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _update_heartbeat(stream_rel: str) -> None:
    """Update meta/last_write_heartbeat.json (best-effort, never raise)."""
    if not _enabled():
        return
    try:
        root = _root()
        meta_dir = root / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        heartbeat_file = meta_dir / "last_write_heartbeat.json"
        now = datetime.now(timezone.utc)
        ts_epoch = time.time()
        data = {
            "ts_iso": now.isoformat(),
            "ts_epoch": ts_epoch,
            "stream": stream_rel,
        }
        tmp = heartbeat_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(heartbeat_file)
    except Exception:
        pass


_SCHEMA_VERSION = "1.0.0"


def _ensure_meta() -> None:
    """Write meta/schema_version.json and meta/producer_versions.json if missing (best-effort)."""
    try:
        root = _root()
        meta_dir = root / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        sv_path = meta_dir / "schema_version.json"
        if not sv_path.exists():
            tmp = sv_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"schema_version": _SCHEMA_VERSION}, f, indent=2)
            tmp.replace(sv_path)
        # truth_manifest.json: streams, expected freshness, schema
        manifest_path = meta_dir / "truth_manifest.json"
        if not manifest_path.exists():
            manifest = {
                "streams": [
                    {"id": "gates/expectancy.jsonl", "expected_max_age_sec": 300, "schema_version": _SCHEMA_VERSION},
                    {"id": "health/signal_health.jsonl", "expected_max_age_sec": 600, "schema_version": _SCHEMA_VERSION},
                    {"id": "health/signal_score_breakdown.jsonl", "expected_max_age_sec": 300, "schema_version": _SCHEMA_VERSION},
                    {"id": "exits/exit_truth.jsonl", "expected_max_age_sec": 600, "schema_version": _SCHEMA_VERSION},
                    {"id": "exits/exit_attribution.jsonl", "expected_max_age_sec": 600, "schema_version": _SCHEMA_VERSION},
                    {"id": "telemetry/score_telemetry.json", "expected_max_age_sec": 600, "schema_version": _SCHEMA_VERSION},
                    {"id": "telemetry/score_snapshot.jsonl", "expected_max_age_sec": 300, "schema_version": _SCHEMA_VERSION},
                ],
                "updated_iso": datetime.now(timezone.utc).isoformat(),
            }
            tmp = manifest_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            tmp.replace(manifest_path)
        pv_path = meta_dir / "producer_versions.json"
        if not pv_path.exists():
            import subprocess
            sha = ""
            try:
                r = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                )
                if r.returncode == 0 and r.stdout:
                    sha = r.stdout.strip()[:12]
            except Exception:
                pass
            tmp = pv_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({
                    "git_sha": sha,
                    "service": "stock-bot",
                    "updated_iso": datetime.now(timezone.utc).isoformat(),
                }, f, indent=2)
            tmp.replace(pv_path)
    except Exception:
        pass


def _update_freshness(stream_rel: str, expected_max_age_sec: int = 600) -> None:
    """Update health/freshness.json for this stream (best-effort)."""
    if not _enabled():
        return
    try:
        root = _root()
        health_dir = root / "health"
        health_dir.mkdir(parents=True, exist_ok=True)
        freshness_file = health_dir / "freshness.json"
        now_epoch = time.time()
        # Load existing or start fresh
        data: Dict[str, Any] = {}
        if freshness_file.exists():
            try:
                with open(freshness_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        streams = data.get("streams", {})
        streams[stream_rel] = {
            "last_ts": now_epoch,
            "last_ts_iso": datetime.now(timezone.utc).isoformat(),
            "last_mtime": int(now_epoch),
            "expected_max_age_sec": expected_max_age_sec,
        }
        data["streams"] = streams
        data["updated_iso"] = datetime.now(timezone.utc).isoformat()
        tmp = freshness_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(freshness_file)
    except Exception:
        pass


def append_jsonl(
    rel: str,
    record: Dict[str, Any],
    *,
    expected_max_age_sec: int = 600,
) -> None:
    """
    Append one JSONL record to CTR stream at `rel`. Call only when TRUTH_ROUTER_ENABLED=1.
    Legacy write is caller's responsibility. Updates heartbeat and freshness (best-effort).
    Never raises; logs on failure.
    """
    if not _enabled():
        return
    path = Path(truth_path(rel))
    try:
        _ensure_meta()
        _ensure_parents(path)
        line = json.dumps(record, default=str) + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
        _update_heartbeat(rel)
        _update_freshness(rel, expected_max_age_sec)
    except Exception as e:
        if os.environ.get("TRUTH_ROUTER_DEBUG") == "1":
            import traceback
            traceback.print_exc()
        # Do not raise; mirror must not break trading


def write_json(
    rel: str,
    obj: Dict[str, Any],
    *,
    expected_max_age_sec: int = 600,
) -> None:
    """
    Atomically write JSON object to CTR path `rel`. Uses temp file + rename.
    Updates heartbeat and freshness. Never raises.
    """
    if not _enabled():
        return
    path = Path(truth_path(rel))
    try:
        _ensure_meta()
        _ensure_parents(path)
        tmp = path.parent / (path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, default=str)
        tmp.replace(path)
        _update_heartbeat(rel)
        _update_freshness(rel, expected_max_age_sec)
    except Exception as e:
        if os.environ.get("TRUTH_ROUTER_DEBUG") == "1":
            import traceback
            traceback.print_exc()


def is_writable() -> bool:
    """Return True if CTR root exists and is writable (for startup check when enabled)."""
    if not _enabled():
        return True
    root = _root()
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".probe"
        probe.write_text("ok")
        probe.unlink()
        return True
    except Exception:
        return False
