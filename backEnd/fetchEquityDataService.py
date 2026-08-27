from collections import defaultdict
import numpy as np
import requests
from config import db
from mutualFunds.mutualFund import MutualFund
from mutualFunds.investment import Investment
import pandas as pd
from datetime import datetime, timedelta, date
from sqlalchemy import desc
import time
import yfinance as yf
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
import applicationConfig
import state
import supportAndResistanceLevels

def def_value():
    return defaultdict(list)
equitiesData = defaultdict(def_value) 

def fetchEquityData(allTradedEquities, portfolioAsOnDate):
    for row in range(len(allTradedEquities)): 
        equityMasterList = EquityMaster.query.all()
        equityMasterMap = {}
        for equityMaster in equityMasterList:
            equityMasterMap[equityMaster.getId()] = equityMaster
        equityMarketDataList = EquityMarketData.query.filter_by(marketDate = portfolioAsOnDate).all()
        while len(equityMarketDataList) == 0:
            if isinstance(portfolioAsOnDate, str):
                portfolioAsOnDate = datetime.strptime(portfolioAsOnDate, "%Y-%m-%d").date()
            portfolioAsOnDate = portfolioAsOnDate - timedelta(1)
            equityMarketDataList = EquityMarketData.query.filter_by(marketDate=portfolioAsOnDate).all()
        if len(equityMarketDataList) != 0:
            lastTradingDayData = getLastClose(equityMarketDataList, portfolioAsOnDate)
            for equityMarketData in equityMarketDataList:
                equity = equityMasterMap[equityMarketData.getEquityId()]
                equityShortName = equity.getEquityShortName()
                equitiesData[equityShortName]['lastPrice'] = equityMarketData.getClose()
                equitiesData[equityShortName]['Open'] = equityMarketData.getOpen()
                equitiesData[equityShortName]['High'] = equityMarketData.getHigh()
                equitiesData[equityShortName]['Low'] = equityMarketData.getLow()
                equitiesData[equityShortName]['lastClose'] = lastTradingDayData[equityShortName]
    return equitiesData

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


def getLatestEquityExistingData(equity):
    latestMarketData = EquityMarketData.query.filter_by(equityId = equity.getId()).order_by(desc(EquityMarketData.marketDate)).first()
    if latestMarketData == None:
        return -1
    return latestMarketData.getMarketDate()


def updateEquityData():
    todayDateTime = datetime.now()
    equityMasters = EquityMaster.query.all()
    for equity in equityMasters:
        lastUpdatedTime = equity.getLastUpdatedTime()
        if todayDateTime - lastUpdatedTime < timedelta(hours=applicationConfig.refreshFrequencyEquity): 
            print("The difference is less than " + str(applicationConfig.refreshFrequencyEquity) + " hours for " + equity.getEquityShortName() + ", not updating equity data")
            continue
        start_time = time.time()
        latestExisitingDate = getLatestEquityExistingData(equity)
        ticker = yf.Ticker(equity.getEquityShortName() + ".NS")
        if latestExisitingDate == -1:
            equityData = ticker.history(period="5y", interval="1d")
        else:
            equityData = ticker.history(start=latestExisitingDate, end=todayDateTime + timedelta(1), interval="1d")
        for i in range(len(equityData)):
            data = equityData.iloc[i]
            open = data["Open"]
            close = data["Close"]
            high = data["High"]
            low = data["Low"]
            marketDate = equityData.index[i].date()
            new_entry = EquityMarketData(
                equityId = equity.getId(),
                marketDate = marketDate,
                open = open, 
                close = close, 
                low = low, 
                high = high)
            db.session.add(new_entry)
        equity.lastUpdatedTime = todayDateTime 
        end_time = time.time()
        elapsed_time = end_time - start_time
        print ("Time taken to update data is : " + str(elapsed_time) + " for Equity : " + equity.getEquityLongName())
    db.session.commit()

def updateEquityDataNew():
    todayDateTime = datetime.now()
    print ("I am here")
    equityMaster = state.equityMasterCache
    for equityId in equityMaster:
        equity = equityMaster[equityId]
        lastUpdatedTime = equityMaster[equityId].getLastUpdatedTime()
        if todayDateTime - lastUpdatedTime < timedelta(hours=applicationConfig.refreshFrequencyEquity): 
            print("The difference is less than " + str(applicationConfig.refreshFrequencyEquity) + " hours for " + equity.getEquityShortName() + ", not updating equity data")
            continue
        startTime = time.time()

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
