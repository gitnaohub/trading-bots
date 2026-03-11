#!/bin/bash
# Start MEXC Scanner V4 Telegram Bot

cd ~/trading

# Check if bot is already running
if [ -f data/telegram_bot_v4.pid ]; then
    PID=$(cat data/telegram_bot_v4.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ Bot V4 is already running (PID: $PID)"
        echo "Stop it first with: kill $PID"
        exit 1
    fi
fi

# Check environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Missing environment variables"
    echo "Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
    exit 1
fi

echo "🤖 Starting MEXC Scanner V4 Telegram Bot..."
echo "📱 Chat ID: $TELEGRAM_CHAT_ID"

# Start bot in background
nohup python3 telegram_bot_v4.py > logs/telegram_bot_v4.log 2>&1 &
BOT_PID=$!

# Save PID
mkdir -p data
echo $BOT_PID > data/telegram_bot_v4.pid

echo "✅ Bot started (PID: $BOT_PID)"
echo "📋 Logs: ~/trading/logs/telegram_bot_v4.log"
echo ""
echo "To stop: kill $BOT_PID"
echo "To view logs: tail -f ~/trading/logs/telegram_bot_v4.log"
