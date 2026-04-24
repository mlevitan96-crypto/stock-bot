import json
import sys
from pathlib import Path

sys.path.insert(0, "/root/stock-bot")
from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START, evaluate_completeness

g = evaluate_completeness(Path("/root/stock-bot"), open_ts_epoch=STRICT_EPOCH_START, audit=True)
print(
    json.dumps(
        {
            "reason_histogram": g.get("reason_histogram"),
            "incomplete_examples": g.get("incomplete_examples"),
            "trades_seen": g.get("trades_seen"),
            "trades_complete": g.get("trades_complete"),
            "trades_incomplete": g.get("trades_incomplete"),
            "LEARNING_STATUS": g.get("LEARNING_STATUS"),
        },
        indent=2,
    )
)
