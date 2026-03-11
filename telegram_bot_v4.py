#!/usr/bin/env python3
"""
MEXC Scanner V4 - Telegram Bot Controller
BTC/ETH scalping with RSI 20/80 and ATR stops (Research-validated)
"""

import os
import sys
import json
import time
import requests
import subprocess
import threading
import signal
from datetime import datetime
from pathlib import Path

# Scanner import disabled - causing bot to hang at startup
# TODO: Re-implement check command without blocking import
SCANNER_AVAILABLE = False

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
SCANNER_SCRIPT = os.path.expanduser('~/trading/scripts/mexc_pro_scannerV4.py')
RESULTS_JSON = os.path.expanduser('~/trading/data/scan_results_v4.json')
STATE_FILE = os.path.expanduser('~/trading/data/bot_state_v4.json')

# Bot state
class BotState:
    def __init__(self):
        self.live_mode = False
        self.scan_interval = 60
        self.min_threshold = 70  # V4 uses 70/110 minimum (RSI 20/80 stricter)
        self.notifications_enabled = True
        self.time_filter_enabled = True  # 12:00-18:00 UTC filter (optimal hours)
        self.last_scan_time = None
        self.last_signal_time = None
        self.scan_thread = None
        self.stop_flag = False
        self.focus_pairs = []
        self.load_state()

    def load_state(self):
        """Load state from file"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.scan_interval = data.get('scan_interval', 60)
                    self.min_threshold = data.get('min_threshold', 70)
                    self.notifications_enabled = data.get('notifications_enabled', True)
                    self.time_filter_enabled = data.get('time_filter_enabled', True)
                    self.last_signal_time = data.get('last_signal_time', None)
                    self.focus_pairs = data.get('focus_pairs', [])
        except Exception as e:
            print(f"Error loading state: {e}")

    def save_state(self):
        """Save state to file"""
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'scan_interval': self.scan_interval,
                    'min_threshold': self.min_threshold,
                    'notifications_enabled': self.notifications_enabled,
                    'time_filter_enabled': self.time_filter_enabled,
                    'last_scan_time': self.last_scan_time,
                    'last_signal_time': self.last_signal_time,
                    'focus_pairs': self.focus_pairs
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

state = BotState()

def get_main_keyboard():
    """Get main reply keyboard"""
    return {
        'keyboard': [
            ['📊 Scan', '▶️ Start', '⏹️ Stop'],
            ['📈 Status', '🎯 Signals', '🔍 Check'],
            ['⏰ Hours', '💹 Market', '📄 Paper'],
            ['⚙️ Settings', '❓ Help']
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }

def send_message(text: str, parse_mode: str = 'Markdown', keyboard: bool = False, inline_keyboard: dict = None) -> bool:
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': parse_mode
        }

        if keyboard:
            payload['reply_markup'] = get_main_keyboard()
        elif inline_keyboard:
            payload['reply_markup'] = inline_keyboard

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print(f"❌ Telegram API error: {response.status_code}")
            print(f"Response: {response.text}")

        return response.status_code == 200
    except (requests.RequestException, requests.Timeout, ConnectionError) as e:
        print(f"Error sending message: {e}")
        return False

def run_single_scan(force_scan=False) -> dict:
    """Run a single scan and return results

    Args:
        force_scan: If True, temporarily disable time filter for this scan
    """
    try:
        env = os.environ.copy()
        env['SCANNER_LIVE_MODE'] = '0'
        env['MEXC_API_KEY'] = os.getenv('MEXC_API_KEY', '')
        env['MEXC_API_SECRET'] = os.getenv('MEXC_API_SECRET', '')

        # Temporarily disable time filter if force_scan or if user disabled it
        if force_scan or not state.time_filter_enabled:
            # Read scanner file and temporarily modify USE_TRADING_HOURS_FILTER
            scanner_backup = None
            try:
                with open(SCANNER_SCRIPT, 'r') as f:
                    scanner_content = f.read()
                    scanner_backup = scanner_content

                # Temporarily set filter to False
                modified_content = scanner_content.replace(
                    'USE_TRADING_HOURS_FILTER = True',
                    'USE_TRADING_HOURS_FILTER = False'
                )

                with open(SCANNER_SCRIPT, 'w') as f:
                    f.write(modified_content)
            except Exception as e:
                print(f"Warning: Could not modify time filter: {e}")

        result = subprocess.run(
            ['python3', SCANNER_SCRIPT],
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Restore scanner file if we modified it
        if scanner_backup and (force_scan or not state.time_filter_enabled):
            try:
                with open(SCANNER_SCRIPT, 'w') as f:
                    f.write(scanner_backup)
            except Exception as e:
                print(f"Warning: Could not restore scanner: {e}")

        state.last_scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state.save_state()

        if os.path.exists(RESULTS_JSON):
            with open(RESULTS_JSON, 'r') as f:
                results = json.load(f)
                # Update last signal time if signals found
                if results.get('qualified'):
                    state.last_signal_time = state.last_scan_time
                    state.save_state()
                return results
        return {}
    except subprocess.TimeoutExpired:
        print(f"Scanner timeout after 120s")
        return {'error': 'Scanner timeout'}
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Error running scan: {e}")
        return {'error': str(e)}
    except json.JSONDecodeError as e:
        print(f"Error parsing scan results: {e}")
        return {'error': 'Invalid scan results'}

def live_scan_loop():
    """Background thread for live scanning"""
    while not state.stop_flag:
        try:
            results = run_single_scan()

            if 'qualified' in results and results['qualified']:
                signals = results['qualified']

                if state.focus_pairs:
                    signals = filter_signals_by_focus(signals)

                if signals:
                    focus_msg = f" (Focus: {', '.join(state.focus_pairs)})" if state.focus_pairs else ""
                    msg = f"🚨 *SCALPING ALERT*{focus_msg}\n\n"
                    msg += f"Found {len(signals)} qualified signal(s):\n\n"

                    for i, sig in enumerate(signals[:3], 1):
                        score = sig['score']
                        icon = "🔥" if score >= 85 else "⚡" if score >= 75 else "💡"
                        dir_icon = "🟢" if sig['direction'] == 'LONG' else "🔴"

                        msg += f"*#{i} {icon} {sig['symbol']}*\n"
                        msg += f"{dir_icon} {sig['direction']} | Score: {score}/110\n"
                        msg += f"💰 Entry: ${sig['entry_price']:.4f}\n"
                        msg += f"🛑 Stop: ${sig['risk_params']['stop_loss']:.4f}\n"
                        msg += f"🎯 Target: ${sig['risk_params']['target']:.4f}\n"
                        msg += f"⏱️ Max: {sig['risk_params']['max_hold_minutes']}min\n\n"

                    send_message(msg)

            for _ in range(state.scan_interval):
                if state.stop_flag:
                    break
                time.sleep(1)
        except Exception as e:
            send_message(f"❌ Error in live scan: {e}")
            break

    state.live_mode = False
    send_message("⏹️ Live scanning stopped")

def filter_signals_by_focus(signals):
    """Filter signals by focused pairs"""
    if not state.focus_pairs:
        return signals
    return [sig for sig in signals if sig['symbol'] in state.focus_pairs]

def cmd_scan(args):
    """Run single scan"""
    send_message("🔍 Starting scalping scan...")
    results = run_single_scan()

    if 'error' in results:
        return f"❌ Scan failed: {results['error']}"

    qualified = results.get('qualified', [])
    near_misses = results.get('near_misses', [])

    if state.focus_pairs:
        original_qualified = len(qualified)
        original_near_misses = len(near_misses)
        qualified = filter_signals_by_focus(qualified)
        near_misses = filter_signals_by_focus(near_misses)
        focus_info = f"\n🎯 Focus: {', '.join(state.focus_pairs)}\n"
        focus_info += f"Qualified: {len(qualified)}/{original_qualified} | Near misses: {len(near_misses)}/{original_near_misses}\n"
    else:
        focus_info = ""

    msg = f"✅ Scan complete{focus_info}\n"

    if qualified:
        msg += f"🎯 Found {len(qualified)} qualified signal(s):\n\n"
        for i, sig in enumerate(qualified[:3], 1):
            score = sig['score']
            icon = "🔥" if score >= 85 else "⚡"
            dir_icon = "🟢" if sig['direction'] == 'LONG' else "🔴"

            msg += f"*#{i} {icon} {sig['symbol']}*\n"
            msg += f"{dir_icon} {sig['direction']} | Score: {score}/110\n"
            msg += f"💰 Entry: ${sig['entry_price']:.4f}\n"
            msg += f"🛑 Stop: ${sig['risk_params']['stop_loss']:.4f} (0.5%)\n"
            msg += f"🎯 Target: ${sig['risk_params']['target']:.4f} (1.0%)\n"
            msg += f"⏱️ Max: {sig['risk_params']['max_hold_minutes']}min\n\n"
    else:
        msg += "📊 No qualified signals found\n\n"

    if near_misses:
        msg += f"\n👀 *Near Misses* ({len(near_misses)}) - Watch These:\n\n"
        for i, sig in enumerate(near_misses[:5], 1):
            score = sig['score']
            dir_icon = "🟢" if sig['direction'] == 'LONG' else "🔴"
            
            msg += f"*#{i} {sig['symbol']}*\n"
            msg += f"{dir_icon} {sig['direction']} | Score: {score}/110\n"
            msg += f"💰 Entry: ${sig['entry_price']:.4f}\n"
            
            # Show what's missing
            checks = sig.get('confluence_checks', {})
            missing = []
            if not checks.get('timeframe_alignment'):
                missing.append("TF align")
            if not checks.get('stochastic_extreme'):
                missing.append("Stoch")
            if not checks.get('volume_strong'):
                missing.append("Volume")
            if not checks.get('near_vwap'):
                missing.append("VWAP")
            
            if missing:
                msg += f"⚠️ Missing: {', '.join(missing)}\n"
            
            msg += "\n"

    return msg

def cmd_start_live(args):
    """Start live scanning"""
    if state.live_mode:
        return "⚠️ Live mode already running"

    state.live_mode = True
    state.stop_flag = False
    state.scan_thread = threading.Thread(target=live_scan_loop, daemon=True)
    state.scan_thread.start()

    return f"🔄 Live scalping scanner started\n📊 Interval: {state.scan_interval}s\n\nUse /stop_live to stop"

def cmd_stop_live(args):
    """Stop live scanning"""
    if not state.live_mode:
        return "⚠️ Live mode not running"

    state.stop_flag = True
    return "⏹️ Stopping live mode..."

def cmd_interval(args):
    """Change scan interval"""
    if not args:
        return f"Current interval: {state.scan_interval}s\n\nUsage: /interval <seconds>"

    try:
        interval = int(args[0])
        if interval < 30:
            return "❌ Minimum interval is 30 seconds (API limits)"
        if interval > 3600:
            return "❌ Maximum interval is 3600 seconds"

        state.scan_interval = interval
        state.save_state()
        return f"✅ Scan interval set to {interval}s"
    except ValueError:
        return "❌ Invalid number"

def cmd_settings(args):
    """Show settings and how to change them"""
    mode = "🔄 LIVE" if state.live_mode else "⏸️ IDLE"
    focus_status = f"{len(state.focus_pairs)} pair(s)" if state.focus_pairs else "BTC/ETH"
    hours_status = "12:00-18:00 UTC" if state.time_filter_enabled else "24/7"

    msg = f"*⚙️ Bot Settings*\n\n"
    msg += f"*Current Configuration:*\n"
    msg += f"• Scan Interval: {state.scan_interval}s\n"
    msg += f"• Min Score: {state.min_threshold}/110\n"
    msg += f"• Focus: {focus_status}\n"
    msg += f"• Trading Hours: {hours_status}\n"
    msg += f"• Notifications: {'✅ ON' if state.notifications_enabled else '🔕 OFF'}\n"
    msg += f"• Mode: {mode}\n\n"

    msg += f"*Change Settings:*\n"
    msg += f"• `/interval <seconds>` - Change scan interval\n"
    msg += f"• `/threshold <score>` - Change min score (60-110)\n"
    msg += f"• `/toggle_hours` - Toggle 12-18 UTC / 24/7\n"
    msg += f"• `/mute` - Disable notifications\n"
    msg += f"• `/unmute` - Enable notifications\n\n"

    msg += f"*Examples:*\n"
    msg += f"• `/interval 120` - Scan every 2 minutes\n"
    msg += f"• `/threshold 75` - Only show 75+ scores\n"
    msg += f"• `/toggle_hours` - Scan 24/7 or optimal hours\n"

    return msg


def cmd_status(args):
    """Show bot status"""
    mode = "🔄 LIVE" if state.live_mode else "⏸️ IDLE"
    last_scan = state.last_scan_time or "Never"
    last_signal = state.last_signal_time or "No signals yet"
    focus_status = f"{len(state.focus_pairs)} pair(s)" if state.focus_pairs else "BTC/ETH"
    hours_status = "12:00-18:00 UTC ⏰" if state.time_filter_enabled else "24/7 🌍"

    msg = f"*📈 Scanner Status*\n\n"
    msg += f"Mode: {mode}\n"
    msg += f"Interval: {state.scan_interval}s\n"
    msg += f"Min Score: {state.min_threshold}/110\n"
    msg += f"Focus: {focus_status}\n"
    msg += f"Hours: {hours_status}\n"
    msg += f"Notifications: {'✅ ON' if state.notifications_enabled else '🔕 OFF'}\n"
    msg += f"Last Scan: {last_scan}\n"
    msg += f"Last Signal: {last_signal}\n"

    return msg

def cmd_signals(args):
    """Show latest signals"""
    if not os.path.exists(RESULTS_JSON):
        return "📊 No scan results available\n\nRun /scan first"

    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)

        qualified = results.get('qualified', [])
        if not qualified:
            return "📊 No qualified signals in last scan"

        msg = f"📊 *Latest Signals* (Top 3)\n\n"
        for i, sig in enumerate(qualified[:3], 1):
            score = sig['score']
            icon = "🔥" if score >= 85 else "⚡"
            dir_icon = "🟢" if sig['direction'] == 'LONG' else "🔴"
            
            msg += f"*#{i} {icon} {sig['symbol']}*\n"
            msg += f"{dir_icon} {sig['direction']} | Score: {score}/110\n"
            msg += f"💰 Entry: ${sig['entry_price']:.4f}\n"
            msg += f"🛑 Stop: ${sig['risk_params']['stop_loss']:.4f}\n"
            msg += f"🎯 Target: ${sig['risk_params']['target']:.4f}\n\n"

        return msg
    except Exception as e:
        return f"❌ Error reading results: {e}"

def cmd_threshold(args):
    """Change minimum score threshold"""
    if not args:
        return f"Current threshold: {state.min_threshold}/110\n\nUsage: /threshold <score>"

    try:
        threshold = int(args[0])
        if threshold < 60 or threshold > 110:
            return "❌ Threshold must be between 60 and 110"

        state.min_threshold = threshold
        state.save_state()
        return f"✅ Minimum score threshold set to {threshold}/110"
    except ValueError:
        return "❌ Invalid number"

def cmd_focus(args):
    """Add pair to focus list"""
    # If no args, show last 5 opportunities to choose from
    if not args:
        if state.focus_pairs:
            msg = f"🎯 *Current Focus*\n" + "\n".join(f"  • {p}" for p in state.focus_pairs) + "\n\n"
        else:
            msg = "🎯 No focus set\n\n"
        
        # Try to load last scan results
        if os.path.exists(RESULTS_JSON):
            try:
                with open(RESULTS_JSON, 'r') as f:
                    results = json.load(f)
                
                qualified = results.get('qualified', [])
                if qualified:
                    msg += "*Last 5 Opportunities:*\n\n"
                    for i, sig in enumerate(qualified[:5], 1):
                        score = sig['score']
                        dir_icon = "🟢" if sig['direction'] == 'LONG' else "🔴"
                        msg += f"{i}. {sig['symbol']} {dir_icon} ({score}/110)\n"
                    
                    msg += f"\n*To focus on a pair:*\n"
                    msg += f"• Type number: `/focus 1` or `/focus 1,2,3`\n"
                    msg += f"• Type symbol: `/focus BTC/USDT:USDT`"
                    return msg
            except Exception as e:
                pass
        
        msg += "Run /scan first to see opportunities\n\n"
        msg += "Usage: `/focus <symbol>` or `/focus <number>`"
        return msg
    
    # Check if arg is a number (selecting from last scan)
    arg = args[0]
    
    # Handle comma-separated numbers (e.g., "1,2,3")
    if ',' in arg:
        try:
            numbers = [int(n.strip()) for n in arg.split(',')]
            return add_focus_by_numbers(numbers)
        except ValueError:
            pass
    
    # Handle single number
    try:
        number = int(arg)
        return add_focus_by_numbers([number])
    except ValueError:
        pass
    
    # Handle symbol (existing behavior)
    symbol = arg.upper()
    if not ':USDT' in symbol:
        if not symbol.endswith('/USDT'):
            symbol += '/USDT'
        symbol += ':USDT'

    if symbol in state.focus_pairs:
        return f"⚠️ {symbol} already in focus list"

    state.focus_pairs.append(symbol)
    state.save_state()
    return f"✅ Added {symbol} to focus\n\n🎯 Focus list:\n" + "\n".join(f"  • {p}" for p in state.focus_pairs)

def add_focus_by_numbers(numbers):
    """Add pairs to focus by their number in last scan results"""
    if not os.path.exists(RESULTS_JSON):
        return "❌ No scan results available\n\nRun /scan first"
    
    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        
        qualified = results.get('qualified', [])
        if not qualified:
            return "❌ No signals in last scan"
        
        added = []
        for num in numbers:
            if num < 1 or num > len(qualified):
                continue
            
            sig = qualified[num - 1]
            symbol = sig['symbol']
            
            if symbol not in state.focus_pairs:
                state.focus_pairs.append(symbol)
                added.append(symbol)
        
        if not added:
            return "⚠️ No new pairs added (already in focus or invalid numbers)"
        
        state.save_state()
        
        msg = f"✅ Added {len(added)} pair(s) to focus:\n"
        for sym in added:
            msg += f"  • {sym}\n"
        
        msg += f"\n🎯 *Total Focus* ({len(state.focus_pairs)}):\n"
        msg += "\n".join(f"  • {p}" for p in state.focus_pairs)
        
        return msg
    except Exception as e:
        return f"❌ Error: {e}"

def cmd_unfocus(args):
    """Remove pair from focus list"""
    if not args:
        return "Usage: /unfocus <symbol>\n\nOr use /clear_focus to remove all"

    symbol = args[0].upper()
    if not ':USDT' in symbol:
        if not symbol.endswith('/USDT'):
            symbol += '/USDT'
        symbol += ':USDT'

    if symbol not in state.focus_pairs:
        return f"⚠️ {symbol} not in focus list"

    state.focus_pairs.remove(symbol)
    state.save_state()

    if state.focus_pairs:
        return f"✅ Removed {symbol}\n\n🎯 Focus list:\n" + "\n".join(f"  • {p}" for p in state.focus_pairs)
    else:
        return f"✅ Removed {symbol}\n\n🎯 Focus cleared (scanning all pairs)"

def cmd_clear_focus(args):
    """Clear all focused pairs"""
    if not state.focus_pairs:
        return "🎯 No focus set"

    count = len(state.focus_pairs)
    state.focus_pairs = []
    state.save_state()
    return f"✅ Cleared {count} pair(s) from focus\n\n🎯 Now scanning all pairs"

def cmd_focus_list(args):
    """Show focus list"""
    if not state.focus_pairs:
        return "🎯 No focus set (scanning all pairs)\n\nUse /focus <symbol> to add pairs"

    return "🎯 *Focus List*\n\n" + "\n".join(f"  • {p}" for p in state.focus_pairs) + f"\n\n({len(state.focus_pairs)} pair(s))"

def cmd_mute(args):
    """Mute notifications"""
    state.notifications_enabled = False
    state.save_state()
    return "🔕 Notifications muted\n\nBot will still respond to commands"

def cmd_unmute(args):
    """Unmute notifications"""
    state.notifications_enabled = True
    state.save_state()
    return "🔔 Notifications enabled"

def cmd_toggle_hours(args):
    """Toggle trading hours filter (12:00-18:00 UTC vs 24/7)"""
    state.time_filter_enabled = not state.time_filter_enabled
    state.save_state()

    print(f"⏰ Hours toggled to: {'12-18 UTC' if state.time_filter_enabled else '24/7'}")

    if state.time_filter_enabled:
        return ("⏰ *Trading Hours: 12:00-18:00 UTC*\n\n"
                "✅ Scanner will only scan during optimal hours\n"
                "📊 Peak liquidity window (US/EU overlap)\n"
                "💡 Best for quality signals\n\n"
                "Tap ⏰ Hours again to scan 24/7")
    else:
        return ("🌍 *Trading Hours: 24/7*\n\n"
                "✅ Scanner will scan at all hours\n"
                "⚠️ Lower liquidity outside 12:00-18:00 UTC\n"
                "💡 More signals but lower quality\n\n"
                "Tap ⏰ Hours again for optimal hours only")

def cmd_market(args):
    """Show quick market overview for BTC/ETH"""
    try:
        import sys
        scripts_path = os.path.expanduser('~/trading/scripts')
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        from mexc_pro_scannerV4 import ScalpingScanner
        import logging
        logger = logging.getLogger('market_command')
        logger.setLevel(logging.ERROR)

        scanner = ScalpingScanner(logger)

        msg = "💹 *Market Overview*\n\n"

        for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
            try:
                ticker = scanner.exchange.fetch_ticker(symbol)
                ohlcv_1h = scanner.exchange.fetch_ohlcv(symbol, '1h', limit=24)

                if not ticker or not ohlcv_1h:
                    continue

                price = ticker.get('last', 0)
                volume_24h = ticker.get('quoteVolume', 0)
                change_24h = ticker.get('percentage', 0)

                # Calculate 1h trend
                prices_1h = [x[4] for x in ohlcv_1h]
                trend_1h = "📈" if prices_1h[-1] > prices_1h[0] else "📉"

                # High/Low 24h
                high_24h = ticker.get('high', 0)
                low_24h = ticker.get('low', 0)

                coin = symbol.split('/')[0]
                msg += f"*{coin}*\n"
                msg += f"Price: ${price:,.2f}\n"
                msg += f"24h: {change_24h:+.2f}% {trend_1h}\n"
                msg += f"Vol: ${volume_24h/1e6:.1f}M\n"
                msg += f"Range: ${low_24h:,.2f} - ${high_24h:,.2f}\n\n"

            except Exception as e:
                msg += f"*{symbol.split('/')[0]}*\n❌ Error fetching data\n\n"

        # Add current UTC time
        current_utc = datetime.utcnow().strftime('%H:%M UTC')
        msg += f"🕐 Current: {current_utc}\n"

        # Trading hours status
        current_hour = datetime.utcnow().hour
        if 12 <= current_hour < 18:
            msg += "✅ Optimal trading hours"
        else:
            msg += f"⏰ Optimal hours: 12:00-18:00 UTC"

        return msg

    except Exception as e:
        return f"❌ Error fetching market data: {e}"

def cmd_check(args):
    """Check/analyze a specific pair for position management - ALWAYS provides analysis"""
    if not args:
        # Show inline keyboard with BTC/ETH options
        inline_keyboard = {
            'inline_keyboard': [
                [
                    {'text': '₿ BTC', 'callback_data': '/check BTC'},
                    {'text': 'Ξ ETH', 'callback_data': '/check ETH'}
                ]
            ]
        }

        msg = ("*🔍 Check Position*\n\n"
               "Select a pair to analyze:\n\n"
               "Or type:\n"
               "`/check BTC` or `/check ETH`")

        send_message(msg, inline_keyboard=inline_keyboard)
        return None  # Already sent message with inline keyboard
    
    # Parse the argument
    arg = args[0].upper()
    
    # Check if it's a number (referring to last scan results)
    try:
        number = int(arg)
        if not os.path.exists(RESULTS_JSON):
            return "❌ No scan results available\n\nRun /scan first or use /check <symbol>"
        
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        
        all_signals = results.get('qualified', []) + results.get('near_misses', [])
        if number < 1 or number > len(all_signals):
            return f"❌ Invalid number. Last scan had {len(all_signals)} signals."
        
        symbol = all_signals[number - 1]['symbol']
    except ValueError:
        # It's a symbol, not a number
        symbol = arg
        if not ':USDT' in symbol:
            if not symbol.endswith('/USDT'):
                symbol += '/USDT'
            symbol += ':USDT'
    
    # Try to use scanner directly for deep analysis (lazy import)
    send_message(f"🔍 Analyzing {symbol}...\n⏳ Fetching data from MEXC...")
    
    try:
        # Lazy import - only load scanner when needed
        import sys
        scripts_path = os.path.expanduser('~/trading/scripts')
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        from mexc_pro_scannerV4 import ScalpingScanner, Config as ScannerConfig
        import logging
        logger = logging.getLogger('check_command')
        logger.setLevel(logging.ERROR)  # Suppress scanner logs
        
        scanner = ScalpingScanner(logger)
        
        # Fetch ticker to get current price and volume
        ticker = scanner.exchange.fetch_ticker(symbol)
        if not ticker:
            return f"❌ Could not fetch data for {symbol}\n\nMake sure the symbol is correct."
        
        pair_info = {
            'symbol': symbol,
            'volume_usd': ticker.get('quoteVolume', 0),
            'spread_pct': 0,  # Not critical for analysis
            'last_price': ticker.get('last', 0)
        }
        
        # Analyze the pair directly
        signal = scanner.analyze_pair(pair_info)
        
        if not signal:
            # Pair exists but couldn't get full analysis - provide basic analysis
            try:
                # Fetch OHLCV data for basic analysis
                ohlcv_1h = scanner.exchange.fetch_ohlcv(symbol, '1h', limit=24)
                ohlcv_15m = scanner.exchange.fetch_ohlcv(symbol, '15m', limit=20)
                
                if not ohlcv_1h or not ohlcv_15m:
                    return (f"📊 *{symbol}*\n\n"
                           f"❌ Could not fetch price data.\n\n"
                           f"Current Price: ${pair_info['last_price']:.4f}\n"
                           f"24h Volume: ${pair_info['volume_usd']:,.0f}")
                
                # Calculate basic metrics
                current_price = pair_info['last_price']
                prices_1h = [x[4] for x in ohlcv_1h]  # Close prices
                highs_1h = [x[2] for x in ohlcv_1h]
                lows_1h = [x[3] for x in ohlcv_1h]
                prices_15m = [x[4] for x in ohlcv_15m]
                highs_15m = [x[2] for x in ohlcv_15m]
                lows_15m = [x[3] for x in ohlcv_15m]
                
                # Simple trend detection
                trend_1h = "Bullish" if prices_1h[-1] > prices_1h[0] else "Bearish"
                trend_15m = "Bullish" if prices_15m[-1] > prices_15m[0] else "Bearish"
                
                # Price change
                change_1h = ((prices_1h[-1] - prices_1h[0]) / prices_1h[0]) * 100
                change_24h = ((prices_1h[-1] - prices_1h[-24]) / prices_1h[-24]) * 100 if len(prices_1h) >= 24 else 0
                
                # Calculate realistic support/resistance levels
                # Recent swing highs/lows (last 12 hours)
                recent_highs = sorted(highs_1h[-12:], reverse=True)
                recent_lows = sorted(lows_1h[-12:])
                
                # Current support: highest recent low below current price
                support_levels = [low for low in recent_lows if low < current_price]
                current_support = support_levels[-1] if support_levels else recent_lows[0]
                
                # Current resistance: lowest recent high above current price
                resistance_levels = [high for high in recent_highs if high > current_price]
                current_resistance = resistance_levels[0] if resistance_levels else recent_highs[0]
                
                # Estimated next levels based on trend and volatility
                price_range = max(highs_1h[-12:]) - min(lows_1h[-12:])
                volatility = price_range / current_price
                
                if trend_1h == "Bullish":
                    # In uptrend: estimate next resistance, support is current level
                    estimated_resistance = current_resistance + (price_range * 0.3)
                    estimated_support = current_price - (price_range * 0.2)
                else:
                    # In downtrend: estimate next support, resistance is current level
                    estimated_support = current_support - (price_range * 0.3)
                    estimated_resistance = current_price + (price_range * 0.2)
                
                # Validate estimates are realistic
                estimated_support = max(estimated_support, min(lows_1h[-24:]))
                estimated_resistance = min(estimated_resistance, max(highs_1h[-24:]) * 1.05)
                
                msg = f"🔍 *Basic Analysis: {symbol}*\n\n"
                msg += f"⚠️ *Limited Data Available*\n"
                msg += f"Providing basic analysis for decision support.\n\n"
                
                msg += f"*Current Price:* ${current_price:.4f}\n"
                msg += f"*24h Volume:* ${pair_info['volume_usd']:,.0f}\n\n"
                
                msg += f"*Support & Resistance:*\n"
                msg += f"🔴 Current Resistance: ${current_resistance:.4f}\n"
                msg += f"   Distance: {((current_resistance - current_price) / current_price * 100):+.2f}%\n"
                msg += f"🟢 Current Support: ${current_support:.4f}\n"
                msg += f"   Distance: {((current_support - current_price) / current_price * 100):+.2f}%\n\n"
                
                msg += f"*Estimated Levels:*\n"
                msg += f"📈 Est. Resistance: ${estimated_resistance:.4f}\n"
                msg += f"📉 Est. Support: ${estimated_support:.4f}\n"
                msg += f"💹 Volatility: {(volatility * 100):.2f}%\n\n"
                
                msg += f"*Price Changes:*\n"
                msg += f"1h: {change_1h:+.2f}%\n"
                msg += f"24h: {change_24h:+.2f}%\n\n"
                
                msg += f"*Trend Analysis:*\n"
                msg += f"{'🟢' if trend_1h == 'Bullish' else '🔴'} 1h: {trend_1h}\n"
                msg += f"{'🟢' if trend_15m == 'Bullish' else '🔴'} 15m: {trend_15m}\n\n"
                
                msg += f"*💡 Trading Guidance:*\n"
                if trend_1h == trend_15m:
                    msg += f"✅ Trends aligned ({trend_1h.lower()})\n"
                    if trend_1h == "Bullish":
                        msg += f"• LONG Entry: Above ${current_support:.4f}\n"
                        msg += f"• Target 1: ${current_resistance:.4f}\n"
                        msg += f"• Target 2: ${estimated_resistance:.4f}\n"
                        msg += f"• Stop Loss: Below ${current_support:.4f}\n"
                        msg += f"• Risk/Reward: {((current_resistance - current_price) / (current_price - current_support)):.2f}:1\n"
                    else:
                        msg += f"• SHORT Entry: Below ${current_resistance:.4f}\n"
                        msg += f"• Target 1: ${current_support:.4f}\n"
                        msg += f"• Target 2: ${estimated_support:.4f}\n"
                        msg += f"• Stop Loss: Above ${current_resistance:.4f}\n"
                        msg += f"• Risk/Reward: {((current_price - current_support) / (current_resistance - current_price)):.2f}:1\n"
                else:
                    msg += f"⚠️ Mixed signals (1h {trend_1h}, 15m {trend_15m})\n"
                    msg += f"• Wait for breakout above ${current_resistance:.4f}\n"
                    msg += f"• Or breakdown below ${current_support:.4f}\n"
                    msg += f"• Current range: ${current_support:.4f} - ${current_resistance:.4f}\n"
                    msg += f"• Reduce position size in ranging market\n"
                
                msg += f"\n⚠️ *Note:* Full technical analysis unavailable. Use with caution."
                
                return msg
                
            except Exception as e:
                return (f"📊 *{symbol}*\n\n"
                       f"❌ Could not analyze: {str(e)}\n\n"
                       f"Current Price: ${pair_info['last_price']:.4f}\n"
                       f"24h Volume: ${pair_info['volume_usd']:,.0f}")
        
        # Format detailed analysis
        score = signal['score']
        direction = signal['direction']
        entry = signal['entry_price']
        risk = signal['risk_params']
        checks = signal.get('confluence_checks', {})
        tf_data = signal.get('timeframe_data', {})
        
        # Determine status
        is_qualified = score >= 75
        if score >= 85:
            status = "🔥 STRONG SIGNAL"
        elif score >= 75:
            status = "✅ QUALIFIED"
        elif score >= 60:
            status = "⚠️ NEAR MISS"
        else:
            status = "❌ WEAK SETUP"
        
        dir_icon = "🟢" if direction == 'LONG' else "🔴"
        
        msg = f"🔍 *Position Analysis: {symbol}*\n\n"
        msg += f"*Status:* {status}\n"
        msg += f"*Direction:* {dir_icon} {direction}\n"
        msg += f"*Score:* {score}/110\n\n"
        
        msg += f"*Current Price:* ${entry:.4f}\n"
        msg += f"*Stop Loss:* ${risk['stop_loss']:.4f} (0.5%)\n"
        msg += f"*Target:* ${risk['target']:.4f} (1.0%)\n"
        msg += f"*Max Hold:* {risk['max_hold_minutes']} min\n\n"
        
        # Timeframe trends
        msg += "*Timeframe Trends:*\n"
        for tf in ['15m', '5m', '1m']:
            if tf in tf_data:
                trend = tf_data[tf]['trend']
                trend_icon = "🟢" if trend == 'bullish' else "🔴" if trend == 'bearish' else "⚪"
                msg += f"{trend_icon} {tf}: {trend.capitalize()}\n"
        msg += "\n"
        
        # Confluence status
        msg += "*Confluence Checks:*\n"
        msg += f"{'✅' if checks.get('timeframe_alignment') else '❌'} Timeframe alignment\n"
        msg += f"{'✅' if checks.get('stochastic_extreme') else '❌'} Stochastic extreme\n"
        msg += f"{'✅' if checks.get('volume_strong') else '❌'} Volume spike\n"
        msg += f"{'✅' if checks.get('near_vwap') else '❌'} Near VWAP\n\n"
        
        # Detailed guidance based on score and conditions
        msg += "*💡 Position Guidance:*\n"
        
        if is_qualified:
            if direction == 'LONG':
                msg += "✅ *Strong LONG setup*\n"
                msg += "• ✓ Hold if price above entry\n"
                msg += "• ✓ Add if dips to support\n"
                msg += "• ⚠️ Exit if breaks stop loss\n"
                msg += "• 🎯 Take profit at target\n"
            else:
                msg += "✅ *Strong SHORT setup*\n"
                msg += "• ✓ Hold if price below entry\n"
                msg += "• ✓ Add if rallies to resistance\n"
                msg += "• ⚠️ Exit if breaks stop loss\n"
                msg += "• 🎯 Take profit at target\n"
        else:
            # Weak setup - provide cautious guidance
            msg += "⚠️ *Weak/Ranging setup*\n"
            
            # Check what's missing
            missing = []
            if not checks.get('timeframe_alignment'):
                missing.append("timeframes not aligned")
            if not checks.get('stochastic_extreme'):
                missing.append("no extreme stochastic")
            if not checks.get('volume_strong'):
                missing.append("low volume")
            if not checks.get('near_vwap'):
                missing.append("far from VWAP")
            
            if missing:
                msg += f"Missing: {', '.join(missing)}\n\n"
            
            msg += "*Recommendations:*\n"
            msg += "• 🔻 Reduce position size\n"
            msg += "• 🛑 Use tight stop loss\n"
            msg += "• 👀 Watch for reversal signs\n"
            msg += "• ⏰ Don't hold too long\n"
            
            if direction == 'LONG':
                msg += "• ⚠️ Exit if price breaks below support\n"
            else:
                msg += "• ⚠️ Exit if price breaks above resistance\n"
        
        return msg
        
    except Exception as e:
        return (f"❌ Error analyzing {symbol}:\n{str(e)}\n\n"
               f"Try:\n"
               f"• Check symbol format (e.g., BTC/USDT:USDT)\n"
               f"• Run /scan first\n"
               f"• Contact support if issue persists")

def cmd_help(args):
    """Show help"""
    return """*MEXC Scanner V4 Bot Commands*

*Scalping Scanner:*
/scan - Run single scan now
/start_live - Start continuous scanning
/stop_live - Stop continuous scanning
/interval <sec> - Set scan interval (default: 60)

*Market Info:*
/market - Quick BTC/ETH overview
/check <symbol> - Analyze specific pair
/signals - Show latest qualified signals

*Paper Trading:*
/paper - View 24h paper trading stats
/paper_reset - Reset paper trading data

*Settings:*
/toggle_hours - Toggle 12-18 UTC / 24/7 scanning
/threshold <score> - Min score (default: 70/110)
/mute / /unmute - Toggle notifications
/status - Bot status and settings

*Utility:*
/help - Show this help
/ping - Check if bot is alive

*V4 Features (Research-Validated):*
• BTC/ETH only (highest liquidity)
• RSI 20/80 (strict mean-reversion)
• ATR 1.0x stops (professional standard)
• 12:00-18:00 UTC optimal hours (toggle)
• 1-5 quality signals/day target
• Paper trading tracks all signals

*Quick Buttons:*
📊 Scan | ▶️ Start | ⏹️ Stop
📈 Status | 🎯 Signals | 🔍 Check
⏰ Hours | 💹 Market | 📄 Paper
⚙️ Settings | ❓ Help
"""

def cmd_paper(args):
    """Show paper trading statistics"""
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/trading'))
        from paper_trading import PaperTradingTracker

        paper_file = os.path.expanduser('~/trading/data/paper_trading_v4.json')
        tracker = PaperTradingTracker(paper_file)

        stats = tracker.get_stats()

        msg = "📊 *Paper Trading Stats (24h)*\n\n"

        if stats['total_trades'] == 0:
            msg += "No trades yet. Paper trading monitor will track all V4 signals automatically.\n\n"
            msg += "Start monitor: `./start_paper_trading.sh`"
            return msg

        # Overall stats
        msg += f"*Performance:*\n"
        msg += f"Total Trades: {stats['total_trades']}\n"
        msg += f"Win Rate: {stats['win_rate']:.1f}%\n"
        msg += f"Total PnL: {stats['total_pnl_pct']:+.2f}%\n\n"

        # Breakdown
        msg += f"*Breakdown:*\n"
        msg += f"✅ Wins: {stats['wins']}\n"
        msg += f"❌ Losses: {stats['losses']}\n"
        msg += f"⏱️ Timeouts: {stats['timeouts']}\n\n"

        # Averages
        msg += f"*Averages:*\n"
        msg += f"Avg Win: {stats['avg_win_pct']:+.2f}%\n"
        msg += f"Avg Loss: {stats['avg_loss_pct']:+.2f}%\n"
        msg += f"Avg Hold: {stats['avg_hold_time_min']}min\n\n"

        # Open trades
        if tracker.open_trades:
            msg += f"*Open Trades: {len(tracker.open_trades)}*\n"
            for trade in tracker.open_trades[:3]:  # Show first 3
                dir_icon = "🟢" if trade.direction == 'LONG' else "🔴"
                msg += f"{dir_icon} {trade.symbol} @ ${trade.entry_price:.2f}\n"
            if len(tracker.open_trades) > 3:
                msg += f"...and {len(tracker.open_trades) - 3} more\n"

        return msg

    except Exception as e:
        return f"❌ Error loading paper trading stats: {e}\n\nMake sure paper trading monitor is running."

def cmd_paper_reset(args):
    """Reset paper trading statistics"""
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/trading'))
        from paper_trading import PaperTradingTracker

        paper_file = os.path.expanduser('~/trading/data/paper_trading_v4.json')
        tracker = PaperTradingTracker(paper_file)

        old_stats = tracker.get_stats()
        tracker.reset()

        msg = "🔄 *Paper Trading Reset*\n\n"
        msg += f"Previous stats:\n"
        msg += f"• {old_stats['total_trades']} trades\n"
        msg += f"• {old_stats['win_rate']:.1f}% win rate\n"
        msg += f"• {old_stats['total_pnl_pct']:+.2f}% total PnL\n\n"
        msg += "All data cleared. Starting fresh."

        return msg

    except Exception as e:
        return f"❌ Error resetting paper trading: {e}"

def cmd_ping(args):
    """Ping command"""
    return "🏓 Pong! Scanner V4 Bot is alive."

COMMANDS = {
    '/scan': cmd_scan,
    '/start_live': cmd_start_live,
    '/startlive': cmd_start_live,  # Alias without underscore
    '/stop_live': cmd_stop_live,
    '/stoplive': cmd_stop_live,  # Alias without underscore
    '/interval': cmd_interval,
    '/status': cmd_status,
    '/settings': cmd_settings,
    '/signals': cmd_signals,
    '/threshold': cmd_threshold,
    '/mute': cmd_mute,
    '/unmute': cmd_unmute,
    '/toggle_hours': cmd_toggle_hours,
    '/market': cmd_market,
    '/check': cmd_check,
    '/paper': cmd_paper,
    '/paper_reset': cmd_paper_reset,
    '/help': cmd_help,
    '/ping': cmd_ping,
    '/focus': cmd_focus,
    '/unfocus': cmd_unfocus,
    '/clear_focus': cmd_clear_focus,
    '/focus_list': cmd_focus_list,
    # Button text mappings
    '📊 scan': cmd_scan,
    '▶️ start': cmd_start_live,
    '⏹️ stop': cmd_stop_live,
    '📈 status': cmd_status,
    '🎯 signals': cmd_signals,
    '🔍 check': cmd_check,
    '⏰ hours': cmd_toggle_hours,
    '💹 market': cmd_market,
    '📄 paper': cmd_paper,
    '⚙️ settings': cmd_settings,
    '❓ help': cmd_help,
}

def process_command(text: str) -> tuple:
    """Process command and return (response, show_keyboard)"""
    parts = text.strip().split()
    if not parts:
        return ("❌ Empty command", False)

    # Handle button text (e.g., "📊 Scan" → "scan")
    cmd = text.lower().strip()
    
    # Try exact match first (for button text)
    if cmd in COMMANDS:
        try:
            return (COMMANDS[cmd]([]), True)
        except Exception as e:
            return (f"❌ Error executing command: {e}", False)
    
    # Try command format
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd not in COMMANDS:
        return (f"❌ Unknown command: {cmd}\n\nUse /help for available commands", False)

    try:
        # Show keyboard for help and status commands
        show_keyboard = cmd in ['/help', '/status', '❓ help', '⚙️ settings']
        return (COMMANDS[cmd](args), show_keyboard)
    except Exception as e:
        return (f"❌ Error executing command: {e}", False)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n⏹️  Received shutdown signal, cleaning up...")
    if state.live_mode:
        state.stop_flag = True
        print("⏹️  Stopping live scan thread...")
        if state.scan_thread and state.scan_thread.is_alive():
            state.scan_thread.join(timeout=5)

    state.save_state()
    print("✅ State saved")
    send_message("🛑 *Bot Stopped*\n\nBot has been shut down gracefully.")
    print("👋 Goodbye!")
    sys.exit(0)


def main():
    """Main bot loop"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        sys.exit(1)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("🤖 MEXC Scanner V4 Telegram Bot")
    print(f"📱 Chat ID: {CHAT_ID}")
    print("✅ Bot started. Listening for commands...")

    print("📤 Sending startup message to Telegram...")
    startup_sent = send_message("🤖 *MEXC Scanner V4 Bot Started*\n\n✅ BTC/ETH only\n✅ RSI 20/80 (research-validated)\n✅ ATR stops\n✅ 12:00-18:00 UTC optimal\n\nUse the menu buttons below or type /help", keyboard=True)
    print(f"📤 Startup message sent: {startup_sent}")

    print("🔄 Entering main loop...")
    last_update_id = 0
    error_count = 0
    max_error_sleep = 60

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 30}

            print(f"🔄 Polling Telegram API (offset: {last_update_id + 1})...")
            response = requests.get(url, params=params, timeout=35)

            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                error_count += 1
                sleep_time = min(5 * (2 ** (error_count - 1)), max_error_sleep)
                print(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue

            # Reset error count on success
            error_count = 0

            data = response.json()
            if not data.get('ok'):
                print(f"❌ API response not ok: {data}")
                error_count += 1
                sleep_time = min(5 * (2 ** (error_count - 1)), max_error_sleep)
                print(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue

            updates = data.get('result', [])
            print(f"📨 Received {len(updates)} update(s)")

            for update in updates:
                last_update_id = update['update_id']
                print(f"📬 Processing update {last_update_id}")

                # Handle callback queries (inline button clicks)
                if 'callback_query' in update:
                    callback = update['callback_query']
                    callback_id = callback['id']
                    chat_id = str(callback['message']['chat']['id'])

                    if chat_id != CHAT_ID:
                        print(f"⚠️ Ignoring callback from wrong chat: {chat_id}")
                        continue

                    # Get the callback data (the command to execute)
                    callback_data = callback.get('data', '')
                    print(f"🔘 Callback data: {callback_data}")

                    # Answer the callback to remove loading state
                    answer_url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
                    requests.post(answer_url, json={'callback_query_id': callback_id}, timeout=5)

                    # Process the command from callback
                    if callback_data:
                        response, show_keyboard = process_command(callback_data)
                        if response:  # cmd_check returns None when it sends its own message
                            send_message(response, keyboard=show_keyboard)

                # Handle regular messages
                elif 'message' in update:
                    message = update['message']
                    chat_id = str(message['chat']['id'])

                    if chat_id != CHAT_ID:
                        print(f"⚠️ Ignoring message from wrong chat: {chat_id}")
                        continue

                    text = message.get('text', '')
                    print(f"💬 Received text: {text}")

                    if text.startswith('/') or any(text.startswith(emoji) for emoji in ['📊', '▶️', '⏹️', '📈', '🎯', '🔍', '⚙️', '❓', '⏰', '💹']):
                        print(f"✅ Processing command: {text}")
                        response, show_keyboard = process_command(text)
                        if response:  # cmd_check returns None when it sends its own message
                            print(f"📤 Sending response...")
                            send_message(response, keyboard=show_keyboard)
                            print(f"✅ Response sent")
                    else:
                        print(f"⚠️ Text doesn't match command pattern")

        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            print(f"Network error: {e}")
            error_count += 1
            sleep_time = min(5 * (2 ** (error_count - 1)), max_error_sleep)
            print(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            error_count += 1
            sleep_time = min(10 * (2 ** (error_count - 1)), max_error_sleep)
            print(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()

