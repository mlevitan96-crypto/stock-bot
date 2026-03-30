#!/usr/bin/env python3
"""
Hardened Alpaca liquidation unblock: stop engine, cancel-all + settle, wave liquidation, stuck triage.

Run on Linux droplet from repo root (e.g. cd /root/stock-bot && python3 scripts/repair/...).

Evidence: reports/daily/<ET-date>/evidence/
  - ALPACA_LIQUIDATION_UNBLOCK_CONTEXT.md
  - ALPACA_CANCEL_ALL_ORDERS_EVIDENCE.md | ALPACA_CANCEL_ALL_ORDERS_BLOCKER.md
  - ALPACA_LIQUIDATION_WAVE_<N>.md
  - ALPACA_LIQUIDATION_STUCK_POSITIONS_BLOCKER.md (if needed)
  - ALPACA_LIQUIDATION_FLAT_PROOF.md (if flat)

Does NOT restart stock-bot (Phase E leaves service stopped).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _et_date() -> str:
    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _evidence_dir() -> Path:
    d = REPO / "reports" / "daily" / _et_date() / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run_shell(cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
    r = subprocess.run(
        ["bash", "-lc", cmd],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return r.stdout or "", r.stderr or "", r.returncode


def _make_api():
    import alpaca_trade_api as tradeapi  # type: ignore

    from main import Config

    return tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)


def _position_row(p: Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "symbol": getattr(p, "symbol", "") or "",
        "side": getattr(p, "side", "") or "",
        "qty": str(getattr(p, "qty", "") or ""),
        "market_value": getattr(p, "market_value", None),
        "avg_entry_price": getattr(p, "avg_entry_price", None),
    }
    qa = getattr(p, "qty_available", None)
    if qa is not None:
        row["qty_available"] = str(qa)
    raw = getattr(p, "_raw", None)
    if isinstance(raw, dict):
        for k in ("qty_available", "available_qty", "asset_id"):
            if k in raw and k not in row:
                row[k] = raw[k]
    return row


def _order_row(o: Any) -> Dict[str, Any]:
    return {
        "id": str(getattr(o, "id", "") or ""),
        "symbol": getattr(o, "symbol", "") or "",
        "side": getattr(o, "side", "") or "",
        "qty": str(getattr(o, "qty", "") or ""),
        "filled_qty": str(getattr(o, "filled_qty", "") or ""),
        "status": getattr(o, "status", "") or "",
        "type": getattr(o, "type", "") or "",
    }


def snapshot_positions(api: Any) -> List[Dict[str, Any]]:
    return [_position_row(p) for p in (api.list_positions() or [])]


def snapshot_open_orders(api: Any) -> List[Dict[str, Any]]:
    try:
        orders = api.list_orders(status="open") or []
    except Exception:
        orders = []
    return [_order_row(o) for o in orders]


def count_open_orders(api: Any) -> int:
    return len(snapshot_open_orders(api))


def close_position_safe(api: Any, sym: str) -> Tuple[bool, Optional[str]]:
    try:
        try:
            api.close_position(sym, cancel_orders=True)
        except TypeError:
            api.close_position(sym)
        return True, None
    except Exception as e:
        return False, str(e)


def cancel_all_and_poll_to_zero(
    api: Any, poll_interval_s: float = 5.0, max_wait_s: float = 120.0
) -> Tuple[bool, List[str]]:
    """Global cancel; poll until open orders == 0. Returns (ok, log lines)."""
    log: List[str] = []
    try:
        api.cancel_all_orders()
        log.append(f"cancel_all_orders() invoked at UTC {datetime.now(timezone.utc).isoformat()}")
    except Exception as e:
        log.append(f"cancel_all_orders() raised: {e!r}")
    deadline = time.monotonic() + max_wait_s
    while time.monotonic() < deadline:
        n = count_open_orders(api)
        log.append(f"{datetime.now(timezone.utc).isoformat()}Z open_orders={n}")
        if n == 0:
            return True, log
        time.sleep(poll_interval_s)
    n = count_open_orders(api)
    log.append(f"FINAL after timeout: open_orders={n}")
    return n == 0, log


def liquidation_evidence_has_insufficient_qty(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "insufficient qty" in text.lower() and "available" in text.lower()


def run_controlled_liquidation_wave(evidence_md: Path) -> Tuple[int, str, str]:
    """Subprocess: same script path as operator mission."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "repair" / "alpaca_controlled_liquidation.py"),
        "--execute",
        "--evidence-md",
        str(evidence_md),
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout or "", r.stderr or ""


def phase_a(
    assume_stopped: bool,
) -> Tuple[bool, str, Optional[str], str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns: ok, is_active_line, git_head, date_u, service_section, positions, orders
    """
    if sys.platform != "linux" and not assume_stopped:
        return (
            False,
            "non-linux",
            None,
            "",
            "Refusing Phase A: not Linux (systemctl unavailable). Run on droplet.",
            [],
            [],
        )

    if not assume_stopped:
        _run_shell("systemctl stop stock-bot", timeout=90)
        time.sleep(2)
        out, _, _ = _run_shell("systemctl is-active stock-bot 2>&1", timeout=15)
        line = out.strip()
        if line == "active":
            return False, line, None, "", "stock-bot still active after stop", [], []
    else:
        out, _, _ = _run_shell("systemctl is-active stock-bot 2>&1", timeout=15)
        line = out.strip()
        if line == "active":
            return False, line, None, "", "--assume-engine-stopped but stock-bot is active", [], []

    gh, _, _ = _run_shell("git rev-parse HEAD", timeout=15)
    du, _, _ = _run_shell("date -u", timeout=15)
    api = _make_api()
    pos = snapshot_positions(api)
    ord_ = snapshot_open_orders(api)
    return True, out.strip() if assume_stopped else line, gh.strip(), du.strip(), "", pos, ord_


def write_context_md(
    path: Path,
    is_active_line: str,
    git_head: str,
    date_u: str,
    positions: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    extra: str = "",
) -> None:
    lines = [
        "# ALPACA LIQUIDATION UNBLOCK — Phase A context\n\n",
        f"- UTC generated: `{datetime.now(timezone.utc).isoformat()}`\n",
        f"- `systemctl is-active stock-bot`: **`{is_active_line}`** (must not be `active`)\n",
        f"- `git rev-parse HEAD`: `{git_head}`\n",
        f"- `date -u`: `{date_u}`\n\n",
        "## Broker snapshot (pre cancel-all)\n\n",
        f"- Positions count: **{len(positions)}**\n",
        f"- Open orders count: **{len(orders)}**\n\n",
        "### Positions\n\n",
        "```json\n",
        json.dumps(positions, indent=2),
        "\n```\n\n",
        "### Open orders\n\n",
        "```json\n",
        json.dumps(orders, indent=2),
        "\n```\n\n",
    ]
    if extra:
        lines.append(extra + "\n")
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--assume-engine-stopped",
        action="store_true",
        help="Skip systemctl stop; verify inactive only. For operators who already stopped stock-bot.",
    )
    args = ap.parse_args()

    ev = _evidence_dir()
    ctx_path = ev / "ALPACA_LIQUIDATION_UNBLOCK_CONTEXT.md"

    ok_a, is_active_line, git_head, date_u, err_a, pos0, ord0 = phase_a(args.assume_engine_stopped)
    if not ok_a:
        api = None
        try:
            api = _make_api()
            pos0 = snapshot_positions(api)
            ord0 = snapshot_open_orders(api)
        except Exception:
            pass
        write_context_md(
            ctx_path,
            is_active_line,
            git_head or "unknown",
            date_u or "unknown",
            pos0,
            ord0,
            f"## FAILURE\n\n{err_a}\n",
        )
        print(json.dumps({"phase": "A", "ok": False, "error": err_a, "evidence": str(ctx_path)}, indent=2))
        sys.stdout.flush()
        return 1

    write_context_md(ctx_path, is_active_line, git_head, date_u, pos0, ord0)
    print(json.dumps({"phase": "A", "ok": True, "evidence": str(ctx_path)}, indent=2))
    sys.stdout.flush()

    api = _make_api()

    # Phase B
    b_path = ev / "ALPACA_CANCEL_ALL_ORDERS_EVIDENCE.md"
    blocker_b = ev / "ALPACA_CANCEL_ALL_ORDERS_BLOCKER.md"
    try:
        api.cancel_all_orders()
    except Exception as e:
        pass
    b_ok, b_log = cancel_all_and_poll_to_zero(api, 5.0, 120.0)
    if not b_ok:
        blocker_body = [
            "# ALPACA CANCEL ALL ORDERS — BLOCKER\n\n",
            "Open orders never reached 0 within 120s polling (5s interval).\n\n",
            "## Poll log\n\n",
            "```text\n",
            "\n".join(b_log),
            "\n```\n\n",
            "## Final open orders\n\n",
            "```json\n",
            json.dumps(snapshot_open_orders(api), indent=2),
            "\n```\n\n",
        ]
        blocker_b.write_text("".join(blocker_body), encoding="utf-8")
        print(json.dumps({"phase": "B", "ok": False, "evidence": str(blocker_b)}, indent=2))
        sys.stdout.flush()
        return 2

    time.sleep(20)
    pos_b = snapshot_positions(api)
    ord_b = snapshot_open_orders(api)
    b_path.write_text(
        "".join(
            [
                "# ALPACA CANCEL ALL ORDERS — Evidence\n\n",
                "## Poll log (until open_orders==0, then +20s settle)\n\n",
                "```text\n",
                "\n".join(b_log),
                "\n```\n\n",
                "## Post-cancel broker truth\n\n",
                f"- Open orders: **{len(ord_b)}** (expect 0)\n",
                f"- Positions: **{len(pos_b)}**\n\n",
                "### Positions\n\n",
                "```json\n",
                json.dumps(pos_b, indent=2),
                "\n```\n\n",
                "### Open orders\n\n",
                "```json\n",
                json.dumps(ord_b, indent=2),
                "\n```\n",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"phase": "B", "ok": True, "evidence": str(b_path)}, indent=2))
    sys.stdout.flush()

    # Phase C — up to 4 waves
    flat = False
    ts = _utc_ts()
    for wave in range(1, 5):
        pos_before = snapshot_positions(api)
        n_before = len(pos_before)
        liq_md = ev / f"ALPACA_FULL_LIQUIDATION_ORCH_WAVE{wave}_{ts}.md"
        rc, out, err = run_controlled_liquidation_wave(liq_md)
        pos_after = snapshot_positions(api)
        ord_after = snapshot_open_orders(api)
        sym_after = [p["symbol"] for p in pos_after if p.get("symbol")]

        err_lines = [ln for ln in (err or "").splitlines() if ln.strip()]
        out_lines = [ln for ln in (out or "").splitlines() if ln.strip()]
        w_lines = [
            f"# ALPACA LIQUIDATION WAVE {wave}\n\n",
            f"- Orchestrator UTC: `{datetime.now(timezone.utc).isoformat()}`\n",
            f"- Subprocess exit code: **{rc}**\n",
            f"- Controlled liquidation evidence: `{liq_md.name}`\n\n",
            "## Subprocess stdout (full)\n\n",
            "```text\n",
            (out or "").strip() or "(empty)",
            "\n```\n\n",
            "## Subprocess stderr (full)\n\n",
            "```text\n",
            (err or "").strip() or "(empty)",
            "\n```\n\n",
            f"- positions_before: **{n_before}**\n",
            f"- positions_after: **{len(pos_after)}**\n",
            f"- open_orders_after: **{len(ord_after)}**\n\n",
            "## Symbols still open after wave\n\n",
            "```json\n",
            json.dumps(sym_after, indent=2),
            "\n```\n\n",
        ]
        if err_lines:
            w_lines.append("## Error lines (stderr, verbatim)\n\n")
            w_lines.append("```text\n" + "\n".join(err_lines) + "\n```\n\n")

        # Parse liquidation JSON for close errors from evidence file
        if liq_md.is_file():
            m = re.search(r"## close_position results.*?```json\n(.*?)```", liq_md.read_text(encoding="utf-8", errors="replace"), re.DOTALL)
            if m:
                w_lines.append("## close_position results (excerpt from liquidation evidence)\n\n")
                w_lines.append("```json\n" + m.group(1).strip()[:8000] + "\n```\n\n")

        (ev / f"ALPACA_LIQUIDATION_WAVE_{wave}.md").write_text("".join(w_lines), encoding="utf-8")

        if len(pos_after) == 0:
            flat = True
            break

        need_recancel = liquidation_evidence_has_insufficient_qty(liq_md)
        if need_recancel:
            ok_r, r_log = cancel_all_and_poll_to_zero(api, 5.0, 120.0)
            append = ev / f"ALPACA_LIQUIDATION_WAVE_{wave}_RECANCEL.md"
            append.write_text(
                "## Post-wave recancel (insufficient qty / available 0 path)\n\n```text\n"
                + "\n".join(r_log)
                + "\n```\n",
                encoding="utf-8",
            )
            if not ok_r:
                blk = ev / "ALPACA_LIQUIDATION_WAVE_RECANCEL_BLOCKER.md"
                blk.write_text(
                    f"# Recancel blocker after wave {wave}\n\nCould not clear open orders after insufficient-qty path.\n\n```text\n"
                    + "\n".join(r_log)
                    + "\n```\n",
                    encoding="utf-8",
                )
                print(json.dumps({"phase": "C", "ok": False, "wave": wave, "evidence": str(blk)}, indent=2))
                sys.stdout.flush()
                return 2

            time.sleep(20)

        if wave < 4:
            time.sleep(30)

    if flat:
        pos_f = snapshot_positions(api)
        ord_f = snapshot_open_orders(api)
        proof = ev / "ALPACA_LIQUIDATION_FLAT_PROOF.md"
        proof.write_text(
            "".join(
                [
                    "# ALPACA LIQUIDATION — Flat proof (Phase E)\n\n",
                    f"- UTC: `{datetime.now(timezone.utc).isoformat()}`\n",
                    f"- Positions count: **{len(pos_f)}** (expect 0)\n",
                    f"- Open orders count: **{len(ord_f)}** (expect 0)\n\n",
                    "## Final positions\n\n",
                    "```json\n",
                    json.dumps(pos_f, indent=2),
                    "\n```\n\n",
                    "## Final open orders\n\n",
                    "```json\n",
                    json.dumps(ord_f, indent=2),
                    "\n```\n\n",
                    "## Service\n\n",
                    "**stock-bot remains STOPPED** — do not restart until Phase 3+ archive and post-cut smoke.\n",
                ]
            ),
            encoding="utf-8",
        )
        print(json.dumps({"phase": "E", "ok": True, "flat": True, "evidence": str(proof)}, indent=2))
        sys.stdout.flush()
        return 0

    # Phase D — stuck triage
    remaining = snapshot_positions(api)
    ord_chk = snapshot_open_orders(api)
    d_lines = [
        "# ALPACA LIQUIDATION — Stuck positions blocker (Phase D)\n\n",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`\n",
        "## Remaining positions (broker fields)\n\n",
    ]
    table_rows: List[Dict[str, Any]] = []
    for p in api.list_positions() or []:
        table_rows.append(_position_row(p))
    d_lines.append("```json\n" + json.dumps(table_rows, indent=2) + "\n```\n\n")
    d_lines.append(f"## Open orders count (must be 0): **{len(ord_chk)}**\n\n")
    d_lines.append("```json\n" + json.dumps(ord_chk, indent=2) + "\n```\n\n")
    d_lines.append("## Per-symbol close attempts (same SDK path as controlled liquidation)\n\n")

    for row in table_rows:
        sym = row.get("symbol") or ""
        if not sym:
            continue
        ok_c, er = close_position_safe(api, sym)
        d_lines.append(f"### `{sym}`\n\n")
        d_lines.append(f"- ok: **{ok_c}**\n")
        if er:
            d_lines.append(f"- error (verbatim): ```\n{er}\n```\n\n")
        else:
            d_lines.append("- error: none\n\n")

    time.sleep(2)
    pos_end = snapshot_positions(api)
    d_lines.append(f"## Positions after Phase D attempts: **{len(pos_end)}**\n\n")
    d_lines.append("```json\n" + json.dumps([p["symbol"] for p in pos_end], indent=2) + "\n```\n")
    d_path = ev / "ALPACA_LIQUIDATION_STUCK_POSITIONS_BLOCKER.md"
    d_path.write_text("".join(d_lines), encoding="utf-8")
    print(json.dumps({"phase": "D", "ok": False, "flat": False, "evidence": str(d_path)}, indent=2))
    sys.stdout.flush()
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
