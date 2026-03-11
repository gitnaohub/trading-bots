#!/bin/bash
# Check Status - All Trading Processes

echo "📊 Trading System Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check V3 Bot
if ps aux | grep -v grep | grep "telegram_bot_v3.py" > /dev/null; then
    echo "✅ V3 Bot (Telegram) - Running"
else
    echo "❌ V3 Bot (Telegram) - Not running"
fi

# Check V4 Bot
if ps aux | grep -v grep | grep "telegram_bot_v4.py" > /dev/null; then
    echo "✅ V4 Bot (Telegram) - Running"
else
    echo "❌ V4 Bot (Telegram) - Not running"
fi

# Check Paper Trading Bot
if ps aux | grep -v grep | grep "paper_trading_bot.py" > /dev/null; then
    echo "✅ Paper Trading Bot - Running"
else
    echo "❌ Paper Trading Bot - Not running"
fi

echo ""

# Check V3 Scanner
if ps aux | grep -v grep | grep "mexc_pro_scannerV3.py" > /dev/null; then
    echo "✅ V3 Scanner - Running"
else
    echo "❌ V3 Scanner - Not running"
fi

# Check V4 Scanner
if ps aux | grep -v grep | grep "mexc_pro_scannerV4.py" > /dev/null; then
    echo "✅ V4 Scanner - Running"
else
    echo "❌ V4 Scanner - Not running"
fi

echo ""

# Check Paper Trading Monitors
if ps aux | grep -v grep | grep "paper_trading_monitor_v3.py" > /dev/null; then
    echo "✅ V3 Paper Monitor - Running"
else
    echo "⚠️  V3 Paper Monitor - Not running (needed for tracking)"
fi

if ps aux | grep -v grep | grep "paper_trading_monitor.py" > /dev/null; then
    echo "✅ V4 Paper Monitor - Running"
else
    echo "⚠️  V4 Paper Monitor - Not running (needed for tracking)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if monitors need to be started
if ! ps aux | grep -v grep | grep "paper_trading_monitor" > /dev/null; then
    echo "⚠️  Paper Trading Monitors are NOT running"
    echo ""
    echo "To start tracking signals, run:"
    echo "  cd ~/trading"
    echo "  ./start_both_monitors.sh"
    echo ""
else
    echo "✅ Paper Trading Monitors are running"
    echo ""
    echo "System is tracking signals automatically."
    echo "Check stats in Paper Trading Bot (Telegram)."
    echo ""
fi
