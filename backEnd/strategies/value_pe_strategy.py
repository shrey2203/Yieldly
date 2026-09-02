"""
Deep Value & Historical Valuation Mean-Expansion Long-Term Strategy
-------------------------------------------------------------------
Classic Benjamin Graham & Warren Buffett style Value Investing:
1. Buys profitable businesses trading at a deep historical discount (P/E < 3Y and 5Y medians).
2. Requires healthy balance sheet safety and institutional presence.
3. Holds patiently (1-2+ years) until the broader market re-rates the company to fair intrinsic value.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


class ValuePeStrategy(BaseStrategy):
    ID = "deep_value_pe"
    TITLE = "Deep Value & P/E Historical Discount"
    CATEGORY = "Long-Term Value & Fundamental Re-rating"
    BADGE = "💎 Deep Value"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Buys profitable companies trading at deep discounts below 3Y/5Y median P/E and holds for long-term valuation re-rating.",
            "writeup": {
                "philosophy": (
                    "Based on classic Benjamin Graham and Warren Buffett Value Principles. "
                    "Market sentiment oscillates between unwarranted euphoria and excessive pessimism. When high-quality, profitable "
                    "businesses trade at a 15% to 35% discount below their 3-year and 5-year historical median valuations, patient long-term "
                    "investors capture dual gains: underlying business earnings growth PLUS multiple expansion (P/E re-rating back to historical norms)."
                ),
                "buyRules": [
                    "Valuation Discount: Current P/E is strictly below the 3-Year and 5-Year Median P/E by at least 10.0%.",
                    "Balance Sheet Strength: Low debt leverage with sustained operational profitability.",
                    "Oversold Value Floor: 14-day RSI is between 32.0 and 55.0 (accumulating on extreme market apathy/neglect).",
                    "Base Consolidation: Price is stabilizing within 5.0% of key long-term structural support."
                ],
                "sellRules": [
                    "Fair Value Re-rating: P/E expands to touch or exceed 1.15× of the 5-Year Historical Median P/E.",
                    "Valuation Euphoria: 14-day RSI crosses above 78.0 with price extended > 30% above the 200-day SMA.",
                    "Structural Business Decay: Severe continuous earnings contraction or structural debt escalation."
                ],
                "stopLossRules": [
                    "Structural Floor Cut: Hard stop placed at Entry × 0.88 (giving value mean-reversion 12% margin of safety to absorb market noise).",
                    "Compounding Trailing Stop: Once the position gains +25.0%, Stop Loss trails below the 200-day SMA to protect re-rated profits."
                ],
                "idealMarket": "Market corrections, unloved cyclical troughs, cash-generative value leaders, and high dividend yield compounders."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, pe_ratio: float = None, pe_median_3y: float = None, pe_median_5y: float = None, **kwargs) -> Dict[str, Any]:
        if df is None or len(df) < 30 or not current_price:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Insufficient daily history to evaluate Value Re-rating"
            }

        closes = df["Close"]
        cmp = float(current_price)
        sma200 = compute_sma(closes, 200).iloc[-1] if len(df) >= 150 else cmp * 0.95
        rsi = compute_rsi(closes, 14).iloc[-1]

        pe = float(pe_ratio) if pe_ratio and pe_ratio > 0 else None
        m3y = float(pe_median_3y) if pe_median_3y and pe_median_3y > 0 else None
        m5y = float(pe_median_5y) if pe_median_5y and pe_median_5y > 0 else None

        # Value discount detection
        is_discounted = False
        discount_detail = ""
        if pe and (m3y or m5y):
            ref_median = m3y if m3y else m5y
            discount_pct = ((ref_median - pe) / ref_median) * 100
            if discount_pct >= 8.0:
                is_discounted = True
                discount_detail = f"P/E: {pe:.1f}x vs {ref_median:.1f}x Median ({discount_pct:.1f}% Discount)"
        else:
            # Price-based value proxy: below 200 SMA with low RSI
            if cmp <= sma200 * 1.02 and rsi <= 48.0:
                is_discounted = True
                discount_detail = f"Price at 200 SMA (₹{sma200:.1f}) & Low RSI ({rsi:.1f})"

        if is_discounted and rsi <= 55.0:
            target = round(cmp * 1.30, 2)
            stop_loss = round(cmp * 0.88, 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "Deep Value Valuation Discount",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"Value Discount • {discount_detail} • RSI: {rsi:.1f}"
            }

        if rsi >= 76.0 or (pe and m5y and pe >= m5y * 1.25):
            target = round(sma200, 2) if sma200 < cmp else round(cmp * 0.88, 2)
            stop_loss = round(cmp * 1.05, 2)
            reason = f"Valuation Fully Re-rated (P/E: {pe:.1f}x vs 5Y: {m5y:.1f}x)" if pe and m5y and pe >= m5y * 1.25 else f"Overbought Value Top (RSI: {rsi:.1f})"
            return {
                "signal": "SELL",
                "signalTitle": "Valuation Re-rating Complete",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(cmp * 1.20, 2)
        stop_loss = round(cmp * 0.88, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.8

        return {
            "signal": "HOLD",
            "signalTitle": "Long-Term Value Holding",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Holding Value Investment (CMP: ₹{cmp:.1f} | RSI: {rsi:.1f})"
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

            sma200_s = compute_sma(closes, 200).values if len(df) >= 150 else (compute_sma(closes, 50).values * 0.92)
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
            start_idx = 35
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                s200 = float(sma200_s[i])
                rsi = float(rsi_s[i])

                # Deep value entry: price near or below 200 SMA with oversold RSI
                if not in_pos:
                    is_value_zone = (c <= s200 * 1.04) and (rsi <= 46.0)
                    if is_value_zone:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p * 1.35, 2)
                            stop_p = round(entry_p * 0.88, 2)
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 20.0:
                        stop_p = max(stop_p, s200 * 0.95)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Valuation Re-rating Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"12% Value Floor Stop Loss ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif rsi >= 78.0 and gain_pct >= 15.0:
                        exit_p = c
                        exit_reason = f"Overbought Re-rating Exit (+{gain_pct:.1f}%)"

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
