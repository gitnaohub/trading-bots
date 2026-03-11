#!/usr/bin/env python3
"""
Paper Trading Monitor - Tracks V4 signals and simulates trades
Runs alongside scanner, updates trades with live prices
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Add trading directory to path
sys.path.insert(0, os.path.expanduser('~/trading'))
sys.path.insert(0, os.path.expanduser('~/trading/scripts'))

from paper_trading import PaperTradingTracker
from mexc_pro_scannerV4 import ScalpingScanner

# Configuration
RESULTS_JSON = os.path.expanduser('~/trading/data/scan_results_v4.json')
PAPER_TRADING_DATA = os.path.expanduser('~/trading/data/paper_trading_v4.json')
LAST_PROCESSED_FILE = os.path.expanduser('~/trading/data/paper_trading_last_scan.txt')
UPDATE_INTERVAL = 10  # Update trades every 10 seconds

def setup_logging():
    """Configure logging"""
    log_dir = os.path.expanduser('~/trading/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'paper_trading_{datetime.now().strftime("%Y%m%d")}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_last_scan_time():
    """Get timestamp of last processed scan"""
    try:
        if os.path.exists(LAST_PROCESSED_FILE):
            with open(LAST_PROCESSED_FILE, 'r') as f:
                return float(f.read().strip())
    except:
        pass
    return 0

def save_last_scan_time(timestamp: float):
    """Save timestamp of last processed scan"""
    try:
        os.makedirs(os.path.dirname(LAST_PROCESSED_FILE), exist_ok=True)
        with open(LAST_PROCESSED_FILE, 'w') as f:
            f.write(str(timestamp))
    except Exception as e:
        print(f"Error saving last scan time: {e}")

def check_new_signals(tracker: PaperTradingTracker, logger):
    """Check for new signals from scanner and add to paper trading"""
    try:
        if not os.path.exists(RESULTS_JSON):
            return []

        # Get file modification time
        scan_mtime = os.path.getmtime(RESULTS_JSON)
        last_processed = get_last_scan_time()

        # Only process if file is newer
        if scan_mtime <= last_processed:
            return []

        # Load scan results
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)

        qualified = results.get('qualified', [])
        if not qualified:
            save_last_scan_time(scan_mtime)
            return []

        # Add new signals to paper trading
        new_trades = []
        for signal in qualified:
            trade = tracker.add_signal(signal)
            new_trades.append(trade)
            logger.info(f"📝 New paper trade: {signal['symbol']} {signal['direction']} @ ${signal['entry_price']:.2f} (Score: {signal['score']})")

        save_last_scan_time(scan_mtime)
        return new_trades

    except Exception as e:
        logger.error(f"Error checking new signals: {e}")
        return []

def get_current_prices(scanner, symbols: list) -> dict:
    """Fetch current prices for symbols"""
    prices = {}
    for symbol in symbols:
        try:
            ticker = scanner.exchange.fetch_ticker(symbol)
            if ticker:
                prices[symbol] = ticker.get('last', 0)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
    return prices

def main():
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("PAPER TRADING MONITOR V4 - STARTED")
    logger.info("=" * 80)

    # Initialize tracker
    tracker = PaperTradingTracker(PAPER_TRADING_DATA)
    logger.info(f"📊 Loaded paper trading state: {len(tracker.open_trades)} open, {len(tracker.closed_trades)} closed")

    # Initialize scanner for price fetching
    scanner = ScalpingScanner(logger)

    try:
        while True:
            # Check for new signals
            new_trades = check_new_signals(tracker, logger)

            # Update open trades with current prices
            if tracker.open_trades:
                symbols = list(set(t.symbol for t in tracker.open_trades))
                current_prices = get_current_prices(scanner, symbols)

                closed_trades = tracker.update_trades(current_prices)

                # Log closed trades
                for trade in closed_trades:
                    status_icon = "✅" if trade.status == 'WIN' else "❌" if trade.status == 'LOSS' else "⏱️"
                    logger.info(f"{status_icon} Trade closed: {trade.symbol} {trade.direction} | "
                              f"Status: {trade.status} | PnL: {trade.pnl_pct:+.2f}% | "
                              f"Hold: {trade.hold_time_minutes}min")

            # Sleep before next update
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Paper trading monitor stopped by user")
        stats = tracker.get_stats()
        logger.info(f"📊 Final stats: {stats['total_trades']} trades, {stats['win_rate']:.1f}% win rate, {stats['total_pnl_pct']:+.2f}% total PnL")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
