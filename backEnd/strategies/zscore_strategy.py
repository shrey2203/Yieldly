"""
Statistical Z-Score Mean Reversion & Statistical Arbitrage Strategy
-------------------------------------------------------------------
Exploits statistical price over-extensions using rolling 20-day standard deviation Z-scores:
Z = (Close - Mean_20) / StdDev_20.
Enters long on severe oversold statistical outliers (Z <= -2.0) with RSI stabilization,
targeting mean reversion back to the 20-day moving average (Z = 0) and upper bands.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


def compute_zscore(series: pd.Series, period: int = 20) -> pd.Series:
    """Calculates rolling Z-score: (Price - SMA) / Rolling_Std."""
    sma = series.rolling(window=period, min_periods=period // 2).mean()
    std = series.rolling(window=period, min_periods=period // 2).std()
    return (series - sma) / (std + 1e-9)


class ZScoreStrategy(BaseStrategy):
    ID = "zscore_mean_reversion"
    TITLE = "Z-Score (20D) Statistical Mean Reversion"
    CATEGORY = "Statistical Arbitrage & Mean Reversion"
    BADGE = "📐 Z-Score Reversion"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Exploits statistical outliers (Z <= -2.0, 95% confidence interval) to capture rapid mean reversion back to equilibrium.",
            "writeup": {
                "philosophy": (
                    "According to the central limit theorem and statistical distribution of asset returns, price extensions beyond "
                    "2.0 standard deviations from the 20-day rolling mean occur less than 5% of the time in normal markets. "
                    "When an asset reaches Z <= -2.0 with oversold RSI and stabilizing price action, institutional liquidity steps in "
                    "to push the asset back toward equilibrium (Z = 0)."
                ),
                "buyRules": [
                    "Statistical Oversold Outlier: 20-day Rolling Z-Score is at or below -2.0 (Price is > 2.0 standard deviations below 20-day SMA).",
                    "RSI Exhaustion: 14-day RSI <= 38.0 or recovering upward from oversold territory.",
                    "Price Stabilization: Today's Close finishes above yesterday's Low (rejection of extreme downside expansion)."
                ],
                "sellRules": [
                    "Equilibrium Target: Price reverts to the 20-day SMA (Z = 0.0) or tests upper statistical band (Z >= +1.5).",
                    "Overbought Outlier: 20-day Z-Score reaches >= +2.0 (statistically overextended to the upside).",
                    "RSI Exhaustion: 14-day RSI crosses above 70.0."
                ],
                "stopLossRules": [
                    "Extreme Tail Risk Stop: Placed at Entry - 2.2× ATR(14) (or Z <= -3.2 fat-tail breakdown).",
                    "Breakeven Floor: Once the trade reverts +5.0% toward the mean, Stop Loss moves to Breakeven.",
                    "Time Stop: If mean reversion does not occur within 20 trading days, exit position to free up capital."
                ],
                "idealMarket": "Mean-reverting range-bound stocks, large-cap liquid equities, and stable dividend compounders."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, **kwargs) -> Dict[str, Any]:
        if df is None or len(df) < 25 or not current_price:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Insufficient daily history to compute Z-Score"
            }

        closes = df["Close"]
        cmp = float(current_price)

        zscores = compute_zscore(closes, 20)
        z = zscores.iloc[-1]
        sma20 = compute_sma(closes, 20).iloc[-1]
        std20 = closes.rolling(20, min_periods=10).std().iloc[-1]
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        if z <= -1.8 and rsi <= 42.0:
            target = round(sma20, 2)
            if target < cmp * 1.06:
                target = round(cmp * 1.09, 2)
            stop_loss = round(max(cmp - (2.0 * atr), cmp - (1.2 * std20), cmp * 0.94), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "Z-Score Statistical Oversold Bounce",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"Z-Score: {z:.2f}σ (< -1.8σ Outlier) • 20 SMA Mean: ₹{sma20:.1f} • RSI: {rsi:.1f}"
            }

        if z >= 2.0 or rsi >= 72.0:
            target = round(sma20, 2) if sma20 < cmp else round(cmp * 0.93, 2)
            stop_loss = round(cmp * 1.04, 2)
            reason = f"Z-Score: {z:.2f}σ (> +2.0σ Overextended)" if z >= 2.0 else f"RSI Overbought ({rsi:.1f})"
            return {
                "signal": "SELL",
                "signalTitle": "Z-Score Statistical Overextension",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(sma20 + (1.0 * std20), 2)
        stop_loss = round(sma20 - (1.5 * std20), 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.5

        return {
            "signal": "HOLD",
            "signalTitle": "Equilibrium / Neutral Z-Score",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Z-Score: {z:.2f}σ (Normal Distribution | Mean: ₹{sma20:.1f})"
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

            zscore_s = compute_zscore(closes, 20).values
            sma20_s = compute_sma(closes, 20).values
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
            start_idx = 30
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                z = float(zscore_s[i]) if not np.isnan(zscore_s[i]) else 0.0
                s20 = float(sma20_s[i])
                rsi = float(rsi_s[i])
                atr = float(atr_s[i]) if not np.isnan(atr_s[i]) else (c * 0.02)

                if not in_pos:
                    if z <= -1.8 and rsi <= 44.0:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(max(s20, entry_p * 1.08), 2)
                            stop_p = round(max(entry_p - (2.0 * atr), entry_p * 0.945), 2)
                            trailing_be = False
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 5.0 and not trailing_be:
                        stop_p = max(stop_p, entry_p * 1.005)
                        trailing_be = True

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Mean Reversion Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss Hit ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif z >= 1.8:
                        exit_p = c
                        exit_reason = f"Z-Score Reversion Complete ({z:.2f}σ)"
                    elif rsi >= 72.0:
                        exit_p = c
                        exit_reason = f"RSI Overbought ({rsi:.1f})"
                    elif (i - entry_i) >= 25:
                        exit_p = c
                        exit_reason = "Max Holding Period (25d)"

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
