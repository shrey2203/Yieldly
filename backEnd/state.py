from collections import defaultdict

# Persistent Caches
equityMasterCache = {}      # {id: EquityObject}
marketDataCache = {}        # {date: [MarketDataObjects]}
prevDayCloseCache = {}      # {date: {equityShortName: closePrice}}
mutualFundMasterCache = {}
mutualFundMarketDataCache = {}
indexDataCache = {}

# Response & Overview Caches
portfolioResponseCache = {}    # {(userId, selectedDate): (timestamp, data)}
mfResponseCache = {}           # {userId: (timestamp, data)}
dashboardOverviewCache = {}    # {userId: (timestamp, data)}