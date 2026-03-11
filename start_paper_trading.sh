#!/bin/bash
# Start Paper Trading Monitor V4

cd ~/trading

if [ -z "$MEXC_API_KEY" ] || [ -z "$MEXC_API_SECRET" ]; then
    echo "❌ MEXC credentials not set"
    echo ""
    echo "Set them first:"
    echo "export MEXC_API_KEY='your_key'"
    echo "export MEXC_API_SECRET='your_secret'"
    echo ""
    exit 1
fi

echo "📊 Starting Paper Trading Monitor V4"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Tracks V4 scanner signals (RSI 20/80)"
echo "✅ Fewer signals, higher quality"
echo "✅ Updates every 10 seconds"
echo ""
echo "⏹️  Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 paper_trading_monitor.py
