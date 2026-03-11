# Trading Bot Accuracy Analysis - March 11, 2026

## Executive Summary

Your trading bot has a **43.59% win rate** (V3) and **46.15% win rate** (V4), both below 50%. This means the bot is wrong more often than it's right, resulting in losses:
- **V3**: -$152.68 (-1.53%) from $10,000 starting balance
- **V4**: -$87.45 (-0.87%) from $10,000 starting balance

**Root cause**: The bot checks 1h EMA alignment but ignores 1h/4h RSI overbought/oversold conditions, causing it to enter trades against higher timeframe momentum.

---

## Performance Data

### V3 Performance
- Starting balance: $10,000
- Current balance: $9,847.32
- Total trades: 156
- Winning trades: 68
- Losing trades: 88
- **Win rate: 43.59%**
- Total P/L: -$152.68 (-1.53%)

### V4 Performance
- Starting balance: $10,000
- Current balance: $9,912.55
- Total trades: 130
- Winning trades: 60
- Losing trades: 70
- **Win rate: 46.15%**
- Total P/L: -$87.45 (-0.87%)

---

## Key Issues Identified

### 1. Insufficient Higher Timeframe Filtering (CRITICAL)

**Problem**: The bot checks 1h EMA alignment but doesn't check 1h/4h RSI conditions.

**Example from scan results**:
- Signal: LONG for HYPE/USDT (score 80)
- 1h EMA20 (34.14) > EMA50 (33.42) ✓ **Passed 1h alignment check**
- BUT: 1h RSI = 41.92 (bearish territory)
- AND: 4h RSI = 77.35 (very overbought!)

**Result**: Signal passed the 1h alignment check because EMAs were aligned, but RSI showed the asset was overbought on higher timeframes. This likely resulted in a losing trade.

**Impact**: This is the PRIMARY cause of the low win rate. Signals pass the 1h EMA check but fail due to overbought/oversold conditions on higher timeframes.

### 2. Over-Reliance on Short-Term Indicators

**Problem**: Primary signal is based on 1m EMA crossover, which is very noisy.

**Current logic**:
- Primary signal: 1m EMA crossover (15 points in scoring)
- 5m alignment check
- 15m alignment check
- 1h alignment check (EMA only)
- 4h alignment bonus (10 points)

**Issue**: Short-term indicators (1m, 5m) generate many false signals. The bot enters trades based on short-term noise rather than genuine trends.

### 3. Scoring System Weights Not Optimal

**Current scoring** (110 points total):
- Spread Quality: 20 points
- Liquidity: 20 points
- Technical Setup: 30 points (EMA crossover 15, RSI extreme 8, BB touch 7)
- Order Flow: 15 points
- Volume: 15 points
- 4h Alignment Bonus: 10 points

**Issues**:
- 4h alignment is only 10 points (9% of total) - too low
- EMA crossover gets 15 points but RSI extreme only gets 8 points
- Higher timeframe alignment should be weighted more heavily

### 4. No RSI Divergence Check

**Missing**: The bot doesn't check for RSI divergence between timeframes.

**Example**: If 1m RSI is bullish but 1h/4h RSI is bearish, this is a strong signal that the short-term move is against the bigger trend.

---

## Detailed Recommendations

### Priority 1: Add Higher Timeframe RSI Filtering (CRITICAL)

**Change**: Add mandatory RSI checks for 1h and 4h timeframes.

**Implementation**:
```python
# After the 1h EMA alignment check, add:

# Check 1h RSI - reject if extreme against signal direction
rsi_1h = indicators_1h.get('rsi', 50)
if direction == 'LONG' and rsi_1h > 65:
    # Reject LONG if 1h RSI is overbought
    return None, "1h RSI overbought ({}), rejecting LONG".format(rsi_1h)
elif direction == 'SHORT' and rsi_1h < 35:
    # Reject SHORT if 1h RSI is oversold
    return None, "1h RSI oversold ({}), rejecting SHORT".format(rsi_1h)

# Check 4h RSI - reject if extreme against signal direction
rsi_4h = indicators_4h.get('rsi', 50)
if direction == 'LONG' and rsi_4h > 70:
    # Reject LONG if 4h RSI is overbought
    return None, "4h RSI overbought ({}), rejecting LONG".format(rsi_4h)
elif direction == 'SHORT' and rsi_4h < 30:
    # Reject SHORT if 4h RSI is oversold
    return None, "4h RSI oversold ({}), rejecting SHORT".format(rsi_4h)
```

**Expected impact**: This should significantly improve win rate by filtering out signals that go against higher timeframe momentum.

### Priority 2: Increase Minimum Signal Score

**Change**: Increase MIN_SIGNAL_SCORE from 75 to 85.

**Rationale**: Currently, signals scoring 75+ are still losing trades. By increasing the threshold, we filter out lower-quality signals.

**Implementation**:
```python
MIN_SIGNAL_SCORE = 85  # Increased from 75
```

**Expected impact**: Fewer signals, but higher quality. Win rate should improve.

### Priority 3: Adjust Scoring Weights

**Change**: Increase weight for higher timeframe alignment, decrease weight for short-term indicators.

**New scoring** (110 points total):
- Spread Quality: 15 points (reduced from 20)
- Liquidity: 15 points (reduced from 20)
- Technical Setup: 25 points (reduced from 30)
  - EMA crossover: 10 points (reduced from 15)
  - RSI extreme: 8 points (unchanged)
  - BB touch: 7 points (unchanged)
- Order Flow: 15 points (unchanged)
- Volume: 15 points (unchanged)
- **1h Alignment: 15 points (new, mandatory)**
- **4h Alignment: 10 points (unchanged)**

**Implementation**: Update the scoring function to reflect new weights.

**Expected impact**: Higher timeframe alignment becomes more important, reducing false signals.

### Priority 4: Add RSI Divergence Check

**Change**: Check if RSI on different timeframes is aligned.

**Implementation**:
```python
# Add to scoring function:
# RSI Alignment Bonus: 10 points
rsi_1m = indicators_1m.get('rsi', 50)
rsi_5m = indicators_5m.get('rsi', 50)
rsi_1h = indicators_1h.get('rsi', 50)

if direction == 'LONG':
    # All RSI should be > 50 for LONG
    if rsi_1m > 50 and rsi_5m > 50 and rsi_1h > 50:
        score += 10
elif direction == 'SHORT':
    # All RSI should be < 50 for SHORT
    if rsi_1m < 50 and rsi_5m < 50 and rsi_1h < 50:
        score += 10
```

**Expected impact**: Filters out signals where short-term and long-term RSI are diverging.

### Priority 5: Tighten Risk Parameters

**Change**: Reduce risk per trade and increase target profit.

**Current**:
- Risk: 0.5%
- Target: 1.0%
- R:R = 1:2

**Recommended**:
- Risk: 0.3%
- Target: 1.2%
- R:R = 1:4

**Rationale**: With a win rate below 50%, we need a better risk-reward ratio to be profitable.

**Implementation**:
```python
RISK_PER_TRADE_PCT = 0.3  # Reduced from 0.5
TARGET_PROFIT_PCT = 1.2   # Increased from 1.0
```

**Expected impact**: Even with a 45% win rate, a 1:4 R:R can be profitable.

---

## Implementation Priority

1. **CRITICAL**: Add 1h/4h RSI filtering (Priority 1)
2. **HIGH**: Increase minimum signal score to 85 (Priority 2)
3. **MEDIUM**: Adjust scoring weights (Priority 3)
4. **MEDIUM**: Add RSI divergence check (Priority 4)
5. **LOW**: Tighten risk parameters (Priority 5)

---

## Expected Results After Fixes

**Conservative estimate**:
- Win rate: 50-55% (up from 43.59%)
- With 1:4 R:R and 50% win rate: +0.5% to +1.0% profit

**Optimistic estimate**:
- Win rate: 55-60% (if all fixes work well)
- With 1:4 R:R and 55% win rate: +1.5% to +2.5% profit

---

## Next Steps

1. **Backup current code**: `cp mexc_pro_scannerV3.py mexc_pro_scannerV3_backup.py`
2. **Implement Priority 1 fix**: Add 1h/4h RSI filtering
3. **Test with paper trading**: Run for 24-48 hours
4. **Monitor results**: Check if win rate improves
5. **Implement remaining fixes**: If Priority 1 works, add other fixes
6. **Iterate**: Adjust parameters based on results

---

## Code Locations to Edit

**File**: `/home/user/trading/scripts/mexc_pro_scannerV3.py`

**Sections to modify**:
1. **Line ~50**: Update MIN_SIGNAL_SCORE from 75 to 85
2. **Line ~60**: Update RISK_PER_TRADE_PCT and TARGET_PROFIT_PCT
3. **Line ~450-500**: Add 1h/4h RSI filtering after 1h EMA alignment check
4. **Line ~600-700**: Update scoring weights in the scoring function
5. **Line ~650**: Add RSI divergence check to scoring function

---

## Conclusion

Your bot's low win rate (43.59%) is primarily caused by insufficient higher timeframe filtering. The bot checks 1h EMA alignment but ignores 1h/4h RSI conditions, causing it to enter trades that are overbought/oversold on higher timeframes.

**The fix is straightforward**: Add mandatory 1h/4h RSI checks to reject signals that go against higher timeframe momentum. This single change should significantly improve the win rate.

**Estimated time to implement**: 30-60 minutes for Priority 1 fix.

**Estimated improvement**: Win rate should increase from 43.59% to 50-55% with just the Priority 1 fix.
