#!/usr/bin/env python3
"""Write ALPACA_STRICT_ERA_ENTRY_FILTER_FIX proof artifacts (no wait). Droplet + local."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)


def _ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("/root/stock-bot"))
    args = ap.parse_args()
    root = args.root.resolve()
    ts = _ts_slug()

    audit = evaluate_completeness(
        root,
        open_ts_epoch=STRICT_EPOCH_START,
        audit=True,
    )

    ts_seen = int(audit.get("trades_seen") or 0)
    ts_inc = int(audit.get("trades_incomplete") or 0)
    if ts_seen == 0:
        verdict, cond = "BLOCKED", audit.get("learning_fail_closed_reason") or "NO_POST_DEPLOY_PROOF_YET"
    elif ts_inc > 0:
        verdict, cond = "BLOCKED", audit.get("learning_fail_closed_reason") or "incomplete_trade_chain"
    else:
        verdict, cond = "ARMED", "strict_entry_cohort_complete"

    inc_m = audit.get("chain_matrices_sample") or []
    comp_m = audit.get("chain_matrices_complete_sample") or []
    matrices = (comp_m[:3] if verdict == "ARMED" else (inc_m + comp_m)[:3])

    sum_path = root / "reports" / f"ALPACA_STRICT_ERA_ENTRY_FILTER_FIX_PROOF_SUMMARY_{ts}.md"
    full_path = root / "reports" / f"ALPACA_STRICT_ERA_ENTRY_FILTER_FIX_PROOF_{ts}.md"
    sum_path.parent.mkdir(parents=True, exist_ok=True)

    lcid_note = ""
    capped = audit.get("excluded_trade_ids_capped") or []
    if any("LCID" in str(x) for x in capped):
        lcid_note = "Sample excluded list includes an LCID trade_id (pre-era open).\n"

    vacuous_note = ""
    if ts_seen == 0 and int(audit.get("strict_cohort_excluded_preera_open_count") or 0) > 0:
        vacuous_note = (
            "\n**Note:** `trades_seen == 0` with positive `PREERA_OPEN` exclusions means every terminal close "
            "in the exit-time window came from a position **opened before** STRICT_EPOCH_START. "
            "Learning stays fail-closed until at least one close whose `trade_id` embeds an open time "
            "`>=` STRICT_EPOCH_START.\n\n"
        )

    summary = f"""# ALPACA strict era entry filter - proof summary ({ts})

## 1) STRICT_EPOCH_START and why

- **STRICT_EPOCH_START:** `{STRICT_EPOCH_START}` (2026-03-25T17:01:20Z UTC)
- **Why:** Forward-only strict learning boundary; cohort membership uses **position open** time from `trade_id`, not only exit time.

## 2) Cohort rule and code

- **Rule:** After exit-time floor (`open_ts_epoch`), include a trade only if open instant parsed from `open_<SYM>_<ISO8601>` is **>=** that floor. Pre-era opens that close post-era are excluded (`PREERA_OPEN`).
- **Implementation:** `telemetry/alpaca_strict_completeness_gate.py` (`evaluate_completeness`, `_open_epoch_from_trade_id`).

## 3) Exclusions

- **strict_cohort_excluded_preera_open_count:** {audit.get("strict_cohort_excluded_preera_open_count")}
- **strict_cohort_exclusion_reasons:** `{json.dumps(audit.get("strict_cohort_exclusion_reasons") or {})}`
- **excluded_trade_ids_capped (20):** `{json.dumps(capped)}`
{lcid_note}{vacuous_note}
## 4) Strict audit (post filter)

- **trades_seen:** {audit.get("trades_seen")}
- **trades_complete:** {audit.get("trades_complete")}
- **trades_incomplete:** {audit.get("trades_incomplete")}
- **reason_histogram:** `{json.dumps(audit.get("reason_histogram") or {})}`

## 5) Chain matrices (up to 3)

Vacuous cohort: matrices may be empty. When `trades_incomplete > 0`, incomplete samples populate; when `ARMED`, complete samples populate.

```json
{json.dumps(matrices, indent=2)}
```

## 6) CSA FINAL VERDICT

- **{verdict}**
- **Exact condition:** {cond}

"""

    full = f"""# ALPACA strict era entry filter - full proof ({ts})

## Audit JSON

```json
{json.dumps(audit, indent=2)}
```

"""

    sum_path.write_text(summary, encoding="utf-8")
    full_path.write_text(full, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "summary": str(sum_path), "full": str(full_path)}, indent=2))


if __name__ == "__main__":
    main()
