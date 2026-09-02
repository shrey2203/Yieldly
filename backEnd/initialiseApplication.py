from datetime import timedelta, datetime
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.mutualFundMasterQuery import MutualFundMaster
from dataQuery.mutualFundMarketDataQuery import MutualFundMarketData
import state
from datetime import timedelta, datetime
from sqlalchemy import func
from config import db

_EQUITY_MASTER_CACHE = {}
_MARKET_DATA_CACHE = {}

def initialise():
    try:
        from autoDiscoveryService import auto_sync_all_investments
        auto_sync_all_investments()
    except Exception as e:
        print(f"[AutoDiscovery] Initial sync error: {e}")

    try:
        import fetchEquityDayWisePnlPosition
        fetchEquityDayWisePnlPosition.updateDividendsForHoldings()
    except Exception as e:
        print(f"[Dividends] Sync error: {e}")

    initiateCacheEquity()
    initiateCacheEquityMF()
    prepareLatestAvailableSnapsMap()
    initiateIndexMarketDataCache()
    

def getLastClose(portfolioAsOnDate):
    if isinstance(portfolioAsOnDate, str):
        targetDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
    else:
        targetDate = portfolioAsOnDate
    if targetDate in state.prevDayCloseCache:
        return state.prevDayCloseCache[targetDate]
        
    if not state.equityMasterCache:
        masters = EquityMaster.query.all()
        state.equityMasterCache = {m.getId(): m for m in masters}

    # Query the most recent trading close strictly before targetDate for EVERY equity individually
    subquery = (
        db.session.query(
            EquityMarketData.equityId,
            func.max(EquityMarketData.marketDate).label('maxDate')
        )
        .filter(EquityMarketData.marketDate < targetDate)
        .group_by(EquityMarketData.equityId)
        .subquery()
    )
    
    records = (
        db.session.query(EquityMarketData.equityId, EquityMarketData.close)
        .join(subquery, (EquityMarketData.equityId == subquery.c.equityId) & (EquityMarketData.marketDate == subquery.c.maxDate))
        .all()
    )

    dailyClosePrices = {}
    for eq_id, close_val in records:
        equity = state.equityMasterCache.get(eq_id)
        if equity and close_val is not None:
            dailyClosePrices[equity.getEquityShortName()] = float(close_val)

    state.prevDayCloseCache[targetDate] = dailyClosePrices
    return dailyClosePrices


def initiateCacheEquity(portfolioAsOnDate=None):
    if isinstance(portfolioAsOnDate, str):
        portfolioAsOnDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
    if not state.equityMasterCache:
        allEquities = EquityMaster.query.all()
        for m in allEquities:
            db.session.expunge(m)
        state.equityMasterCache = {m.getId(): m for m in allEquities}
    marketData, latestAvailableDate = getLatestMarketData(portfolioAsOnDate)
    if not marketData:
        print("Error: No market data found.")
        return
    lastTradingDayData = getLastClose(latestAvailableDate)
    for mData in marketData:
        equity = state.equityMasterCache.get(mData.getEquityId())
        if not equity: 
            continue
        shortName = equity.getEquityShortName()
        date_entry = state.marketDataCache.setdefault(latestAvailableDate, {})
        date_entry[shortName] = {
            'lastPrice': mData.getClose(),
            'Open': mData.getOpen(),
            'High': mData.getHigh(),
            'Low': mData.getLow(),
            'lastClose': lastTradingDayData.get(shortName, 0),
            'dataDate': latestAvailableDate
        }
    print(f"Cache Initialized for {len(state.marketDataCache[latestAvailableDate])} equities on {latestAvailableDate}.")



def getLatestMarketData(ceilingDate=None):
    query = EquityMarketData.query    
    if ceilingDate:
        query = query.filter(EquityMarketData.marketDate <= ceilingDate)
    latestEntry = query.order_by(EquityMarketData.marketDate.desc()).first()
    if not latestEntry:
        return [], None
    actualLatestDate = latestEntry.marketDate
    marketData = EquityMarketData.query.filter_by(marketDate=actualLatestDate).all()
    equitiesWithData = {m.getEquityId() for m in marketData}
    allEquityIds = set(state.equityMasterCache.keys())
    missing_ids = allEquityIds - equitiesWithData
    if missing_ids:
        print(f"--- Missing Market Data for {actualLatestDate} ---")
        for eq_id in missing_ids:
            equity_obj = state.equityMasterCache.get(eq_id)
            print(f"Missing: {equity_obj.getEquityShortName() if equity_obj else eq_id}")
        print(f"Total Missing: {len(missing_ids)}")
    return marketData, actualLatestDate


def prepareLatestAvailableSnapsMap():
    if not state.equityMasterCache:
        masters = EquityMaster.query.all()
        state.equityMasterCache = {m.getId(): m for m in masters}
    latestDateSubquery = (db.session.query(EquityMarketData.equityId, func.max(EquityMarketData.marketDate).label('latestDate')).group_by(EquityMarketData.equityId).subquery())
    latestMarketRecords = (
        EquityMarketData.query.join(latestDateSubquery, (EquityMarketData.equityId == latestDateSubquery.c.equityId) & (EquityMarketData.marketDate == latestDateSubquery.c.latestDate)).all())
    priceMap = {obj: -1 for obj in state.equityMasterCache.keys()}
    for record in latestMarketRecords:
        equityObj = state.equityMasterCache.get(record.getEquityId())
        if equityObj:
            priceMap[record.getEquityId()] = (record.getMarketDate(), record.getClose())

    # Update global state
    state.latestSnaps = priceMap
    print(f"Latest price map initialized for {len(state.latestSnaps)} equities.")

def initiateCacheEquityMF(portfolioAsOnDate=None):
    if isinstance(portfolioAsOnDate, str):
            portfolioAsOnDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
    if not state.mutualFundMasterCache:
        state.mutualFundMasterCache = {m.getId(): m for m in MutualFundMaster.query.all()}
    marketData, latestAvailableDate = getLatestMarketDataMF(portfolioAsOnDate)
    if not marketData:
            print("Error: No market data found.")
            return
    for mData in marketData:
        mutualFund = state.mutualFundMasterCache.get(mData.getMutualFundId())
        if not mutualFund: 
            continue
        shortName = mutualFund.getMutualFund()
        # date_entry = state.mutualFundMarketDataCache.setdefault(latestAvailableDate, {})
        state.mutualFundMarketDataCache[shortName] = {
            'nav': mData.getNav(),
            'dataDate': latestAvailableDate
        }
    print(f"Cache Initialized for {len(state.mutualFundMarketDataCache)} mutual Funds on {latestAvailableDate}.")


def getLatestMarketDataMF(ceilingDate=None):
    query = MutualFundMarketData.query    
    if ceilingDate:
        query = query.filter(MutualFundMarketData.marketDate <= ceilingDate)
    latestEntry = query.order_by(MutualFundMarketData.marketDate.desc()).first()
    if not latestEntry:
        return [], None
    actualLatestDate = latestEntry.marketDate
    marketData = MutualFundMarketData.query.filter_by(marketDate=actualLatestDate).all()
    mutualFundWithData = {m.getMutualFundId() for m in marketData}
    allMutualFundIds = set(state.mutualFundMasterCache.keys())
    missing_ids = allMutualFundIds - mutualFundWithData
    if missing_ids:
        print(f"--- Missing Market Data for {actualLatestDate} ---")
        for mf_id in missing_ids:
            mutualFund_obj = state.mutualFundMasterCache.get(mf_id)
            print(f"Missing: {mutualFund_obj.getMutualFund() if mutualFund_obj else mf_id}")
        print(f"Total Missing: {len(missing_ids)}")
    return marketData, actualLatestDate

def initiateIndexMarketDataCache():
    allEntries = (EquityMarketData.query.filter(EquityMarketData.equityId.in_([142, 143])).order_by(EquityMarketData.marketDate.desc()).all())
    for entry in allEntries:
        equity = state.equityMasterCache.get(entry.getEquityId())
        if not equity: 
            continue
        shortName = equity.getEquityShortName()
        date_entry = state.indexDataCache.setdefault(entry.getMarketDate(), {})
        date_entry[shortName] = {
            'lastPrice': entry.getClose(),
            'Open': entry.getOpen(),
            'High': entry.getHigh(),
            'Low': entry.getLow(),
            'dataDate': entry.getMarketDate()
        }

def getIndexPrice(date, indexShortName):
    dateEntry = state.indexDataCache.get(date)    
    if dateEntry and dateEntry.get(indexShortName):
        return dateEntry[indexShortName].get('lastPrice', 0)
    available_dates = [
        cache_date for cache_date, daily_data in state.indexDataCache.items() 
        if daily_data.get(indexShortName)
    ]
    if not available_dates:
        return 0
    latest_date = max(available_dates)
    return state.indexDataCache[latest_date][indexShortName].get('lastPrice', 0)