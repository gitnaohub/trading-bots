#!/bin/bash
# MEXC Bot Status Checker - See if bot is running

echo "═══════════════════════════════════════════════════════════"
echo "MEXC Trading Bot V3 - Status Check"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check for running bot processes
BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")

if [ -z "$BOT_PIDS" ]; then
    echo "❌ Bot is NOT running"
    echo ""
    echo "To start the bot:"
    echo "  cd ~/trading"
    echo "  ./run_telegram_bot_v3.sh"
    echo ""
else
    echo "✅ Bot is RUNNING"
    echo ""
    echo "Process details:"
    ps aux | grep "telegram_bot_v3.py" | grep -v grep
    echo ""
    echo "To stop the bot:"
    echo "  - If running in terminal: Press Ctrl+C"
    echo "  - If running in background: ./stop_bot.sh"
    echo ""
fi

# Check Telegram connection
CONNECTIONS=$(netstat -tn 2>/dev/null | grep "149.154.166.110:443" | grep ESTABLISHED | wc -l)
if [ "$CONNECTIONS" -gt 0 ]; then
    echo "🌐 Connected to Telegram API ($CONNECTIONS connection(s))"
else
    echo "⚠️  Not connected to Telegram API"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
