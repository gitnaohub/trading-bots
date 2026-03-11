#!/bin/bash
# Start Paper Trading Monitor V3

cd ~/trading

if [ -z "$MEXC_API_KEY" ] || [ -z "$MEXC_API_SECRET" ]; then
    echo "❌ MEXC credentials not set"
    exit 1
fi

echo "📊 Starting Paper Trading Monitor V3"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Tracks V3 scanner signals (RSI 30/70)"
echo "✅ More signals, lower quality"
echo "✅ Updates every 10 seconds"
echo ""
echo "⏹️  Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 paper_trading_monitor_v3.py
