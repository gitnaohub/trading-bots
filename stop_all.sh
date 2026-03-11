#!/bin/bash
# Stop All Trading Processes

echo "🛑 Stopping All Trading Processes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop scanners
if [ -f ~/trading/data/scanner_v3.pid ]; then
    kill $(cat ~/trading/data/scanner_v3.pid) 2>/dev/null && echo "✅ V3 Scanner stopped"
fi

if [ -f ~/trading/data/scanner_v4.pid ]; then
    kill $(cat ~/trading/data/scanner_v4.pid) 2>/dev/null && echo "✅ V4 Scanner stopped"
fi

# Stop monitors
if [ -f ~/trading/data/paper_monitor_v3.pid ]; then
    kill $(cat ~/trading/data/paper_monitor_v3.pid) 2>/dev/null && echo "✅ V3 Monitor stopped"
fi

if [ -f ~/trading/data/paper_monitor_v4.pid ]; then
    kill $(cat ~/trading/data/paper_monitor_v4.pid) 2>/dev/null && echo "✅ V4 Monitor stopped"
fi

# Stop telegram bots
pkill -f telegram_bot_v3.py 2>/dev/null && echo "✅ V3 Bot stopped"
pkill -f telegram_bot_v4.py 2>/dev/null && echo "✅ V4 Bot stopped"
pkill -f paper_trading_bot.py 2>/dev/null && echo "✅ Paper Bot stopped"

echo ""
echo "✅ All processes stopped"
