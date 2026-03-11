#!/bin/bash
# Comprehensive test of all improvements

echo "═══════════════════════════════════════════════════════════"
echo "Testing All Bot Improvements"
echo "═══════════════════════════════════════════════════════════"
echo ""

FAILED=0

# Test 1: Scanner imports
echo "1. Testing scanner import..."
if python3 -c "import sys; sys.path.insert(0, 'scripts'); from mexc_pro_scannerV3 import ScalpingScanner, retry_on_failure" 2>/dev/null; then
    echo "   ✅ Scanner imports successfully"
else
    echo "   ❌ Scanner import failed"
    FAILED=1
fi

# Test 2: Bot imports
echo "2. Testing bot import..."
if python3 -c "import telegram_bot_v3" 2>/dev/null; then
    echo "   ✅ Bot imports successfully"
else
    echo "   ❌ Bot import failed"
    FAILED=1
fi

# Test 3: Signal handling
echo "3. Testing signal handlers..."
if python3 -c "import telegram_bot_v3, signal; assert hasattr(telegram_bot_v3, 'signal_handler')" 2>/dev/null; then
    echo "   ✅ Signal handlers present"
else
    echo "   ❌ Signal handlers missing"
    FAILED=1
fi

# Test 4: Retry decorator
echo "4. Testing retry decorator..."
if python3 -c "import sys; sys.path.insert(0, 'scripts'); from mexc_pro_scannerV3 import retry_on_failure, ScalpingScanner; assert hasattr(ScalpingScanner.fetch_ohlcv, '__wrapped__')" 2>/dev/null; then
    echo "   ✅ Retry decorator working"
else
    echo "   ❌ Retry decorator not applied"
    FAILED=1
fi

# Test 5: Backups exist
echo "5. Checking backups..."
if [ -f "telegram_bot_v3.py.backup" ] && [ -f "scripts/mexc_pro_scannerV3.py.backup" ]; then
    echo "   ✅ Backups exist"
else
    echo "   ❌ Backups missing"
    FAILED=1
fi

# Test 6: Scripts are executable
echo "6. Checking script permissions..."
if [ -x "start_bot.sh" ] && [ -x "stop_bot.sh" ] && [ -x "cleanup_logs.sh" ]; then
    echo "   ✅ All scripts executable"
else
    echo "   ❌ Some scripts not executable"
    FAILED=1
fi

# Test 7: Helper module
echo "7. Testing helper module..."
if [ -f "check_helpers.py" ]; then
    echo "   ✅ check_helpers.py created"
else
    echo "   ⚠️  check_helpers.py not found (optional)"
fi

# Test 8: Documentation
echo "8. Checking documentation..."
if [ -f "IMPROVEMENTS.md" ]; then
    echo "   ✅ IMPROVEMENTS.md created"
else
    echo "   ⚠️  IMPROVEMENTS.md not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - Bot is ready!"
else
    echo "❌ SOME TESTS FAILED - Check errors above"
fi
echo "═══════════════════════════════════════════════════════════"

exit $FAILED
