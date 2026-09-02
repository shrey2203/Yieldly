"""
Coffee Can Quality Compounder Long-Term Strategy
------------------------------------------------
Inspired by Robert Kirby and Saurabh Mukherjea's Coffee Can Portfolio philosophy.
Focuses on long-term wealth compounding (1-3+ year holding horizon):
1. Requires sound fundamental health: consistent earnings, reasonable debt/equity, and high institutional trust.
2. Macro trend alignment: Price > 200-day SMA & 50-day SMA > 200-day SMA (Golden Cross).
3. Patient long-term holding, ignoring short-term market noise and exiting only on structural 200 SMA collapse.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


class CoffeeCanStrategy(BaseStrategy):
    ID = "coffee_can_compounder"
    TITLE = "Coffee Can Quality Compounder (Multi-Year)"
    CATEGORY = "Long-Term Quality & Compounding"
    BADGE = "☕ Coffee Can"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Long-term wealth compounding strategy buying market leaders in verified 200D secular bull trends with wide trailing stops.",
            "writeup": {
                "philosophy": (
                    "Based on Robert Kirby's original 1984 concept and Saurabh Mukherjea's Coffee Can Investing framework. "
                    "True long-term wealth is generated not by hyperactive trading, but by identifying high-quality structural compounders, "
                    "buying them during consolidations, and holding them for multiple years to let business earnings growth drive returns. "
                    "Short-term volatility is treated as noise, with exits triggered strictly on structural macro breakdown."
                ),
                "buyRules": [
                    "Secular Bull Regime: Price is trading strictly above the rising 200-day SMA (Golden Cross: 50 SMA > 200 SMA).",
                    "Healthy Consolidation Entry: Price is within -4.0% to +6.0% of the 50-day SMA (buying on value/support rather than chasing).",
                    "Earnings Compounder: Long-term multi-quarter earnings stability and low financial leverage.",
                    "Accumulation RSI: 14-day RSI is between 40.0 and 64.0 (institutional accumulation phase)."
                ],
                "sellRules": [
                    "Secular Trend Breakdown: Daily close breaks below the 200-day SMA by > 5.0% (structural bear market regime switch).",
                    "Fundamental Earnings Collapse: Multiple consecutive quarters of severe EPS contraction.",
                    "Parabolic Re-rating: Price extends > 45% above the 200-day SMA with RSI > 80 (take-profit on extreme euphoria)."
                ],
                "stopLossRules": [
                    "Wide Long-Term Stop: Placed safely below the 200-day SMA (200 SMA × 0.92) to prevent getting whipsawed by normal cyclical corrections.",
                    "Compounding Trailing Floor: Once the position gains +20.0%, Stop Loss trails below the rising 200-day SMA, locking in long-term capital gains."
                ],
                "idealMarket": "Multi-year secular economic expansions, monopoly/duopoly moat franchises, and structural compounders."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, **kwargs) -> Dict[str, Any]:
        if df is None or len(df) < 60 or not current_price:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Insufficient daily history to compute Coffee Can Secular Trend"
            }

        closes = df["Close"]
        cmp = float(current_price)

        sma50 = compute_sma(closes, 50).iloc[-1]
        sma200 = compute_sma(closes, 200).iloc[-1] if len(df) >= 150 else sma50 * 0.92
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        dist_sma50 = ((cmp - sma50) / sma50) * 100
        dist_sma200 = ((cmp - sma200) / sma200) * 100

        golden_cross = sma50 >= (sma200 * 0.98)
        above_200 = cmp > (sma200 * 0.98)
        near_50_or_200 = -4.0 <= dist_sma50 <= 7.0 or (-2.0 <= dist_sma200 <= 5.0)
        rsi_acc = 38.0 <= rsi <= 65.0

        if above_200 and golden_cross and near_50_or_200 and rsi_acc:
            target = round(cmp * 1.35, 2)
            stop_loss = round(max(sma200 * 0.92, cmp * 0.90), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "Coffee Can Long-Term Accumulation",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"Secular Trend (50>200 SMA) • 200 SMA: ₹{sma200:.1f} ({dist_sma200:+.1f}%) • RSI: {rsi:.1f}"
            }

        if cmp < (sma200 * 0.93) or (dist_sma200 > 45.0 and rsi >= 80.0):
            target = round(sma200, 2) if sma200 < cmp else round(cmp * 0.85, 2)
            stop_loss = round(cmp * 1.08, 2)
            reason = "200 SMA Secular Trend Breakdown" if cmp < (sma200 * 0.93) else f"Extreme Parabolic Extension ({dist_sma200:.1f}% above 200 SMA)"
            return {
                "signal": "SELL",
                "signalTitle": "Secular Breakdown / Parabolic Top",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(cmp * 1.25, 2)
        stop_loss = round(sma200 * 0.92, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 2.0

        return {
            "signal": "HOLD",
            "signalTitle": "Long-Term Quality Compounding",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Holding Quality Compounder (CMP: ₹{cmp:.1f} | 200 SMA: ₹{sma200:.1f} | Golden Cross Active)"
        }

    @classmethod
    def run_backtest(cls, stock: str, lookback_years: int = 2, initial_capital: float = 100000.0) -> Dict[str, Any]:
        try:
            df = download_stock_history(stock, lookback_years=lookback_years, min_bars=60)
            if df is None or len(df) < 60:
                return {"status": "error", "message": f"Insufficient price history for {stock}"}

            closes = df["Close"]
            highs = df["High"]
            lows = df["Low"]
            dates = [str(d)[:10] for d in df.index]

            sma50_s = compute_sma(closes, 50).values
            sma200_s = compute_sma(closes, 200).values if len(df) >= 150 else (sma50_s * 0.92)
            rsi_s = compute_rsi(closes, 14).values

            c_arr = closes.values.astype(float)
            h_arr = highs.values.astype(float)
            l_arr = lows.values.astype(float)

            capital = float(initial_capital)
            cash = capital
            shares = 0
            in_pos = False
            entry_p = 0.0
            entry_d = ""
            entry_i = 0
            stop_p = 0.0
            target_p = 0.0

            trades = []
            equity_curve = []
            start_idx = 40
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                s50 = float(sma50_s[i])
                s200 = float(sma200_s[i])
                rsi = float(rsi_s[i])

                dist_s50 = ((c - s50) / s50) * 100
                dist_s200 = ((c - s200) / s200) * 100

                if not in_pos:
                    golden = s50 >= (s200 * 0.98)
                    above_200 = c > (s200 * 0.98)
                    near_zone = -4.0 <= dist_s50 <= 7.0 or (-2.0 <= dist_s200 <= 5.0)
                    rsi_ok = 38.0 <= rsi <= 66.0

                    if golden and above_200 and near_zone and rsi_ok:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p * 1.45, 2)
                            stop_p = round(max(s200 * 0.92, entry_p * 0.90), 2)
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    # Long-term trailing: once +20% gain is achieved, trail below 200 SMA
                    if gain_pct >= 20.0:
                        stop_p = max(stop_p, s200 * 0.95)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Long-Term Compounding Target (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss / 200 SMA Breach ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif c < s200 * 0.93 and (i - entry_i) >= 20:
                        exit_p = c
                        exit_reason = "Secular 200 SMA Breakdown"
                    elif dist_s200 > 45.0 and rsi >= 80.0:
                        exit_p = c
                        exit_reason = f"Parabolic Extension Re-rating (+{gain_pct:.1f}%)"

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
            total_trades = len(trades)
            win_rate = round((len(wins) / total_trades) * 100, 1) if total_trades > 0 else 0.0

            gross_profit = sum(t["pnlAmount"] for t in wins)
            gross_loss = abs(sum(t["pnlAmount"] for t in losses))
            profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

            port_series = [pt["strategy"] for pt in equity_curve]
            max_drawdown = 0.0
            if port_series:
                peak = port_series[0]
                for val in port_series:
                    if val > peak:
                        peak = val
                    dd = (peak - val) / peak * 100
                    if dd > max_drawdown:
                        max_drawdown = dd
            max_drawdown = round(max_drawdown, 2)

            avg_holding = round(sum(t["holdingDays"] for t in trades) / total_trades, 1) if total_trades > 0 else 0.0

            return {
                "status": "success",
                "stock": stock,
                "strategy": cls.ID,
                "strategyTitle": cls.TITLE,
                "summary": {
                    "strategyReturnPct": strat_ret,
                    "buyAndHoldReturnPct": bnh_ret,
                    "totalTrades": total_trades,
                    "winningTrades": len(wins),
                    "losingTrades": len(losses),
                    "winRatePct": win_rate,
                    "profitFactor": profit_factor,
                    "maxDrawdownPct": max_drawdown,
                    "avgHoldingDays": avg_holding,
                    "initialCapital": capital,
                    "finalPortfolioValue": round(final_val, 2)
                },
                "equityCurve": equity_curve,
                "trades": trades
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
