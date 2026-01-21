#!/usr/bin/env python3
"""
Replacement Logic (v2, shadow-only)
==================================

Contract:
- Replacement only triggers when:
  - exit_score above threshold
  - AND candidate entry score exceeds current score + margin
  - AND universe v2 supports candidate (best-effort via ranking/order)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def choose_replacement_candidate(
    *,
    exit_score: float,
    threshold: float,
    current_symbol: str,
    current_v2_score: float,
    candidate_symbol: Optional[str],
    candidate_v2_score: Optional[float],
    margin: float = 0.25,
) -> Tuple[Optional[str], Dict[str, Any]]:
    if float(exit_score) < float(threshold):
        return None, {"reason": "exit_score_below_threshold", "exit_score": float(exit_score), "threshold": float(threshold)}
    if not candidate_symbol:
        return None, {"reason": "no_candidate"}
    if candidate_v2_score is None:
        return None, {"reason": "missing_candidate_score"}
    ok = float(candidate_v2_score) >= float(current_v2_score) + float(margin)
    if not ok:
        return None, {"reason": "candidate_not_superior", "current_v2_score": float(current_v2_score), "candidate_v2_score": float(candidate_v2_score), "margin": float(margin)}
    return str(candidate_symbol).upper(), {
        "reason": "replacement_candidate_selected",
        "exit_score": float(exit_score),
        "threshold": float(threshold),
        "current_symbol": str(current_symbol).upper(),
        "current_v2_score": float(current_v2_score),
        "candidate_symbol": str(candidate_symbol).upper(),
        "candidate_v2_score": float(candidate_v2_score),
        "margin": float(margin),
    }

