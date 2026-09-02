"""
12-1 Month Quantitative Relative Strength & Intermediate Momentum Strategy
-------------------------------------------------------------------------
Based on the foundational Jegadeesh-Titman (1993) academic momentum anomaly.
Ranks and enters assets demonstrating strong 12-month return momentum with a 1-month skip
(t-252 to t-21) to filter short-term microstructure bid-ask bounce/mean-reversion.
Rides winners with 50-day moving average trailing stops.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


class MomentumStrategy(BaseStrategy):
    ID = "cross_sectional_momentum"
    TITLE = "12-1M Quantitative Relative Momentum"
    CATEGORY = "Academic Momentum Anomaly"
    BADGE = "🚀 12M Momentum"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Classic academic 12-1 Month momentum (Jegadeesh & Titman) filtering out short-term 1M microstructure reversal.",
            "writeup": {
                "philosophy": (
                    "Documented by Narasimhan Jegadeesh and Sheridan Titman (Journal of Finance, 1993), assets with superior past 12-month returns "
                    "continue to outperform over intermediate 3-12 month horizons due to slow institutional information diffusion and earnings drift. "
                    "Skipping the most recent month (21 days) completely removes short-term bid-ask microstructure noise and reversal traps."
                ),
                "buyRules": [
                    "12-1M Momentum Anomaly: Return over the past 252 days skipping the last 21 days (t-252 to t-21) exceeds +15.0%.",
                    "Intermediate 6-Month Trend: Return over the past 126 days is strictly positive (> +6.0%).",
                    "Regime Confirmation: Price is trading above both the 50-day and 200-day Simple Moving Averages.",
                    "Healthy Momentum RSI: 14-day RSI is between 46.0 and 68.0 (active momentum expansion without topping)."
                ],
                "sellRules": [
                    "Intermediate Breakdown: Daily close breaks below the 50-day SMA by > 2.5%.",
                    "6-Month Momentum Negative: Intermediate 6-month return turns negative (loss of leadership status).",
                    "Overbought Blow-off: RSI crosses above 78.0 with extreme extension > 25% above 200 SMA.",
                    "Profit Target: Dynamic milestone target reached at +20.0% gain from entry."
                ],
                "stopLossRules": [
                    "Initial Stop Loss: Placed at max(50 SMA × 0.97, Entry - 2.2× ATR(14)) — strictly capped at 5.0% risk.",
                    "Breakeven Floor: Once trade gains +7.0%, Stop Loss automatically ratchets to Breakeven.",
                    "Trailing Moving Average: Once trade exceeds +12.0%, Stop Loss trails tightly below the rising 50-day SMA."
                ],
                "idealMarket": "Sustained secular bull trends, high relative-strength market leaders, and earnings compounders."
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
                "reason": "Insufficient daily history to compute 12-1M Momentum"
            }

        closes = df["Close"]
        cmp = float(current_price)

        # 12-1M Momentum calculation (t-252 to t-21)
        idx_12m = max(0, len(closes) - min(252, len(closes)))
        idx_1m = max(0, len(closes) - 21)
        p_12m = closes.iloc[idx_12m]
        p_1m = closes.iloc[idx_1m]
        mom_12_1m = ((p_1m - p_12m) / p_12m) * 100

        # 6-Month Momentum (t-126)
        idx_6m = max(0, len(closes) - min(126, len(closes)))
        p_6m = closes.iloc[idx_6m]
        mom_6m = ((closes.iloc[-1] - p_6m) / p_6m) * 100

        sma50 = compute_sma(closes, 50).iloc[-1]
        sma200 = compute_sma(closes, 200).iloc[-1] if len(df) >= 150 else sma50 * 0.92
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        mom_strong = mom_12_1m >= 12.0 and mom_6m >= 5.0
        trend_bull = cmp > sma50 and (cmp > sma200 * 0.985)
        rsi_bull = 45.0 <= rsi <= 68.0

        if mom_strong and trend_bull and rsi_bull:
            target = round(cmp * 1.18, 2)
            stop_loss = round(max(sma50 * 0.97, cmp - (2.0 * atr), cmp * 0.95), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "12-1M Relative Strength Leadership",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"12-1M Mom: +{mom_12_1m:.1f}% • 6M Mom: +{mom_6m:.1f}% • Price > 50 & 200 SMA • RSI: {rsi:.1f}"
            }

        if cmp < (sma50 * 0.975) or mom_6m < -5.0 or rsi >= 78.0:
            target = round(sma200, 2) if sma200 < cmp else round(cmp * 0.90, 2)
            stop_loss = round(cmp * 1.05, 2)
            reason = "50 SMA Breakdown" if cmp < (sma50 * 0.975) else (f"Momentum Negative ({mom_6m:.1f}%)" if mom_6m < -5.0 else f"RSI Overbought ({rsi:.1f})")
            return {
                "signal": "SELL",
                "signalTitle": "Momentum Leadership Breakdown",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(cmp * 1.12, 2)
        stop_loss = round(sma50 * 0.97, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.5

        return {
            "signal": "HOLD",
            "signalTitle": "Maintaining Momentum Trajectory",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Holding Momentum (CMP: ₹{cmp:.1f} | 12-1M Mom: {mom_12_1m:+.1f}% | 6M Mom: {mom_6m:+.1f}%)"
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
            atr_s = compute_atr(df, 14).values

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
            trailing_be = False

            trades = []
            equity_curve = []
            start_idx = 45
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                s50 = float(sma50_s[i])
                s200 = float(sma200_s[i])
                rsi = float(rsi_s[i])
                atr = float(atr_s[i]) if not np.isnan(atr_s[i]) else (c * 0.02)

                # 12-1M Momentum at step i
                idx_12m = max(0, i - min(252, i))
                idx_1m = max(0, i - 21)
                p_12m = float(c_arr[idx_12m])
                p_1m = float(c_arr[idx_1m])
                mom_12_1 = ((p_1m - p_12m) / p_12m) * 100

                idx_6m = max(0, i - min(126, i))
                p_6m = float(c_arr[idx_6m])
                mom_6 = ((c - p_6m) / p_6m) * 100

                if not in_pos:
                    mom_ok = (mom_12_1 >= 10.0 or i < 70) and mom_6 >= 4.0
                    trend_ok = c > s50 and (c > s200 * 0.985)
                    rsi_ok = 45.0 <= rsi <= 68.0

                    if mom_ok and trend_ok and rsi_ok:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p * 1.18, 2)
                            stop_p = round(max(s50 * 0.97, entry_p - (2.0 * atr), entry_p * 0.95), 2)
                            trailing_be = False
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 7.0 and not trailing_be:
                        stop_p = max(stop_p, entry_p * 1.005)
                        trailing_be = True
                    if gain_pct >= 12.0:
                        stop_p = max(stop_p, s50 * 0.98)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Momentum Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss Hit ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif c < s50 * 0.975 and (i - entry_i) >= 5:
                        exit_p = c
                        exit_reason = "50 SMA Breakdown"
                    elif mom_6 < -5.0:
                        exit_p = c
                        exit_reason = "6M Relative Momentum Loss"
                    elif (i - entry_i) >= 50:
                        exit_p = c
                        exit_reason = "Max Holding Period (50d)"

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
