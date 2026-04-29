"""Sanity for ablation auto-tune percentile helper."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_ablation_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "research" / "entry_funnel_ablation.py"
    name = "entry_funnel_ablation_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_percentile_linear_median():
    m = _load_ablation_module()
    assert m._percentile_linear([1.0, 2.0, 3.0, 4.0, 5.0], 50.0) == 3.0


def test_percentile_linear_endpoints():
    m = _load_ablation_module()
    xs = [10.0, 20.0, 30.0]
    assert abs(m._percentile_linear(xs, 0.0) - 10.0) < 1e-9
    assert abs(m._percentile_linear(xs, 100.0) - 30.0) < 1e-9
