#!/bin/bash
# Quick progress check for Phase 1 testing

echo "🤖 Bot Status Check - $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if bot is running
if ps aux | grep -q "[t]elegram_bot_v3"; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is NOT running!"
    exit 1
fi

# Check latest scan results
if [ -f "$HOME/trading/data/scan_results_v3.json" ]; then
    QUALIFIED=$(jq '.qualified_count' "$HOME/trading/data/scan_results_v3.json" 2>/dev/null)
    NEAR_MISSES=$(jq '.near_misses_count' "$HOME/trading/data/scan_results_v3.json" 2>/dev/null)
    TIMESTAMP=$(jq -r '.timestamp' "$HOME/trading/data/scan_results_v3.json" 2>/dev/null)

    echo "📊 Latest Scan: $TIMESTAMP"
    echo "   Qualified: $QUALIFIED"
    echo "   Near Misses: $NEAR_MISSES"

    if [ "$QUALIFIED" -gt 0 ]; then
        echo ""
        echo "🎯 Top Signal:"
        jq -r '.qualified[0] | "   \(.symbol) \(.direction) - Score: \(.score)/110"' "$HOME/trading/data/scan_results_v3.json" 2>/dev/null
    fi
fi

# Count today's qualified signals (score >= 70)
LOG_FILE="$HOME/trading/logs/scanner_v3_$(date +%Y%m%d).log"
if [ -f "$LOG_FILE" ]; then
    SIGNALS_70_PLUS=$(grep "Qualified signal" "$LOG_FILE" | awk -F'Score: ' '{print $2}' | awk -F'/' '{print $1}' | awk '$1 >= 70' | wc -l)
    TOTAL_SCANS=$(grep -c "Scan complete" "$LOG_FILE" 2>/dev/null)

    echo ""
    echo "📈 Today's Stats:"
    echo "   Total scans: $TOTAL_SCANS"
    echo "   Signals (70+): $SIGNALS_70_PLUS"
fi

echo ""
echo "Run './monitor_performance.sh' for detailed analysis"
