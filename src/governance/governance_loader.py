"""Governance loader: loads strategy_governance + mode_governance + exit_timing_scenarios."""
import json
import os
from pathlib import Path


def _load_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_governance(repo_root: str | None = None):
    root = Path(repo_root or Path(__file__).resolve().parents[2])
    cfg = root / "config"
    return {
        "strategy_governance": _load_json(cfg / "strategy_governance.json"),
        "mode_governance": _load_json(cfg / "mode_governance.json"),
        "exit_timing_scenarios": _load_json(cfg / "exit_timing_scenarios.json"),
    }


def resolve_policy(*, mode: str, strategy: str | None, regime: str | None, scenario: str):
    g = load_governance()
    mode = (mode or "UNKNOWN").upper()
    strategy = (strategy or "UNKNOWN").upper()
    regime = (regime or "UNKNOWN").upper()

    # Base mode settings
    mode_g = (g.get("mode_governance") or {}).get("modes", {}).get(mode, {})
    # Strategy settings
    strat_g = (g.get("strategy_governance") or {}).get("strategies", {}).get(strategy, {})

    # Scenario params (may be empty)
    scen = (g.get("exit_timing_scenarios") or {}).get("scenarios", {}).get(scenario, {})
    params_by_mode = (scen.get("params") or {}).get(mode, {})

    # Regime overrides inside scenario
    regime_overrides = (params_by_mode.get("regime_overrides") or {}).get(regime, {})

    resolved = {
        "mode": mode,
        "strategy": strategy,
        "regime": regime,
        "scenario": scenario,
        "mode_governance": mode_g,
        "strategy_governance": strat_g,
        "exit_timing_params": {k: v for k, v in params_by_mode.items() if k != "regime_overrides"},
        "exit_timing_regime_overrides": regime_overrides,
    }
    return resolved
