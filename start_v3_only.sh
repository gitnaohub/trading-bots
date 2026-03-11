#!/bin/bash
# Start V3 Bot + Scanner + Paper Trading

cd ~/trading

echo "🚀 Starting V3 System Only"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start V3 Bot
echo "Starting V3 Telegram Bot..."
nohup ./run_telegram_bot_v3.sh > logs/bot_v3.log 2>&1 &
echo $! > data/bot_v3.pid
echo "✅ V3 Bot started (PID: $(cat data/bot_v3.pid))"
sleep 2

# Start V3 Scanner
echo "Starting V3 Scanner..."
export SCANNER_LIVE_MODE=1
export SCAN_INTERVAL=60
nohup python3 scripts/mexc_pro_scannerV3.py > logs/scanner_v3_live.log 2>&1 &
echo $! > data/scanner_v3.pid
echo "✅ V3 Scanner started (PID: $(cat data/scanner_v3.pid))"
sleep 2

# Start V3 Paper Monitor
echo "Starting V3 Paper Monitor..."
nohup python3 paper_trading_monitor_v3.py > logs/paper_monitor_v3.log 2>&1 &
echo $! > data/paper_monitor_v3.pid
echo "✅ V3 Paper Monitor started (PID: $(cat data/paper_monitor_v3.pid))"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ V3 System Running"
echo ""
echo "📊 V3 Scanner: Finding signals every 60s"
echo "📝 V3 Monitor: Tracking paper trades"
echo "📱 V3 Bot: Control via Telegram"
echo ""
echo "View logs:"
echo "  tail -f logs/scanner_v3_live.log"
echo "  tail -f logs/paper_monitor_v3.log"
echo ""
