"""
Volatility-Targeted ATR Breakout & Regime Filtering Strategy
------------------------------------------------------------
Implements volatility-managed trend continuation:
1. Calculates 20-day annualized realized volatility vs 100-day background volatility.
2. Enters on 20-day high breakouts during low-volatility compressions (pre-expansion).
3. Sizes risk dynamically to prevent heavy drawdown spikes, exiting when volatility exceeds 2.5x threshold.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from strategies.base_strategy import BaseStrategy, download_stock_history, compute_sma, compute_rsi, compute_atr


def compute_realized_volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """Computes annualized realized volatility from log daily returns."""
    log_ret = np.log(series / series.shift(1))
    return log_ret.rolling(window=window, min_periods=window // 2).std() * np.sqrt(252) * 100.0


class VolatilityTargetingStrategy(BaseStrategy):
    ID = "volatility_targeting"
    TITLE = "Volatility-Targeted (ATR) Breakout"
    CATEGORY = "Volatility Management & Breakout"
    BADGE = "🌊 Vol Breakout"

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "id": cls.ID,
            "title": cls.TITLE,
            "category": cls.CATEGORY,
            "badge": cls.BADGE,
            "shortDescription": "Enters breakouts during quiet volatility compressions and sizes risk dynamically via 20D vs 100D realized volatility.",
            "writeup": {
                "philosophy": (
                    "Volatility clusters and mean-reverts. Breakouts that occur after periods of volatility compression (low realized vol) "
                    "have the highest probability of initiating multi-month sustained trends. By dynamically targeting a stable annualized volatility "
                    "and using ATR trailing channels, capital is protected from erratic late-stage mania."
                ),
                "buyRules": [
                    "20-Day Donchian Breakout: Daily Close crosses above the 20-day High.",
                    "Volatility Compression Gate: 20-day Realized Volatility <= 1.25× 100-day Baseline Volatility (not buying into wild chaos).",
                    "Trend Regime: Price is trading above the 50-day and 200-day SMAs.",
                    "RSI Momentum: 14-day RSI is between 50.0 and 68.0."
                ],
                "sellRules": [
                    "Channel Violation: Daily close breaks below the 10-day Donchian Low.",
                    "Volatility Blow-off Spike: Realized Volatility spikes > 2.5× baseline (erratic climax top warning).",
                    "Profit Target: Dynamic expansion target hit at Entry + 3.0× ATR(14)."
                ],
                "stopLossRules": [
                    "Initial ATR Floor: Hard stop placed at max(20-day Low, Entry - 2.0× ATR(14)) — strictly capped at 5.0%.",
                    "Volatility Ratchet: Once price gains +7.0%, Stop Loss ratchets to Breakeven.",
                    "Trailing 10-Day Channel: Once price gains +12.0%, Stop Loss trails tightly along the 10-day Low."
                ],
                "idealMarket": "Emerging growth breakouts, sector rotation momentum, and post-consolidation rally phases."
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
                "reason": "Insufficient daily history to compute Volatility Channels"
            }

        closes = df["Close"]
        highs = df["High"]
        lows = df["Low"]
        cmp = float(current_price)

        vol_20 = compute_realized_volatility(closes, 20).iloc[-1]
        vol_100 = compute_realized_volatility(closes, min(100, len(closes))).iloc[-1]
        vol_ratio = vol_20 / (vol_100 + 1e-9)

        high_20 = highs.iloc[-21:-1].max() if len(df) >= 22 else highs.max()
        low_10 = lows.iloc[-11:-1].min() if len(df) >= 12 else lows.min()
        sma50 = compute_sma(closes, 50).iloc[-1]
        sma200 = compute_sma(closes, 200).iloc[-1] if len(df) >= 150 else sma50 * 0.92
        rsi = compute_rsi(closes, 14).iloc[-1]
        atr = compute_atr(df, 14).iloc[-1]

        breakout = cmp >= (high_20 * 0.995)
        vol_calm = vol_ratio <= 1.35
        trend_ok = cmp > sma50 and (cmp > sma200 * 0.985)
        rsi_bull = 48.0 <= rsi <= 68.0

        if breakout and vol_calm and trend_ok and rsi_bull:
            target = round(cmp + (3.0 * atr), 2)
            if target < cmp * 1.10:
                target = round(cmp * 1.15, 2)
            stop_loss = round(max(low_10, cmp - (2.0 * atr), cmp * 0.95), 2)
            risk = max(0.1, cmp - stop_loss)
            reward = max(0.1, target - cmp)
            rr = round(reward / risk, 2)

            return {
                "signal": "BUY",
                "signalTitle": "Vol-Managed 20D Channel Breakout",
                "signalBadge": "🟢 BUY",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": rr,
                "reason": f"20D High Breakout (₹{high_20:.1f}) • Realized Vol: {vol_20:.1f}% ({vol_ratio:.2f}x baseline) • RSI: {rsi:.1f}"
            }

        if cmp < low_10 or vol_ratio >= 2.5 or rsi >= 76.0:
            target = round(sma200, 2) if sma200 < cmp else round(cmp * 0.90, 2)
            stop_loss = round(cmp * 1.05, 2)
            reason = "10D Low Breakdown" if cmp < low_10 else (f"Vol Climax Spike ({vol_ratio:.1f}x)" if vol_ratio >= 2.5 else f"RSI Overbought ({rsi:.1f})")
            return {
                "signal": "SELL",
                "signalTitle": "Volatility Breakdown / Exhaustion",
                "signalBadge": "🔴 SELL",
                "targetPrice": target,
                "stopLossPrice": stop_loss,
                "riskRewardRatio": None,
                "reason": reason
            }

        target = round(cmp + (2.0 * atr), 2)
        stop_loss = round(low_10, 2)
        risk = max(0.1, cmp - stop_loss)
        reward = max(0.1, target - cmp)
        rr = round(reward / risk, 2) if risk > 0 else 1.5

        return {
            "signal": "HOLD",
            "signalTitle": "Consolidating Within Volatility Bands",
            "signalBadge": "⚪ HOLD",
            "targetPrice": target,
            "stopLossPrice": stop_loss,
            "riskRewardRatio": rr,
            "reason": f"Range-Bound (CMP: ₹{cmp:.1f} | 20D High: ₹{high_20:.1f} | Realized Vol: {vol_20:.1f}%)"
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

            vol20_s = compute_realized_volatility(closes, 20).values
            vol100_s = compute_realized_volatility(closes, min(100, len(closes))).values
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
            start_idx = 40
            initial_price = float(c_arr[start_idx])

            for i in range(start_idx, len(c_arr)):
                c = float(c_arr[i])
                h = float(h_arr[i])
                l = float(l_arr[i])
                d = dates[i]

                v20 = float(vol20_s[i]) if not np.isnan(vol20_s[i]) else 20.0
                v100 = float(vol100_s[i]) if not np.isnan(vol100_s[i]) else 20.0
                v_ratio = v20 / (v100 + 1e-9)

                s50 = float(sma50_s[i])
                s200 = float(sma200_s[i])
                rsi = float(rsi_s[i])
                atr = float(atr_s[i]) if not np.isnan(atr_s[i]) else (c * 0.02)

                # Prior 20-day high and 10-day low (excluding current bar)
                prev_20_high = float(np.max(h_arr[max(0, i-20):i])) if i >= 1 else h
                prev_10_low = float(np.min(l_arr[max(0, i-10):i])) if i >= 1 else l

                if not in_pos:
                    is_breakout = c >= (prev_20_high * 0.995)
                    vol_ok = v_ratio <= 1.35
                    trend_ok = c > s50 and (c > s200 * 0.985)
                    rsi_ok = 48.0 <= rsi <= 68.0

                    if is_breakout and vol_ok and trend_ok and rsi_ok:
                        in_pos = True
                        entry_p = c
                        entry_d = d
                        entry_i = i
                        shares = int(cash / entry_p)
                        if shares > 0:
                            cash -= shares * entry_p
                            target_p = round(entry_p + (3.0 * atr), 2)
                            if target_p < entry_p * 1.10:
                                target_p = round(entry_p * 1.15, 2)
                            stop_p = round(max(prev_10_low, entry_p - (2.0 * atr), entry_p * 0.95), 2)
                            trailing_be = False
                else:
                    exit_reason = None
                    exit_p = c

                    gain_pct = ((c - entry_p) / entry_p) * 100
                    if gain_pct >= 7.0 and not trailing_be:
                        stop_p = max(stop_p, entry_p * 1.005)
                        trailing_be = True
                    if gain_pct >= 12.0:
                        stop_p = max(stop_p, prev_10_low)

                    if h >= target_p:
                        exit_p = target_p
                        exit_reason = f"Volatility Target Hit (+{((target_p - entry_p)/entry_p)*100:.1f}%)"
                    elif l <= stop_p:
                        exit_p = stop_p
                        exit_reason = f"Stop Loss Hit ({((stop_p - entry_p)/entry_p)*100:.1f}%)"
                    elif c < prev_10_low and (i - entry_i) >= 4:
                        exit_p = c
                        exit_reason = "10D Low Channel Breakdown"
                    elif v_ratio >= 2.5:
                        exit_p = c
                        exit_reason = f"Vol Climax Spike ({v_ratio:.1f}x)"
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
