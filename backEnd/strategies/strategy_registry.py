"""
Strategy Registry & Auto-Discovery Engine
-----------------------------------------
Allows plug-and-play addition of new trading strategies.
Any new file created in backEnd/strategies/ inheriting BaseStrategy is
automatically discovered or can be registered here in one line.
"""

import os
import importlib
import inspect
from typing import Dict, Type, List, Any, Optional
from strategies.base_strategy import BaseStrategy


class StrategyRegistry:
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, strategy_cls: Type[BaseStrategy]):
        """Explicitly registers a strategy class."""
        if hasattr(strategy_cls, "ID") and strategy_cls.ID:
            cls._strategies[strategy_cls.ID.lower()] = strategy_cls
        return strategy_cls

    @classmethod
    def _auto_discover(cls):
        """Auto-discovers all BaseStrategy subclasses from files in the strategies directory."""
        if cls._initialized:
            return

        current_dir = os.path.dirname(__file__)
        for fname in os.listdir(current_dir):
            if fname.endswith(".py") and not fname.startswith("__") and fname != "base_strategy.py" and fname != "strategy_registry.py":
                mod_name = fname[:-3]
                try:
                    module = importlib.import_module(f"strategies.{mod_name}")
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                            cls.register(obj)
                except Exception as e:
                    print(f"Warning: Could not load strategy module {mod_name}: {e}")

        cls._initialized = True

    @classmethod
    def get_strategy(cls, strategy_id: str) -> Optional[Type[BaseStrategy]]:
        """Retrieves a registered strategy by ID, defaulting to sr_poc if not found."""
        cls._auto_discover()
        strat_id = (strategy_id or "sr_poc").strip().lower()
        return cls._strategies.get(strat_id) or cls._strategies.get("sr_poc")

    @classmethod
    def get_all_strategies(cls) -> List[Type[BaseStrategy]]:
        """Returns all registered strategy classes."""
        cls._auto_discover()
        return list(cls._strategies.values())

    @classmethod
    def get_all_strategy_infos(cls) -> List[Dict[str, Any]]:
        """Returns metadata and detailed writeup for all available strategies for frontend consumption."""
        cls._auto_discover()
        return [strat.get_info() for strat in cls._strategies.values()]

    @classmethod
    def run_backtest(cls, strategy_id: str, stock: str, lookback_years: int = 2, initial_capital: float = 100000.0) -> Dict[str, Any]:
        """Dispatches backtest execution to the requested strategy."""
        strat = cls.get_strategy(strategy_id)
        if not strat:
            return {"status": "error", "message": f"Strategy '{strategy_id}' not found"}
        return strat.run_backtest(stock=stock, lookback_years=lookback_years, initial_capital=initial_capital)
