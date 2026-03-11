#!/usr/bin/env python3
"""
Paper Trading Tracker for V4 Scanner
Tracks all signals and simulates trades to measure performance
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class PaperTrade:
    def __init__(self, signal: dict):
        self.symbol = signal['symbol']
        self.direction = signal['direction']
        self.entry_price = signal['entry_price']
        self.stop_loss = signal['risk_params']['stop_loss']
        self.target = signal['risk_params']['target']
        self.entry_time = datetime.now().isoformat()
        self.score = signal['score']
        self.status = 'OPEN'  # OPEN, WIN, LOSS, TIMEOUT
        self.exit_price = None
        self.exit_time = None
        self.pnl_pct = 0.0
        self.hold_time_minutes = 0
        self.max_hold_minutes = signal['risk_params']['max_hold_minutes']

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'target': self.target,
            'entry_time': self.entry_time,
            'score': self.score,
            'status': self.status,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time,
            'pnl_pct': self.pnl_pct,
            'hold_time_minutes': self.hold_time_minutes,
            'max_hold_minutes': self.max_hold_minutes
        }

    @classmethod
    def from_dict(cls, data: dict):
        trade = cls.__new__(cls)
        trade.__dict__.update(data)
        return trade

class PaperTradingTracker:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.open_trades: List[PaperTrade] = []
        self.closed_trades: List[PaperTrade] = []
        self.load_state()

    def load_state(self):
        """Load paper trading state from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.open_trades = [PaperTrade.from_dict(t) for t in data.get('open_trades', [])]
                    self.closed_trades = [PaperTrade.from_dict(t) for t in data.get('closed_trades', [])]
        except Exception as e:
            print(f"Error loading paper trading state: {e}")

    def save_state(self):
        """Save paper trading state to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump({
                    'open_trades': [t.to_dict() for t in self.open_trades],
                    'closed_trades': [t.to_dict() for t in self.closed_trades]
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving paper trading state: {e}")

    def add_signal(self, signal: dict) -> PaperTrade:
        """Add new signal as paper trade"""
        trade = PaperTrade(signal)
        self.open_trades.append(trade)
        self.save_state()
        return trade

    def update_trades(self, current_prices: Dict[str, float]) -> List[PaperTrade]:
        """Update open trades with current prices, return closed trades"""
        closed_now = []

        for trade in self.open_trades[:]:  # Copy list to modify during iteration
            symbol = trade.symbol
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            # Calculate hold time
            entry_dt = datetime.fromisoformat(trade.entry_time)
            hold_minutes = (datetime.now() - entry_dt).total_seconds() / 60
            trade.hold_time_minutes = int(hold_minutes)

            # Check if stopped out or hit target
            hit_stop = False
            hit_target = False

            if trade.direction == 'LONG':
                hit_stop = current_price <= trade.stop_loss
                hit_target = current_price >= trade.target
            else:  # SHORT
                hit_stop = current_price >= trade.stop_loss
                hit_target = current_price <= trade.target

            # Check timeout
            timed_out = hold_minutes >= trade.max_hold_minutes

            if hit_stop:
                trade.status = 'LOSS'
                trade.exit_price = trade.stop_loss
                trade.exit_time = datetime.now().isoformat()
                if trade.direction == 'LONG':
                    trade.pnl_pct = ((trade.stop_loss - trade.entry_price) / trade.entry_price) * 100
                else:
                    trade.pnl_pct = ((trade.entry_price - trade.stop_loss) / trade.entry_price) * 100
                self.open_trades.remove(trade)
                self.closed_trades.append(trade)
                closed_now.append(trade)

            elif hit_target:
                trade.status = 'WIN'
                trade.exit_price = trade.target
                trade.exit_time = datetime.now().isoformat()
                if trade.direction == 'LONG':
                    trade.pnl_pct = ((trade.target - trade.entry_price) / trade.entry_price) * 100
                else:
                    trade.pnl_pct = ((trade.entry_price - trade.target) / trade.entry_price) * 100
                self.open_trades.remove(trade)
                self.closed_trades.append(trade)
                closed_now.append(trade)

            elif timed_out:
                trade.status = 'TIMEOUT'
                trade.exit_price = current_price
                trade.exit_time = datetime.now().isoformat()
                if trade.direction == 'LONG':
                    trade.pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                else:
                    trade.pnl_pct = ((trade.entry_price - current_price) / trade.entry_price) * 100
                self.open_trades.remove(trade)
                self.closed_trades.append(trade)
                closed_now.append(trade)

        if closed_now:
            self.save_state()

        return closed_now

    def get_stats(self) -> dict:
        """Calculate performance statistics"""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'timeouts': 0,
                'win_rate': 0.0,
                'avg_win_pct': 0.0,
                'avg_loss_pct': 0.0,
                'total_pnl_pct': 0.0,
                'avg_hold_time_min': 0
            }

        wins = [t for t in self.closed_trades if t.status == 'WIN']
        losses = [t for t in self.closed_trades if t.status == 'LOSS']
        timeouts = [t for t in self.closed_trades if t.status == 'TIMEOUT']

        total = len(self.closed_trades)
        win_count = len(wins)
        loss_count = len(losses)
        timeout_count = len(timeouts)

        win_rate = (win_count / total * 100) if total > 0 else 0
        avg_win = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl_pct for t in losses) / len(losses) if losses else 0
        total_pnl = sum(t.pnl_pct for t in self.closed_trades)
        avg_hold = sum(t.hold_time_minutes for t in self.closed_trades) / total if total > 0 else 0

        return {
            'total_trades': total,
            'wins': win_count,
            'losses': loss_count,
            'timeouts': timeout_count,
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'total_pnl_pct': total_pnl,
            'avg_hold_time_min': int(avg_hold)
        }

    def reset(self):
        """Reset all paper trading data"""
        self.open_trades = []
        self.closed_trades = []
        self.save_state()
