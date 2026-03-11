#!/usr/bin/env python3
"""
Helper functions for the /check command
Extracted from telegram_bot_v3.py for better maintainability
"""

def parse_check_argument(arg: str, results_json_path: str):
    """
    Parse /check argument - can be a number (from scan results) or a symbol
    Returns: (symbol, error_message)
    """
    import json
    import os

    arg = arg.upper()

    # Check if it's a number (referring to last scan results)
    try:
        number = int(arg)
        if not os.path.exists(results_json_path):
            return None, "❌ No scan results available\n\nRun /scan first or use /check <symbol>"

        with open(results_json_path, 'r') as f:
            results = json.load(f)

        all_signals = results.get('qualified', []) + results.get('near_misses', [])
        if number < 1 or number > len(all_signals):
            return None, f"❌ Invalid number. Last scan had {len(all_signals)} signals."

        symbol = all_signals[number - 1]['symbol']
        return symbol, None
    except ValueError:
        # It's a symbol, not a number
        symbol = arg
        if ':USDT' not in symbol:
            if not symbol.endswith('/USDT'):
                symbol += '/USDT'
            symbol += ':USDT'
        return symbol, None


def format_basic_analysis(symbol: str, pair_info: dict, ohlcv_data: dict) -> str:
    """
    Format basic analysis when full technical analysis is unavailable
    """
    current_price = pair_info['last_price']
    prices_1h = ohlcv_data['prices_1h']
    highs_1h = ohlcv_data['highs_1h']
    lows_1h = ohlcv_data['lows_1h']
    prices_15m = ohlcv_data['prices_15m']

    # Simple trend detection
    trend_1h = "Bullish" if prices_1h[-1] > prices_1h[0] else "Bearish"
    trend_15m = "Bullish" if prices_15m[-1] > prices_15m[0] else "Bearish"

    # Price changes
    change_1h = ((prices_1h[-1] - prices_1h[0]) / prices_1h[0]) * 100
    change_24h = ((prices_1h[-1] - prices_1h[-24]) / prices_1h[-24]) * 100 if len(prices_1h) >= 24 else 0

    # Calculate support/resistance
    recent_highs = sorted(highs_1h[-12:], reverse=True)
    recent_lows = sorted(lows_1h[-12:])

    support_levels = [low for low in recent_lows if low < current_price]
    current_support = support_levels[-1] if support_levels else recent_lows[0]

    resistance_levels = [high for high in recent_highs if high > current_price]
    current_resistance = resistance_levels[0] if resistance_levels else recent_highs[0]

    # Estimate next levels
    price_range = max(highs_1h[-12:]) - min(lows_1h[-12:])
    volatility = price_range / current_price

    if trend_1h == "Bullish":
        estimated_resistance = current_resistance + (price_range * 0.3)
        estimated_support = current_price - (price_range * 0.2)
    else:
        estimated_support = current_support - (price_range * 0.3)
        estimated_resistance = current_price + (price_range * 0.2)

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

    msg += format_trading_guidance(trend_1h, trend_15m, current_price, current_support,
                                   current_resistance, estimated_support, estimated_resistance)

    msg += f"\n⚠️ *Note:* Full technical analysis unavailable. Use with caution."

    return msg


def format_trading_guidance(trend_1h: str, trend_15m: str, current_price: float,
                            current_support: float, current_resistance: float,
                            estimated_support: float, estimated_resistance: float) -> str:
    """Format trading guidance based on trends"""
    msg = f"*💡 Trading Guidance:*\n"

    if trend_1h == trend_15m:
        msg += f"✅ Trends aligned ({trend_1h.lower()})\n"
        if trend_1h == "Bullish":
            msg += f"• LONG Entry: Above ${current_support:.4f}\n"
            msg += f"• Target 1: ${current_resistance:.4f}\n"
            msg += f"• Target 2: ${estimated_resistance:.4f}\n"
            msg += f"• Stop Loss: Below ${current_support:.4f}\n"
            rr = ((current_resistance - current_price) / (current_price - current_support))
            msg += f"• Risk/Reward: {rr:.2f}:1\n"
        else:
            msg += f"• SHORT Entry: Below ${current_resistance:.4f}\n"
            msg += f"• Target 1: ${current_support:.4f}\n"
            msg += f"• Target 2: ${estimated_support:.4f}\n"
            msg += f"• Stop Loss: Above ${current_resistance:.4f}\n"
            rr = ((current_price - current_support) / (current_resistance - current_price))
            msg += f"• Risk/Reward: {rr:.2f}:1\n"
    else:
        msg += f"⚠️ Mixed signals (1h {trend_1h}, 15m {trend_15m})\n"
        msg += f"• Wait for breakout above ${current_resistance:.4f}\n"
        msg += f"• Or breakdown below ${current_support:.4f}\n"
        msg += f"• Current range: ${current_support:.4f} - ${current_resistance:.4f}\n"
        msg += f"• Reduce position size in ranging market\n"

    return msg


def format_detailed_analysis(symbol: str, signal: dict) -> str:
    """Format detailed analysis from scanner signal"""
    score = signal['score']
    direction = signal['direction']
    entry = signal['entry_price']
    risk = signal['risk_params']
    checks = signal.get('confluence_checks', {})
    tf_data = signal.get('timeframe_data', {})

    # Determine status
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

    msg += format_position_guidance(score >= 75, direction, checks)

    return msg


def format_position_guidance(is_qualified: bool, direction: str, checks: dict) -> str:
    """Format position guidance based on signal quality"""
    msg = "*💡 Position Guidance:*\n"

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
        msg += "⚠️ *Weak/Ranging setup*\n"

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
