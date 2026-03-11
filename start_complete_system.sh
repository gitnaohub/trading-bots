#!/bin/bash
# Start Complete Paper Trading System
# Starts scanners and monitors (bots already running)

cd ~/trading

if [ -z "$MEXC_API_KEY" ] || [ -z "$MEXC_API_SECRET" ]; then
    echo "❌ MEXC credentials not set"
    exit 1
fi

echo "🚀 Starting Complete Paper Trading System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start V3 Scanner
echo "Starting V3 Scanner (RSI 30/70)..."
export SCANNER_LIVE_MODE=1
export SCAN_INTERVAL=60
nohup python3 scripts/mexc_pro_scannerV3.py > logs/scanner_v3_live.log 2>&1 &
V3_SCANNER_PID=$!
echo $V3_SCANNER_PID > data/scanner_v3.pid
echo "✅ V3 Scanner started (PID: $V3_SCANNER_PID)"

sleep 2

# Start V4 Scanner
echo "Starting V4 Scanner (RSI 20/80)..."
nohup python3 scripts/mexc_pro_scannerV4.py > logs/scanner_v4_live.log 2>&1 &
V4_SCANNER_PID=$!
echo $V4_SCANNER_PID > data/scanner_v4.pid
echo "✅ V4 Scanner started (PID: $V4_SCANNER_PID)"

sleep 2

# Start V3 Paper Monitor
echo "Starting V3 Paper Monitor..."
nohup python3 paper_trading_monitor_v3.py > logs/paper_monitor_v3.log 2>&1 &
V3_MONITOR_PID=$!
echo $V3_MONITOR_PID > data/paper_monitor_v3.pid
echo "✅ V3 Paper Monitor started (PID: $V3_MONITOR_PID)"

sleep 2

# Start V4 Paper Monitor
echo "Starting V4 Paper Monitor..."
nohup python3 paper_trading_monitor.py > logs/paper_monitor_v4.log 2>&1 &
V4_MONITOR_PID=$!
echo $V4_MONITOR_PID > data/paper_monitor_v4.pid
echo "✅ V4 Paper Monitor started (PID: $V4_MONITOR_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Complete System Running"
echo ""
echo "📊 V3 Scanner: Scanning every 60s (RSI 30/70)"
echo "📊 V4 Scanner: Scanning every 60s (RSI 20/80)"
echo "📝 V3 Monitor: Tracking V3 signals"
echo "📝 V4 Monitor: Tracking V4 signals"
echo ""
echo "📱 Check Paper Trading Bot in Telegram:"
echo "   - Tap 📊 V3 Stats"
echo "   - Tap 📊 V4 Stats"
echo "   - Tap 📊 All Stats"
echo ""
echo "📋 View logs:"
echo "   V3 Scanner: tail -f logs/scanner_v3_live.log"
echo "   V4 Scanner: tail -f logs/scanner_v4_live.log"
echo "   V3 Monitor: tail -f logs/paper_monitor_v3.log"
echo "   V4 Monitor: tail -f logs/paper_monitor_v4.log"
echo ""
echo "🛑 Stop all:"
echo "   ./stop_all.sh"
echo ""
