#!/usr/bin/env python3
import argparse, json, os, sys
from datetime import datetime, timezone

REQUIRED_TOP_LEVEL_KEYS = ["date", "executed", "blocked", "counter_intel"]

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.ledger):
        print(f"Ledger missing: {args.ledger}", file=sys.stderr)
        sys.exit(2)

    ledger = load_json(args.ledger)

    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in ledger]
    executed = ledger.get("executed", [])
    blocked = ledger.get("blocked", [])
    counter_intel = ledger.get("counter_intel", [])

    # Minimal integrity checks (best-effort, no ts=0 duplicate enforcement here)
    issues = []
    if missing:
        issues.append({"severity": "FAIL", "code": "LEDGER_SCHEMA_MISSING_KEYS", "detail": missing})
    if ledger.get("date") != args.date:
        issues.append({"severity": "WARN", "code": "LEDGER_DATE_MISMATCH", "detail": {"ledger_date": ledger.get("date"), "arg_date": args.date}})
    if not isinstance(executed, list) or not isinstance(blocked, list) or not isinstance(counter_intel, list):
        issues.append({"severity": "FAIL", "code": "LEDGER_SCHEMA_BAD_TYPES"})
    if isinstance(executed, list) and len(executed) == 0:
        issues.append({"severity": "WARN", "code": "NO_EXECUTED_TRADES"})
    if isinstance(blocked, list) and len(blocked) == 0:
        issues.append({"severity": "WARN", "code": "NO_BLOCKED_EVENTS"})

    # Field presence spot-check (non-fatal; we're certifying "usable", not "perfect")
    def spot_check(rows, name, fields):
        if not isinstance(rows, list) or len(rows) == 0:
            return
        sample = rows[:50]
        for f in fields:
            if any((f not in r) for r in sample if isinstance(r, dict)):
                issues.append({"severity": "WARN", "code": f"MISSING_FIELD_{name.upper()}_{f.upper()}"})
                break

    spot_check(executed, "executed", ["symbol"])
    spot_check(blocked, "blocked", ["symbol"])
    # counter_intel may be empty; only check if present
    if isinstance(counter_intel, list) and len(counter_intel) > 0:
        spot_check(counter_intel, "counter_intel", ["symbol"])

    # Verdict: FAIL if any FAIL issues, else PASS (with warnings allowed)
    verdict = "FAIL" if any(i["severity"] == "FAIL" for i in issues) else "PASS"
    out = {
        "date": args.date,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "verdict": verdict,
        "counts": {
            "executed": len(executed) if isinstance(executed, list) else None,
            "blocked": len(blocked) if isinstance(blocked, list) else None,
            "counter_intel": len(counter_intel) if isinstance(counter_intel, list) else None,
        },
        "issues": issues,
        "notes": [
            "SRE stub: certifies ledger usability and basic schema; does not enforce ts uniqueness.",
            "Warnings do not block downstream phases; FAIL blocks promotion and stops pipeline."
        ],
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    if verdict == "FAIL":
        print("SRE_DAY_HEALTH: FAIL", file=sys.stderr)
        sys.exit(3)

    print("SRE_DAY_HEALTH: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
