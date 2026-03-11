#!/bin/bash
# Compare V4 vs V4.1 scan results

echo "═══════════════════════════════════════════════════════════"
echo "Scanner V4 vs V4.1 Results Comparison"
echo "═══════════════════════════════════════════════════════════"
echo ""

V4_RESULTS="$HOME/trading/data/scan_results_v4.json"
V41_RESULTS="$HOME/trading/data/scan_results_v4.1.json"

if [ ! -f "$V4_RESULTS" ]; then
    echo "❌ V4 results not found"
    echo "   Run V4 scanner first"
    exit 1
fi

if [ ! -f "$V41_RESULTS" ]; then
    echo "❌ V4.1 results not found"
    echo "   Run V4.1 scanner first"
    exit 1
fi

echo "📊 V4 Results:"
echo "   Qualified: $(jq '.qualified_count' $V4_RESULTS)"
echo "   Near Misses: $(jq '.near_misses_count' $V4_RESULTS)"
echo "   Timestamp: $(jq -r '.timestamp' $V4_RESULTS)"
echo ""

echo "📊 V4.1 Results:"
echo "   Qualified: $(jq '.qualified_count' $V41_RESULTS)"
echo "   Near Misses: $(jq '.near_misses_count' $V41_RESULTS)"
echo "   Timestamp: $(jq -r '.timestamp' $V41_RESULTS)"
echo ""

echo "🎯 V4 Signals:"
jq -r '.qualified[] | "   • \(.symbol) \(.direction) - Score: \(.score)/110"' $V4_RESULTS
echo ""

echo "🎯 V4.1 Signals:"
jq -r '.qualified[] | "   • \(.symbol) \(.direction) - Score: \(.score)/110"' $V41_RESULTS
echo ""

echo "═══════════════════════════════════════════════════════════"
