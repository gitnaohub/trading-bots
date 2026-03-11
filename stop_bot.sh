#!/bin/bash
# MEXC Bot Stopper - Gracefully stop the bot

echo "Stopping MEXC Trading Bot V3..."

BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")

if [ -z "$BOT_PIDS" ]; then
    echo "❌ No bot is running"
    exit 0
fi

echo "Found bot process(es): $BOT_PIDS"
echo "Sending graceful shutdown signal (SIGTERM)..."

# Try graceful shutdown first
kill -15 $BOT_PIDS
sleep 3

# Check if still running
BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")
if [ -z "$BOT_PIDS" ]; then
    echo "✅ Bot stopped gracefully"
    exit 0
fi

# If still running, wait a bit more
echo "⏳ Waiting for bot to finish cleanup..."
sleep 2

BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")
if [ -z "$BOT_PIDS" ]; then
    echo "✅ Bot stopped successfully"
    exit 0
fi

# Force kill as last resort
echo "⚠️  Bot not responding, forcing shutdown..."
kill -9 $BOT_PIDS
sleep 1

BOT_PIDS=$(pgrep -f "telegram_bot_v3.py")
if [ -z "$BOT_PIDS" ]; then
    echo "✅ Bot stopped (forced)"
else
    echo "❌ Failed to stop bot: $BOT_PIDS"
    echo "Try manually: kill -9 $BOT_PIDS"
fi
