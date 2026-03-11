#!/bin/bash
# Start Both Paper Trading Monitors (V3 and V4)

cd ~/trading

if [ -z "$MEXC_API_KEY" ] || [ -z "$MEXC_API_SECRET" ]; then
    echo "❌ MEXC credentials not set"
    exit 1
fi

echo "📊 Starting Both Paper Trading Monitors"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will start TWO monitors in background:"
echo "  1. V3 Monitor (RSI 30/70) - Tracks V3 signals"
echo "  2. V4 Monitor (RSI 20/80) - Tracks V4 signals"
echo ""
echo "Both will track signals automatically and update paper trades."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start V3 monitor in background
echo "Starting V3 monitor..."
nohup python3 paper_trading_monitor_v3.py > logs/paper_monitor_v3.log 2>&1 &
V3_PID=$!
echo $V3_PID > data/paper_monitor_v3.pid
echo "✅ V3 Monitor started (PID: $V3_PID)"

# Start V4 monitor in background
echo "Starting V4 monitor..."
nohup python3 paper_trading_monitor.py > logs/paper_monitor_v4.log 2>&1 &
V4_PID=$!
echo $V4_PID > data/paper_monitor_v4.pid
echo "✅ V4 Monitor started (PID: $V4_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Both monitors running in background"
echo ""
echo "📊 They will now track all V3 and V4 signals automatically"
echo "📱 Check stats in Paper Trading Bot (Telegram)"
echo ""
echo "View logs:"
echo "  V3: tail -f ~/trading/logs/paper_monitor_v3.log"
echo "  V4: tail -f ~/trading/logs/paper_monitor_v4.log"
echo ""
echo "Stop monitors:"
echo "  kill $(cat ~/trading/data/paper_monitor_v3.pid)"
echo "  kill $(cat ~/trading/data/paper_monitor_v4.pid)"
echo ""
