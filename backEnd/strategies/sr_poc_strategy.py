"""
Support/Resistance & Robust Volume Profile POC Floor Strategy
--------------------------------------------------------------
Mean-reversion strategy entering at validated institutional price floors (S1 Support & Volume POC)
with low RSI and riding bounces to overhead resistance targets.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from scipy.signal import argrelextrema

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_rsi, compute_sma


class SrPocStrategy(BaseStrategy):
    ID = "sr_poc"
    TITLE = "S/R & Robust Volume Profile POC Floor"
    CATEGORY = "Institutional Mean Reversion"
    BADGE = "🎯 S/R & POC"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Buys near institutional support zones and Robust Volume POC with low RSI, exiting at resistance ceilings.",
            "writeup": {
                "philosophy": (
                    "Heavy volume accumulations (Point of Control) and historical swing reaction lows represent price levels where large institutions defend positions. "
                    "Entering near these validated floors provides a tight, well-defined stop loss with large upside to the next overhead resistance zone."
                ),
                "buyRules": [
                    "Support Confluence: Price is within -3.5% to +1.0% of Key Support (S1) or Robust Volume POC floor.",
                    "RSI Cool-off: 14-day RSI ≤ 58.0 (guaranteeing room for momentum expansion before reaching overbought).",
                    "Candle Confirmation: Daily close finishes in upper half of range, rejecting lower price levels."
                ],
                "sellRules": [
                    "Resistance Target: Price tests overhead Resistance ceiling (R1 ± 1.5%) or hits +12.0% take-profit.",
                    "Overbought Warning: 14-day RSI ≥ 68.0 indicating exhaustion of short-term buying power."
                ],
                "stopLossRules": [
                    "Floor Breach: Strict hard stop placed at S1 Support × 0.965 (3.5% below the support level).",
                    "Trend Breakdown: Exit if daily close violates 50-day SMA by > 5%."
                ],
                "idealMarket": "Range-bound markets, institutional consolidation channels, and high-quality value/growth compounders."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, 
                        supports: list = None, resistances: list = None, 
                        poc: dict = None, rsi: float = None) -> Dict[str, Any]:
        if not current_price or current_price <= 0:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Current price unavailable"
            }

        cmp = float(current_price)
        s1 = supports[0]["price"] if supports else None
        r1 = resistances[0]["price"] if resistances else None
        poc_price = poc["price"] if poc else None
        poc_side = poc.get("side") if poc else None

        dist_s1 = ((s1 - cmp) / cmp * 100) if s1 else None
        dist_poc = ((poc_price - cmp) / cmp * 100) if (poc_price and poc_side == "support") else None
        dist_r1 = ((r1 - cmp) / cmp * 100) if r1 else None

        # BUY check
        near_s1 = dist_s1 is not None and -3.5 <= dist_s1 <= 1.0
        near_poc = dist_poc is not None and -3.0 <= dist_poc <= 1.0
        rsi_ok_buy = rsi is not None and rsi <= 58.0

        if (near_s1 or near_poc) and rsi_ok_buy:
            ref_support = s1 if near_s1 else poc_price
            target = r1 if (r1 and r1 > cmp * 1.04) else round(cmp * 1.12, 2)
            stop_loss = round(ref_support * 0.965, 2)

            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            reason_parts = []
            if near_s1: reason_parts.append(f"At S1 Support ₹{s1} ({dist_s1:+.1f}%)")
            if near_poc: reason_parts.append(f"At Volume POC ₹{poc_price}")
            if rsi: reason_parts.append(f"RSI {rsi:.1f} (Room to Run)")

            return {
                "signal": "BUY",
                "signalTitle": "Buy at Support Zone",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": " • ".join(reason_parts)
            }

        # SELL check
        near_r1 = dist_r1 is not None and abs(dist_r1) <= 1.5
        rsi_overbought = rsi is not None and rsi >= 68.0

        if near_r1 or rsi_overbought:
            target = s1 if (s1 and s1 < cmp * 0.96) else round(cmp * 0.90, 2)
            stop_loss = round(r1 * 1.035, 2) if r1 else round(cmp * 1.05, 2)

            reason_parts = []
            if near_r1: reason_parts.append(f"Testing R1 Resistance ₹{r1} ({dist_r1:+.1f}%)")
            if rsi_overbought: reason_parts.append(f"RSI {rsi:.1f} (Overbought Exhaustion)")

            return {
                "signal": "SELL",
                "signalTitle": "Sell at Resistance / Overbought",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": " • ".join(reason_parts)
            }

        # HOLD
        target = r1 if r1 else round(cmp * 1.10, 2)
        stop_loss = s1 if s1 else round(cmp * 0.95, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.5

        return {
            "signal": "HOLD",
            "signalTitle": "Hold / Mid-Range Consolidation",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Trading in mid-range between Support (₹{s1 or '—'}) and Resistance (₹{r1 or '—'})"
        }

    @classmethod
    def run_backtest(cls, stock: str, lookback_years: int = 2, initial_capital: float = 100000.0) -> Dict[str, Any]:
        try:
            df = download_stock_history(stock, lookback_years=lookback_years, min_bars=60)
            if df is None or len(df) < 60:
                return {"status": "error", "message": f"Insufficient price history for {stock}"}

            closes = df["Close"].values.astype(float)
            highs = df["High"].values.astype(float)
            lows = df["Low"].values.astype(float)
            dates = [str(d)[:10] for d in df.index]

            rsi_series = compute_rsi(df["Close"], 14).values
            sma50_series = compute_sma(df["Close"], 50).values

            capital = float(initial_capital)
            cash = capital
            shares = 0
            in_pos = False
            entry_p = 0.0
            entry_d = ""
            entry_i = 0
            stop_p = 0.0
            target_p = 0.0
            trailing_sl = False

            trades = []
            equity_curve = []
            start_idx = min(50, len(closes) - 10)
            initial_price = float(closes[start_idx])

            for i in range(start_idx, len(closes)):
                c = float(closes[i])
                h = float(highs[i])
                l = float(lows[i])
                d = dates[i]

                # Rolling Support/Resistance window (no future lookahead)
                w_lows = lows[max(0, i-60):i]
                w_highs = highs[max(0, i-60):i]

                s_idx = argrelextrema(w_lows, np.less_equal, order=5)[0]
                supps = [float(w_lows[idx]) for idx in s_idx if w_lows[idx] < c]
                nearest_s = max(supps) if supps else float(w_lows.min())

                r_idx = argrelextrema(w_highs, np.greater_equal, order=5)[0]
                resis = [float(w_highs[idx]) for idx in r_idx if w_highs[idx] > c]
                nearest_r = min(resis) if resis else c * 1.15

                if not in_pos:
                    near_supp = (c - nearest_s) / nearest_s <= 0.025 and (c >= nearest_s * 0.985)
                    candle_strong = (c - l) >= 0.60 * (h - l + 1e-6) and (i > 0 and c >= closes[i-1])
                    rsi_val = float(rsi_series[i])
                    sma50_val = float(sma50_series[i]) if not np.isnan(sma50_series[i]) else c

                    if near_supp and candle_strong and (rsi_val <= 55.0) and (c >= sma50_val * 0.95):
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = nearest_r if nearest_r > entry_p * 1.05 else round(entry_p * 1.12, 2)
                            stop_p = round(nearest_s * 0.965, 2)
                            trailing_sl = False
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 5.0 and not trailing_sl:
                        stop_p = max(stop_p, entry_p * 1.005)  # Breakeven
                        trailing_sl = True
                    if gain_pct >= 8.0:
                        stop_p = max(stop_p, entry_p * 1.04)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss Hit ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif float(rsi_series[i]) >= 70.0:
                        exit_p = c
                        exit_reason = f"RSI Overbought ({rsi_series[i]:.1f})"
                    elif (i - entry_i) >= 30:
                        exit_p = c
                        exit_reason = "Max Holding Period (30d)"

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
                last_c = float(closes[-1])
                cash += shares * last_c
                pnl_pct = round(((last_c - entry_p) / entry_p) * 100, 2)
                trades.append({
                    "entryDate": entry_d,
                    "entryPrice": round(entry_p, 2),
                    "exitDate": dates[-1],
                    "exitPrice": round(last_c, 2),
                    "holdingDays": len(closes) - 1 - entry_i,
                    "pnlPct": pnl_pct,
                    "pnlAmount": round((last_c - entry_p) * shares, 2),
                    "reason": "Backtest Period End"
                })

            final_val = cash
            strat_ret = round(((final_val - capital) / capital) * 100, 2)
            last_price = float(closes[-1])
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
