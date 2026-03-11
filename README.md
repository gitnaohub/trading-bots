# Trading Bots & Systems

Automated trading bots and monitoring systems for cryptocurrency trading.

## Bots

### V3 Scanner Bot (telegram_bot_v3.py)
- RSI 30/70 scalping strategy
- Perpetual futures support
- Live scanning and notifications
- Paper trading integration

### V4 Scanner Bot (telegram_bot_v4.py)
- RSI 20/80 strategy (higher quality signals)
- Improved filtering
- Paper trading comparison

### Paper Trading Bot (paper_trading_bot.py)
- Dedicated Telegram bot for tracking V3 and V4 performance
- Compare RSI 30/70 vs RSI 20/80 strategies
- View stats, reset data, analyze results

## Monitors

- `paper_trading_monitor_v3.py` - Monitors V3 scanner signals
- `paper_trading.py` - Paper trading tracker library

## Scripts

- `start_paper_bot.sh` - Start paper trading bot
- `start_both_monitors.sh` - Start both V3 and V4 monitors
- `check_status.sh` - Check bot status
- `compare_scanners.sh` - Compare V3 vs V4 performance

## Setup

1. Set environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `PAPER_BOT_TOKEN`
   - `PAPER_CHAT_ID`

2. Install dependencies:
   ```bash
   pip3 install python-telegram-bot requests ccxt
   ```

3. Start bots:
   ```bash
   ./start_paper_bot.sh
   ```

## Data

- `data/paper_trading_v3.json` - V3 paper trades
- `data/paper_trading_v4.json` - V4 paper trades
- `data/scan_results_v3.json` - V3 scan results
- `logs/` - Bot logs

## Features

- Real-time market scanning
- Paper trading simulation
- Performance comparison
- Telegram notifications
- Stats tracking
