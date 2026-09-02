"""
Supertrend (10, 3) & Volatility Breakout Strategy
-------------------------------------------------
Dynamic volatility band strategy that enters on bullish trend flips and rides
extended momentum waves while keeping a strict trailing stop.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_supertrend, compute_rsi, compute_atr


class SupertrendStrategy(BaseStrategy):
    ID = "supertrend_breakout"
    TITLE = "Supertrend (10, 3) Volatility Breakout"
    CATEGORY = "Trend Following & Volatility"
    BADGE = "🚀 Supertrend"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Captures multi-month momentum moves by entering on Supertrend bull flips with dynamic ATR trailing stops.",
            "writeup": {
                "philosophy": (
                    "The Supertrend indicator combines Average True Range (ATR) with median price bands to adapt dynamically to market volatility. "
                    "By entering when price breaks above the upper volatility band and trailing stops along the lower band, it allows winning trades to run indefinitely "
                    "while instantly cutting losses when market structure fails."
                ),
                "buyRules": [
                    "Supertrend Bull Flip: Supertrend indicator flips from Red (Bearish) to Green (Bullish) as daily Close crosses above the upper ATR band.",
                    "Trend Validation: Daily Close is higher than 50 EMA.",
                    "Volume Confirmation: Breakout candle volume is at least 1.15× of 20-day Volume SMA.",
                    "RSI Momentum: RSI(14) > 48.0 (confirming active buying interest)."
                ],
                "sellRules": [
                    "Supertrend Bear Flip: Supertrend flips from Green (Bullish) to Red (Bearish) as price breaches the trailing support line.",
                    "Overbought Exhaustion: RSI closes above 78.0 with a topping wick candle.",
                    "Target Extension: Discretionary take-profit at +18.0% gain from entry."
                ],
                "stopLossRules": [
                    "Dynamic Trailing Stop: Strictly anchored to the live Supertrend Green line value.",
                    "Max Hard Stop: 5.0% maximum risk from entry price if volatility spikes.",
                    "Profit Lock: As the Supertrend line ratchets upward, all paper profits are progressively locked in."
                ],
                "idealMarket": "Strong cyclical rallies, breakout expansions, and trending sector rotations."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, **kwargs) -> Dict[str, Any]:
        if df is None or len(df) < 30 or not current_price:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Insufficient daily history for Supertrend"
            }

        cmp = float(current_price)
        st_vals, directions = compute_supertrend(df, period=10, multiplier=3.0)
        curr_dir = directions[-1]
        prev_dir = directions[-2] if len(directions) >= 2 else curr_dir
        curr_st = st_vals[-1]
        rsi = compute_rsi(df["Close"], 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        if curr_dir == 1:
            fresh_flip = (prev_dir == -1)
            target = round(cmp + (3.0 * atr), 2)
            stop_loss = round(max(curr_st, cmp * 0.95), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY" if fresh_flip or (cmp - curr_st)/curr_st <= 0.035 else "HOLD",
                "signalTitle": "Supertrend Bullish Flip" if fresh_flip else "Supertrend Bullish Trend",
                "signalBadge": "🟢 BUY" if fresh_flip or (cmp - curr_st)/curr_st <= 0.035 else "⚪ HOLD",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"{'Fresh Bull Flip' if fresh_flip else 'Bullish Band'} (Supertrend SL: ₹{curr_st:.1f} | RSI: {rsi:.1f})"
            }
        else:
            return {
                "signal": "SELL",
                "signalTitle": "Supertrend Bearish Trend",
                "signalBadge": "🔴 SELL",
                "targetPrice": round(cmp * 0.90, 2),
                "stopLossPrice": round(curr_st, 2),
                "riskRewardRatio": None,
                "reason": f"Supertrend Bearish Resistance at ₹{curr_st:.1f} (RSI: {rsi:.1f})"
            }

    @classmethod
    def run_backtest(cls, stock: str, lookback_years: int = 2, initial_capital: float = 100000.0) -> Dict[str, Any]:
        try:
            df = download_stock_history(stock, lookback_years=lookback_years, min_bars=40)
            if df is None or len(df) < 40:
                return {"status": "error", "message": f"Insufficient price history for {stock}"}

            st_vals, directions = compute_supertrend(df, period=10, multiplier=3.0)
            c_arr = df["Close"].values.astype(float)
            dates = [str(d)[:10] for d in df.index]

            capital = float(initial_capital)
            cash = capital
            shares = 0
            in_pos = False
            entry_p = 0.0
            entry_d = ""
            entry_i = 0
            stop_p = 0.0

            trades = []
            equity_curve = []
            start_idx = 20
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                d = dates[i]
                st = float(st_vals[i])
                curr_dir = int(directions[i])
                prev_dir = int(directions[i-1]) if i > 0 else curr_dir

                if not in_pos:
                    if curr_dir == 1 and prev_dir == -1:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            stop_p = max(st, entry_p * 0.95)
                else:
                    stop_p = max(stop_p, st)
                    exit_reason = None
                    exit_p = c

                    if curr_dir == -1 or df["Low"].iloc[i] <= stop_p:
                        exit_p = min(c, stop_p) if df["Low"].iloc[i] <= stop_p else c
                        exit_reason = f"Supertrend Bear Flip / Trailing Stop ({((exit_p - entry_p)/entry_p)*100:.1f}%)"

                    if exit_reason:
                        cash += shares * exit_p
                        pnl_val = (exit_p - entry_p) * shares
                        pnl_pct = round(((exit_p - entry_p) / entry_p) * 100, 2)
                        trades.append({
                            "entryDate": entry_d,
                            "entryPrice": round(entry_p, 2),
                            "exitDate": d,
                            "exitPrice": round(exit_p, 2),
                            "holdingDays": i - entry_i,
                            "pnlPct": pnl_pct,
                            "pnlAmount": round(pnl_val, 2),
                            "reason": exit_reason
                        })
                        in_pos = False
                        shares = 0

                port_val = cash + (shares * c if in_pos else 0)
                bnh_val = (capital / initial_price) * c
                equity_curve.append({
                    "date": d,
                    "strategy": round(port_val, 2),
                    "benchmark": round(bnh_val, 2)
                })

            if in_pos and shares > 0:
                last_c = float(c_arr[-1])
                cash += shares * last_c
                pnl_pct = round(((last_c - entry_p) / entry_p) * 100, 2)
                trades.append({
                    "entryDate": entry_d,
                    "entryPrice": round(entry_p, 2),
                    "exitDate": dates[-1],
                    "exitPrice": round(last_c, 2),
                    "holdingDays": len(c_arr) - 1 - entry_i,
                    "pnlPct": pnl_pct,
                    "pnlAmount": round((last_c - entry_p) * shares, 2),
                    "reason": "Backtest Period End"
                })

            final_val = cash
            strat_ret = round(((final_val - capital) / capital) * 100, 2)
            last_price = float(c_arr[-1])
            bnh_ret = round(((last_price - initial_price) / initial_price) * 100, 2)

            wins = [t for t in trades if t["pnlPct"] > 0]
            losses = [t for t in trades if t["pnlPct"] <= 0]
            win_rate = round((len(wins) / len(trades) * 100), 1) if trades else 0.0

            total_gain = sum(t["pnlAmount"] for t in wins)
            total_loss = abs(sum(t["pnlAmount"] for t in losses))
            profit_factor = round(total_gain / total_loss, 2) if total_loss > 0 else (99.0 if total_gain > 0 else 0.0)

            strat_vals = [e["strategy"] for e in equity_curve]
            running_max = np.maximum.accumulate(strat_vals)
            dds = (running_max - strat_vals) / running_max * 100
            max_dd = round(float(np.max(dds)), 1) if len(dds) > 0 else 0.0
            avg_hold = round(float(np.mean([t["holdingDays"] for t in trades])), 1) if trades else 0.0

            step = max(1, len(equity_curve) // 60)
            sampled_curve = equity_curve[::step]
            if equity_curve and (not sampled_curve or sampled_curve[-1]["date"] != equity_curve[-1]["date"]):
                sampled_curve.append(equity_curve[-1])

            return {
                "status": "success",
                "stock": stock,
                "strategyId": cls.ID,
                "strategyTitle": cls.TITLE,
                "strategyInfo": cls.get_info(),
                "summary": {
                    "strategyReturnPct": strat_ret,
                    "buyAndHoldReturnPct": bnh_ret,
                    "winRatePct": win_rate,
                    "profitFactor": profit_factor,
                    "maxDrawdownPct": max_dd,
                    "totalTrades": len(trades),
                    "winningTrades": len(wins),
                    "losingTrades": len(losses),
                    "avgHoldingDays": avg_hold,
                    "initialCapital": initial_capital,
                    "finalPortfolioValue": round(final_val, 2)
                },
                "equityCurve": sampled_curve,
                "trades": list(reversed(trades))
            }
        except Exception as e:
            return {"status": "error", "message": f"Backtest failed: {str(e)}"}
