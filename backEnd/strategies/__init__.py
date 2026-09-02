"""
Quantitative Trading Strategies Package
---------------------------------------
Exports BaseStrategy, StrategyRegistry, and pre-built strategies.
"""

from strategies.base_strategy import BaseStrategy
from strategies.strategy_registry import StrategyRegistry
from strategies.sr_poc_strategy import SrPocStrategy
from strategies.ema_momentum_strategy import EmaMomentumStrategy
from strategies.supertrend_strategy import SupertrendStrategy
from strategies.dual_momentum_strategy import DualMomentumStrategy
from strategies.zscore_strategy import ZScoreStrategy
from strategies.volatility_targeting_strategy import VolatilityTargetingStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.coffee_can_strategy import CoffeeCanStrategy
from strategies.canslim_strategy import CanslimStrategy
from strategies.value_pe_strategy import ValuePeStrategy

# Explicitly register default built-in strategies
StrategyRegistry.register(SrPocStrategy)
StrategyRegistry.register(EmaMomentumStrategy)
StrategyRegistry.register(SupertrendStrategy)
StrategyRegistry.register(DualMomentumStrategy)
StrategyRegistry.register(ZScoreStrategy)
StrategyRegistry.register(VolatilityTargetingStrategy)
StrategyRegistry.register(MomentumStrategy)
StrategyRegistry.register(CoffeeCanStrategy)
StrategyRegistry.register(CanslimStrategy)
StrategyRegistry.register(ValuePeStrategy)

__all__ = [
    "BaseStrategy",
    "StrategyRegistry",
    "SrPocStrategy",
    "EmaMomentumStrategy",
    "SupertrendStrategy",
    "DualMomentumStrategy",
    "ZScoreStrategy",
    "VolatilityTargetingStrategy",
    "MomentumStrategy",
    "CoffeeCanStrategy",
    "CanslimStrategy",
    "ValuePeStrategy",
]
