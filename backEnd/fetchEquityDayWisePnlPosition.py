from collections import defaultdict, deque
import numpy as np
from config import db
from mutualFunds.mutualFund import MutualFund
from mutualFunds.investment import Investment
import pandas as pd
from datetime import datetime, timedelta, date
from sqlalchemy import desc
from sqlalchemy import func
import time
import yfinance as yf
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.equityDayWisePositionQuery import EquityDayWisePosition
from dataQuery.dividendsQuery import Dividends
from dataQuery.dividendsHistoricalQuery import DividendsHistorical
import helperFunctions
import applicationConfig
import state
from decimal import Decimal
from initialiseApplication import getIndexPrice
# import datetime

def def_value():
    return defaultdict(list)
equitiesData = defaultdict(def_value) 

def createPositionsForSingleDay(rawData, currentDay):
    if isinstance(currentDay, str):
            currentDay = datetime.strptime(currentDay, "%Y-%m-%d").date()
    elif isinstance(currentDay, date):
        rawDataDayWise = rawData[rawData['DATE'].dt.date <= currentDay]
    else:
        rawDataDayWise = rawData[rawData['DATE'].dt.date <= currentDay.date()]
    realisedPnL, equityFinalHoldings, transactionSummary = processEquityData(rawData)
    finalHoldings = prepareAggregatedHoldings(equityFinalHoldings)
    return realisedPnL, finalHoldings, transactionSummary

def getPositions(rawData, username, portfolioAsOnDate=None):
    xLabel, yLabel1, yLabel2 = [], [], []
    startDate = pd.to_datetime(rawData['DATE']).min().date()
    endDate = pd.to_datetime(rawData['DATE']).max().date()
    
    if portfolioAsOnDate:
        if isinstance(portfolioAsOnDate, str) and portfolioAsOnDate:
            try:
                portfolioAsOnDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
            except Exception:
                pass
        if isinstance(portfolioAsOnDate, date):
            endDate = max(endDate, portfolioAsOnDate)
            
    latestMarketDate = helperFunctions.getLatestExistingEquityMarketData()
    if latestMarketDate:
        endDate = min(endDate, latestMarketDate)
        
    if str(username).upper() == 'COMBINED':
        dbResults = EquityDayWisePosition.query.filter(
            EquityDayWisePosition.asOfDate >= startDate,
            EquityDayWisePosition.asOfDate <= endDate
        ).all()
    else:
        userId = helperFunctions.getUserId(username)
        dbResults = EquityDayWisePosition.query.filter(
            EquityDayWisePosition.userId == userId,
            EquityDayWisePosition.asOfDate >= startDate,
            EquityDayWisePosition.asOfDate <= endDate
        ).all()
    
    dailyStats = defaultdict(lambda: {'invested': 0, 'current': 0})
    for record in dbResults:
        dailyStats[record.asOfDate]['invested'] += float(record.totalInvestment or 0)
        dailyStats[record.asOfDate]['current'] += float(record.currentInvestment or 0)
        
    lastKnown = None
    for currentDay in pd.date_range(startDate, endDate):
        currentDayDate = currentDay.date()
        if currentDayDate in dailyStats and dailyStats[currentDayDate]['invested'] > 0:
            lastKnown = dailyStats[currentDayDate]
            
        if lastKnown and lastKnown['invested'] > 0:
            xLabel.append(currentDayDate.strftime("%Y-%m-%d"))
            yLabel1.append(round(lastKnown['invested'], 2))
            yLabel2.append(round(lastKnown['current'], 2))
            
    return xLabel, yLabel1, yLabel2

def getPrice(date, equity_short_name):
    if isinstance(date, pd.Timestamp):
        date = date.date()
    if date in state.marketDataCache and equity_short_name in state.marketDataCache[date]:
        if state.marketDataCache[date][equity_short_name]['lastPrice'] != None:
            return state.marketDataCache[date][equity_short_name]['lastPrice']
    target_id = next((id for id, obj in state.equityMasterCache.items() if obj.getEquityShortName() == equity_short_name), None)
    if not target_id:
        print(f"Equity {equity_short_name} not found in Master Cache")
        return 0
    market_data = EquityMarketData.query.filter_by(marketDate=date, equityId=target_id).first()
    if not market_data:
        market_data = (EquityMarketData.query.filter(EquityMarketData.equityId == target_id).filter(EquityMarketData.marketDate <= date).order_by(desc(EquityMarketData.marketDate)).first())
    if market_data:
        return market_data.getClose()
    return 0

def processEquityData(df):
    df['DATE'] = pd.to_datetime(df['DATE']).dt.date
    df = df.sort_values(by=['DATE', 'QTY'], ascending=[True, False])
    
    realisedPnL = defaultdict(list)
    equityFinalHoldings = {}
    transactionSummary = defaultdict(list)
    
    for equity, group in df.groupby('EQUITY'):
        buyQueue = deque()
        for row in group.itertuples(index=False):
            qty = row.QTY
            price = row.TRADED_AT
            tradeType = getattr(row, 'TYPE', getattr(row, 'type', getattr(row, 'Type', 'NORMAL')))
            if qty > 0:
                buyQueue.append([row.DATE, qty, price, tradeType])
            elif qty < 0:
                sellQty = abs(qty)
                while sellQty > 0 and buyQueue:
                    buyDate, buyQty, buyPrice, buyType = buyQueue[0]
                    matchQty = min(buyQty, sellQty)
                    realisedPnL[equity].append([buyDate, row.DATE, matchQty, buyPrice, price])
                    # if buyDate != row.DATE:
                    holding_days = (row.DATE - buyDate).days
                    niftyLevelAtBuy = getIndexPrice(buyDate, "^NSEI")
                    niftyLevelAtSell = getIndexPrice(row.DATE, "^NSEI")
                    niftyReturns = round(((niftyLevelAtSell - niftyLevelAtBuy) / niftyLevelAtBuy) * 100, 2) if niftyLevelAtBuy > 0 else -1
                    alphaGenerated = (round(((price - buyPrice) / buyPrice) * 100, 2) if buyPrice > 0 else -1) - niftyReturns
                    alphaGeneratedPerDay = round(alphaGenerated / holding_days, 4) if holding_days > 0 else alphaGenerated
                    transactionSummary[equity].append({
                        'buyDate': buyDate,
                        'sellDate': row.DATE,
                        'quantity': matchQty,
                        'buyPrice': buyPrice,
                        'sellPrice': price,
                        'pnl': round((price - buyPrice) * matchQty, 2),
                        'status': 'Closed',
                        'type': str(buyType) if pd.notna(buyType) else 'NORMAL',
                        'holdingDays': holding_days,
                        'niftyLevelAtBuy': niftyLevelAtBuy,
                        'niftyLevelAtSell': niftyLevelAtSell,
                        'niftyReturns': niftyReturns,
                        'alphaGenerated': alphaGenerated,
                        'alphaGeneratedPerDay': alphaGeneratedPerDay
                    })
                    buyQueue[0][1] -= matchQty
                    sellQty -= matchQty
                    
                    if buyQueue[0][1] == 0:
                        buyQueue.popleft()
        if buyQueue:
            latest_key = max(state.marketDataCache.keys()) if state.marketDataCache else None
            ltp = (
                state.marketDataCache.get(latest_key, {})
                .get(equity, {})
                .get('lastPrice', 0) 
                if latest_key is not None else 0
            )
            equityFinalHoldings[equity] = list(buyQueue)
            today = date.today()
            for buyDate, qty_remaining, buyPrice, buyType in buyQueue:
                holding_days = (today - buyDate).days
                unrealised_pnl = round((ltp - buyPrice) * qty_remaining, 2) if ltp > 0 else 0
                niftyLevelAtBuy = getIndexPrice(buyDate, "^NSEI")
                niftyLevelCurrent = getIndexPrice(today, "^NSEI")
                niftyReturns = round(((niftyLevelCurrent - niftyLevelAtBuy) / niftyLevelAtBuy) * 100, 2) if niftyLevelAtBuy > 0 else -1
                alphaGenerated = (round(((ltp - buyPrice) / buyPrice) * 100, 2) if buyPrice > 0 else -1) - niftyReturns
                alphaGeneratedPerDay = round(alphaGenerated / holding_days, 4) if holding_days > 0 else alphaGenerated
                transactionSummary[equity].append({
                    'buyDate': buyDate,
                    'sellDate': None,
                    'quantity': qty_remaining,
                    'buyPrice': buyPrice,
                    'sellPrice': ltp,
                    'pnl': unrealised_pnl,
                    'status': 'Open',
                    'type': str(buyType) if pd.notna(buyType) else 'NORMAL',
                    'holdingDays': holding_days,
                    'niftyLevelAtBuy': niftyLevelAtBuy,
                    'niftyLevelAtSell': niftyLevelCurrent,
                    'niftyReturns': niftyReturns,
                    'alphaGenerated': alphaGenerated,
                    'alphaGeneratedPerDay': alphaGeneratedPerDay
                })
    capitalGains = determineCapitalGains(transactionSummary, filterDate=date(2025, 4, 1))
    return realisedPnL, equityFinalHoldings, dict(transactionSummary)

def prepareAggregatedHoldings(equityFinalHoldings):
    aggregatedHoldings = {}
    for equity, trades in equityFinalHoldings.items():
        totalCost = sum(trade[1] * trade[2] for trade in trades)
        totalQty = sum(trade[1] for trade in trades)
        
        if totalQty > 0:
            avgPrice = totalCost / totalQty
            aggregatedHoldings[equity] = [avgPrice, totalQty]
            
    return aggregatedHoldings


def getLastClose(equityMarketDataList, portfolioAsOnDate):
    global prevDayClosePrice
    prevDayClosePrice = defaultdict(def_value) 
    if len(prevDayClosePrice.values()): return prevDayClosePrice
    if isinstance(portfolioAsOnDate, str): 
        lastTradingDay = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date() 
        lastTradingDay = lastTradingDay - timedelta(1) 
    else: 
        lastTradingDay = portfolioAsOnDate - timedelta(1)
    equityMarketDataList = EquityMarketData.query.filter_by(marketDate=lastTradingDay).all()
    while len(equityMarketDataList) == 0:
        if isinstance(lastTradingDay, str):
                lastTradingDay = datetime.strptime(lastTradingDay, "%Y-%m-%d").date()
        lastTradingDay = lastTradingDay - timedelta(1)
        equityMarketDataList = EquityMarketData.query.filter_by(marketDate=lastTradingDay).all()
    equityMasterMap = {}
    equityMasterList = EquityMaster.query.all()
    for equityMaster in equityMasterList:
        equityMasterMap[equityMaster.getId()] = equityMaster
    for i in equityMarketDataList:
        equity = equityMasterMap[i.getEquityId()]
        prevDayClosePrice[equity.getEquityShortName()] = i.getClose()
    return prevDayClosePrice

def getLatestEquityExistingData():
    results = db.session.query(
        EquityMarketData.equityId, 
        func.max(EquityMarketData.marketDate)
    ).group_by(EquityMarketData.equityId).all()
    return {equityId: latestDate for equityId, latestDate in results}

def updateEquityDataFromDateCustom(equityName, startDate):
    """
    Updates the database for a specific equity from a given startDate
    up until the earliest record currently existing in the DB.
    """
    todayDateTime = datetime.now()
    equityId = EquityMaster.query.filter_by(equityShortName=equityName).first().getId()
    firstDateInDb = db.session.query(func.min(EquityMarketData.marketDate))\
        .filter(EquityMarketData.equityId == equityId).scalar()
    if firstDateInDb:
        downloadEndDate = firstDateInDb
    else:
        downloadEndDate = (todayDateTime + timedelta(days=1)).date()
    if firstDateInDb and startDate >= firstDateInDb:
        print(f"Data for {equityName} already exists from {firstDateInDb}. No backfill needed.")
        return
    tickerSymbol = equityName if (equityName.startswith("^") or equityName.endswith(".BO")) else f"{equityName}.NS"
    print(f"Fetching data for {tickerSymbol} from {startDate} to {downloadEndDate}...")
    
    tickerData = yf.download(
        tickers=tickerSymbol,
        start=startDate,
        end=downloadEndDate,
        progress=False
    ).dropna()

    if tickerData.empty:
        print(f"No new data found for {tickerSymbol} in the specified range.")
        return
    entries_added = 0
    for marketTimestamp, row in tickerData.iterrows():
        marketDate = marketTimestamp.date()
        exists = EquityMarketData.query.filter_by(
            equityId=equityId, 
            marketDate=marketDate
        ).first()

        if not exists:
            newEntry = EquityMarketData(
                equityId = equityId,
                marketDate = marketDate,
                open = float(row["Open"]), 
                close = float(row["Close"]), 
                low = float(row["Low"]), 
                high = float(row["High"])
            )
            db.session.add(newEntry)
            entries_added += 1

    try:
        db.session.commit()
        print(f"Successfully added {entries_added} rows for {equityName}.")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to update {equityName}: {str(e)}")

# def updateEquityDataBulk():
#     todayDateTime = datetime.now()
#     refreshLimit = todayDateTime - timedelta(hours=applicationConfig.refreshFrequencyEquity)
#     delistedTickers = ["TATAMOTORS"]
#     equitiesToUpdate = EquityMaster.query.filter(EquityMaster.lastUpdatedTime < refreshLimit,~EquityMaster.equityShortName.in_(delistedTickers)).all()
#     if not equitiesToUpdate:
#         return
#     latestDateMap = getLatestEquityExistingData()
#     oldestDateNeeded = None
#     tickerToLatestDateMap = {}
#     for equity in equitiesToUpdate:
#         latestInDb = latestDateMap.get(equity.getId(), -1)
#         tickerToLatestDateMap[equity.getId()] = latestInDb
#         comparisonDate = latestInDb + timedelta(days=1) if latestInDb != -1 else (todayDateTime - timedelta(days=3100)).date()
#         if oldestDateNeeded is None or comparisonDate < oldestDateNeeded:
#             oldestDateNeeded = comparisonDate
            
#     tickerList = [e.getEquityShortName() if e.getEquityShortName().startswith("^") or e.getEquityShortName().endswith(".BO") else f"{e.getEquityShortName()}.NS" for e in equitiesToUpdate]
#     bulkData = yf.download(
#         tickers=tickerList,
#         start=oldestDateNeeded,
#         end=(todayDateTime + timedelta(days=1)).strftime('%Y-%m-%d'),
#         auto_adjust=True,
#         group_by='ticker',
#         threads=True,
#         progress=False
#     )
#     for equity in equitiesToUpdate:
#         shortName = equity.getEquityShortName()
#         tickerSymbol = shortName if shortName.startswith("^") or shortName.endswith(".BO") else f"{shortName}.NS"
#         if len(tickerList) == 1:
#             tickerData = bulkData.dropna()
#         elif tickerSymbol in bulkData.columns.levels[0]:
#             tickerData = bulkData[tickerSymbol].dropna()
#             if isinstance(tickerData.columns, pd.MultiIndex):
#                 tickerData.columns = tickerData.columns.get_level_values(-1)
#         else:
#             print(f"No data found for {tickerSymbol}, skipping...")
#             continue
#         lastDateInDb = latestDateMap.get(equity.getId(), -1)
#         for marketTimestamp, row in tickerData.iterrows():
#             marketDate = marketTimestamp.date()
#             if lastDateInDb == -1 or marketDate >= lastDateInDb:
#                 if len(tickerList) == 1:
#                     newEntry = EquityMarketData(
#                         equityId = equity.getId(),
#                         marketDate = marketDate,
#                         open = row[(tickerSymbol, "Open")], 
#                         close = row[(tickerSymbol, "Close")], 
#                         low = row[(tickerSymbol, "Low")],
#                         high = row[(tickerSymbol, "High")]
#                     )
#                 else:
#                     newEntry = EquityMarketData(
#                         equityId = equity.getId(),
#                         marketDate = marketDate,
#                         open = row["Open"], 
#                         close = row["Close"], 
#                         low = row["Low"],
#                         high = row["High"]
#                     )
#                 db.session.add(newEntry)
#         equity.lastUpdatedTime = todayDateTime 
#     try:
#         db.session.commit()
#         print(f"Successfully synchronized {len(equitiesToUpdate)} equities.")
#     except Exception as e:
#         db.session.rollback()
#         print(f"Bulk update failed: {str(e)}")

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
# Assuming db, EquityMaster, EquityMarketData, applicationConfig, getLatestEquityExistingData are imported/available

def updateEquityDataBulk():
    todayDateTime = datetime.now()
    refreshLimit = todayDateTime - timedelta(hours=applicationConfig.refreshFrequencyEquity)
    delistedTickers = ["TATAMOTORS"]
    equitiesToUpdate = EquityMaster.query.filter(
        EquityMaster.lastUpdatedTime < refreshLimit,
        ~EquityMaster.equityShortName.in_(delistedTickers)
    ).all()
    
    if not equitiesToUpdate:
        return
        
    latestDateMap = getLatestEquityExistingData()
    oldestDateNeeded = None
    tickerToLatestDateMap = {}
    
    for equity in equitiesToUpdate:
        latestInDb = latestDateMap.get(equity.getId(), -1)
        tickerToLatestDateMap[equity.getId()] = latestInDb
        comparisonDate = latestInDb + timedelta(days=1) if latestInDb != -1 else (todayDateTime - timedelta(days=3100)).date()
        if oldestDateNeeded is None or comparisonDate < oldestDateNeeded:
            oldestDateNeeded = comparisonDate
            
    tickerList = [e.getEquityShortName() if e.getEquityShortName().startswith("^") or e.getEquityShortName().endswith(".BO") else f"{e.getEquityShortName()}.NS" for e in equitiesToUpdate]
    
    bulkData = yf.download(
        tickers=tickerList,
        start=oldestDateNeeded,
        end=(todayDateTime + timedelta(days=1)).strftime('%Y-%m-%d'),
        auto_adjust=True,
        group_by='ticker',
        threads=True,
        progress=False
    )
    
    for equity in equitiesToUpdate:
        shortName = equity.getEquityShortName()
        tickerSymbol = shortName if shortName.startswith("^") or shortName.endswith(".BO") else f"{shortName}.NS"
        
        if len(tickerList) == 1:
            tickerData = bulkData.dropna()
        elif tickerSymbol in bulkData.columns.levels[0]:
            tickerData = bulkData[tickerSymbol].dropna()
            if isinstance(tickerData.columns, pd.MultiIndex):
                tickerData.columns = tickerData.columns.get_level_values(-1)
        else:
            print(f"No data found for {tickerSymbol}, skipping...")
            continue
            
        lastDateInDb = latestDateMap.get(equity.getId(), -1)
        
        for marketTimestamp, row in tickerData.iterrows():
            marketDate = marketTimestamp.date()
            
            if lastDateInDb == -1 or marketDate >= lastDateInDb:
                # 1. Extract values cleanly to avoid code duplication
                if len(tickerList) == 1:
                    r_open = row[(tickerSymbol, "Open")]
                    r_close = row[(tickerSymbol, "Close")]
                    r_low = row[(tickerSymbol, "Low")]
                    r_high = row[(tickerSymbol, "High")]
                else:
                    r_open = row["Open"]
                    r_close = row["Close"]
                    r_low = row["Low"]
                    r_high = row["High"]

                # 2. Check for the exact overlapping day to UPDATE rather than insert
                if lastDateInDb != -1 and marketDate == lastDateInDb:
                    existingEntry = EquityMarketData.query.filter_by(
                        equityId=equity.getId(), 
                        marketDate=marketDate
                    ).first()
                    
                    if existingEntry:
                        # Update existing fields
                        existingEntry.open = r_open
                        existingEntry.close = r_close
                        existingEntry.low = r_low
                        existingEntry.high = r_high
                    else:
                        # Fallback just in case the map said it existed but it didn't
                        newEntry = EquityMarketData(
                            equityId=equity.getId(), marketDate=marketDate,
                            open=r_open, close=r_close, low=r_low, high=r_high
                        )
                        db.session.add(newEntry)
                        
                # 3. For all subsequent dates, it is safe to INSERT
                else:
                    newEntry = EquityMarketData(
                        equityId=equity.getId(), marketDate=marketDate,
                        open=r_open, close=r_close, low=r_low, high=r_high
                    )
                    db.session.add(newEntry)
                    
        equity.lastUpdatedTime = todayDateTime 
        
    try:
        db.session.commit()
        print(f"Successfully synchronized {len(equitiesToUpdate)} equities.")
    except Exception as e:
        db.session.rollback()
        print(f"Bulk update failed: {str(e)}")

        
def fetchDividendsForHoldings(tickers):
    dividendReport = []
    for ticker in tickers:
        yfTicker = yf.Ticker(f"{ticker}.NS")
        yfDividends = yfTicker.dividends
        dividends = yfDividends[yfDividends.index.tz_localize(None) > datetime.now() - timedelta(days=365)]
        if not dividends.empty:
            dividendReport.append({
                "stock": ticker,
                "amount": dividends.sum(),
                "last_date": dividends.index[-1].strftime('%Y-%m-%d')
            })
    return dividendReport

def syncUserDividends(userId):
    try:
        # 1. Fetch only equities the user has actually held
        user_equity_ids = [
            r[0] for r in db.session.query(EquityDayWisePosition.equityId)
            .filter_by(userId=userId)
            .distinct()
            .all()
        ]
        
        if not user_equity_ids:
            return

        # 2. Pre-load already recorded historical dividends with normalized date keys for O(1) checks
        already_recorded_set = {
            (rec.equityId, str(rec.payoutDate)[:10])
            for rec in DividendsHistorical.query.filter_by(userId=userId).all()
        }

        # 3. Only fetch dividends for the user's specific equities
        relevant_dividends = Dividends.query.filter(Dividends.equityId.in_(user_equity_ids)).all()
        if not relevant_dividends:
            return

        # 4. In-memory bulk load of user positions (one single fast query)
        all_positions = EquityDayWisePosition.query.filter(
            EquityDayWisePosition.userId == userId,
            EquityDayWisePosition.equityId.in_(user_equity_ids)
        ).order_by(EquityDayWisePosition.asOfDate.asc()).all()

        pos_map = defaultdict(list)
        for pos in all_positions:
            p_date = pos.asOfDate if hasattr(pos.asOfDate, 'year') else datetime.strptime(str(pos.asOfDate)[:10], '%Y-%m-%d').date()
            pos_map[pos.equityId].append((p_date, float(pos.quantity or 0)))

        equityIdNameMap = {eid: e.getEquityShortName() for eid, e in state.equityMasterCache.items()} if state.equityMasterCache else {}
        new_records = 0

        for div_event in relevant_dividends:
            eid = div_event.equityId
            p_date = div_event.payoutDate
            date_key = str(p_date)[:10]
            
            # Skip if already recorded
            if (eid, date_key) in already_recorded_set:
                continue

            div_date = p_date.date() if hasattr(p_date, 'date') else datetime.strptime(date_key, '%Y-%m-%d').date()
            div_amount = Decimal(str(div_event.dividendAmount))

            # Fast in-memory lookup of latest position on or before dividend date
            eq_positions = pos_map.get(eid, [])
            matching_qty = 0
            for p_as_of, p_qty in reversed(eq_positions):
                if p_as_of <= div_date:
                    if (div_date - p_as_of).days <= 10:
                        matching_qty = p_qty
                    break

            if matching_qty > 0:
                total_payout = div_amount * Decimal(str(matching_qty))
                
                user_div_record = DividendsHistorical(
                    userId=userId,
                    equityId=eid,
                    payoutDate=p_date,
                    dividendPerShare=div_amount,
                    quantityHeld=Decimal(str(matching_qty)),
                    totalDividendAmount=total_payout
                )
                
                db.session.add(user_div_record)
                already_recorded_set.add((eid, date_key))
                new_records += 1
                print(f"Adding Dividend: {equityIdNameMap.get(eid, eid)} | Date: {date_key} | Payout: {total_payout}")

        if new_records > 0:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error in syncUserDividends: {e}")

def updateDividendsForHoldings():
    dividendUpdateFreq = applicationConfig.dividendUpdateFrequency
    thresholdDate = datetime.utcnow() - timedelta(days=dividendUpdateFreq)
    equityMasters = EquityMaster.query.all()
    for equity in equityMasters:
        if equity.getDivLastUpdatedTime() is None or equity.getDivLastUpdatedTime() < thresholdDate:
            symbol = equity.getEquityShortName()
            print(f"Syncing: {symbol} (Last Update: {equity.getDivLastUpdatedTime()})")
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                yfDividends = ticker.dividends
                if not yfDividends.empty:
                    yfDividends.index = yfDividends.index.tz_localize(None)
                    for payoutDate, dividendAmount in yfDividends.items():
                        payoutDateOnly = payoutDate.date()
                        existingDividend = Dividends.query.filter_by(
                            equityId=equity.getId(),
                            payoutDate=payoutDateOnly
                        ).first()
                        if not existingDividend:
                            newDividend = Dividends(
                                equityId=equity.getId(),
                                payoutDate=payoutDateOnly,
                                dividendAmount=float(dividendAmount)
                            )
                            db.session.add(newDividend)
                equity.divLastUpdatedTime = datetime.utcnow()
            except Exception as e:
                print(f"Skipping {symbol} due to error: {e}")
                continue
    try:
        db.session.commit()
        print("Dividend fetched successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Critical error during commit: {e}")

def updateEquitySectors():
    equityMasters = EquityMaster.query.all()
    for equity in equityMasters:
        if equity.getSector() == "":
            ticker = yf.Ticker(equity.getEquityShortName() + ".NS")
            output = ticker.info
            print (equity.getEquityShortName())
            if 'sector' in output:
                equity.sector = output['sector']
    db.session.commit()

def persistEquityDayWisePnlPosition(username, dataframe):
    userId = helperFunctions.getUserId(username)
    
    # 1. Date and Data Setup
    if applicationConfig.backfillEquityPnlPosition: 
        startDate = datetime.strptime(applicationConfig.startDateEquityPnl, '%d/%m/%Y').date()
    else:
        startDate = helperFunctions.getLatestDateForDayWiseEquityPosition(userId)
    
    latestDate = helperFunctions.getLatestExistingEquityMarketData()
    equityNameIdMap = {e.getEquityShortName(): eid for eid, e in state.equityMasterCache.items()}

    dataframe['DATE'] = pd.to_datetime(dataframe['DATE']).dt.date
    dataframe = dataframe.sort_values(by=['DATE', 'QTY'], ascending=[True, False])
    
    portfolioState = defaultdict(deque)
    # Tracker for "Market Movement" calculation: {equityId: yesterday_closing_price}
    lastClosingPriceMap = {}

    # Pre-load trades before startDate
    historicalTrades = dataframe[dataframe['DATE'] < startDate]
    if not historicalTrades.empty:
        portfolioState, _ = updatePortfolioState(portfolioState, historicalTrades)
        # Initialize prices for the day before startDate
        dayBeforeStart = startDate - timedelta(days=1)
        for symbol in portfolioState.keys():
            eid = equityNameIdMap.get(symbol)
            if eid:
                lastClosingPriceMap[eid] = getPrice(dayBeforeStart, symbol)

    currentDate = startDate
    while currentDate <= latestDate:
        t1 = time.time()
        
        # A. Get Opening State
        openingState = {
            equityNameIdMap.get(sym): sum(item[1] for item in q) 
            for sym, q in portfolioState.items() if sym in equityNameIdMap
        }

        # B. Track Today's Activity for P&L
        # Calculate: sum((CurrentPrice - ExecutionPrice) * Qty) for today's buys
        todaysTrades = dataframe[dataframe['DATE'] == currentDate]
        tradeGainLoss = defaultdict(float)
        
        if not todaysTrades.empty:
            currentPrices = {sym: getPrice(currentDate, sym) for sym in todaysTrades['EQUITY'].unique()}
            
            for _, row in todaysTrades.iterrows():
                eid = equityNameIdMap.get(row['EQUITY'])
                if eid:
                    # If QTY > 0 (Buy), gain is (MarketClose - BuyPrice) * Qty
                    # If QTY < 0 (Sell), gain is realized (handled by your updatePortfolioState)
                    if row['QTY'] > 0:
                        tradeGainLoss[eid] += (currentPrices[row['EQUITY']] - row['TRADED_AT']) * row['QTY']

            # Update the actual portfolio state (queues)
            portfolioState, realizedEvents = updatePortfolioState(portfolioState, todaysTrades)

        # C. Save snapshots
        for symbol, buyQueue in portfolioState.items():
            if not buyQueue: continue
            equityId = equityNameIdMap.get(symbol)
            if not equityId: continue

            totalQty = sum(item[1] for item in buyQueue)
            if totalQty <= 0: continue
                
            totalCost = sum(item[1] * item[2] for item in buyQueue)
            avgPrice = totalCost / totalQty
            currentPrice = getPrice(currentDate, symbol)
            totalCurrentValue = totalQty * currentPrice

            # D. Enhanced Daily Change Calculation
            yesterdayPrice = lastClosingPriceMap.get(equityId, currentPrice)
            openQty = openingState.get(equityId, 0)
            
            # 1. Gain from existing shares (Price movement since yesterday)
            movementGain = (currentPrice - yesterdayPrice) * openQty
            
            # 2. Gain from new shares (Price movement since purchase today)
            newPurchaseGain = tradeGainLoss.get(equityId, 0)
            
            dailyTotalChange = movementGain + newPurchaseGain
            
            lastClosingPriceMap[equityId] = currentPrice

            # E. Database logic
            existingEntry = EquityDayWisePosition.query.filter_by(
                userId=userId, equityId=equityId, asOfDate=currentDate
            ).first()

            if existingEntry:
                existingEntry.totalInvestment = totalCost
                existingEntry.currentInvestment = totalCurrentValue
                existingEntry.quantity = totalQty
                existingEntry.avgPrice = avgPrice
                existingEntry.dailyChange = dailyTotalChange
            else:
                db.session.add(EquityDayWisePosition(
                    equityId=equityId, userId=userId, asOfDate=currentDate, 
                    totalInvestment=totalCost, currentInvestment=totalCurrentValue,
                    quantity=totalQty, avgPrice=avgPrice, dailyChange=dailyTotalChange
                ))

        db.session.commit()
        print(f"Processed {currentDate} in {time.time() - t1:.4f}s")
        currentDate += timedelta(days=1)


def updatePortfolioState(portfolioState, todaysTrades):
    realizedEvents = [] # This is where the magic happens
    
    for row in todaysTrades.itertuples(index=False):
        symbol = row.EQUITY
        qty = row.QTY
        price = getattr(row, 'TRADED_AT')
        
        if qty > 0:
            portfolioState[symbol].append([row.DATE, qty, price])
        elif qty < 0:
            sellQty = abs(qty)
            buyQueue = portfolioState[symbol]
            
            while sellQty > 0 and buyQueue:
                buyDate, buyQty, buyPrice = buyQueue[0]
                matchQty = min(buyQty, sellQty)
                
                # Capture the P&L data for this specific match
                profit = (price - buyPrice) * matchQty
                holdingDays = (row.DATE - buyDate).days
                
                realizedEvents.append({
                    'symbol': symbol,
                    'buyDate': buyDate,
                    'sellDate': row.DATE,
                    'qty': matchQty,
                    'buyPrice': buyPrice,
                    'sellPrice': price,
                    'pnl': profit,
                    'holdingPeriod': holdingDays
                })
                
                buyQueue[0][1] -= matchQty
                sellQty -= matchQty
                if buyQueue[0][1] == 0:
                    buyQueue.popleft()
                    
    return portfolioState, realizedEvents

def determineCapitalGains(equityTrades, filterDate=None):
    results = []
    
    for equity in equityTrades:
        for trade in equityTrades[equity]:
            buy_date = trade['buyDate']
            sell_date = trade['sellDate']
            
            # Skip if not sold yet
            if buy_date is None or sell_date is None:
                continue 
            
            # --- NEW FILTER LOGIC ---
            if filterDate and sell_date <= filterDate:
                continue

            holding_period = (sell_date - buy_date).days
            gain = (trade['sellPrice'] - trade['buyPrice']) * trade['quantity']
            
            gain_type = 'STCG' if holding_period <= 365 else 'LTCG'
                
            results.append({
                'equity': equity,
                'type': gain_type,
                'gain': gain,
                'holding_period': holding_period,
                'buyDate': buy_date, # Useful to keep for verification
                'sellDate': sell_date # Useful to keep for verification
            })
    print ({t: sum(r['gain'] for r in results if r['type'] == t) for t in ['STCG', 'LTCG']})
    return results