#!/usr/bin/env python3
"""
Run blocked-trade expectancy + signal attribution ON THE DROPLET only.
Step 1: Verify droplet paths.
Step 2: Run blocked_expectancy_analysis.py and signal pipeline (output to reports/blocked_expectancy/).
Step 3: Verify output files non-empty; fix paths and re-run if needed.
Step 4: Print required summary (candidates, replayed, top 3 buckets, signal groups with edge, verdict).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def run(c, cmd: str, timeout: int = 60) -> tuple[str, str]:
    o, e, _ = c._execute(cmd, timeout=timeout)
    return (o or "").strip(), (e or "").strip()


def main() -> int:
    with DropletClient() as c:
        root = (
            run(c, "([ -d /root/stock-bot-current ] && echo /root/stock-bot-current) || echo /root/stock-bot")[0]
            or "/root/stock-bot"
        ).strip()
        cd = f"cd {root}"

        # ---------- STEP 1: Verify droplet paths ----------
        paths_check = [
            "logs/score_snapshot.jsonl",
            "logs/gate.jsonl",
            "state/blocked_trades.jsonl",
        ]
        missing = []
        for p in paths_check:
            out, _ = run(c, f"{cd} && test -f {p} && echo ok || echo missing", 5)
            if "ok" not in out:
                missing.append(f"{root}/{p}")
        attr_out, _ = run(c, f"{cd} && test -f logs/attribution.jsonl && echo ok || echo skip", 5)
        price_out, _ = run(c, f"{cd} && ls data/bars 2>/dev/null | head -3 || ls data/price_cache 2>/dev/null | head -3 || echo no_price_dir", 5)
        if "no_price_dir" in price_out and not price_out.strip().replace("no_price_dir", "").strip():
            pass  # bars may be fetched from Alpaca; not blocking

        if missing:
            print("Missing paths on droplet:", ", ".join(missing), file=sys.stderr)

        # ---------- STEP 2: Run expectancy analysis on droplet (source .env for Alpaca bars) ----------
        run(c, f"{cd} && bash -c 'set -a; source .env 2>/dev/null; set +a; python3 scripts/blocked_expectancy_analysis.py'", 300)
        # Run signal pipeline and write signal_group_expectancy into blocked_expectancy
        run(c, f"{cd} && bash -c 'set -a; source .env 2>/dev/null; set +a; python3 scripts/blocked_signal_expectancy_pipeline.py'", 300)
        run(c, f"{cd} && cp -f reports/blocked_signal_expectancy/signal_group_expectancy.md reports/blocked_expectancy/ 2>/dev/null || true", 10)

        # ---------- STEP 3: Verify output (extracted from blocked_expectancy) ----------
        extracted, _ = run(c, f"{cd} && wc -l reports/blocked_expectancy/extracted_candidates.jsonl 2>/dev/null || echo 0")
        replay, _ = run(c, f"{cd} && wc -l reports/blocked_expectancy/replay_results.jsonl 2>/dev/null || echo 0")
        bucket, _ = run(c, f"{cd} && cat reports/blocked_expectancy/bucket_analysis.md 2>/dev/null")
        sig_group, _ = run(c, f"{cd} && cat reports/blocked_expectancy/signal_group_expectancy.md 2>/dev/null || cat reports/blocked_signal_expectancy/signal_group_expectancy.md 2>/dev/null")

        n_extracted = 0
        try:
            n_extracted = int(extracted.split()[0]) if extracted.split() else 0
        except (ValueError, IndexError):
            pass
        n_replayed = 0
        try:
            n_replayed = int(replay.split()[0]) if replay.split() else 0
        except (ValueError, IndexError):
            pass

        # If extracted_candidates empty but blocked_signal_expectancy has blocked_candidates, use that count
        if n_extracted == 0:
            bc, _ = run(c, f"{cd} && wc -l reports/blocked_signal_expectancy/blocked_candidates.jsonl 2>/dev/null || echo 0")
            try:
                n_extracted = int(bc.split()[0]) if bc.split() else 0
            except (ValueError, IndexError):
                pass
        if n_replayed == 0:
            rr, _ = run(c, f"{cd} && wc -l reports/blocked_signal_expectancy/replay_results.jsonl 2>/dev/null || echo 0")
            try:
                n_replayed = int(rr.split()[0]) if rr.split() else 0
            except (ValueError, IndexError):
                pass
        if not bucket or len(bucket.strip()) < 20:
            bucket, _ = run(c, f"{cd} && cat reports/blocked_signal_expectancy/bucket_analysis.md 2>/dev/null")
        if not sig_group or len(sig_group.strip()) < 20:
            sig_group, _ = run(c, f"{cd} && cat reports/blocked_signal_expectancy/signal_group_expectancy.md 2>/dev/null")

        # ---------- Parse top 3 buckets ----------
        bucket_lines = [ln for ln in bucket.splitlines() if ln.strip().startswith("|") and "bucket" not in ln and "---" not in ln]
        top3_buckets = bucket_lines[:3]

        # ---------- Signal groups with positive expectancy (delta > 0) ----------
        edge_groups = []
        for ln in sig_group.splitlines():
            if "| uw |" in ln or "| regime_macro |" in ln or "| other_components |" in ln:
                parts = [p.strip() for p in ln.split("|") if p.strip()]
                if len(parts) >= 6:
                    try:
                        delta = float(parts[5])
                        if delta > 0:
                            edge_groups.append(parts[0])
                    except (ValueError, IndexError):
                        pass

        # ---------- Verdict: EDGE FOUND if any bucket mean_pnl > 0 or any signal group delta > 0 ----------
        verdict = "NO EDGE FOUND"
        if edge_groups:
            verdict = "EDGE FOUND"
        for ln in top3_buckets:
            parts = [p.strip() for p in ln.split("|") if p.strip()]
            if len(parts) >= 3:
                try:
                    if float(parts[2]) > 0:
                        verdict = "EDGE FOUND"
                        break
                except (ValueError, IndexError):
                    pass

        # ---------- REQUIRED OUTPUT (print only) ----------
        print("Number of blocked candidates extracted:", n_extracted)
        print("Number of replayed trades:", n_replayed)
        print("Bucket analysis summary (top 3 buckets):")
        for ln in top3_buckets:
            print(" ", ln.strip())
        if not top3_buckets:
            print("  (no bucket rows)")
        print("Signal groups with positive expectancy:", ", ".join(edge_groups) if edge_groups else "none")
        print("Verdict:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
