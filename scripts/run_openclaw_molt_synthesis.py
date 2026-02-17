#!/usr/bin/env python3
"""
Molt workflow → OpenClaw synthesis.
After the in-repo Molt workflow completes, call OpenClaw to produce
operator actions and one optional MEMORY_BANK suggestion (NOT APPLIED).
Writes reports/MOLT_OPENCLAW_SYNTHESIS_<date>.md.
NO-APPLY: all outputs are advisory for human review.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

CLAWDBOT_PATH = os.environ.get("CLAWDBOT_PATH") or (
    r"C:\Users\markl\AppData\Roaming\npm\clawdbot.cmd" if sys.platform == "win32" else "clawdbot"
)

PROMPT_TEMPLATE = """You are a NON-AUTHORITATIVE REVIEWER.
Do NOT propose code or config changes.
Do NOT override governance decisions.

Given the following governance artifacts:
- Learning status
- Engineering health
- Promotion proposal or rejection
- Memory bank change proposal

Produce:
1) Five concise bullet points for the human operator:
   - What matters today
   - What is blocked
   - What is risky
   - What should be reviewed next
   - What should NOT be touched yet

2) ONE optional MEMORY_BANK change to CONSIDER (not apply),
   clearly labeled as a suggestion.

Output valid JSON with keys:
- operator_actions (array of strings)
- memory_bank_suggestion (string or null)
"""


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def _extract_json(raw: str) -> str | None:
    raw = raw.strip()
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        cand = m.group(1).strip()
        try:
            json.loads(cand)
            return cand
        except json.JSONDecodeError:
            pass
    start = raw.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    cand = raw[start : i + 1]
                    try:
                        json.loads(cand)
                        return cand
                    except json.JSONDecodeError:
                        break
    return None


def run_openclaw_synthesis(date: str, base_dir: Path, dry_run: bool = False) -> int:
    """
    Load Molt artifacts, call OpenClaw, write reports/MOLT_OPENCLAW_SYNTHESIS_<date>.md.
    On OpenClaw unavailable or parse failure, write stub file. Never raises; returns 0 or 1.
    """
    reports_dir = base_dir / "reports"
    out_path = reports_dir / f"MOLT_OPENCLAW_SYNTHESIS_{date}.md"

    learning = _load_text(reports_dir / f"LEARNING_STATUS_{date}.md")
    engineering = _load_text(reports_dir / f"ENGINEERING_HEALTH_{date}.md")
    promotion = _load_text(reports_dir / f"PROMOTION_PROPOSAL_{date}.md")
    if not promotion:
        promotion = _load_text(reports_dir / f"REJECTION_WITH_REASON_{date}.md")
    memory_proposal = _load_text(reports_dir / f"MEMORY_BANK_CHANGE_PROPOSAL_{date}.md")

    body = f"""
## Learning status
{learning or "(none)"}

## Engineering health
{engineering or "(none)"}

## Promotion proposal or rejection
{promotion or "(none)"}

## Memory bank change proposal
{memory_proposal or "(none)"}
""".strip()

    prompt = PROMPT_TEMPLATE.strip() + "\n\n---\n\n" + body

    if dry_run:
        stub = {
            "operator_actions": ["[Dry-run] Run without --dry-run and OpenClaw in PATH for real synthesis."],
            "memory_bank_suggestion": None,
        }
        _write_synthesis_md(out_path, date, stub)
        log.info("Dry-run: wrote stub synthesis to %s", out_path)
        return 0

    session_id = os.environ.get("CLAWDBOT_SESSION_ID") or f"molt_synthesis_{date}"
    cmd = [CLAWDBOT_PATH, "agent", "--session-id", session_id, "--message", prompt]

    try:
        r = subprocess.run(
            cmd,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
        raw = r.stdout or ""
        if r.returncode != 0:
            log.warning("OpenClaw exit %s stderr: %s", r.returncode, (r.stderr or "")[:500])
    except FileNotFoundError:
        log.error("OpenClaw (clawdbot) not found. Use --dry-run or install clawdbot and add to PATH.")
        _write_stub_failure(out_path, date, "OpenClaw (clawdbot) not found in PATH.")
        return 1
    except subprocess.TimeoutExpired:
        log.error("OpenClaw call timed out.")
        _write_stub_failure(out_path, date, "OpenClaw call timed out (300s).")
        return 1
    except Exception as e:
        log.exception("OpenClaw call failed.")
        _write_stub_failure(out_path, date, str(e))
        return 1

    extracted = _extract_json(raw)
    if not extracted:
        _write_stub_failure(out_path, date, "Could not extract valid JSON from OpenClaw response.")
        return 1

    try:
        data = json.loads(extracted)
        operator_actions = data.get("operator_actions")
        memory_bank_suggestion = data.get("memory_bank_suggestion")
        if not isinstance(operator_actions, list):
            operator_actions = [str(operator_actions)] if operator_actions else []
        if memory_bank_suggestion is not None:
            memory_bank_suggestion = str(memory_bank_suggestion)
        stub = {"operator_actions": operator_actions, "memory_bank_suggestion": memory_bank_suggestion}
        _write_synthesis_md(out_path, date, stub)
        log.info("Wrote %s", out_path)
        return 0
    except (json.JSONDecodeError, TypeError) as e:
        log.warning("Parse error: %s", e)
        _write_stub_failure(out_path, date, f"Parse error: {e}")
        return 1


def _write_synthesis_md(path: Path, date: str, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Molt → OpenClaw Synthesis — {date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**NO-APPLY.** Advisory only. Human review required.",
        "",
        "## Operator Actions",
        "",
    ]
    for item in data.get("operator_actions") or []:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Memory Bank Suggestion (NOT APPLIED)",
        "",
    ])
    suggestion = data.get("memory_bank_suggestion")
    if suggestion:
        lines.append(suggestion)
        lines.append("")
        lines.append("*This is a suggestion only. Do not apply unless explicitly approved.*")
    else:
        lines.append("*None.*")
    lines.extend([
        "",
        "---",
        "*Generated by scripts/run_openclaw_molt_synthesis.py. NO-APPLY.*",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_stub_failure(path: Path, date: str, reason: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Molt → OpenClaw Synthesis — {date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**Status:** Synthesis failed (stub file).",
        "",
        "## Operator Actions",
        "",
        f"- Synthesis could not be produced: {reason}",
        "",
        "## Memory Bank Suggestion (NOT APPLIED)",
        "",
        "*None (synthesis unavailable).*",
        "",
        "---",
        "*Generated by scripts/run_openclaw_molt_synthesis.py. Stub on OpenClaw failure.*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Molt workflow → OpenClaw synthesis (NO-APPLY)")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script parent)")
    ap.add_argument("--dry-run", action="store_true", help="Skip OpenClaw call, write stub")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return run_openclaw_synthesis(date, base, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
