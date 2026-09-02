"""
Financial and Mathematical Calculations Engine.
Provides centralized, high-precision, and robust calculations for:
- CAGR (Compound Annual Growth Rate)
- XIRR (Extended Internal Rate of Return with Newton-Raphson & Bisection solvers)
- Absolute Return / P&L Percentage
- Holding Period & Capital Gains Tax Classification (STCG / LTCG)
"""

from datetime import date, datetime
from typing import List, Tuple, Union, Optional
import math


def calculate_holding_days(start_date: Union[date, datetime, str], end_date: Optional[Union[date, datetime, str]] = None) -> int:
    """
    Calculate the elapsed days between start_date and end_date (defaults to today).
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
    elif isinstance(start_date, datetime):
        start_date = start_date.date()

    if end_date is None:
        end_date = date.today()
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date[:10], "%Y-%m-%d").date()
    elif isinstance(end_date, datetime):
        end_date = end_date.date()

    return max((end_date - start_date).days, 0)


def calculate_abs_return(pnl: float, total_investment: float) -> float:
    """
    Calculate absolute percentage return: (PnL / Total Investment) * 100
    """
    if not total_investment or total_investment == 0:
        return 0.0
    return round((float(pnl) / float(total_investment)) * 100.0, 2)


def calculate_cagr(initial_value: float, final_value: float, days: int) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR).
    Formula: ((final_value / initial_value) ** (365 / days) - 1) * 100
    """
    if days <= 0 or initial_value <= 0 or final_value <= 0:
        return 0.0
    try:
        one_by_time = 365.0 / float(days)
        cagr = ((float(final_value) / float(initial_value)) ** one_by_time - 1.0) * 100.0
        return round(cagr, 2)
    except (ZeroDivisionError, OverflowError, ValueError):
        return 0.0


def calculate_xirr(
    cashflows: List[Tuple[Union[date, datetime, str], float]],
    as_of_date: Optional[Union[date, datetime, str]] = None,
    fallback_cagr: bool = True
) -> float:
    """
    Calculate Extended Internal Rate of Return (XIRR) for irregular cashflows.
    
    Args:
        cashflows: List of (date, amount) tuples. 
                   Negative amounts = investments/outflows.
                   Positive amounts = dividends/redemptions/current valuation.
        as_of_date: Optional valuation date.
        fallback_cagr: If True, falls back to CAGR if convergence fails.
        
    Returns:
        XIRR percentage (e.g. 15.42 for 15.42%).
    """
    if not cashflows:
        return 0.0

    # Normalize entries
    cleaned_entries = []
    for d, amt in cashflows:
        if isinstance(d, str):
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        elif isinstance(d, datetime):
            d = d.date()
            
        amt_f = float(amt)
        if abs(amt_f) > 1e-6:
            cleaned_entries.append((d, amt_f))

    if len(cleaned_entries) < 2:
        return 0.0

    # Sort chronologically
    cleaned_entries.sort(key=lambda x: x[0])
    
    has_negative = any(amt < 0 for _, amt in cleaned_entries)
    has_positive = any(amt > 0 for _, amt in cleaned_entries)
    if not (has_negative and has_positive):
        return 0.0

    d0 = cleaned_entries[0][0]
    total_days = (cleaned_entries[-1][0] - d0).days
    if total_days <= 0:
        return 0.0

    # Time fractions in years: (d_i - d_0) / 365.0
    times = [(d - d0).days / 365.0 for d, _ in cleaned_entries]
    cfs = [amt for _, amt in cleaned_entries]

    def npv(rate: float) -> float:
        if rate <= -0.999999:
            return float('inf')
        return sum(cf / ((1.0 + rate) ** t) for cf, t in zip(cfs, times))

    def d_npv(rate: float) -> float:
        if rate <= -0.999999:
            return float('inf')
        return sum(-cf * t / ((1.0 + rate) ** (t + 1.0)) for cf, t in zip(cfs, times))

    # 1. Newton-Raphson Solver with multiple starting guesses
    guesses = [0.10, 0.0, 0.25, -0.10, 0.50, -0.30, 1.0]
    for start_rate in guesses:
        rate = start_rate
        for _ in range(100):
            f = npv(rate)
            df = d_npv(rate)

            if abs(df) < 1e-12:
                break

            new_rate = rate - f / df
            # Clamp step to avoid runaway
            new_rate = min(max(new_rate, -0.999), 10.0)

            if abs(new_rate - rate) < 1e-7 and abs(f) < 1e-3:
                return round(new_rate * 100.0, 2)

            rate = new_rate

    # 2. Bisection Root Finder Fallback across [-0.999, 10.0]
    low = -0.999
    high = 10.0
    f_low = npv(low)
    f_high = npv(high)

    if f_low * f_high <= 0:
        for _ in range(100):
            mid = (low + high) / 2.0
            f_mid = npv(mid)

            if abs(f_mid) < 1e-4 or (high - low) < 1e-6:
                return round(mid * 100.0, 2)

            if f_low * f_mid <= 0:
                high = mid
                f_high = f_mid
            else:
                low = mid
                f_low = f_mid

    # 3. Fallback to CAGR if enabled
    if fallback_cagr:
        total_invested = sum(-cf for cf in cfs if cf < 0)
        total_terminal = sum(cf for cf in cfs if cf > 0)
        return calculate_cagr(total_invested, total_terminal, total_days)

    return 0.0


def get_tax_holding_type(holding_days: int, threshold_days: int = 365) -> str:
    """
    Classify Capital Gains tax holding type:
    - LTCG (Long-Term Capital Gains) if holding_days > threshold_days
    - STCG (Short-Term Capital Gains) otherwise
    """
    return "LTCG" if holding_days > threshold_days else "STCG"


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI) using Wilder's smoothing.
    
    Args:
        prices: List of chronological closing prices (oldest to newest).
        period: Lookback period (default 14).
        
    Returns:
        RSI value rounded to 2 decimal places (0 - 100), or None if insufficient prices.
    """
    if not prices:
        return None

    # Filter out None, NaN, and non-positive prices
    clean_prices = []
    for p in prices:
        try:
            if p is not None:
                val = float(p)
                if not math.isnan(val) and not math.isinf(val) and val > 0:
                    clean_prices.append(val)
        except (ValueError, TypeError):
            continue

    if len(clean_prices) < period + 1:
        return None

    deltas = [clean_prices[i] - clean_prices[i - 1] for i in range(1, len(clean_prices))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = sum(gains[:period]) / float(period)
    avg_loss = sum(losses[:period]) / float(period)

    # Wilder's smoothing for remaining periods
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / float(period)
        avg_loss = (avg_loss * (period - 1) + losses[i]) / float(period)

    if avg_loss == 0.0:
        return 100.0
    if avg_gain == 0.0:
        return 0.0

    try:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        if math.isnan(rsi) or math.isinf(rsi):
            return None
        return round(float(rsi), 2)
    except (ZeroDivisionError, OverflowError, ValueError):
        return None

