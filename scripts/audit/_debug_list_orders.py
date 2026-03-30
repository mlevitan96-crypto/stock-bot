import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
import os

os.chdir(REPO)
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
from main import Config  # noqa: E402
import alpaca_trade_api as t  # noqa: E402

api = t.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
for st in ("all", "closed", "open"):
    o = api.list_orders(status=st, limit=20, nested=True)
    print("status=", st, "n=", len(o or []))
    for i, x in enumerate((o or [])[:3]):
        print(" ", i, getattr(x, "status", None), getattr(x, "filled_qty", None), getattr(x, "id", None))
