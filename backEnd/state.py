from collections import defaultdict

# Persistent Caches
equityMasterCache = {}      # {id: EquityObject}
marketDataCache = {}        # {date: [MarketDataObjects]}
prevDayCloseCache = {}      # {date: {equityShortName: closePrice}}
mutualFundMasterCache = {}
mutualFundMarketDataCache = {}
indexDataCache = {}