# V3 System Maintenance Log
**Date:** 2026-03-11 04:00-04:15 GMT+1

## Problem Discovered
When starting the V3 system, duplicate processes were running:
- **3 scanner processes** (PIDs: 138101, 141828, 142335)
- **2 paper monitor processes** (PIDs: 138102, 141849)
- **2 telegram bot processes** (PIDs: 141458, 141819)

### Root Cause
Services were started twice:
1. First manually with nohup commands
2. Then again via `./start_v3_only.sh` script

This caused resource waste, potential API rate limiting, and possible trade conflicts.

## Fix Applied
Killed duplicate processes:
```bash
kill 138101 138102 141457 141458 142335
```

## Current Clean State (as of 04:15)
Only correct processes from `start_v3_only.sh` are running:
- **Bot wrapper:** PID 141816 (`/bin/bash ./run_telegram_bot_v3.sh`)
- **Bot process:** PID 141819 (`python3 telegram_bot_v3.py`)
- **Scanner:** PID 141828 (`python3 scripts/mexc_pro_scannerV3.py`)
- **Paper Monitor:** PID 141849 (`python3 paper_trading_monitor_v3.py`)

### Verification
- ✅ Scanner: Working, scanning every 60s
- ✅ Paper Monitor: Running (0 open, 974 closed trades)
- ✅ Bot: Connected and polling Telegram API

## How to Check System Health
```bash
# Check running processes
ps aux | grep -E "(mexc_pro_scannerV3|paper_trading_monitor_v3|telegram_bot_v3)" | grep -v grep

# Check logs
tail -f logs/scanner_v3_live.log
tail -f logs/paper_monitor_v3.log

# Should see exactly 4 processes (1 bot wrapper, 1 bot, 1 scanner, 1 monitor)
```

## How to Avoid This Issue
**Choose ONE method to start services:**

### Option 1: Use the start script (RECOMMENDED)
```bash
./start_v3_only.sh
```

### Option 2: Manual start
```bash
cd ~/trading
nohup ./run_telegram_bot_v3.sh > logs/bot_v3.log 2>&1 &
export SCANNER_LIVE_MODE=1 SCAN_INTERVAL=60
nohup python3 scripts/mexc_pro_scannerV3.py > logs/scanner_v3_live.log 2>&1 &
nohup python3 paper_trading_monitor_v3.py > logs/paper_monitor_v3.log 2>&1 &
```

**DO NOT** run both methods - this creates duplicates!

## Notes
- Bot log (bot_v3.log) may be empty - this is normal, the bot logs to stdout
- Bot is confirmed working (polling Telegram API successfully)
- All services started at 04:00 and verified healthy at 04:15
