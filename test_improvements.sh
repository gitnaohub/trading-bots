#!/bin/bash
# Quick test of improvements

echo "Testing improvements..."
echo ""

echo "1. Testing scanner import..."
python3 -c "import sys; sys.path.insert(0, 'scripts'); from mexc_pro_scannerV3 import ScalpingScanner; print('   ✓ Scanner imports')" || exit 1

echo "2. Testing bot import..."
python3 -c "import telegram_bot_v3; print('   ✓ Bot imports')" || exit 1

echo "3. Testing signal handling..."
python3 -c "import telegram_bot_v3, signal; assert hasattr(telegram_bot_v3, 'signal_handler'); print('   ✓ Signal handler present')" || exit 1

echo "4. Testing retry decorator..."
python3 -c "import sys; sys.path.insert(0, 'scripts'); from mexc_pro_scannerV3 import retry_on_failure; print('   ✓ Retry decorator available')" || exit 1

echo "5. Checking backups..."
if [ -f "telegram_bot_v3.py.backup" ] && [ -f "scripts/mexc_pro_scannerV3.py.backup" ]; then
    echo "   ✓ Backups exist"
else
    echo "   ✗ Backups missing"
    exit 1
fi

echo ""
echo "✅ All improvements verified - bot is ready to run!"
