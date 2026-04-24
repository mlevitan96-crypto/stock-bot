import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from droplet_client import DropletClient

with DropletClient() as c:
    o, _, _ = c._execute(
        "ls -t /root/stock-bot/reports/ALPACA_DATA_PATH_WIRING_PROOF_*.md | head -1",
        timeout=20,
    )
    r = o.strip()
    if not r:
        print("none")
        sys.exit(1)
    c.get_file(r, str(Path("reports") / Path(r).name))
    print(Path("reports") / Path(r).name)
