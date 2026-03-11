#!/bin/bash
# Start Scanner V4 in foreground (full control, Ctrl+C to stop)

cd ~/trading

echo "═══════════════════════════════════════════════════════════"
echo "MEXC Scanner V4 - BTC/ETH + ATR Stops"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if already running
SCANNER_PIDS=$(pgrep -f "mexc_pro_scannerV4.py")

if [ ! -z "$SCANNER_PIDS" ]; then
    echo "⚠️  Scanner V4 is ALREADY running (PID: $SCANNER_PIDS)"
    echo ""
    read -p "Stop it and start fresh? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing scanner..."
        kill -TERM $SCANNER_PIDS 2>/dev/null
        sleep 2
    else
        echo "Cancelled."
        exit 0
    fi
fi

echo "Starting Scanner V4..."
echo "- Scanning: BTC/ETH only"
echo "- Interval: 60 seconds"
echo "- RSI: 20/80 (strict)"
echo "- Stops: ATR-based"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Scanner running in THIS terminal"
echo "You will see all output here"
echo ""
echo "To STOP: Press Ctrl+C"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run in foreground with live mode enabled
SCANNER_LIVE_MODE=1 python3 scripts/mexc_pro_scannerV4.py
