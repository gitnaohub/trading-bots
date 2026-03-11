#!/bin/bash
# Monitor bot performance and signal quality

echo "═══════════════════════════════════════════════════════════"
echo "BOT PERFORMANCE MONITOR"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if results file exists
RESULTS_FILE="$HOME/trading/data/scan_results_v3.json"

if [ ! -f "$RESULTS_FILE" ]; then
    echo "❌ No scan results found yet"
    echo "Run a scan first: /scan in Telegram"
    exit 1
fi

# Parse results
QUALIFIED=$(jq '.qualified | length' "$RESULTS_FILE" 2>/dev/null || echo "0")
NEAR_MISSES=$(jq '.near_misses | length' "$RESULTS_FILE" 2>/dev/null || echo "0")
TIMESTAMP=$(jq -r '.timestamp' "$RESULTS_FILE" 2>/dev/null || echo "Unknown")

echo "📊 Latest Scan Results:"
echo "  Time: $TIMESTAMP"
echo "  Qualified Signals: $QUALIFIED"
echo "  Near Misses: $NEAR_MISSES"
echo ""

if [ "$QUALIFIED" -gt 0 ]; then
    echo "🎯 Qualified Signals:"
    jq -r '.qualified[] | "  • \(.symbol) \(.direction) - Score: \(.score)/110"' "$RESULTS_FILE" 2>/dev/null
    echo ""

    # Show score distribution
    echo "📈 Score Distribution:"
    jq -r '.qualified[] | .score' "$RESULTS_FILE" 2>/dev/null | sort -n | while read score; do
        echo "  Score $score: $(printf '█%.0s' $(seq 1 $((score/5))))"
    done
    echo ""
fi

# Check today's log for signal count
LOG_FILE="$HOME/trading/logs/scanner_v3_$(date +%Y%m%d).log"
if [ -f "$LOG_FILE" ]; then
    SIGNAL_COUNT=$(grep -c "Qualified signal" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "📅 Today's Activity:"
    echo "  Total signals found: $SIGNAL_COUNT"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════"
echo "WHAT TO MONITOR:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✓ Signal Frequency: Expect 3-5 per day (was 1-2 per week)"
echo "✓ Score Range: Should see 70-90 (was 75-110)"
echo "✓ Signal Quality: Check if setups look reasonable"
echo "✓ Diversity: Should see different pairs, not just one"
echo ""
echo "Run this script periodically to track performance:"
echo "  ./monitor_performance.sh"
echo ""
