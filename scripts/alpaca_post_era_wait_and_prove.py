#!/usr/bin/env python3
"""
Wait for first post-era terminal close + unified exit row, then run strict chain audit and write proof artifacts.
Droplet: venv/bin/python3 scripts/alpaca_post_era_wait_and_prove.py --root /root/stock-bot
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STRICT_EPOCH_START = 1774458080.0  # 2026-03-25T17:01:20Z
STRICT_EPOCH_ISO = "2026-03-25T17:01:20+00:00"
SLEEP_SEC = 60
MAX_ITERATIONS = 180  # 180 minutes


def _parse_iso_ts(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _scan_exit_attribution_post_era(logs: Path, epoch: float) -> Tuple[int, List[dict]]:
    path = logs / "exit_attribution.jsonl"
    n = 0
    examples: List[dict] = []
    if not path.is_file():
        return 0, examples
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_iso_ts(rec.get("timestamp"))
            if ts is None or ts < epoch:
                continue
            ep = rec.get("exit_price")
            try:
                ok_price = ep is not None and float(ep) > 0
            except (TypeError, ValueError):
                ok_price = False
            if not ok_price:
                continue
            n += 1
            if len(examples) < 5:
                examples.append(
                    {
                        "symbol": str(rec.get("symbol") or "").upper(),
                        "timestamp": rec.get("timestamp"),
                        "trade_id": rec.get("trade_id"),
                    }
                )
    return n, examples


def _scan_orders_close_post_era(logs: Path, epoch: float) -> Tuple[int, List[dict]]:
    path = logs / "orders.jsonl"
    n = 0
    examples: List[dict] = []
    if not path.is_file():
        return 0, examples
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            act = (rec.get("action") or "").lower()
            if act != "close_position":
                continue
            ts = _parse_iso_ts(rec.get("timestamp")) or _parse_iso_ts(rec.get("ts"))
            if ts is None or ts < epoch:
                continue
            n += 1
            if len(examples) < 5:
                examples.append(
                    {
                        "symbol": str(rec.get("symbol") or "").upper(),
                        "timestamp": rec.get("timestamp") or rec.get("ts"),
                    }
                )
    return n, examples


def _scan_unified_exit_post_era(logs: Path, epoch: float) -> Tuple[int, List[dict]]:
    path = logs / "alpaca_unified_events.jsonl"
    n = 0
    examples: List[dict] = []
    if not path.is_file():
        return 0, examples
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = rec.get("event_type") or rec.get("type")
            if et != "alpaca_exit_attribution":
                continue
            ts = _parse_iso_ts(rec.get("timestamp"))
            if ts is None or ts < epoch:
                continue
            n += 1
            if len(examples) < 5:
                examples.append(
                    {
                        "symbol": str(rec.get("symbol") or "").upper(),
                        "timestamp": rec.get("timestamp"),
                        "trade_id": rec.get("trade_id"),
                    }
                )
    return n, examples


def wait_for_post_era_evidence(logs: Path, epoch: float) -> Tuple[bool, Dict[str, Any]]:
    last_snap: Dict[str, Any] = {}
    for iteration in range(MAX_ITERATIONS):
        ex_n, ex_ex = _scan_exit_attribution_post_era(logs, epoch)
        ord_n, ord_ex = _scan_orders_close_post_era(logs, epoch)
        uni_n, uni_ex = _scan_unified_exit_post_era(logs, epoch)
        cond_terminal = ex_n > 0 or ord_n > 0
        cond_unified = uni_n > 0
        last_snap = {
            "iteration": iteration + 1,
            "exit_attribution_post_era_count": ex_n,
            "orders_close_position_post_era_count": ord_n,
            "unified_alpaca_exit_post_era_count": uni_n,
            "examples_exit_attribution": ex_ex[:3],
            "examples_orders_close": ord_ex[:3],
            "examples_unified_exit": uni_ex[:3],
        }
        if cond_terminal and cond_unified:
            return True, last_snap
        if iteration < MAX_ITERATIONS - 1:
            time.sleep(SLEEP_SEC)
    return False, last_snap


def _ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Post-era wait + strict completeness proof")
    ap.add_argument("--root", type=Path, default=Path("/root/stock-bot"))
    ap.add_argument(
        "--skip-wait",
        action="store_true",
        help="Do not sleep/retry; single evidence check then audit (for smoke test)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    ts = _ts_slug()

    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness  # noqa: E402

    if args.skip_wait:
        ex_n, ex_ex = _scan_exit_attribution_post_era(logs, STRICT_EPOCH_START)
        ord_n, ord_ex = _scan_orders_close_post_era(logs, STRICT_EPOCH_START)
        uni_n, uni_ex = _scan_unified_exit_post_era(logs, STRICT_EPOCH_START)
        ok = (ex_n > 0 or ord_n > 0) and uni_n > 0
        snap = {
            "iteration": 0,
            "exit_attribution_post_era_count": ex_n,
            "orders_close_position_post_era_count": ord_n,
            "unified_alpaca_exit_post_era_count": uni_n,
            "examples_exit_attribution": ex_ex[:3],
            "examples_orders_close": ord_ex[:3],
            "examples_unified_exit": uni_ex[:3],
        }
    else:
        ok, snap = wait_for_post_era_evidence(logs, STRICT_EPOCH_START)

    audit = evaluate_completeness(root, open_ts_epoch=STRICT_EPOCH_START, audit=True)

    # Phase 3 verdict (explicit)
    ts_seen = int(audit.get("trades_seen") or 0)
    ts_inc = int(audit.get("trades_incomplete") or 0)
    if ts_seen == 0:
        csa_verdict = "BLOCKED"
        csa_condition = audit.get("learning_fail_closed_reason") or "NO_POST_DEPLOY_PROOF_YET"
    elif ts_inc > 0:
        csa_verdict = "BLOCKED"
        csa_condition = audit.get("learning_fail_closed_reason") or "incomplete_trade_chain"
    else:
        csa_verdict = "ARMED"
        csa_condition = "strict_completeness_passed_for_post_era_cohort"

    if not ok:
        wait_status = "WAITING_FOR_POST_ERA_TERMINAL_CLOSE"
    else:
        wait_status = "POST_ERA_EVIDENCE_SATISFIED"

    # Matrices: prefer complete sample when ARMED, else incomplete sample (pad to 3 if needed)
    inc_m = audit.get("chain_matrices_sample") or []
    comp_m = audit.get("chain_matrices_complete_sample") or []
    if csa_verdict == "ARMED":
        matrices_for_doc = comp_m[:3]
    else:
        matrices_for_doc = (inc_m + comp_m)[:3]

    summary_body = f"""# ALPACA strict completeness arming - proof summary ({ts})

## 1) STRICT_EPOCH_START and why

- **STRICT_EPOCH_START:** `{STRICT_EPOCH_START}` ({STRICT_EPOCH_ISO})
- **Why:** Forward-only strict learning cohort boundary from `stock-bot.service` restart / chain-validation era (2026-03-25T17:01:20Z UTC).

## 2) Wait outcome and first post-era evidence

- **WAIT_STATUS:** `{wait_status}`
- **Evidence snapshot (last iteration):** `{json.dumps(snap, indent=0)}`

"""

    if ok and snap.get("examples_exit_attribution"):
        summary_body += "\n**First post-era terminal close (exit_attribution):** " + json.dumps(
            snap["examples_exit_attribution"][0], indent=2
        )
    if ok and snap.get("examples_unified_exit"):
        summary_body += "\n\n**First post-era unified exit:** " + json.dumps(
            snap["examples_unified_exit"][0], indent=2
        )

    summary_body += f"""

## 3) Strict audit (`open_ts_epoch={STRICT_EPOCH_START}`)

- **trades_seen:** {audit.get("trades_seen")}
- **trades_complete:** {audit.get("trades_complete")}
- **trades_incomplete:** {audit.get("trades_incomplete")}
- **reason_histogram:** `{json.dumps(audit.get("reason_histogram") or {})}`

## 4) Chain matrices (up to 3)

```json
{json.dumps(matrices_for_doc, indent=2)}
```

## 5) CSA FINAL VERDICT

- **{csa_verdict}**
- **Exact condition:** {csa_condition}

"""

    if not ok:
        summary_body += """
## Timeout / wait path

- **NEXT_TRIGGER:** Re-run after first terminal close (exit_attribution or orders `close_position`) **and** unified `alpaca_exit_attribution` with timestamp ≥ STRICT_EPOCH_START.
"""

    full_body = f"""# ALPACA strict completeness arming - full proof ({ts})

## Constants

- STRICT_EPOCH_START = `{STRICT_EPOCH_START}` (UTC epoch seconds)
- STRICT_EPOCH_ISO = `{STRICT_EPOCH_ISO}`

## Phase 1 — wait condition

- **ok:** `{ok}`
- **max_wait_minutes:** {MAX_ITERATIONS}
- **sleep_seconds:** {SLEEP_SEC}
- **evidence_snapshot:** 

```json
{json.dumps(snap, indent=2)}
```

## Phase 2 — audit JSON

```json
{json.dumps(audit, indent=2)}
```

## Phase 3 — CSA verdict

- **{csa_verdict}**
- **condition:** {csa_condition}

"""

    rep = root / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    sum_path = rep / f"ALPACA_STRICT_COMPLETENESS_ARMING_PROOF_SUMMARY_{ts}.md"
    full_path = rep / f"ALPACA_STRICT_COMPLETENESS_ARMING_PROOF_{ts}.md"
    sum_path.write_text(summary_body, encoding="utf-8")
    full_path.write_text(full_body, encoding="utf-8")
    print(json.dumps({"wait_ok": ok, "csa_verdict": csa_verdict, "summary": str(sum_path), "full": str(full_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
