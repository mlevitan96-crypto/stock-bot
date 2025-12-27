#!/usr/bin/env python3
"""Analyze trade performance from attribution logs"""
import json
from pathlib import Path
from collections import defaultdict

attr_log = Path("logs/attribution.jsonl")
if not attr_log.exists():
    print("No attribution log found")
    exit(1)

wins = []
losses = []
by_symbol = defaultdict(lambda: {"wins": [], "losses": []})
by_reason = defaultdict(lambda: {"wins": [], "losses": []})
hold_times = []

print("=" * 60)
print("TRADE PERFORMANCE ANALYSIS")
print("=" * 60)
print()

with open(attr_log, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            # Check for both formats: "type": "attribution" or "msg": "attribution_logged"
            if rec.get('type') != 'attribution' and rec.get('msg') != 'attribution_logged':
                continue
            
            symbol = rec.get('symbol', 'UNKNOWN')
            
            # Handle nested context structure
            context = rec.get('context', {})
            if context:
                pnl_pct = context.get('pnl_pct', rec.get('pnl_pct', 0))
                reason = context.get('close_reason', rec.get('reason', 'unknown'))
                hold_min = context.get('hold_minutes', rec.get('hold_min', 0))
            else:
                pnl_pct = rec.get('pnl_pct', 0)
                reason = rec.get('reason', 'unknown')
                hold_min = rec.get('hold_min', rec.get('hold_minutes', 0))
            
            pnl_usd = rec.get('pnl_usd', 0)
            
            if pnl_pct > 0:
                wins.append(pnl_pct)
                by_symbol[symbol]["wins"].append(pnl_pct)
                by_reason[reason]["wins"].append(pnl_pct)
            elif pnl_pct < 0:
                losses.append(pnl_pct)
                by_symbol[symbol]["wins"].append(pnl_pct)  # This should be losses
                by_symbol[symbol]["losses"].append(pnl_pct)
                by_reason[reason]["losses"].append(pnl_pct)
            
            hold_times.append(hold_min)
        except Exception as e:
            continue

# Fix the bug above
for symbol in by_symbol:
    by_symbol[symbol]["wins"] = [w for w in by_symbol[symbol]["wins"] if w > 0]
    by_symbol[symbol]["losses"] = [l for l in by_symbol[symbol]["losses"] if l < 0]

total_trades = len(wins) + len(losses)
if total_trades == 0:
    print("No trades found in attribution log")
    print("Checking log format...")
    # Show first few lines for debugging
    with open(attr_log, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            if line.strip():
                try:
                    rec = json.loads(line)
                    print(f"Sample record keys: {list(rec.keys())}")
                    if 'type' in rec:
                        print(f"  type: {rec['type']}")
                    if 'msg' in rec:
                        print(f"  msg: {rec['msg']}")
                except:
                    print(f"  (parse error)")
    exit(0)

win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0

print(f"Total Trades: {total_trades}")
print(f"Wins: {len(wins)} ({len(wins)/total_trades*100:.1f}%)")
print(f"Losses: {len(losses)} ({len(losses)/total_trades*100:.1f}%)")
print()

if wins:
    avg_win = sum(wins) / len(wins)
    max_win = max(wins)
    min_win = min(wins)
    print(f"Average Win: {avg_win:.2f}%")
    print(f"Max Win: {max_win:.2f}%")
    print(f"Min Win: {min_win:.2f}%")
else:
    print("No wins found")
print()

if losses:
    avg_loss = sum(losses) / len(losses)
    max_loss = min(losses)  # Most negative
    min_loss = max(losses)  # Least negative
    print(f"Average Loss: {avg_loss:.2f}%")
    print(f"Max Loss: {max_loss:.2f}%")
    print(f"Min Loss: {min_loss:.2f}%")
else:
    print("No losses found")
print()

if wins and losses:
    risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)
    print(f"Risk/Reward Ratio: {risk_reward:.2f}")
    print(f"Expectancy: {expectancy:.2f}%")
print()

if hold_times:
    avg_hold = sum(hold_times) / len(hold_times)
    print(f"Average Hold Time: {avg_hold:.1f} minutes ({avg_hold/60:.1f} hours)")
    print(f"Min Hold: {min(hold_times):.1f} minutes")
    print(f"Max Hold: {max(hold_times):.1f} minutes")
print()

print("=" * 60)
print("BY SYMBOL")
print("=" * 60)
for symbol in sorted(by_symbol.keys()):
    sym_wins = by_symbol[symbol]["wins"]
    sym_losses = by_symbol[symbol]["losses"]
    sym_total = len(sym_wins) + len(sym_losses)
    if sym_total > 0:
        sym_wr = len(sym_wins) / sym_total * 100
        sym_avg_win = sum(sym_wins) / len(sym_wins) if sym_wins else 0
        sym_avg_loss = sum(sym_losses) / len(sym_losses) if sym_losses else 0
        print(f"{symbol:6s} {sym_total:3d} trades | WR: {sym_wr:5.1f}% | Avg Win: {sym_avg_win:6.2f}% | Avg Loss: {sym_avg_loss:6.2f}%")
print()

print("=" * 60)
print("BY EXIT REASON")
print("=" * 60)
for reason in sorted(by_reason.keys()):
    reason_wins = by_reason[reason]["wins"]
    reason_losses = by_reason[reason]["losses"]
    reason_total = len(reason_wins) + len(reason_losses)
    if reason_total > 0:
        reason_wr = len(reason_wins) / reason_total * 100
        print(f"{reason:20s} {reason_total:3d} trades | WR: {reason_wr:5.1f}% | Wins: {len(reason_wins):3d} | Losses: {len(reason_losses):3d}")
