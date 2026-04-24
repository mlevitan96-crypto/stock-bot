import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.telemetry.alpaca_trade_key import build_trade_key

r = json.loads(Path("logs/exit_attribution.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
print("side", repr(r.get("side")))
print("tk", build_trade_key(r["symbol"], r.get("side") or "long", r["entry_timestamp"]))
