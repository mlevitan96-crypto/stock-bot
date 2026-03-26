#!/usr/bin/env python3
"""Emit forward-cert markdown + JSON extracts from ALPACA_FORWARD_DROPLET_RAW bundle."""
from __future__ import annotations

import json
from json import JSONDecoder
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    raw_path = REPO / "reports" / "ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json"
    d = json.loads(raw_path.read_text(encoding="utf-8"))
    ts = "20260326_1707Z"
    deploy_epoch = d["DEPLOY_TS_UTC_EPOCH"]
    parity = d["forward_parity_json"]
    tail = d["steps"]["strict_gate_forward"]["stdout_tail"]
    dec = JSONDecoder()
    gi = tail.find("{")
    strict = dec.raw_decode(tail, gi)[0] if gi >= 0 else {}

    (REPO / f"reports/ALPACA_STRICT_GATE_FORWARD_{ts}.json").write_text(
        json.dumps(strict, indent=2), encoding="utf-8"
    )
    (REPO / f"reports/ALPACA_FORWARD_PARITY_COUNTS_{ts}.json").write_text(
        json.dumps(parity, indent=2), encoding="utf-8"
    )
    (REPO / f"reports/ALPACA_FORWARD_TRACE_{ts}.json").write_text(
        json.dumps({"note": "forward_cohort_vacuous", "traces": []}, indent=2),
        encoding="utf-8",
    )

    def write(rel: str, text: str) -> None:
        p = REPO / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    dg_out = d["steps"]["deploy_git"]["stdout"]
    dg_err = d["steps"]["deploy_git"]["stderr"]
    status = d["steps"]["systemctl_status"]
    rs_sb = d["steps"]["restart_stock-bot.service"]["exit_code"]
    rs_uw = d["steps"]["restart_uw-flow-daemon.service"]["exit_code"]
    rs_dash = d["steps"]["restart_stock-bot-dashboard.service"]["exit_code"]
    gate_exit = d["steps"]["strict_gate_forward"]["exit_code"]

    write(
        f"reports/audit/ALPACA_FORWARD_CERT_CONTRACT_{ts}.md",
        f"""# ALPACA forward certification contract (STOP-GATE 0)

**CSA verdict:** APPROVED (as stated below). No revision to A/B/C at execution time.

## A) Forward cohort definition

- **Primary:** Trades with position open time `entry_ts >= DEPLOY_TS_UTC` (epoch **{deploy_epoch}**, UTC **2026-03-26T17:07:29Z** from `date -u +%s` on droplet at deploy).
- **Alternate marker:** First trade after `systemctl restart stock-bot` (same deploy window; services restarted immediately after `git reset --hard origin/main`).

## B) Perfect chain (forward cohort only)

1. `trade_intent(entered)` carries **canonical_trade_id** and **trade_key**.
2. Orders/fills reference the **same** canonical_trade_id / trade_key.
3. `exit_attribution` rows include canonical_trade_id / trade_key.
4. Unified **terminal close** exists for every economic close.
5. Strict completeness gate reports **100% complete** for the forward segment (`forward_trades_incomplete == 0`, cohort not vacuous).

## C) Legacy cohort

- May remain incomplete.
- Labeled **LEGACY_DEBT_QUARANTINED**; not used for forward causal certification.

---
*Artifact: machine bundle `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` + this file.*
""",
    )

    write(
        f"reports/audit/ALPACA_DEPLOY_{ts}.md",
        f"""# ALPACA deploy record ({ts})

## Droplet path

`/root/stock-bot`

## Git

```
{dg_out}
```

**stderr (fetch):**

```
{dg_err[:2000]}
```

## DEPLOY_TS_UTC epoch

`{deploy_epoch}`

## Service restarts (per unit)

- `stock-bot.service` — exit {rs_sb}
- `uw-flow-daemon.service` — exit {rs_uw}
- `stock-bot-dashboard.service` — exit {rs_dash}

Full command transcripts are in `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` under `steps`.
""",
    )

    st = status[:12000] if isinstance(status, str) else str(status)
    write(
        f"reports/audit/ALPACA_SERVICE_HEALTH_{ts}.md",
        f"""# ALPACA service health ({ts})

## systemctl status (no-pager, truncated)

```
{st}
```

## journalctl last 200 lines (per unit)

Captured in full in `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` → `steps.journals_last_200`.

Units:

- `stock-bot.service`
- `uw-flow-daemon.service`
- `stock-bot-dashboard.service`
""",
    )

    write(
        f"reports/audit/ALPACA_FORWARD_COHORT_MARKER_{ts}.md",
        f"""# ALPACA forward cohort marker ({ts})

## Deploy / restart marker

- **DEPLOY_TS_UTC epoch:** `{deploy_epoch}` (2026-03-26T17:07:29Z)
- **Git HEAD after reset:** `0b75150b46850618647f8e41f3e6c68226c1ce8a`
- Services restarted immediately after deploy (see `ALPACA_DEPLOY_{ts}.md`).

## Phase 2 observation (this run)

Certification script did **not** wait 60 minutes or until ≥10 entered + ≥10 economic closes.

**Measured immediately post-deploy:**

- Forward economic closes (`exit_attribution.jsonl`, exit_ts ≥ deploy): **{parity["forward_economic_closes"]}**
- Forward entered intents with canonical ids (parity audit): **{parity["forward_trade_intents_with_ct_and_tk"]}**

**forward_cohort_vacuous:** `{parity["forward_cohort_vacuous"]}`

Therefore the post-deploy cohort is **not yet eligible** for Phase 3–4 “perfect chain” certification under the stated minimums.
""",
    )

    write(
        f"reports/audit/ALPACA_FORWARD_TRACE_{ts}.md",
        f"""# ALPACA forward end-to-end trace ({ts})

## Result

**No traces produced.** `forward_parity_audit.py` exited **2** (`forward_cohort_vacuous`: no forward economic closes).

Phase 3 requires 15 `trade_id` samples; **n = 0**.

## JSON

Empty trace list: `reports/ALPACA_FORWARD_TRACE_{ts}.json`
""",
    )

    parity_note = (
        "PASS"
        if parity["parity_exact"]
        and parity["forward_economic_closes"] == parity["forward_unified_terminal_closes"]
        else "N/A vacuous"
    )
    write(
        f"reports/audit/ALPACA_FORWARD_PARITY_COUNTS_{ts}.md",
        f"""# ALPACA forward parity counts ({ts})

## Forward cohort only (exit_ts / unified ts ≥ DEPLOY_TS)

| Metric | Count |
|--------|------:|
| Economic closes (`exit_attribution.jsonl`) | {parity["forward_economic_closes"]} |
| Unified terminal closes (`alpaca_unified_events.jsonl`) | {parity["forward_unified_terminal_closes"]} |
| Parity (0 tolerance) | **{parity_note}** |
| `alpaca_emit_failures.jsonl` new lines since deploy | {parity["alpaca_emit_failures_since_deploy"]} |

## Note

With **zero** forward closes, parity is **vacuously** equal; this does **not** satisfy the mission’s requirement to prove a **non-empty** forward cohort is perfect.

Machine JSON: `reports/ALPACA_FORWARD_PARITY_COUNTS_{ts}.json`
""",
    )

    write(
        f"reports/audit/ALPACA_STRICT_GATE_FORWARD_{ts}.md",
        f"""# ALPACA strict gate — forward segmentation ({ts})

## Command (droplet)

`PYTHONPATH=/root/stock-bot venv/bin/python telemetry/alpaca_strict_completeness_gate.py --root . --audit --open-ts-epoch 1774458080 --forward-since-epoch {deploy_epoch}`

## Exit code

`{gate_exit}` (non-zero when `LEARNING_STATUS` != ARMED or forward rules fail)

## Summary (from parsed JSON)

| Segment | seen | complete | incomplete |
|---------|-----:|---------:|-----------:|
| Legacy | {strict.get("legacy_trades_seen")} | {strict.get("legacy_trades_complete")} | {strict.get("legacy_trades_incomplete")} |
| Forward | {strict.get("forward_trades_seen")} | {strict.get("forward_trades_complete")} | {strict.get("forward_trades_incomplete")} |

- **FORWARD_COHORT_VACUOUS:** {strict.get("FORWARD_COHORT_VACUOUS")}
- **FORWARD_CHAIN_PERFECT:** {strict.get("FORWARD_CHAIN_PERFECT")}
- **LEARNING_STATUS:** {strict.get("LEARNING_STATUS")}

Full JSON: `reports/ALPACA_STRICT_GATE_FORWARD_{ts}.json`

## Tooling note

An earlier bundle could mark `strict_gate_json_parse_error` if a parser used `rfind("{{")` (nested structures). `run_forward_cert_on_droplet.py` now uses `find("{{")` + `JSONDecoder.raw_decode`.
""",
    )

    write(
        f"reports/audit/ALPACA_FORWARD_ADVERSARIAL_REVIEW_{ts}.md",
        f"""# ALPACA forward certification — adversarial review ({ts})

## Objective

Attempt to disprove **FORWARD_CERTIFIED** using droplet evidence.

## Findings

1. **Cohort boundary:** DEPLOY epoch `{deploy_epoch}` is consistent with `date -u +%s` before `git fetch/reset`. Forward filters use this floor; legacy opens are excluded by design.

2. **Vacuous forward cohort:** `forward_economic_closes=0` immediately after deploy. **Cannot** validate canonical_trade_id/trade_key drift across legs, partial fills, or unified terminal edge cases on **live** forward trades — there are none in the window.

3. **Parity:** `economic_closes == unified_terminal_closes == 0` is **true** but **misleading** for certification: the mission requires proving parity on **real** closes, not an empty set.

4. **emit_failures:** `alpaca_emit_failures_since_deploy=0` — no new failure lines in the short post-deploy window.

5. **Phase 2 gate:** Mission requires ≥10 entered + ≥10 economic closes **or** 60 minutes. **Not met.** Any “certified” claim would be invalid.

## Conclusion (adversarial)

Forward certification is **not defensible** for this run: the forward cohort is empty with respect to economic closes, and minimum observation time / trade counts were not satisfied.
""",
    )

    write(
        f"reports/audit/ALPACA_FORWARD_CERT_CLOSEOUT_{ts}.md",
        f"""# ALPACA forward certification — CSA closeout ({ts})

## Binary verdict

### **STILL_BLOCKED**

## Blockers (exact)

1. **Forward cohort vacuous:** `forward_economic_closes=0`, `forward_trade_intents_with_ct_and_tk=0` (post-DEPLOY window). Phase 2 minimums (**≥10 entered**, **≥10 economic closes**, or **60 minutes** observation) **not** satisfied.
2. **FORWARD_CHAIN_PERFECT:** `false` (`FORWARD_COHORT_VACUOUS: true` in strict gate JSON).
3. **Phase 3:** Cannot sample 15 `trade_id` traces; `trace_sample_size=0`.
4. **forward_incomplete:** Not meaningful proof when `forward_trades_seen=0`; certification requires a **non-vacuous** forward cohort per contract §B.

## Legacy

**LEGACY_DEBT_QUARANTINED** — historical incompletes are out of scope for forward proof; no claim is made that history is repaired.

## Evidence index

| Artifact |
|----------|
| `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` |
| `reports/audit/ALPACA_FORWARD_CERT_CONTRACT_{ts}.md` |
| `reports/audit/ALPACA_DEPLOY_{ts}.md` |
| `reports/audit/ALPACA_SERVICE_HEALTH_{ts}.md` |
| `reports/audit/ALPACA_FORWARD_COHORT_MARKER_{ts}.md` |
| `reports/audit/ALPACA_FORWARD_TRACE_{ts}.md` |
| `reports/ALPACA_FORWARD_TRACE_{ts}.json` |
| `reports/audit/ALPACA_FORWARD_PARITY_COUNTS_{ts}.md` |
| `reports/ALPACA_FORWARD_PARITY_COUNTS_{ts}.json` |
| `reports/audit/ALPACA_STRICT_GATE_FORWARD_{ts}.md` |
| `reports/ALPACA_STRICT_GATE_FORWARD_{ts}.json` |
| `reports/audit/ALPACA_FORWARD_ADVERSARIAL_REVIEW_{ts}.md` |
""",
    )

    print("wrote artifacts", ts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
