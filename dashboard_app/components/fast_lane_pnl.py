"""
Alpaca Fast-Lane 25-Trade PnL panel.
Rendered in dashboard.py via /api/stockbot/fast_lane_ledger and loadFastLanePnl() JS.
This module documents the panel contract; actual HTML/JS lives in dashboard.py.
"""
# Panel: Alpaca Fast-Lane 25-Trade PnL
# - Line chart: PnL per 25-trade cycle (table in dashboard)
# - Cumulative PnL curve (running sum in table)
# - Cycle table: cycle_id, pnl_usd, best_candidate_id, timestamp_completed
