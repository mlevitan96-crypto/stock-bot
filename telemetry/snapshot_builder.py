"""
Snapshot builder — builds signal snapshots including SHADOW mode (NO-APPLY).
Shadow profiles recompute composite score with altered weights; never mutate global state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]


def _load_shadow_profiles() -> Dict[str, Dict]:
    """Load shadow profiles from config. Never raises."""
    try:
        path = REPO / "config" / "shadow_snapshot_profiles.yaml"
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8")
        try:
            import yaml
            data = yaml.safe_load(text)
        except ImportError:
            data = {}
        return (data or {}).get("profiles", {})
    except Exception:
        pass
    return {}


COMPONENT_ALIAS = {
    "flow": "options_flow",
    "iv_skew": "iv_term_skew",
    "smile": "smile_slope",
    "whale": "whale_persistence",
    "event": "event_alignment",
    "motif_bonus": "temporal_motif",
    "regime": "regime_modifier",
    "calendar": "calendar_catalyst",
}


def _apply_shadow_profile(
    components: Dict[str, Dict],
    composite_score_baseline: float,
    profile_multipliers: Dict[str, float],
) -> float:
    """
    Recompute composite using component contribs and profile multipliers.
    new_score = sum(contrib[c] * mult.get(alias(c), 1.0))
    """
    total = 0.0
    for comp_name, comp_val in (components or {}).items():
        if not isinstance(comp_val, dict):
            continue
        contrib = comp_val.get("contrib")
        if contrib is None:
            continue
        try:
            c = float(contrib)
        except (TypeError, ValueError):
            continue
        alias = COMPONENT_ALIAS.get(comp_name, comp_name)
        mult = profile_multipliers.get(comp_name) or profile_multipliers.get(alias, 1.0)
        total += c * mult
    return round(total, 4)


def build_signal_snapshot(
    symbol: str,
    lifecycle_event: str,
    mode: str,
    composite_score_v2: Optional[float] = None,
    freshness_factor: Optional[float] = None,
    composite_meta: Optional[Dict] = None,
    enriched: Optional[Dict] = None,
    regime_label: Optional[str] = None,
    trade_id: Optional[str] = None,
    uw_artifacts_used: Optional[Dict] = None,
    notes: Optional[List[str]] = None,
    timestamp_utc: Optional[str] = None,
    shadow_profile: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build snapshot record. If shadow_profile provided, recompute score with profile multipliers.
    Never mutates global state.
    """
    from telemetry.signal_snapshot_writer import build_snapshot_record

    rec = build_snapshot_record(
        symbol=symbol,
        lifecycle_event=lifecycle_event,
        mode=mode,
        composite_score_v2=composite_score_v2,
        freshness_factor=freshness_factor,
        composite_meta=composite_meta,
        enriched=enriched,
        regime_label=regime_label,
        trade_id=trade_id,
        uw_artifacts_used=uw_artifacts_used,
        notes=notes or [],
        timestamp_utc=timestamp_utc,
    )

    if shadow_profile:
        profiles = _load_shadow_profiles()
        profile_def = profiles.get(shadow_profile, {})
        mults = profile_def.get("component_multipliers") or {}
        components = rec.get("components") or {}
        base = rec.get("composite_score_v2") or 0.0
        shadow_score = _apply_shadow_profile(components, base, mults)
        rec = dict(rec)
        rec["mode"] = "SHADOW"
        rec["composite_score_v2"] = shadow_score
        rec["shadow_profile"] = shadow_profile
        notes = list(rec.get("notes") or [])
        notes.append(f"shadow:{shadow_profile}")
        rec["notes"] = notes
    return rec


def write_shadow_snapshots(
    base_dir: Path,
    date_str: str,
    records: List[Dict[str, Any]],
    profiles: Optional[List[str]] = None,
) -> int:
    """
    For each record, emit baseline + one shadow record per profile.
    Writes to logs/signal_snapshots_shadow_<DATE>.jsonl.
    Returns count written.
    """
    from telemetry.signal_snapshot_writer import write_snapshot

    path = base_dir / "logs" / f"signal_snapshots_shadow_{date_str}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.write_text("")

    profs = profiles or list(_load_shadow_profiles().keys())
    if "baseline" in profs:
        profs = [p for p in profs if p != "baseline"]

    written = 0
    for rec in records:
        symbol = rec.get("symbol", "")
        lifecycle = rec.get("lifecycle_event", "ENTRY_DECISION")
        feats = rec.get("feature_snapshot") or {}
        if not feats and rec.get("components"):
            feats = {k: v.get("contrib") for k, v in (rec.get("components") or {}).items() if isinstance(v, dict)}
        meta = rec.get("composite_meta") or {"components": feats, "component_contributions": feats}
        ts = rec.get("entry_ts") or rec.get("exit_ts") or rec.get("timestamp_utc", "")
        tid = rec.get("trade_id", "")
        score = rec.get("v2_score") or rec.get("entry_v2_score") or rec.get("exit_v2_score") or 2.0
        regime = (rec.get("regime_snapshot") or {}).get("regime") if isinstance(rec.get("regime_snapshot"), dict) else None

        for profile in ["baseline"] + profs:
            shad = build_signal_snapshot(
                symbol=symbol,
                lifecycle_event=lifecycle,
                mode="PAPER",
                composite_score_v2=float(score),
                freshness_factor=1.0,
                composite_meta=meta,
                regime_label=regime,
                trade_id=tid,
                uw_artifacts_used=rec.get("uw_artifacts_used") or {},
                notes=["shadow_batch", "NO_ORDERS_PLACED"],
                timestamp_utc=ts,
                shadow_profile=profile if profile != "baseline" else None,
            )
            if write_snapshot(base_dir, shad, path):
                written += 1
    return written
