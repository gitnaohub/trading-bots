#!/bin/bash
# MEXC Bot Starter - Safely start the bot (checks for duplicates first)

echo "═══════════════════════════════════════════════════════════"
echo "MEXC Trading Bot V3 - Safe Starter"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if bot is already running
BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")

if [ ! -z "$BOT_PIDS" ]; then
    echo "⚠️  Bot is ALREADY running (PID: $BOT_PIDS)"
    echo ""
    echo "Options:"
    echo "  1. Stop it first: ./stop_bot.sh"
    echo "  2. Check status: ./check_bot.sh"
    echo ""
    read -p "Stop existing bot and start fresh? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing bot..."
        ./stop_bot.sh
        sleep 2
    else
        echo "Cancelled. Existing bot still running."
        exit 0
    fi
fi

echo "Starting bot..."
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Bot is now running in THIS terminal"
echo "You will see all logs here in real-time"
echo ""
echo "To STOP the bot: Press Ctrl+C"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run bot in foreground (no & at the end)
./run_telegram_bot_v3.sh
