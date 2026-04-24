#!/usr/bin/env python3
"""
Assemble DAILY_MARKET_SESSION_REPORT.{md,json} from evidence/ (run after producers).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read_text(p: Path, limit: int = 200_000) -> str:
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")[:limit]


def _find_glob(evidence: Path, pat: str) -> list[Path]:
    return sorted(evidence.glob(pat), key=lambda x: x.stat().st_mtime, reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-date-et", required=True, help="YYYY-MM-DD")
    ap.add_argument("--repo", type=Path, default=REPO)
    args = ap.parse_args()
    sys.path.insert(0, str(args.repo))
    from src.report_output.paths import canonical_json_path, canonical_md_path, evidence_dir

    repo = args.repo.resolve()
    evd = evidence_dir(repo, args.session_date_et)
    if not evd.is_dir():
        print(json.dumps({"error": "evidence_dir_missing", "path": str(evd)}))
        return 1

    meta_path = evd / "EVIDENCE_RUN_META.json"
    ts = ""
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ts = str(meta.get("ts") or "")

    scope_files = _find_glob(evd, "ALPACA_PNL_MARKET_SESSION_SCOPE_*.md")
    close_files = _find_glob(evd, "ALPACA_PNL_REVIEW_CLOSEOUT_*.md")
    recon_csvs = _find_glob(evd, "ALPACA_PNL_REVIEW_RECONCILIATION_*.csv")
    truth_jsons = _find_glob(evd, "ALPACA_MARKET_SESSION_TRUTH_*.json")

    scope_txt = _read_text(scope_files[0]) if scope_files else ""
    close_txt = _read_text(close_files[0]) if close_files else ""
    truth = json.loads(truth_jsons[0].read_text(encoding="utf-8")) if truth_jsons else {}

    fg = truth.get("final_gate") or {}
    trades_seen = fg.get("trades_seen")
    trades_complete = fg.get("trades_complete")
    cids = fg.get("complete_trade_ids") or []

    recon_md_table = ""
    net_pnl = 0.0
    if recon_csvs:
        rows = []
        with recon_csvs[0].open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                rows.append(row)
                try:
                    net_pnl += float(row.get("net_pnl") or 0)
                except (TypeError, ValueError):
                    pass
        if rows:
            headers = list(rows[0].keys())
            recon_md_table = "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n"
            for row in rows[:50]:
                recon_md_table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

    prom = "NO"
    if re.search(r"CSA_VERDICT:\s*PNL_REVIEW_COMPLETE", close_txt):
        prom = "YES"
    elif re.search(r"CSA_VERDICT:\s*STILL_BLOCKED", close_txt):
        prom = "NO"

    bundle_js = _find_glob(evd, "ALPACA_PNL_REVIEW_TRUTH_BUNDLE_*.json")
    blocked_n = None
    if bundle_js:
        try:
            man = json.loads(bundle_js[0].read_text(encoding="utf-8"))
            blocked_n = (man.get("row_counts") or {}).get("trade_intent_non_entered_lines")
        except Exception:
            pass

    signal_files = _find_glob(evd, "ALPACA_PNL_SIGNAL_ATTRIBUTION_*.md")
    signal_txt = _read_text(signal_files[0], 12_000) if signal_files else ""

    learn_md = evd / "ALPACA_LEARNING_STATUS_SUMMARY.md"
    learn_json = evd / "ALPACA_LEARNING_STATUS_SUMMARY.json"
    learn_txt = _read_text(learn_md, 6_000) if learn_md.is_file() else ""
    learn_verdict = ""
    if learn_json.is_file():
        try:
            lj = json.loads(learn_json.read_text(encoding="utf-8"))
            learn_verdict = str(lj.get("verdict") or "")
        except Exception:
            pass

    lw_verdict_files = _find_glob(evd, "ALPACA_LAST_WINDOW_LEARNING_VERDICT_*.md")
    lw_txt = _read_text(lw_verdict_files[0], 8_000) if lw_verdict_files else ""

    def _csa_excerpt(*chunks: str) -> str:
        parts: list[str] = []
        for ch in chunks:
            if not ch.strip():
                continue
            lines = ch.splitlines()
            for i, line in enumerate(lines):
                if "CSA_VERDICT" in line.upper():
                    lo = max(0, i - 2)
                    hi = min(len(lines), i + 5)
                    parts.append("\n".join(lines[lo:hi]))
        seen: set[str] = set()
        out: list[str] = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return "\n---\n".join(out)[:8000]

    csa_block = _csa_excerpt(close_txt, lw_txt, learn_txt)

    md_lines = [
        f"# Daily market session report — {args.session_date_et}",
        "",
        "## Market session (ET)",
        "",
        "```",
        scope_txt[:8000] or "(no scope evidence file)",
        "```",
        "",
        "## Trades",
        "",
        f"- **Executed (strict complete cohort):** {trades_complete} (seen {trades_seen})",
        f"- **Cohort trade_ids (count {len(cids)}):** see evidence `ALPACA_MARKET_SESSION_COMPLETE_TRADE_IDS_*.json`",
        f"- **Blocked intents (log-derived hint):** {blocked_n if blocked_n is not None else 'n/a'}",
        "",
        "## Net PnL (cohort, reconciliation CSV)",
        "",
        f"**Sum net_pnl:** {net_pnl}",
        "",
        recon_md_table or "(no reconciliation rows)",
        "",
        "## Learning status",
        "",
        f"**verdict (from evidence JSON):** `{learn_verdict or 'n/a'}`",
        "",
        "```",
        learn_txt[:5000] or "(no ALPACA_LEARNING_STATUS_SUMMARY.md in evidence)",
        "```",
        "",
        "## Signal attribution (excerpt from evidence)",
        "",
        "```",
        signal_txt[:8000] or "(no ALPACA_PNL_SIGNAL_ATTRIBUTION_*.md in evidence)",
        "```",
        "",
        "## CSA verdict (from evidence)",
        "",
        "```",
        csa_block or "(no CSA_VERDICT line found in closeout / last-window / learning evidence)",
        "```",
        "",
        "## Promotion decision",
        "",
        f"**{prom}** (from PnL closeout verdict line where applicable)",
        "",
        "```",
        close_txt[:6000] or "(no closeout evidence)",
        "```",
        "",
        "## Evidence index (links — open files, do not paste raw JSON)",
        "",
        f"- Directory: `reports/daily/{args.session_date_et}/evidence/`",
        f"- Run tag: `{ts}`",
        "",
    ]
    md_out = canonical_md_path(repo, args.session_date_et)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    payload = {
        "session_date_et": args.session_date_et,
        "ts": ts,
        "market_session": {"scope_evidence": str(scope_files[0]) if scope_files else None},
        "trades": {
            "trades_seen": trades_seen,
            "trades_complete": trades_complete,
            "complete_trade_ids_count": len(cids),
            "blocked_intent_lines_hint": blocked_n,
        },
        "pnl": {"net_pnl_sum": net_pnl, "reconciliation_csv": str(recon_csvs[0]) if recon_csvs else None},
        "learning": {
            "verdict": learn_verdict or None,
            "summary_md": str(learn_md) if learn_md.is_file() else None,
            "summary_json": str(learn_json) if learn_json.is_file() else None,
        },
        "signal_attribution_md": str(signal_files[0]) if signal_files else None,
        "csa_verdict_excerpt": csa_block[:4000] if csa_block else None,
        "promotion_decision": prom,
        "closeout_evidence": str(close_files[0]) if close_files else None,
        "last_window_verdict_md": str(lw_verdict_files[0]) if lw_verdict_files else None,
        "evidence_dir": str(evd),
    }
    json_out = canonical_json_path(repo, args.session_date_et)
    json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote_md": str(md_out), "wrote_json": str(json_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
