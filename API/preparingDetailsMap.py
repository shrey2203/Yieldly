from collections import defaultdict
from pandas_datareader import data as pdr
import yfinance as yf
from datetime import date
from datetime import datetime
from datetime import timedelta

global today
today = date.today()

def def_value(): 
    return []

def preparedateTradewiseDetailsMap(dataframe, portfolioAsOnDate):
    dateTradewiseDetailsMap = {}
    for header in dataframe.values:
        date, equity, qty, tradePrice =  header[0], header[1], header[2], header[3]
        if isinstance(portfolioAsOnDate, str):
            portfolioAsOnDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
        if date.date() > portfolioAsOnDate: 
            continue
        if date not in dateTradewiseDetailsMap:
            dateTradewiseDetailsMap[date] = [[equity, qty, tradePrice]]
        else:
            dateTradewiseDetailsMap[date].append([equity, qty, tradePrice])
    return dateTradewiseDetailsMap

def prepareEquityTradesMap(dateTradewiseDetailsMap):
    # Prepared a map - 
    # KEY : Equity
    # VALUE : Trades on all dates. 
    equityTradesMap = {}
    for date, details in dateTradewiseDetailsMap.items():
        for trade in details:
            equity, qty, price = trade[0], trade[1], trade[2]
            if equity not in equityTradesMap:
                equityTradesMap[equity] = [[date, qty, price]]
            else:
                equityTradesMap[equity].append([date, qty, price])
    return equityTradesMap

def prepareEquityFinalHoldingsMap(dateTradewiseDetailsMap):
    global realisedPnL
    equityTradesMap = prepareEquityTradesMap(dateTradewiseDetailsMap)
    equityFinalHoldings = defaultdict(def_value)
    realisedPnL = defaultdict(def_value)
    # equity : [buyDate, sellDate, qty, buyPrice, sellPrice]
    for equity, allTrades in equityTradesMap.items():
        queue = allTrades
        finalQueue = []
        while queue:
            element = queue.pop(0)
            date, qty, price = element[0], element[1], element[2]
            if qty > 0:
                finalQueue.append(element)
            else:
                #  Intraday
                if date == finalQueue[-1][0]:
                    if finalQueue[-1][1] > -qty:
                        finalQueue[-1][1] = finalQueue[-1][1] + qty
                        realisedPnL[equity].append([finalQueue[-1][0], date, -qty, finalQueue[-1][2], price])
                        continue
                    elif finalQueue[-1][1] == -qty:
                        realisedPnL[equity].append([finalQueue[-1][0], date, -qty, finalQueue[-1][2], price])
                        del finalQueue[-1]
                        continue
                    else:
                        while date == finalQueue[-1][0]:
                            realisedPnL[equity].append([finalQueue[-1][0], date, -qty, finalQueue[-1][2], price])
                            del finalQueue[-1]
                # If our buy is more than sell we should not pop the element
                # Just realise the proffit/loss and reduce the quantity - doing a plus operator since qty is negative.
                if finalQueue[0][1] > -qty:
                    finalQueue[0] = [finalQueue[0][0], finalQueue[0][1] + qty, finalQueue[0][2]]
                    realisedPnL[equity].append([finalQueue[0][0], date, -qty, finalQueue[0][2], price])
                else:
                    sellQty = abs(qty)
                    while sellQty:
                        #  If sell qty is not higher than second or later instance, then popping of element is not required.
                        if finalQueue[0][1] > sellQty:
                            finalQueue[0] = [finalQueue[0][0], finalQueue[0][1] - sellQty, finalQueue[0][2]]
                            realisedPnL[equity].append([finalQueue[0][0], date, sellQty, finalQueue[0][2], price])
                            sellQty = 0
                        else:
                            firstBuyElement = finalQueue.pop(0)
                            realisedPnL[equity].append([firstBuyElement[0], date, firstBuyElement[1], firstBuyElement[2], price])
                            sellQty = sellQty - firstBuyElement[1]
        equityFinalHoldings[equity] = finalQueue
    return equityFinalHoldings



def prepareAggregatedHoldings(equityFinalHoldings):
    aggregatedHoldings = defaultdict(def_value)
    for equity, trades in equityFinalHoldings.items():
        totalBuy, totalQty = 0, 0
        for _, qty, price in trades:
            totalBuy += qty * price
            totalQty += qty
        if totalQty != 0:
            aggregatedHoldings[equity] = [totalBuy/totalQty, totalQty]
    return aggregatedHoldings

def prepareAllTradedEquities(dataframe):
    alltradedEquities = set()
    for header in dataframe.values:
        equity = header[1]
        alltradedEquities.add(equity)
    return alltradedEquities

def prepareAllPositionalEquities(dataframe):
    positionalEquities = set()
    positionalEquitiesMap = defaultdict(int)
    for header in dataframe.values:
        equity, qty = header[1], header[2]
        positionalEquitiesMap[equity] += qty 
    for key, value in positionalEquitiesMap.items():
        if value != 0:
            positionalEquities.add(key)
    return positionalEquities

def prepareAllTradedDates(dataframe):
    alltradedDates = set()
    for header in dataframe.values:
        date =  header[0]
        alltradedDates.add(date)
    return sorted(list(alltradedDates))

def prepareDailyPnl(dataframe, dateTradewiseDetailsMap): 
    incrementalDateTradewiseDetailsMap = {}
    allTradedEquities = set()
    global masterHistoricalData
    masterHistoricalData = {}
    dailyPnl = {}
    alltradedDates = prepareAllTradedDates(dataframe)
    next = 1
    lastValue = [0, 0]
    for date, details in dateTradewiseDetailsMap.items():
        if len(alltradedDates) <= next: #check again
            nextDate = today
        else: 
            nextDate = alltradedDates[next]
            next += 1
        incrementalDateTradewiseDetailsMap[date] = details
        incrementalEquityFinalHoldings = prepareEquityFinalHoldingsMap(incrementalDateTradewiseDetailsMap)
        incrementalFinalHoldings = prepareAggregatedHoldings(incrementalEquityFinalHoldings)
        for equity, _ in incrementalEquityFinalHoldings.items():
            if equity not in allTradedEquities:
                getHistoricalDataEquity(equity, startDate = date)
                allTradedEquities.add(equity)
        while datetime.timestamp(date) != float(nextDate.strftime("%s")):
            output = getIncrementalDailyPnl(date, incrementalFinalHoldings)
            if output == "useLast":
                dailyPnl[date] = lastValue
            else:
                dailyPnl[date] = output
                lastValue = dailyPnl[date]
            date += timedelta(days=1)
    return dailyPnl

def getHistoricalDataEquity(equity, startDate):
    yf.pdr_override()  
    data = pdr.get_data_yahoo(equity + ".NS", start = startDate, end = today)
    masterHistoricalData[equity] = data

def getIncrementalDailyPnl(date, finalHoldings):
    totalBuyValue, totalCurrValue = 0, 0
    for equity, details in finalHoldings.items():
        price, qty = details[0], details[1]
        if date not in masterHistoricalData[equity].index:
            if not checkIfFinalHoldingsEmpty(finalHoldings):
                return "useLast"
            else:
                continue
        else:
            totalBuyValue += price * qty
            totalCurrValue += masterHistoricalData[equity].loc[date]["Close"] * qty
    return [totalBuyValue, totalCurrValue]

def checkIfFinalHoldingsEmpty(finalHoldings):
    for _, v in finalHoldings.items():
        if len(v) != 0:
            return False