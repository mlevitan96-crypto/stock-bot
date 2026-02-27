#!/usr/bin/env python3
"""
Trace dashboard "signal history" JSON error on droplet.
Identifies the artifact, reproduces parse failure, and writes a trace report.
Run from repo root on droplet (or via droplet client).
"""
import json
import math
from pathlib import Path

SIGNAL_HISTORY_FILE = Path("state/signal_history.jsonl")
OUTPUT_MD = Path("reports/truth_audit_fix/20260218_dashboard_json_error_trace.md")


def _sanitize(obj):
    """Replace NaN/Inf for JSON serialization."""
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    return obj


def main():
    trace = {
        "file_path": str(SIGNAL_HISTORY_FILE.resolve()),
        "file_exists": SIGNAL_HISTORY_FILE.exists(),
        "file_size": SIGNAL_HISTORY_FILE.stat().st_size if SIGNAL_HISTORY_FILE.exists() else 0,
        "error": None,
        "position": None,
        "snippet": None,
        "root_cause": None,
    }

    if not SIGNAL_HISTORY_FILE.exists():
        trace["root_cause"] = "File missing"
        _write_trace(trace)
        return

    signals = []
    malformed = 0
    last_malformed_ts = None
    for line in SIGNAL_HISTORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            signals.append(obj)
        except json.JSONDecodeError as e:
            malformed += 1
            last_malformed_ts = None  # we don't have ts from bad line
            trace["first_line_error"] = str(e)
            trace["first_line_snippet"] = line[:200] if len(line) > 200 else line

    # Build same payload as API; use allow_nan=False to detect NaN/Inf (dashboard parse error)
    payload = {"signals": signals, "last_signal_timestamp": "", "count": len(signals)}
    try:
        raw = json.dumps(payload, allow_nan=False)
        trace["payload_size"] = len(raw)
        trace["root_cause"] = "none (payload serializes)"
        if malformed > 0:
            trace["root_cause"] = "malformed_lines_in_file (API skips them; if payload still fails, check for NaN in parsed objects)"
        trace["malformed_line_count"] = malformed
    except (TypeError, ValueError) as e:
        trace["error"] = str(e)
        trace["root_cause"] = "non_serializable_value (likely NaN/Inf in signal dict)"
        # Try to find bad value
        for i, s in enumerate(signals):
            try:
                json.dumps(s)
            except (TypeError, ValueError) as err:
                trace["first_bad_index"] = i
                trace["first_bad_keys"] = list(s.keys())[:20]
                trace["error"] = str(err)
                break
    except Exception as e:
        trace["error"] = str(e)
        trace["root_cause"] = "unknown"

    # Reproduce "position 24233" style: simulate parsing the response body as JSON
    try:
        body = json.dumps(payload, allow_nan=False)
    except ValueError as e:
        trace["error"] = str(e)
        trace["root_cause"] = trace["root_cause"] or "invalid_number_in_payload (e.g. NaN)"
    else:
        try:
            json.loads(body)
        except json.JSONDecodeError as e:
            trace["error"] = str(e)
            trace["position"] = getattr(e, "pos", None)
            if trace["position"] is not None and body:
                pos = trace["position"]
                trace["snippet"] = body[max(0, pos - 40) : pos + 40]

    _write_trace(trace)


def _write_trace(trace: dict):
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dashboard JSON Error — Trace",
        "",
        "## File",
        "- **Path:** " + trace.get("file_path", "?"),
        "- **Exists:** " + str(trace.get("file_exists")),
        "- **Size:** " + str(trace.get("file_size", 0)),
        "",
        "## Reproduction",
        "- **Error:** " + (trace.get("error") or "none"),
        "- **Position:** " + str(trace.get("position", "N/A")),
        "- **Snippet around position:** " + ("```\n" + (trace.get("snippet") or "") + "\n```" if trace.get("snippet") else "N/A"),
        "",
        "## Root cause classification",
        "- " + (trace.get("root_cause") or "unknown"),
        "",
    ]
    if trace.get("malformed_line_count") is not None:
        lines.append("- Malformed lines in file: " + str(trace["malformed_line_count"]))
        lines.append("")
    if trace.get("first_line_error"):
        lines.append("## First malformed line (sample)")
        lines.append("```")
        lines.append(trace.get("first_line_snippet", ""))
        lines.append("```")
        lines.append("")
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("Trace written to", OUTPUT_MD)


if __name__ == "__main__":
    main()
