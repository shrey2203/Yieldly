"""
20/50/200 EMA Trend-Pullback & Volume Expansion Strategy
---------------------------------------------------------
Enters on institutional trend continuation when price is supported by the 20 EMA
in a confirmed bull regime (Price > 200 EMA & 20 EMA > 50 EMA) accompanied by volume surges.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_ema, compute_rsi, compute_atr


class EmaMomentumStrategy(BaseStrategy):
    ID = "ema_momentum"
    TITLE = "20/50 EMA Trend & Volume Surge"
    CATEGORY = "Momentum & Trend Following"
    BADGE = "⚡ Momentum"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Rides institutional momentum by buying 20 EMA pullbacks in 200 EMA bull regimes with volume expansion.",
            "writeup": {
                "philosophy": (
                    "Institutional accumulation creates sustained momentum where the 20-day Exponential Moving Average "
                    "acts as a dynamic launchpad. Rather than chasing extended tops, this strategy waits for shallow consolidations "
                    "or fresh golden crossovers to enter with an asymmetric risk-reward ratio."
                ),
                "buyRules": [
                    "Macro Bull Regime: Daily Close must be strictly above the 200 EMA (Bull market baseline).",
                    "Intermediate Uptrend: 20 EMA must be trading above the 50 EMA.",
                    "Pullback / Breakout Trigger: Price pulls back to test the 20 EMA (within 2.0%) or 20 EMA crosses above 50 EMA within the last 3 days.",
                    "Volume Confirmation: Daily Volume must exceed 1.3× of the 20-day Volume SMA (Institutional participation).",
                    "RSI Sweet Spot: 14-period RSI must be between 45.0 and 65.0 (bullish expansion zone, avoiding overbought traps)."
                ],
                "sellRules": [
                    "Profit Target: Dynamic Take-Profit set at Entry + 2.5× ATR(14) (yielding approx. +10% to +16% gain).",
                    "Momentum Exhaustion: Daily RSI closes above 75.0 (Overbought blow-off top warning).",
                    "Trend Breakdown: Daily close breaks below the 50-day EMA."
                ],
                "stopLossRules": [
                    "Initial Stop Loss: Set at 50 EMA × 0.98 or Entry - 1.8× ATR(14) (strictly capped at 4.5% max risk).",
                    "Breakeven Trailing: Once the trade reaches +6.0% profit, the Stop Loss is automatically trailed to Breakeven (Entry Price).",
                    "Profit Protection: Once trade reaches +10.0%, trailing SL locks in at least +5.0% profit."
                ],
                "idealMarket": "Strong trending bull markets, high-growth midcaps, and institutional momentum leaders."
            }
        }

    @classmethod
    def generate_signal(cls, df: pd.DataFrame = None, current_price: float = None, **kwargs) -> Dict[str, Any]:
        if df is None or len(df) < 50 or not current_price:
            return {
                "signal": "HOLD",
                "signalTitle": "Data Insufficient",
                "signalBadge": "⚪ HOLD",
                "targetPrice": None,
                "stopLossPrice": None,
                "riskRewardRatio": None,
                "reason": "Insufficient daily history to compute EMAs"
            }

        closes = df["Close"]
        volumes = df["Volume"]
        cmp = float(current_price)

        ema20 = compute_ema(closes, 20).iloc[-1]
        ema50 = compute_ema(closes, 50).iloc[-1]
        ema200 = compute_ema(closes, 200).iloc[-1] if len(df) >= 200 else ema50 * 0.92
        vol_sma20 = volumes.rolling(20, min_periods=5).mean().iloc[-1]
        cur_vol = volumes.iloc[-1]
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        dist_ema20 = ((cmp - ema20) / ema20) * 100
        vol_ratio = (cur_vol / (vol_sma20 + 1e-9))

        above_ema200 = cmp > (ema200 * 0.98)
        trend_up = ema20 > ema50
        near_ema20 = -2.0 <= dist_ema20 <= 2.5
        vol_surge = vol_ratio >= 1.25
        rsi_bullish = 44.0 <= rsi <= 66.0

        if above_ema200 and trend_up and near_ema20 and rsi_bullish:
            target = round(cmp + (2.5 * atr), 2)
            if target < cmp * 1.08:
                target = round(cmp * 1.12, 2)
            stop_loss = round(max(ema50 * 0.98, cmp - (1.8 * atr), cmp * 0.955), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            reasons = [
                f"Tested 20 EMA ₹{ema20:.1f} ({dist_ema20:+.1f}%)",
                f"20>50 EMA Uptrend",
                f"RSI {rsi:.1f} (Expansion)",
            ]
            if vol_surge:
                reasons.append(f"Vol {vol_ratio:.1f}x SMA")

            return {
                "signal": "BUY",
                "signalTitle": "20 EMA Momentum Pullback",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": " • ".join(reasons)
            }

        if rsi >= 74.0 or cmp < (ema50 * 0.98):
            target = round(ema200, 2) if ema200 < cmp else round(cmp * 0.92, 2)
            stop_loss = round(cmp * 1.04, 2)
            reasons = []
            if rsi >= 74.0: reasons.append(f"RSI {rsi:.1f} (Overbought)")
            if cmp < (ema50 * 0.98): reasons.append(f"Broke 50 EMA ₹{ema50:.1f}")

            return {
                "signal": "SELL",
                "signalTitle": "Momentum Exhaustion / Trend Breakdown",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": " • ".join(reasons) or "Trend momentum fading"
            }

        target = round(cmp + (2.0 * atr), 2)
        stop_loss = round(ema50 * 0.98, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.5

        return {
            "signal": "HOLD",
            "signalTitle": "Trend In Progress / Consolidation",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Holding trend (CMP: ₹{cmp:.1f} | 20 EMA: ₹{ema20:.1f} | 50 EMA: ₹{ema50:.1f})"
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

            ema20_s = compute_ema(closes, 20).values
            ema50_s = compute_ema(closes, 50).values
            ema200_s = compute_ema(closes, 200).values if len(df) >= 150 else (ema50_s * 0.93)
            vol_sma20_s = volumes.rolling(20, min_periods=5).mean().values
            rsi_s = compute_rsi(closes, 14).values
            atr_s = compute_atr(df, 14).values

            c_arr = closes.values.astype(float)
            h_arr = highs.values.astype(float)
            l_arr = lows.values.astype(float)
            v_arr = volumes.values.astype(float)

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
            start_idx = 50
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                e20 = float(ema20_s[i])
                e50 = float(ema50_s[i])
                e200 = float(ema200_s[i])
                vol_sma = float(vol_sma20_s[i]) if not np.isnan(vol_sma20_s[i]) else 1.0
                vol = float(v_arr[i])
                rsi = float(rsi_s[i])
                atr = float(atr_s[i]) if not np.isnan(atr_s[i]) else (c * 0.02)

                dist_e20 = ((c - e20) / e20) * 100
                vol_ratio = vol / (vol_sma + 1e-9)

                if not in_pos:
                    trend_ok = (c > e200 * 0.985) and (e20 > e50)
                    near_20 = -2.0 <= dist_e20 <= 2.5
                    fresh_cross = (i >= 2 and ema20_s[i-1] <= ema50_s[i-1] and e20 > e50)
                    vol_ok = vol_ratio >= 1.2
                    rsi_ok = 44.0 <= rsi <= 66.0

                    if trend_ok and (near_20 or fresh_cross) and vol_ok and rsi_ok:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p + (2.5 * atr), 2)
                            if target_p < entry_p * 1.09:
                                target_p = round(entry_p * 1.13, 2)
                            stop_p = round(max(e50 * 0.98, entry_p - (1.8 * atr), entry_p * 0.955), 2)
                            trailing_be = False
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 6.0 and not trailing_be:
                        stop_p = max(stop_p, entry_p * 1.005)
                        trailing_be = True
                    if gain_pct >= 10.0:
                        stop_p = max(stop_p, entry_p * 1.05)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss Hit ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif rsi >= 75.0:
                        exit_p = c
                        exit_reason = f"RSI Overbought ({rsi:.1f})"
                    elif c < e50 * 0.98 and (i - entry_i) >= 4:
                        exit_p = c
                        exit_reason = "50 EMA Breakdown"
                    elif (i - entry_i) >= 40:
                        exit_p = c
                        exit_reason = "Max Holding Period (40d)"

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
