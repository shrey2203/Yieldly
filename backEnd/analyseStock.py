"""
Stock Analysis Engine Coordinator
---------------------------------
Lightweight facade coordinating:
1. Fundamental Analysis Service (Screener.in, yfinance, median P/E, 4-point rating)
2. Technical Analysis Service (S/R pivot detection, Robust Volume Profile POC)
3. Quantitative Strategy Engine (Plug-and-play strategies via StrategyRegistry)
"""

import time
import math
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import Dict, Any, Optional

from services.fundamental_analysis import FundamentalAnalysisService
from services.technical_analysis import TechnicalAnalysisService
from strategies.strategy_registry import StrategyRegistry
from strategies.base_strategy import download_stock_history


class AnalyseStock:
    _session = None
    _cache = {}
    _CACHE_TTL_SECONDS = 3600  # 1 hour

    @classmethod
    def get_session(cls):
        if cls._session is None:
            s = requests.Session()
            retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=retries)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            cls._session = s
        return cls._session

    def __init__(self, stock: str):
        self.stock = stock.strip().upper()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session = self.get_session()

    def fetchStockAnalysisData(self, stock: str = None) -> dict:
        """
        Fetches comprehensive fundamental and technical metrics for a stock.
        """
        target_stock = (stock or self.stock).strip().upper()
        
        # Check in-memory cache (1 hour TTL)
        now = time.time()
        if target_stock in self._cache:
            cached_time, cached_data = self._cache[target_stock]
            if now - cached_time < self._CACHE_TTL_SECONDS:
                return dict(cached_data)

        result = {
            "stock": target_stock,
            "companyName": target_stock,
            "currentPrice": None,
            "marketCap": None,
            "peRatio": None,
            "debtToEquity": None,
            "roce": None,
            "roe": None,
            "rsi": None,
            "promoterHolding": None,
            "promoterChange": None,
            "fiiHolding": None,
            "fiiChange": None,
            "fiiHistory": [],
            "diiHolding": None,
            "diiChange": None,
            "diiHistory": [],
            "publicHolding": None,
            "publicHistory": [],
            "quarterlyEps": [],
            "epsLast4Qtrs": [],
            "source": "Screener",
            "peMedian1Y": None,
            "peMedian3Y": None,
            "peMedian5Y": None,
            "belowMedian1Y": None,
            "belowMedian3Y": None,
            "belowMedian5Y": None,
            "supports": [],
            "resistances": [],
            "distanceToSupport1Pct": None,
            "distanceToResistance1Pct": None,
            "poc": None,
            "signalData": {},
        }

        # 1. Fundamentals from Screener.in
        screener_data = FundamentalAnalysisService.fetch_from_screener(target_stock, self.session, self.headers)
        if screener_data:
            result.update(screener_data)

        # 2. Fallbacks & RSI from yfinance
        yf_data = FundamentalAnalysisService.fetch_from_yfinance(target_stock)
        if yf_data:
            for k, v in yf_data.items():
                if result.get(k) is None or result.get(k) == 0:
                    result[k] = v

        # 3. Historical Median PE comparison
        company_id = result.pop("_companyId", None)
        is_consolidated = result.pop("_isConsolidated", True)
        current_pe = result.get("peRatio")
        pe_medians = FundamentalAnalysisService.fetch_historical_pe_medians(
            target_stock,
            session=self.session,
            headers=self.headers,
            current_pe=current_pe,
            company_id=company_id,
            is_consolidated=is_consolidated
        )
        result.update(pe_medians)

        # 4. Format EPS
        if result.get("quarterlyEps") and not result.get("epsLast4Qtrs"):
            result["epsLast4Qtrs"] = [item["eps"] for item in result["quarterlyEps"]]

        # 5. 4-Point Health Rating Scorecard
        rating_data = FundamentalAnalysisService.calculate_stock_rating(result)
        result.update(rating_data)

        # 6. Technical Support & Resistance + Robust Volume POC
        sr_data = TechnicalAnalysisService.calculate_support_resistance(target_stock, result.get("currentPrice"))
        result.update(sr_data)

        # 7. Generate Live Strategy Signals for all registered strategies
        df_history = download_stock_history(target_stock, lookback_years=1, min_bars=30)
        strategy_signals = {}
        for strat in StrategyRegistry.get_all_strategies():
            try:
                sig = strat.generate_signal(
                    df=df_history,
                    current_price=result.get("currentPrice"),
                    supports=result.get("supports", []),
                    resistances=result.get("resistances", []),
                    poc=result.get("poc"),
                    rsi=result.get("rsi")
                )
                strategy_signals[strat.ID] = sig
            except Exception as e:
                print(f"Error generating signal for strategy {strat.ID}: {e}")

        result["strategySignals"] = strategy_signals
        result["signalData"] = strategy_signals.get("sr_poc") or (next(iter(strategy_signals.values())) if strategy_signals else {})

        # 8. Sanitize NaN/Inf for valid RFC 8259 JSON
        result = self._sanitize_for_json(result)

        # Store in cache
        self._cache[target_stock] = (now, dict(result))
        return result

    @classmethod
    def run_backtest_strategy(cls, stock: str, lookback_years: int = 2, strategy_id: str = "sr_poc", initial_capital: float = 100000.0) -> dict:
        """
        Dispatches backtest execution via the StrategyRegistry.
        """
        res = StrategyRegistry.run_backtest(
            strategy_id=strategy_id,
            stock=stock,
            lookback_years=lookback_years,
            initial_capital=initial_capital
        )
        return cls._sanitize_for_json(res)

    @staticmethod
    def _sanitize_for_json(data):
        """
        Recursively sanitizes NaN and Inf floats into None for clean JSON serialization.
        """
        if isinstance(data, dict):
            return {k: AnalyseStock._sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [AnalyseStock._sanitize_for_json(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
            return data
        elif hasattr(data, "item") and callable(getattr(data, "item")):
            try:
                val = data.item()
                if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    return None
                return val
            except Exception:
                return data
        return data