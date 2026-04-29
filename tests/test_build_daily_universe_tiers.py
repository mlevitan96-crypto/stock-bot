import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_daily_universe import _tier_slices  # noqa: E402


def test_tier_slices_partition():
    rows = [{"symbol": c} for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    sniper, radar, trail = _tier_slices(rows, sniper=5, radar=7)
    assert sniper == ["A", "B", "C", "D", "E"]
    assert radar == ["F", "G", "H", "I", "J", "K", "L"]
    assert trail == list("MNOPQRSTUVWXYZ")
