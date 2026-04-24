"""Side-aware ML feature normalization shared by training and live inference."""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Tuple

from src.core.position_math import get_position_sign


# Positive values in these fields are interpreted as bullish/long-favorable signal.
# For short candidates, invert them so the model sees trade-direction-favorable shape.
DIRECTIONAL_FEATURE_NAMES = frozenset(
    {
        "mlf_direction_intel_embed_canonical_direction_components",
        "mlf_direction_intel_embed_intel_deltas_breadth_adv_dec_delta",
        "mlf_direction_intel_embed_intel_deltas_futures_direction_delta",
        "mlf_direction_intel_embed_intel_deltas_sector_strength_delta",
        "mlf_direction_intel_embed_intel_snapshot_entry_breadth_intel_adv_dec_ratio",
        "mlf_direction_intel_embed_intel_snapshot_entry_breadth_intel_new_highs_lows",
        "mlf_direction_intel_embed_intel_snapshot_entry_breadth_intel_up_vol_down_vol_ratio",
        "mlf_direction_intel_embed_intel_snapshot_entry_etf_flow_intel_iwm_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_etf_flow_intel_qqq_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_etf_flow_intel_spy_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_es_direction",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_nq_direction",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_rty_direction",
        "mlf_direction_intel_embed_intel_snapshot_entry_macro_intel_macro_sentiment_score",
        "mlf_direction_intel_embed_intel_snapshot_entry_overnight_intel_overnight_dark_pool_imbalance",
        "mlf_direction_intel_embed_intel_snapshot_entry_overnight_intel_overnight_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_overnight_intel_overnight_return",
        "mlf_direction_intel_embed_intel_snapshot_entry_postmarket_intel_postmarket_gap_pct",
        "mlf_direction_intel_embed_intel_snapshot_entry_postmarket_intel_postmarket_sentiment",
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_gap_pct",
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_sentiment",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_market_trend",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_qqq_overnight_ret",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret",
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_etf_flow",
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_momentum",
        "mlf_direction_intel_embed_intel_snapshot_entry_uw_intel_uw_overnight_sentiment",
        "mlf_direction_intel_embed_intel_snapshot_entry_uw_intel_uw_premarket_sentiment",
        "mlf_direction_intel_embed_intel_snapshot_entry_uw_intel_uw_preopen_dark_pool",
        "mlf_direction_intel_embed_intel_snapshot_entry_uw_intel_uw_preopen_flow",
        "mlf_entry_uw_darkpool_bias",
        "mlf_entry_uw_flow_strength",
        "mlf_entry_uw_regime_alignment",
        "mlf_entry_uw_sector_alignment",
        "mlf_entry_uw_sentiment",
        "mlf_entry_uw_sentiment_score",
        "mlf_scoreflow_components_dark_pool",
        "mlf_scoreflow_components_etf_flow",
        "mlf_scoreflow_components_flow",
        "mlf_scoreflow_components_greeks_gamma",
        "mlf_scoreflow_components_market_tide",
        "mlf_scoreflow_components_oi_change",
        "mlf_scoreflow_components_whale",
        "uw_gamma_skew",
        "uw_tide_score",
    }
)


ABSOLUTE_FEATURE_NAMES = frozenset(
    {
        "_source_file",
        "entry_price",
        "hour_of_day",
        "mlf_direction_intel_embed_intel_deltas_macro_risk_entry",
        "mlf_direction_intel_embed_intel_deltas_macro_risk_exit",
        "mlf_direction_intel_embed_intel_deltas_overnight_volatility_delta",
        "mlf_direction_intel_embed_intel_deltas_vol_regime_entry",
        "mlf_direction_intel_embed_intel_deltas_vol_regime_exit",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_vx_direction",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_futures_basis",
        "mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_futures_trend_strength",
        "mlf_direction_intel_embed_intel_snapshot_entry_macro_intel_macro_events_today",
        "mlf_direction_intel_embed_intel_snapshot_entry_macro_intel_macro_risk_flag",
        "mlf_direction_intel_embed_intel_snapshot_entry_overnight_intel_overnight_volatility",
        "mlf_direction_intel_embed_intel_snapshot_entry_postmarket_intel_after_hours_volume_ratio",
        "mlf_direction_intel_embed_intel_snapshot_entry_postmarket_intel_earnings_reaction_flag",
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_volatility",
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_volume_ratio",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_risk_on_off",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_stale_1m",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_volatility_regime",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_vxx_vxz_ratio",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_posture",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_posture_flags_allow_new_longs",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_posture_flags_prefer_shorts",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_posture_flags_tighten_long_exits",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_regime_confidence",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_regime_label",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_regime_source",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_structural_confidence",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_structural_regime",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_ts",
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector",
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_strength_rank",
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_volatility",
        "mlf_direction_intel_embed_intel_snapshot_entry_timestamp",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_vix_change",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_vix_level",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_vvix_level",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_1d",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_5d",
        "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_vol_regime",
        "mlf_entry_uw_earnings_proximity",
        "mlf_entry_snapshot_match",
        "mlf_entry_uw_uw_intel_source",
        "mlf_entry_uw_uw_intel_version",
        "mlf_ml_feature_source",
        "mlf_scoreflow_components_calendar",
        "mlf_scoreflow_components_congress",
        "mlf_scoreflow_components_event",
        "mlf_scoreflow_components_freshness_factor",
        "mlf_scoreflow_components_ftd_pressure",
        "mlf_scoreflow_components_insider",
        "mlf_scoreflow_components_institutional",
        "mlf_scoreflow_components_iv_rank",
        "mlf_scoreflow_components_iv_skew",
        "mlf_scoreflow_components_motif_bonus",
        "mlf_scoreflow_components_regime",
        "mlf_scoreflow_components_shorts_squeeze",
        "mlf_scoreflow_components_smile",
        "mlf_scoreflow_components_squeeze_score",
        "mlf_scoreflow_components_toxicity_correlation_penalty",
        "mlf_scoreflow_components_toxicity_penalty",
        "mlf_scoreflow_join_tier",
        "mlf_scoreflow_lookback_sec_applied",
        "mlf_scoreflow_snapshot_age_sec",
        "mlf_scoreflow_total_score",
        "mlf_scoreflow_total_score_imputed",
        "qty",
        "regime_id",
        "shadow_chop_block",
        "side_enc",
        "strict_open_epoch_utc",
        "symbol_enc",
    }
)


def _canonical_feature_name(name: str) -> str:
    return str(name or "").strip().lower()


def is_directional_ml_feature(name: str) -> bool:
    return _canonical_feature_name(name) in DIRECTIONAL_FEATURE_NAMES


def ml_feature_taxonomy() -> Tuple[Iterable[str], Iterable[str]]:
    return tuple(sorted(DIRECTIONAL_FEATURE_NAMES)), tuple(sorted(ABSOLUTE_FEATURE_NAMES))


def _invert_if_number(value: Any, sign: int) -> Any:
    if sign == 1:
        return value
    if isinstance(value, bool):
        return value
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value
    if not math.isfinite(numeric):
        return value
    return -numeric


def normalize_features_for_side(features_dict: Dict[str, Any], side: str) -> Dict[str, Any]:
    """Invert only bullish/long-directional feature values for short candidates."""
    sign = get_position_sign(side)
    normalized = dict(features_dict)
    if sign == 1:
        return normalized
    for key, value in list(normalized.items()):
        if is_directional_ml_feature(key):
            normalized[key] = _invert_if_number(value, sign)
    return normalized
