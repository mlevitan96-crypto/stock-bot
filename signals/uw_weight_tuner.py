#!/usr/bin/env python3
"""
UW Dynamic Weight Tuner + Daily Attribution Reports

Purpose:
- Continuously learn which UW layers (Flow, Dark Pool, Insider) are most predictive.
- Re-weight composite scoring components based on rolling attribution outcomes.
- Produce daily attribution reports (by composite bucket, by layer contribution).
- Keep changes stable via EWMA smoothing, Wilson intervals, and caps.
- Persist state so learning compounds over time.

Integrations:
- Works alongside your existing modules:
  - signals/uw_composite.py (Flow/Dark/Insider weights)
  - signals/uw_adaptive.py (adaptive threshold gate)
  - telemetry logger and daily postmortems
- This tuner writes updated weights to data/uw_weights.json,
  which uw_composite.py should read (or you can import this module and pass weights explicitly).

Files:
- data/uw_attribution.jsonl    (existing; entries from log_uw_attribution)
- data/daily_postmortem.jsonl  (existing; daily summaries)
- data/uw_weights.json         (new; live weights + audit)
- data/uw_tuner_state.json     (new; rolling stats + history)
- data/uw_reports/uw_attribution_<YYYY-MM-DD>.json (new; per-day report)

Usage:
1) Instantiate UWWeightTuner on startup; call load().
2) After each trade outcome (close), call record_outcome(...) with:
     composite_score, pnl, flow_conviction, dark_pool_total_premium, insider_sentiment, flow_sentiment, dark_pool_sentiment
   Or simply point it at uw_attribution.jsonl for batch updates.
3) Periodically (e.g., end-of-day), call update_weights_and_generate_report(...).
4) Wire uw_composite to read weights from data/uw_weights.json, or pass weights into compute_uw_composite_score.
"""

import json
import math
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Paths
DATA_DIR = Path("data")
ATTR_LOG = DATA_DIR / "uw_attribution.jsonl"
POSTMORTEM = DATA_DIR / "daily_postmortem.jsonl"
WEIGHTS_FILE = DATA_DIR / "uw_weights.json"
STATE_FILE = DATA_DIR / "uw_tuner_state.json"
REPORT_DIR = DATA_DIR / "uw_reports"

# Default base weights (match uw_composite initial config)
DEFAULT_WEIGHTS = {
    "W_FLOW": 3.00,
    "W_DARK": 1.25,
    "W_INSIDER": 0.75,
    "W_REGIME": 0.35
}

# Hard caps for safety
WEIGHT_CAPS = {
    "W_FLOW": (2.25, 4.00),
    "W_DARK": (0.75, 2.00),
    "W_INSIDER": (0.25, 1.50),
    "W_REGIME": (0.20, 0.75)
}

# Composite buckets
BUCKETS = [(2.50, 3.00), (3.00, 4.00), (4.00, 10.00)]

# Smoothing + sensitivity
EWMA_ALPHA = 0.2
WEIGHT_STEP = 0.25
MIN_SAMPLES = 100
WINDOW_DAYS = 14
WILSON_Z = 1.96


def layer_alignment(flow_sent: str, dp_sent: str, ins_sent: str) -> Dict[str, int]:
    """Returns signs per layer: +1 for bullish, -1 for bearish, 0 for neutral/mixed."""
    def sgn(s: str) -> int:
        s = (s or "MIXED").upper()
        if s == "BULLISH": return +1
        if s == "BEARISH": return -1
        return 0
    return {"FLOW": sgn(flow_sent), "DARK": sgn(dp_sent), "INSIDER": sgn(ins_sent)}


def same_direction(a: int, b: int) -> bool:
    return (a != 0 and b != 0 and a == b)


def wilson_low_bound(wins: int, total: int, z: float = WILSON_Z) -> float:
    """Compute Wilson score lower bound for win rate confidence interval."""
    if total == 0:
        return 0.0
    p = wins / total
    denom = 1 + (z**2 / total)
    centre = p + (z**2 / (2*total))
    adj = z * math.sqrt((p*(1-p) + (z**2 / (4*total))) / total)
    return (centre - adj) / denom


def ewma(prev: Optional[float], x: float, alpha: float = EWMA_ALPHA) -> float:
    """Exponentially weighted moving average."""
    return x if prev is None else (alpha * x + (1 - alpha) * prev)


class UWWeightTuner:
    """
    Self-optimizing weight tuner for UW composite scoring.
    
    Tracks per-layer performance attribution and automatically adjusts
    composite weights based on which data sources prove most predictive.
    """
    
    def __init__(self):
        self.state = {
            "weights": DEFAULT_WEIGHTS.copy(),
            "history": [],
            "layer_stats": {
                "FLOW": {"wins": 0, "losses": 0, "pnl": 0.0, "ewma_win": None, "ewma_pnl": None},
                "DARK": {"wins": 0, "losses": 0, "pnl": 0.0, "ewma_win": None, "ewma_pnl": None},
                "INSIDER": {"wins": 0, "losses": 0, "pnl": 0.0, "ewma_win": None, "ewma_pnl": None},
            },
            "bucket_stats": {str(b): {"wins": 0, "losses": 0, "pnl": 0.0, "ewma_win": None} for b in BUCKETS},
            "last_update_ts": 0
        }
        self.load()

    def load(self):
        """Load tuner state from disk."""
        try:
            if STATE_FILE.exists():
                self.state = json.loads(STATE_FILE.read_text())
        except Exception:
            pass

    def save(self):
        """Save tuner state to disk."""
        try:
            STATE_FILE.parent.mkdir(exist_ok=True)
            STATE_FILE.write_text(json.dumps(self.state, indent=2))
        except Exception:
            pass

    def save_weights(self):
        """Save current weights to weights file for uw_composite to read."""
        payload = {
            "weights": self.state["weights"],
            "updated_at": int(time.time()),
            "updated_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        WEIGHTS_FILE.write_text(json.dumps(payload, indent=2))

    def record_outcome(self,
                       composite_score: float,
                       pnl: float,
                       flow_sentiment: str,
                       dark_pool_sentiment: str,
                       insider_sentiment: str,
                       decision: Optional[str] = None,
                       ts: Optional[int] = None):
        """Record a trade outcome and update rolling stats."""
        win = pnl > 0
        bkey = self._bucket_key(composite_score)
        b = self.state["bucket_stats"].get(bkey, {"wins": 0, "losses": 0, "pnl": 0.0, "ewma_win": None})
        if win: b["wins"] += 1
        else: b["losses"] += 1
        b["pnl"] += float(pnl)
        total_b = b["wins"] + b["losses"]
        wr_b = (b["wins"] / total_b) if total_b > 0 else 0.0
        b["ewma_win"] = ewma(b.get("ewma_win"), wr_b)
        self.state["bucket_stats"][bkey] = b

        align = layer_alignment(flow_sentiment, dark_pool_sentiment, insider_sentiment)
        outcome_dir = +1 if win else -1
        for layer in ("FLOW", "DARK", "INSIDER"):
            ls = self.state["layer_stats"][layer]
            if align[layer] != 0:
                if same_direction(align[layer], outcome_dir):
                    ls["wins"] += 1
                else:
                    ls["losses"] += 1
                ls["pnl"] += float(pnl)
                total_l = ls["wins"] + ls["losses"]
                wr_l = (ls["wins"] / total_l) if total_l > 0 else 0.0
                ls["ewma_win"] = ewma(ls.get("ewma_win"), wr_l)
                ls["ewma_pnl"] = ewma(ls.get("ewma_pnl"), float(pnl))

        self.state["last_update_ts"] = int(ts or time.time())

    def _bucket_key(self, score: float) -> str:
        for lo, hi in BUCKETS:
            if lo <= score < hi:
                return str((lo, hi))
        return str(BUCKETS[-1])

    def ingest_attribution_log(self,
                               since_dt: Optional[datetime] = None,
                               until_dt: Optional[datetime] = None):
        """Batch ingest outcomes from uw_attribution.jsonl."""
        if not ATTR_LOG.exists():
            return
        lines = ATTR_LOG.read_text().splitlines()
        for line in lines:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = rec.get("_ts", int(time.time()))
            dt = datetime.utcfromtimestamp(ts)
            if since_dt and dt < since_dt: continue
            if until_dt and dt > until_dt: continue
            decision = (rec.get("decision") or "").upper()
            if decision not in ("ENTRY_APPROVED", "EXIT_TIGHTENED", "EXIT_NORMAL"):
                continue
            pnl = 0.0
            extra = rec.get("extra") or {}
            if "pnl" in extra:
                try:
                    pnl = float(extra["pnl"])
                except Exception:
                    pnl = 0.0
            comp_score = float(rec.get("score", 0.0))
            flow_sent = (rec.get("flow_sentiment") or "MIXED").upper()
            dp_sent = (rec.get("dark_pool_sentiment") or "MIXED").upper()
            ins_sent = (rec.get("insider_sentiment") or "MIXED").upper()
            self.record_outcome(comp_score, pnl, flow_sent, dp_sent, ins_sent, decision=decision, ts=ts)

    def _calc_wilson(self, wins: int, losses: int) -> float:
        return wilson_low_bound(wins, wins + losses, z=WILSON_Z)

    def _nudge(self, key: str, direction: int):
        lo, hi = WEIGHT_CAPS[key]
        current = float(self.state["weights"][key])
        proposed = current + (direction * WEIGHT_STEP)
        self.state["weights"][key] = float(max(lo, min(hi, round(proposed, 2))))

    def _audit(self, msg: str):
        self.state["history"].append({
            "ts": int(time.time()),
            "dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "weights": self.state["weights"].copy(),
            "msg": msg
        })
        if len(self.state["history"]) > 500:
            self.state["history"] = self.state["history"][-500:]

    def update_weights(self) -> Dict[str, float]:
        """
        Re-weight layers based on rolling attribution (last WINDOW_DAYS).
        
        Uses Wilson confidence intervals and EWMA smoothing to make
        statistically significant weight adjustments.
        """
        L = self.state["layer_stats"]
        weights_before = self.state["weights"].copy()
        
        for layer, k in [("FLOW","W_FLOW"),("DARK","W_DARK"),("INSIDER","W_INSIDER")]:
            wins = int(L[layer]["wins"])
            losses = int(L[layer]["losses"])
            total = wins + losses
            if total < MIN_SAMPLES:
                continue
            wil = self._calc_wilson(wins, losses)
            ew = L[layer].get("ewma_win") or 0.5
            
            if wil > 0.58 and ew > 0.60:
                self._nudge(k, +1)
                self._audit(f"Increased {k} (wilson={wil:.3f}, ewma={ew:.3f}, total={total})")
            elif wil < 0.42 and ew < 0.45:
                self._nudge(k, -1)
                self._audit(f"Decreased {k} (wilson={wil:.3f}, ewma={ew:.3f}, total={total})")
        
        stable_wr = []
        for bkey, v in self.state["bucket_stats"].items():
            t = v["wins"] + v["losses"]
            if t >= MIN_SAMPLES:
                stable_wr.append(v.get("ewma_win") or 0.0)
        if len(stable_wr) >= 2:
            avg_wr = sum(stable_wr) / len(stable_wr)
            if avg_wr > 0.62:
                self._nudge("W_REGIME", +1)
                self._audit(f"Increased W_REGIME (avg bucket ewma={avg_wr:.3f})")
            elif avg_wr < 0.45:
                self._nudge("W_REGIME", -1)
                self._audit(f"Decreased W_REGIME (avg bucket ewma={avg_wr:.3f})")

        if self.state["weights"] == weights_before:
            self._audit("Weights unchanged (no significant attribution signal)")
        self.save()
        self.save_weights()
        return self.state["weights"]

    def generate_daily_report(self, report_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create per-day attribution report from uw_attribution.jsonl and bucket stats."""
        REPORT_DIR.mkdir(exist_ok=True)
        day = (report_date or datetime.utcnow()).date()
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)
        
        records = []
        if ATTR_LOG.exists():
            for line in ATTR_LOG.read_text().splitlines():
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                ts = rec.get("_ts", int(time.time()))
                dt = datetime.utcfromtimestamp(ts)
                if dt < start or dt >= end:
                    continue
                records.append(rec)

        per_bucket: Dict[str, Dict[str, Any]] = {str(b): {"wins":0,"losses":0,"pnl":0.0,"avg_score":0.0,"n":0} for b in BUCKETS}
        per_layer: Dict[str, Dict[str, Any]] = {"FLOW":{"wins":0,"losses":0,"pnl":0.0,"n":0},
                                                "DARK":{"wins":0,"losses":0,"pnl":0.0,"n":0},
                                                "INSIDER":{"wins":0,"losses":0,"pnl":0.0,"n":0}}

        for rec in records:
            score = float(rec.get("score", 0.0))
            bkey = self._bucket_key(score)
            pnl = float(rec.get("extra", {}).get("pnl", 0.0)) if rec.get("extra") else 0.0
            win = pnl > 0
            per_bucket[bkey]["avg_score"] = ((per_bucket[bkey]["avg_score"] * per_bucket[bkey]["n"]) + score) / (per_bucket[bkey]["n"] + 1) if per_bucket[bkey]["n"] > 0 else score
            per_bucket[bkey]["n"] += 1
            if win: per_bucket[bkey]["wins"] += 1
            else: per_bucket[bkey]["losses"] += 1
            per_bucket[bkey]["pnl"] += pnl

            align = layer_alignment(rec.get("flow_sentiment","MIXED"), rec.get("dark_pool_sentiment","MIXED"), rec.get("insider_sentiment","MIXED"))
            outcome_dir = +1 if win else -1
            for layer in ("FLOW","DARK","INSIDER"):
                if align[layer] != 0:
                    per_layer[layer]["n"] += 1
                    if same_direction(align[layer], outcome_dir):
                        per_layer[layer]["wins"] += 1
                    else:
                        per_layer[layer]["losses"] += 1
                    per_layer[layer]["pnl"] += pnl

        for obj in [per_bucket, per_layer]:
            for k, v in obj.items():
                total = v["wins"] + v["losses"]
                v["win_rate"] = round((v["wins"] / total), 4) if total > 0 else 0.0
                v["wilson_lb"] = round(wilson_low_bound(v["wins"], total), 4) if total > 0 else 0.0
                v["avg_pnl"] = round((v["pnl"] / total), 2) if total > 0 else 0.0

        report = {
            "date": day.strftime("%Y-%m-%d"),
            "weights": self.state["weights"],
            "per_bucket": per_bucket,
            "per_layer": per_layer,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        out_path = REPORT_DIR / f"uw_attribution_{day.strftime('%Y-%m-%d')}.json"
        out_path.write_text(json.dumps(report, indent=2))
        return report

    def update_weights_and_generate_report(self):
        """End-of-day routine: ingest, update weights, report."""
        since = datetime.utcnow() - timedelta(days=WINDOW_DAYS)
        self.ingest_attribution_log(since_dt=since)
        new_weights = self.update_weights()
        report = self.generate_daily_report(datetime.utcnow())
        return {"weights": new_weights, "report": report}


def load_live_weights(fallback: Dict[str, float] = DEFAULT_WEIGHTS) -> Dict[str, float]:
    """Load current optimized weights from weights file."""
    try:
        payload = json.loads(WEIGHTS_FILE.read_text())
        w = payload.get("weights") or {}
        out = fallback.copy()
        for k in out.keys():
            v = float(w.get(k, out[k]))
            lo, hi = WEIGHT_CAPS[k]
            out[k] = float(max(lo, min(hi, v)))
        return out
    except Exception:
        return fallback


if __name__ == "__main__":
    tuner = UWWeightTuner()
    summary = tuner.update_weights_and_generate_report()
    print(json.dumps({"weights": summary["weights"], "report_path": str(REPORT_DIR)}, indent=2))
