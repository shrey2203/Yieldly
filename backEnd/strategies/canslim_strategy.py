"""
CANSLIM Institutional Growth & Leader Momentum Strategy
--------------------------------------------------------
William O'Neil's CANSLIM system:
C: Current quarterly EPS acceleration.
A: Annual earnings growth.
N: New highs / New products / Multi-month base breakout.
S: Supply & Demand (Volume expansion).
L: Leader vs Laggard (Price > 50 SMA > 200 SMA).
I: Institutional Sponsorship (FII / DII presence).
M: Market Direction.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


class CanslimStrategy(BaseStrategy):
    ID = "canslim_growth"
    TITLE = "CANSLIM Institutional Growth & Leadership"
    CATEGORY = "Long-Term Growth & Leadership"
    BADGE = "🏆 CANSLIM Growth"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "William O'Neil's classic methodology: buys market leaders breaking out of consolidation bases with earnings acceleration.",
            "writeup": {
                "philosophy": (
                    "William O'Neil's CANSLIM system is the most successful growth stock methodology in investing history. "
                    "It combines accelerating quarterly earnings and institutional sponsorship (FII/DII accumulation) with "
                    "technical breakouts to 52-week highs. Rather than buying cheap laggards, CANSLIM invests exclusively "
                    "in the top 2% of market leaders."
                ),
                "buyRules": [
                    "Market Leadership & Uptrend: Price is strictly above the 50-day and 200-day SMAs (50 SMA > 200 SMA).",
                    "Base Breakout: Price is trading within 5.0% of its 52-week (252-day) High.",
                    "Volume Accumulation: 5-day average volume exceeds 20-day average volume (institutional pocket pivot).",
                    "Momentum Sweet Spot: 14-day RSI is between 52.0 and 70.0 (strong active leadership expansion)."
                ],
                "sellRules": [
                    "Loss of 50-Day Moving Average: Daily close breaks below the 50-day SMA by > 3.0% on expanding volume.",
                    "Climax Top Exhaustion: RSI reaches > 80.0 with price extended > 35% above the 50-day SMA.",
                    "Major Compounding Milestone: Reaches profit target of +35% to +50% from base breakout."
                ],
                "stopLossRules": [
                    "Strict 7%-8% Hard Stop: Hard cut placed at Entry × 0.925 (O'Neil's golden rule of never taking more than an 8% loss).",
                    "Trailing 50-Day Floor: Once the stock gains +15.0%, Stop Loss automatically trails below the rising 50-day SMA."
                ],
                "idealMarket": "New market bull uptrends, tech & manufacturing sector leaders, and high ROE growth midcaps."
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
                "reason": "Insufficient daily history to compute CANSLIM Base & Highs"
            }

        closes = df["Close"]
        highs = df["High"]
        volumes = df["Volume"]
        cmp = float(current_price)

        high_52w = highs.iloc[-min(252, len(highs)):].max()
        sma50 = compute_sma(closes, 50).iloc[-1]
        sma200 = compute_sma(closes, 200).iloc[-1] if len(df) >= 150 else sma50 * 0.92
        vol5 = volumes.iloc[-5:].mean()
        vol20 = volumes.iloc[-20:].mean()
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        near_high = (cmp >= high_52w * 0.95)
        trend_ok = cmp > sma50 and (sma50 > sma200 * 0.98)
        vol_acc = vol5 >= (vol20 * 1.05)
        rsi_bull = 50.0 <= rsi <= 72.0

        dist_high = ((cmp - high_52w) / high_52w) * 100

        if near_high and trend_ok and rsi_bull:
            target = round(cmp * 1.35, 2)
            stop_loss = round(max(sma50 * 0.965, cmp * 0.925), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "CANSLIM 52-Week High Leadership Base",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"Within {dist_high:+.1f}% of 52W High (₹{high_52w:.1f}) • Leader (50>200 SMA) • RSI: {rsi:.1f}"
            }

        if cmp < (sma50 * 0.96) or rsi >= 82.0:
            target = round(sma200, 2) if sma200 < cmp else round(cmp * 0.88, 2)
            stop_loss = round(cmp * 1.06, 2)
            reason = "50 SMA Institutional Breakdown" if cmp < (sma50 * 0.96) else f"Climax Top Euphoria (RSI: {rsi:.1f})"
            return {
                "signal": "SELL",
                "signalTitle": "CANSLIM Trend Breakdown / Climax",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(cmp * 1.25, 2)
        stop_loss = round(sma50 * 0.965, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 2.0

        return {
            "signal": "HOLD",
            "signalTitle": "Holding CANSLIM Leadership Base",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Leader Structure (CMP: ₹{cmp:.1f} | 52W High: ₹{high_52w:.1f} | 50 SMA: ₹{sma50:.1f})"
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
            volumes = df["Volume"]
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

                # 52-week high up to bar i
                h52 = float(np.max(h_arr[max(0, i-252):i+1]))

                if not in_pos:
                    near_52 = (c >= h52 * 0.95)
                    trend_ok = c > s50 and (s50 > s200 * 0.98)
                    rsi_ok = 50.0 <= rsi <= 72.0

                    if near_52 and trend_ok and rsi_ok:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p * 1.40, 2)
                            stop_p = round(max(s50 * 0.965, entry_p * 0.925), 2)
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 15.0:
                        stop_p = max(stop_p, s50 * 0.97)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"CANSLIM Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"8% Hard Stop / 50 SMA Breach ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif c < s50 * 0.96 and (i - entry_i) >= 10:
                        exit_p = c
                        exit_reason = "50 SMA Institutional Breakdown"
                    elif rsi >= 82.0:
                        exit_p = c
                        exit_reason = f"Climax Top Euphoria (RSI: {rsi:.1f})"

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
