#!/usr/bin/env python3
"""
Stock Quant Officer EOD runner.

- Ensures board/eod/ and board/eod/out/
- Loads canonical 8-file EOD bundle from repo root (logs/, state/)
- Loads Stock Quant Officer contract (board/stock_quant_officer_contract.md)
- Builds prompt (contract + bundle summary), calls Clawdbot agent, parses JSON
- Writes board/eod/out/stock_quant_officer_eod_<DATE>.json and .md

Run from repo root: python board/eod/run_stock_quant_officer_eod.py
Use --dry-run to skip Clawdbot and write stub JSON/memo (for testing without clawdbot).
Set CLAWDBOT_SESSION_ID for clawdbot agent --session-id.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repo root: parent of board/ (script at board/eod/run_...py -> parents[2])
SCRIPT_DIR = Path(__file__).resolve().parent
BOARD_DIR = SCRIPT_DIR.parent
REPO_ROOT = BOARD_DIR.parent
OUT_DIR = SCRIPT_DIR / "out"
CONTRACT_PATH = BOARD_DIR / "stock_quant_officer_contract.md"
CLAWDBOT_PATH = os.environ.get("CLAWDBOT_PATH") or (
    r"C:\Users\markl\AppData\Roaming\npm\clawdbot.cmd" if sys.platform == "win32" else "clawdbot"
)
# Windows CLI length limit; keep prompt under this to avoid "command line too long".
MAX_PROMPT_LEN = 6000

# Canonical EOD bundle paths (source of truth on droplet: logs/, state/ under repo root).
# Do not move or rename; trading engine writes these.
BUNDLE_FILES = [
    ("logs/attribution.jsonl", "attribution"),
    ("logs/exit_attribution.jsonl", "exit_attribution"),
    ("logs/master_trade_log.jsonl", "master_trade_log"),
    ("state/blocked_trades.jsonl", "blocked_trades"),
    ("state/daily_start_equity.json", "daily_start_equity"),
    ("state/peak_equity.json", "peak_equity"),
    ("state/signal_weights.json", "signal_weights"),
    ("state/daily_universe_v2.json", "daily_universe_v2"),
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_dirs() -> None:
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def load_bundle() -> tuple[dict[str, dict | list | None], list[str]]:
    """Load 8-file bundle from repo root (canonical paths: logs/, state/). Returns (data, missing)."""
    data: dict[str, dict | list | None] = {}
    missing: list[str] = []
    for rel, name in BUNDLE_FILES:
        path = (REPO_ROOT / rel).resolve()
        if not path.exists():
            log.error("Bundle file missing: %s", path)
            missing.append(rel)
            data[name] = None
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        if size == 0:
            log.warning("Bundle file empty: %s", path)
            data[name] = [] if name in ("attribution", "exit_attribution", "master_trade_log", "blocked_trades") else None
            continue
        if name in ("attribution", "exit_attribution", "master_trade_log", "blocked_trades"):
            data[name] = _load_jsonl(path)
        else:
            data[name] = _load_json(path)
    return data, missing


def summarize_bundle(data: dict[str, dict | list | None], missing: list[str]) -> str:
    """Build text summary of EOD bundle for the prompt."""
    lines: list[str] = ["## EOD bundle summary", ""]

    # Attribution + exit attribution
    attr = data.get("attribution") or []
    exit_attr = data.get("exit_attribution") or []
    if isinstance(attr, list) and attr:
        wins = sum(1 for r in attr if (r.get("pnl_usd") or 0) > 0)
        losses = sum(1 for r in attr if (r.get("pnl_usd") or 0) < 0)
        total_pnl = sum(float(r.get("pnl_usd") or 0) for r in attr)
        reasons: dict[str, int] = {}
        for r in attr:
            ctx = r.get("context") or {}
            ex = ctx.get("close_reason") or "unknown"
            reasons[ex] = reasons.get(ex, 0) + 1
        sample = attr[-5:] if len(attr) >= 5 else attr
        lines.append("### Attribution (logs/attribution.jsonl)")
        lines.append(f"- Trades: {len(attr)}, Wins: {wins}, Losses: {losses}, Total P&L USD: {total_pnl:.2f}")
        lines.append(f"- Exit reasons: {reasons}")
        lines.append("- Sample trades (last 5):")
        for t in sample:
            lines.append(f"  - {t.get('symbol')} pnl_usd={t.get('pnl_usd')} ts={t.get('ts', '')[:19]}")
        lines.append("")
    elif "logs/attribution.jsonl" not in missing:
        lines.append("### Attribution (logs/attribution.jsonl): empty or invalid.")
        lines.append("")
    else:
        lines.append("### Attribution: **MISSING**")
        lines.append("")

    if isinstance(exit_attr, list) and exit_attr:
        total_pnl_ex = sum(float(r.get("pnl") or 0) for r in exit_attr)
        reasons_ex: dict[str, int] = {}
        for r in exit_attr:
            ex = str(r.get("exit_reason") or "unknown")
            reasons_ex[ex] = reasons_ex.get(ex, 0) + 1
        sample_ex = exit_attr[-5:] if len(exit_attr) >= 5 else exit_attr
        lines.append("### Exit attribution (logs/exit_attribution.jsonl)")
        lines.append(f"- Exits: {len(exit_attr)}, Total P&L: {total_pnl_ex:.2f}")
        lines.append(f"- Exit reasons: {reasons_ex}")
        lines.append("- Sample (last 5):")
        for t in sample_ex:
            lines.append(f"  - {t.get('symbol')} pnl={t.get('pnl')} reason={t.get('exit_reason')}")
        lines.append("")
    elif "logs/exit_attribution.jsonl" not in missing:
        lines.append("### Exit attribution: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Exit attribution: **MISSING**")
        lines.append("")

    # Master trade log
    mtl = data.get("master_trade_log") or []
    if isinstance(mtl, list) and mtl:
        entries = sum(1 for r in mtl if r.get("entry_ts") and not r.get("exit_ts"))
        exits = sum(1 for r in mtl if r.get("exit_ts"))
        lines.append("### Master trade log (logs/master_trade_log.jsonl)")
        lines.append(f"- Records: {len(mtl)}, entries-without-exit: {entries}, with-exit: {exits}")
        lines.append("")
    elif "logs/master_trade_log.jsonl" not in missing:
        lines.append("### Master trade log: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Master trade log: **MISSING**")
        lines.append("")

    # Blocked trades
    bt = data.get("blocked_trades") or []
    if isinstance(bt, list) and bt:
        by_reason: dict[str, int] = {}
        for r in bt:
            reason = str(r.get("reason") or "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        sample_bt = bt[-5:] if len(bt) >= 5 else bt
        lines.append("### Blocked trades (state/blocked_trades.jsonl)")
        lines.append(f"- Count: {len(bt)}")
        lines.append(f"- By reason: {by_reason}")
        lines.append("- Sample (last 5):")
        for t in sample_bt:
            lines.append(f"  - {t.get('symbol')} reason={t.get('reason')} score={t.get('score')}")
        lines.append("")
    elif "state/blocked_trades.jsonl" not in missing:
        lines.append("### Blocked trades: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Blocked trades: **MISSING**")
        lines.append("")

    # Equity
    dse = data.get("daily_start_equity")
    pe = data.get("peak_equity")
    lines.append("### Daily start equity (state/daily_start_equity.json)")
    if isinstance(dse, dict):
        lines.append(f"- equity: {dse.get('equity')}, date: {dse.get('date')}, updated: {dse.get('updated')}")
    elif "state/daily_start_equity.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")
    lines.append("### Peak equity (state/peak_equity.json)")
    if isinstance(pe, dict):
        lines.append(f"- peak_equity: {pe.get('peak_equity')}, peak_timestamp: {pe.get('peak_timestamp')}")
    elif "state/peak_equity.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    # Signal weights
    sw = data.get("signal_weights")
    lines.append("### Signal weights (state/signal_weights.json)")
    if isinstance(sw, dict):
        keys = list(sw.keys())[:20]
        lines.append(f"- Top-level keys (up to 20): {keys}")
    elif "state/signal_weights.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    # Daily universe v2
    uv = data.get("daily_universe_v2")
    lines.append("### Daily universe v2 (state/daily_universe_v2.json)")
    if isinstance(uv, dict):
        syms = uv.get("symbols")
        if isinstance(syms, list):
            lines.append(f"- Symbol count: {len(syms)}, sample: {syms[:15]}")
        else:
            lines.append(f"- Keys: {list(uv.keys())[:15]}")
    elif "state/daily_universe_v2.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    if missing:
        lines.append("### Missing files")
        lines.append(", ".join(missing))
        lines.append("")

    return "\n".join(lines)


def load_contract() -> str:
    if not CONTRACT_PATH.exists():
        log.warning("Contract missing: %s", CONTRACT_PATH)
        return ""
    return CONTRACT_PATH.read_text(encoding="utf-8", errors="replace")


def build_prompt(contract: str, bundle_summary: str, date_str: str) -> str:
    return f"""You are the Gemini Stock Quant Officer. Today's EOD date: {date_str}.
Ignore any prior context. Use ONLY the EOD bundle summary below.

{contract}

---

{bundle_summary}

---

Produce a single JSON object with keys: verdict, summary, pnl_metrics, regime_context, sector_context, recommendations, citations, falsification_criteria. Emit only valid JSON, no markdown fences or surrounding text."""


def _truncate_prompt_for_cli(prompt: str, max_len: int = MAX_PROMPT_LEN) -> str:
    """Truncate prompt to avoid Windows 'command line too long' when passing via --message."""
    if sys.platform != "win32":
        return prompt  # no truncation on Linux (droplet); full bundle summary required
    if len(prompt) <= max_len:
        return prompt
    suffix = "\n\n[EOD bundle summary truncated for Windows CLI length.]"
    return prompt[: max_len - len(suffix)] + suffix


def run_clawdbot_prompt(prompt: str, dry_run: bool = False) -> str:
    """Call Clawdbot agent with prompt, return stdout.
    TODO: Model/provider selection (Gemini). Use clawdbot --help to confirm subcommand.
    Uses `clawdbot agent --message` for one-off agent turn; `message send` targets channels.
    """
    if dry_run:
        log.info("Dry-run: skipping clawdbot call.")
        return json.dumps({
            "verdict": "CAUTION",
            "summary": "Dry-run; no model response.",
            "pnl_metrics": {},
            "regime_context": {"regime_label": "", "regime_confidence": None, "notes": "dry-run"},
            "sector_context": {"sectors_traded": [], "sector_pnl": None, "notes": "dry-run"},
            "recommendations": [],
            "citations": [],
            "falsification_criteria": [{"id": "fc-dry", "description": "Dry-run; replace with real run.", "observed": None, "data_source": "dry-run"}],
        })
    prompt = _truncate_prompt_for_cli(prompt)
    session_id = os.environ.get("CLAWDBOT_SESSION_ID")
    if not session_id:
        log.error("CLAWDBOT_SESSION_ID is not set.")
        raise ValueError("CLAWDBOT_SESSION_ID required")
    cmd = [CLAWDBOT_PATH, "agent", "--session-id", session_id, "--message", prompt]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        log.error("clawdbot not found. Install or add to PATH. Try: npx clawdbot or moltbot. Use --dry-run to skip.")
        raise
    if r.returncode != 0:
        log.warning("clawdbot exit %s stderr: %s", r.returncode, (r.stderr or "")[:500])
    return r.stdout or ""


def extract_json(raw: str) -> str | None:
    """Try to extract JSON from raw response (e.g. ```json ... ```)."""
    raw = raw.strip()
    # Try parse as-is
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
    # Try first { ... } block
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


def parse_response(raw: str) -> dict:
    """Parse agent response as JSON. On failure, raise and save raw."""
    extracted = extract_json(raw)
    if extracted is None:
        raise ValueError("Could not extract valid JSON from response")
    return json.loads(extracted)


def write_artifacts(obj: dict, date_str: str) -> None:
    json_path = OUT_DIR / f"stock_quant_officer_eod_{date_str}.json"
    md_path = OUT_DIR / f"stock_quant_officer_eod_{date_str}.md"
    json_path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    log.info("Wrote %s", json_path)

    md_lines = [
        f"# Stock Quant Officer EOD — {date_str}",
        "",
        f"**Verdict:** {obj.get('verdict', '—')}",
        "",
        "## Summary",
        "",
        str(obj.get("summary") or "—"),
        "",
        "## P&L metrics",
        "",
        "```json",
        json.dumps(obj.get("pnl_metrics") or {}, indent=2),
        "```",
        "",
        "## Regime context",
        "",
        "```json",
        json.dumps(obj.get("regime_context") or {}, indent=2),
        "```",
        "",
        "## Sector context",
        "",
        "```json",
        json.dumps(obj.get("sector_context") or {}, indent=2),
        "```",
        "",
        "## Recommendations",
        "",
    ]
    for rec in obj.get("recommendations") or []:
        md_lines.append(f"- **[{rec.get('priority', '')}]** {rec.get('title', '')}")
        md_lines.append(f"  {rec.get('body', '')}")
        md_lines.append("")
    md_lines.append("## Citations")
    md_lines.append("")
    for c in obj.get("citations") or []:
        md_lines.append(f"- `{c.get('source', '')}`: {c.get('quote', '')}")
    md_lines.append("")
    md_lines.append("## Falsification criteria")
    md_lines.append("")
    for fc in obj.get("falsification_criteria") or []:
        md_lines.append(f"- **{fc.get('id', '')}** ({fc.get('data_source', '')}): {fc.get('description', '')}")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    log.info("Wrote %s", md_path)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    ensure_dirs()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    data, missing = load_bundle()
    if missing:
        log.warning("Missing bundle files: %s; continuing with partial analysis.", missing)

    contract = load_contract()
    bundle_summary = summarize_bundle(data, missing)
    prompt = build_prompt(contract, bundle_summary, date_str)

    log.info("Calling Clawdbot agent (TODO: model/provider Gemini)...")
    try:
        raw = run_clawdbot_prompt(prompt, dry_run=dry_run)
    except (FileNotFoundError, ValueError):
        return 1

    try:
        obj = parse_response(raw)
    except (ValueError, json.JSONDecodeError) as e:
        log.error("Parse failed: %s", e)
        raw_path = OUT_DIR / f"stock_quant_officer_eod_raw_{date_str}.txt"
        raw_path.write_text(raw, encoding="utf-8")
        log.error("Saved raw response to %s", raw_path)
        return 1

    write_artifacts(obj, date_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
