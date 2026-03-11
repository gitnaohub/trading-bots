#!/bin/bash
# Quick Paper Trading Stats Viewer

python3 << 'PYEOF'
import json
from datetime import datetime

with open('data/paper_trading_v3.json', 'r') as f:
    data = json.load(f)

closed = data['closed_trades']
total = len(closed)

if total > 0:
    wins = sum(1 for t in closed if t['pnl_pct'] > 0)
    losses = sum(1 for t in closed if t['pnl_pct'] < 0)
    win_rate = (wins / total) * 100
    total_pnl = sum(t['pnl_pct'] for t in closed)
    
    print(f"\n📊 V3 Paper Trading Stats")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Total Trades: {total}")
    print(f"Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total P&L: {total_pnl:.2f}%")
    print(f"Avg P&L: {total_pnl/total:.3f}%")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\nLast 10 trades:")
    for t in closed[-10:]:
        status = "✅" if t['pnl_pct'] > 0 else "❌"
        print(f"{status} {t['symbol']} {t['direction']}: {t['pnl_pct']:.2f}% ({t['status']})")
    print()
else:
    print("No trades yet")
PYEOF
