"""
Base Strategy Abstract Class & Quantitative Indicator Utilities
---------------------------------------------------------------
Defines the standard interface for all trading strategies in the system.
Any new strategy subclassing BaseStrategy is automatically discoverable.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import yfinance as yf


def compute_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()


def compute_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average."""
    return series.rolling(window=window, min_periods=max(1, window // 4)).mean()


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates 14-period Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """Calculates Supertrend indicator line and direction series."""
    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values
    atr = compute_atr(df, period).values

    hl2 = (high + low) / 2.0
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    supertrend = np.zeros(len(df))
    direction = np.ones(len(df))  # 1 = Bullish, -1 = Bearish

    for i in range(1, len(df)):
        if close[i - 1] > upperband[i - 1]:
            upperband[i] = max(upperband[i], upperband[i - 1])
        if close[i - 1] < lowerband[i - 1]:
            lowerband[i] = min(lowerband[i], lowerband[i - 1])

        if direction[i - 1] == 1:
            if close[i] < lowerband[i]:
                direction[i] = -1
                supertrend[i] = upperband[i]
            else:
                direction[i] = 1
                supertrend[i] = lowerband[i]
        else:
            if close[i] > upperband[i]:
                direction[i] = 1
                supertrend[i] = lowerband[i]
            else:
                direction[i] = -1
                supertrend[i] = upperband[i]

    return supertrend, direction


def download_stock_history(stock: str, lookback_years: int = 2, min_bars: int = 40) -> Optional[pd.DataFrame]:
    """Downloads clean OHLCV daily data for Indian stocks with NSE/BSE fallback."""
    for suffix in [".NS", ".BO"]:
        try:
            raw = yf.download(
                f"{stock}{suffix}", 
                period=f"{lookback_years}y", 
                interval="1d", 
                progress=False, 
                auto_adjust=True
            )
            if raw is not None and not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.get_level_values(0)
                raw = raw.dropna(subset=["Close", "High", "Low", "Volume"])
                raw = raw[(raw["Close"] > 0) & (raw["High"] > 0) & (raw["Low"] > 0)]
                if len(raw) >= min_bars:
                    return raw
        except Exception:
            continue
    return None


class BaseStrategy(ABC):
    """
    Abstract Base Class for all quantitative strategies.
    Subclasses must define ID, TITLE, CATEGORY, BADGE, and implement the abstract methods.
    """
    ID: str = "base"
    TITLE: str = "Base Strategy"
    CATEGORY: str = "Quantitative"
    BADGE: str = "📊 Base"

    @classmethod
    @abstractmethod
    def get_info(cls) -> Dict[str, Any]:
        """Returns metadata, philosophy, and detailed buy/sell/stop loss write-ups."""
        pass

    @classmethod
    @abstractmethod
    def generate_signal(cls, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Generates live trade stance (BUY, SELL, HOLD), Target, Stop Loss, Risk/Reward."""
        pass

    @classmethod
    @abstractmethod
    def run_backtest(cls, stock: str, lookback_years: int = 2, initial_capital: float = 100000.0) -> Dict[str, Any]:
        """Simulates walk-forward historical backtest returning KPIs, Equity Curve, and Trades."""
        pass
