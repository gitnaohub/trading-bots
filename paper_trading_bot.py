#!/usr/bin/env python3
"""
Paper Trading Bot - Dedicated Telegram bot for tracking V3 and V4 performance
Monitors both scanners and provides performance statistics
"""

import os
import sys
import json
import time
import requests
import signal
from datetime import datetime

# Add trading directory to path
sys.path.insert(0, os.path.expanduser('~/trading'))
from paper_trading import PaperTradingTracker

# Configuration
BOT_TOKEN = os.getenv('PAPER_BOT_TOKEN')
CHAT_ID = os.getenv('PAPER_CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Error: PAPER_BOT_TOKEN and PAPER_CHAT_ID environment variables must be set")
    sys.exit(1)

# Data files
PAPER_V3_FILE = os.path.expanduser('~/trading/data/paper_trading_v3.json')
PAPER_V4_FILE = os.path.expanduser('~/trading/data/paper_trading_v4.json')

def get_keyboard():
    """Get main keyboard"""
    return {
        'keyboard': [
            ['📊 V3 Stats', '📊 V4 Stats', '📊 All Stats'],
            ['🔄 Reset V3', '🔄 Reset V4', '🔄 Reset All'],
            ['❓ Help']
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }

def send_message(text: str, keyboard: bool = False) -> bool:
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }

        if keyboard:
            payload['reply_markup'] = get_keyboard()

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def cmd_stats_v3(args):
    """Show V3 paper trading stats"""
    try:
        tracker = PaperTradingTracker(PAPER_V3_FILE)
        stats = tracker.get_stats()

        msg = "📊 *V3 Paper Trading Stats*\n\n"

        if stats['total_trades'] == 0:
            msg += "No V3 trades yet.\n\n"
            msg += "V3 scanner uses RSI 30/70 (more signals, lower quality)"
            return msg

        msg += f"*Performance:*\n"
        msg += f"Total: {stats['total_trades']} trades\n"
        msg += f"Win Rate: {stats['win_rate']:.1f}%\n"
        msg += f"Total PnL: {stats['total_pnl_pct']:+.2f}%\n\n"

        msg += f"*Breakdown:*\n"
        msg += f"✅ Wins: {stats['wins']}\n"
        msg += f"❌ Losses: {stats['losses']}\n"
        msg += f"⏱️ Timeouts: {stats['timeouts']}\n\n"

        msg += f"*Averages:*\n"
        msg += f"Win: {stats['avg_win_pct']:+.2f}%\n"
        msg += f"Loss: {stats['avg_loss_pct']:+.2f}%\n"
        msg += f"Hold: {stats['avg_hold_time_min']}min\n\n"

        if tracker.open_trades:
            msg += f"*Open: {len(tracker.open_trades)}*"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_stats_v4(args):
    """Show V4 paper trading stats"""
    try:
        tracker = PaperTradingTracker(PAPER_V4_FILE)
        stats = tracker.get_stats()

        msg = "📊 *V4 Paper Trading Stats*\n\n"

        if stats['total_trades'] == 0:
            msg += "No V4 trades yet.\n\n"
            msg += "V4 scanner uses RSI 20/80 (fewer signals, higher quality)"
            return msg

        msg += f"*Performance:*\n"
        msg += f"Total: {stats['total_trades']} trades\n"
        msg += f"Win Rate: {stats['win_rate']:.1f}%\n"
        msg += f"Total PnL: {stats['total_pnl_pct']:+.2f}%\n\n"

        msg += f"*Breakdown:*\n"
        msg += f"✅ Wins: {stats['wins']}\n"
        msg += f"❌ Losses: {stats['losses']}\n"
        msg += f"⏱️ Timeouts: {stats['timeouts']}\n\n"

        msg += f"*Averages:*\n"
        msg += f"Win: {stats['avg_win_pct']:+.2f}%\n"
        msg += f"Loss: {stats['avg_loss_pct']:+.2f}%\n"
        msg += f"Hold: {stats['avg_hold_time_min']}min\n\n"

        if tracker.open_trades:
            msg += f"*Open: {len(tracker.open_trades)}*"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_stats_all(args):
    """Show combined V3 and V4 stats"""
    try:
        tracker_v3 = PaperTradingTracker(PAPER_V3_FILE)
        tracker_v4 = PaperTradingTracker(PAPER_V4_FILE)

        stats_v3 = tracker_v3.get_stats()
        stats_v4 = tracker_v4.get_stats()

        msg = "📊 *Combined Paper Trading Stats*\n\n"

        # V3 Summary
        msg += f"*V3 (RSI 30/70):*\n"
        if stats_v3['total_trades'] > 0:
            msg += f"Trades: {stats_v3['total_trades']} | "
            msg += f"Win: {stats_v3['win_rate']:.1f}% | "
            msg += f"PnL: {stats_v3['total_pnl_pct']:+.2f}%\n\n"
        else:
            msg += "No trades yet\n\n"

        # V4 Summary
        msg += f"*V4 (RSI 20/80):*\n"
        if stats_v4['total_trades'] > 0:
            msg += f"Trades: {stats_v4['total_trades']} | "
            msg += f"Win: {stats_v4['win_rate']:.1f}% | "
            msg += f"PnL: {stats_v4['total_pnl_pct']:+.2f}%\n\n"
        else:
            msg += "No trades yet\n\n"

        # Combined totals
        total_trades = stats_v3['total_trades'] + stats_v4['total_trades']
        if total_trades > 0:
            total_wins = stats_v3['wins'] + stats_v4['wins']
            total_pnl = stats_v3['total_pnl_pct'] + stats_v4['total_pnl_pct']
            combined_wr = (total_wins / total_trades * 100)

            msg += f"*Combined:*\n"
            msg += f"Total: {total_trades} trades\n"
            msg += f"Win Rate: {combined_wr:.1f}%\n"
            msg += f"Total PnL: {total_pnl:+.2f}%\n\n"

            msg += f"*Comparison:*\n"
            if stats_v3['total_trades'] > 0 and stats_v4['total_trades'] > 0:
                if stats_v4['win_rate'] > stats_v3['win_rate']:
                    msg += "✅ V4 has higher win rate\n"
                else:
                    msg += "✅ V3 has higher win rate\n"

                if stats_v4['total_pnl_pct'] > stats_v3['total_pnl_pct']:
                    msg += "✅ V4 has higher PnL"
                else:
                    msg += "✅ V3 has higher PnL"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_reset_v3(args):
    """Reset V3 paper trading"""
    try:
        tracker = PaperTradingTracker(PAPER_V3_FILE)
        stats = tracker.get_stats()
        tracker.reset()

        msg = "🔄 *V3 Paper Trading Reset*\n\n"
        if stats['total_trades'] > 0:
            msg += f"Cleared {stats['total_trades']} trades\n"
            msg += f"Previous: {stats['win_rate']:.1f}% WR, {stats['total_pnl_pct']:+.2f}% PnL"
        else:
            msg += "No data to clear"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_reset_v4(args):
    """Reset V4 paper trading"""
    try:
        tracker = PaperTradingTracker(PAPER_V4_FILE)
        stats = tracker.get_stats()
        tracker.reset()

        msg = "🔄 *V4 Paper Trading Reset*\n\n"
        if stats['total_trades'] > 0:
            msg += f"Cleared {stats['total_trades']} trades\n"
            msg += f"Previous: {stats['win_rate']:.1f}% WR, {stats['total_pnl_pct']:+.2f}% PnL"
        else:
            msg += "No data to clear"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_reset_all(args):
    """Reset both V3 and V4 paper trading"""
    try:
        tracker_v3 = PaperTradingTracker(PAPER_V3_FILE)
        tracker_v4 = PaperTradingTracker(PAPER_V4_FILE)

        stats_v3 = tracker_v3.get_stats()
        stats_v4 = tracker_v4.get_stats()

        tracker_v3.reset()
        tracker_v4.reset()

        total = stats_v3['total_trades'] + stats_v4['total_trades']

        msg = "🔄 *All Paper Trading Reset*\n\n"
        msg += f"Cleared {total} total trades\n"
        msg += f"V3: {stats_v3['total_trades']} trades\n"
        msg += f"V4: {stats_v4['total_trades']} trades"

        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_help(args):
    """Show help"""
    return """*Paper Trading Bot*

Track V3 and V4 scanner performance with paper trading.

*Commands:*
/start - Start bot and show menu
/v3 - V3 stats (RSI 30/70)
/v4 - V4 stats (RSI 20/80)
/all - Combined stats
/reset_v3 - Reset V3 data
/reset_v4 - Reset V4 data
/reset_all - Reset all data
/help - This help

*Buttons:*
📊 V3/V4/All Stats - View performance
🔄 Reset - Clear data

*How it works:*
1. Paper trading monitors watch scanners
2. Each signal creates paper trade
3. Trades close at stop/target/timeout
4. Stats calculate win rate and PnL

*Compare V3 vs V4:*
• V3: RSI 30/70 (more signals)
• V4: RSI 20/80 (fewer, higher quality)

Run both for 24h and compare results.
"""

def cmd_start(args):
    """Start command"""
    return """📊 *Paper Trading Bot*

Welcome! This bot tracks V3 and V4 scanner performance.

*Quick Start:*
• Use buttons below to view stats
• Compare RSI 30/70 (V3) vs RSI 20/80 (V4)
• Reset data anytime to start fresh

*Available Commands:*
/v3 - V3 stats
/v4 - V4 stats
/all - Combined stats
/help - Full help

Use the buttons for easy access! 👇"""

COMMANDS = {
    '/start': cmd_start,
    '/v3': cmd_stats_v3,
    '/v4': cmd_stats_v4,
    '/all': cmd_stats_all,
    '/reset_v3': cmd_reset_v3,
    '/reset_v4': cmd_reset_v4,
    '/reset_all': cmd_reset_all,
    '/help': cmd_help,
    '📊 v3 stats': cmd_stats_v3,
    '📊 v4 stats': cmd_stats_v4,
    '📊 all stats': cmd_stats_all,
    '🔄 reset v3': cmd_reset_v3,
    '🔄 reset v4': cmd_reset_v4,
    '🔄 reset all': cmd_reset_all,
    '❓ help': cmd_help,
}

def process_command(text: str) -> tuple:
    """Process command"""
    cmd = text.lower().strip()

    if cmd in COMMANDS:
        try:
            return (COMMANDS[cmd]([]), True)
        except Exception as e:
            return (f"❌ Error: {e}", False)

    parts = text.strip().split()
    if parts:
        cmd = parts[0].lower()
        if cmd in COMMANDS:
            try:
                return (COMMANDS[cmd](parts[1:]), True)
            except Exception as e:
                return (f"❌ Error: {e}", False)

    return ("❌ Unknown command. Use /help", False)

def signal_handler(signum, frame):
    """Handle shutdown"""
    print("\n⏹️  Paper trading bot stopped")
    send_message("🛑 *Paper Trading Bot Stopped*")
    sys.exit(0)

def main():
    """Main bot loop"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Credentials not set")
        sys.exit(1)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("📊 Paper Trading Bot Started")
    print(f"📱 Chat ID: {CHAT_ID}")
    print("✅ Listening for commands...")
    print("")

    send_message("📊 *Paper Trading Bot Started*\n\nTrack V3 and V4 performance.\n\nUse buttons or /help", keyboard=True)

    last_update_id = 0
    error_count = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 30}

            response = requests.get(url, params=params, timeout=35)

            if response.status_code != 200:
                error_count += 1
                time.sleep(min(5 * error_count, 60))
                continue

            error_count = 0
            data = response.json()

            if not data.get('ok'):
                continue

            updates = data.get('result', [])

            for update in updates:
                last_update_id = update['update_id']

                if 'message' in update:
                    message = update['message']
                    chat_id = str(message['chat']['id'])

                    if chat_id != CHAT_ID:
                        continue

                    text = message.get('text', '')
                    print(f"💬 Command: {text}")

                    if text:
                        response_text, show_keyboard = process_command(text)
                        send_message(response_text, keyboard=show_keyboard)

        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"Error: {e}")
            error_count += 1
            time.sleep(min(10 * error_count, 60))

if __name__ == "__main__":
    main()
