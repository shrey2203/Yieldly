from collections import defaultdict
import numpy as np
import requests
from config import db
from mutualFunds.mutualFundPackage import MutualFundPackage
from mutualFunds.mutualFund import MutualFund
from mutualFunds.investment import Investment
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import desc
import time
from dataQuery.mutualFundMasterQuery import MutualFundMaster
from dataQuery.mutualFundMarketDataQuery import MutualFundMarketData
from dataQuery.mutualFundDayWisePositionQuery import MutualFundDayWisePosition
import applicationConfig

def def_value():
    return defaultdict(list)

def updateMutualFundDayWisePositionData(userId, mutualFundDataAsOfDate, mutualFundRawData, backfillSinceInception = False):
    mutualFundMasters = MutualFundMaster.query.all()
    mutualFundMastersMap = {}
    for mutualFund in mutualFundMasters:
        mutualFundMastersMap[mutualFund.getMutualFund()] = mutualFund
    
    latestDate = getLatestExistingData()    
    if not backfillSinceInception:
        latestExisitingDataDate = getLatestDateForDayWiseMFPosition(userId)
        while latestExisitingDataDate < latestDate:
            mutualFundData = createMutualFundPackage(mutualFundRawData, latestExisitingDataDate + timedelta(1), userId) 
            if mutualFundData: persistDayWisePositionMF(mutualFundData, userId, mutualFundMastersMap)
            latestExisitingDataDate += timedelta(days=1)
        return
    dayWisePositionStartDate = applicationConfig.dayWisePositionStartDate
    dayWisePositionStartDate = datetime.strptime(dayWisePositionStartDate, '%d/%m/%Y').date()
    while dayWisePositionStartDate <= latestDate:
        mutualFundData = createMutualFundPackage(mutualFundRawData, dayWisePositionStartDate, userId) 
        persistDayWisePositionMF(mutualFundData, userId, mutualFundMastersMap)
        dayWisePositionStartDate += timedelta(days=1)

            
def persistDayWisePositionMF(mutualFundData, userId, mutualFundMastersMap):
    todayDateTime = datetime.now()
    for mutualFund in mutualFundData.getMutualFunds():
        if mutualFund.getTotalUnits() * 1e8 - 1 < 0: continue
        mutualFundName = mutualFund.getFundName()
        mutualFundId = mutualFundMastersMap[mutualFundName].getId()
        mutualFundAsOfDate = mutualFundData.getAsOfDate()
        mutualFundTotalInvestment = mutualFund._mutualFundInvestedValue
        mutualFundTotalCurrentValue = mutualFund._mutualFundCurrentValue
        startTime = time.time()
        newEntry = MutualFundDayWisePosition(
                userId = userId,
                mutualFundId = mutualFundId,
                asOfDate = mutualFundAsOfDate,
                totalInvestment = mutualFundTotalInvestment,
                currentInvestment = mutualFundTotalCurrentValue)
        db.session.add(newEntry)
        mutualFundMastersMap[mutualFundName].dayWisePositionlastUpdatedTime = todayDateTime 
        endTime = time.time()
        elapsedTime = endTime - startTime
        print ("Time taken to update MF Position data is : " + str(elapsedTime) + " for MF : " + mutualFundName + " dated: " + str(mutualFundAsOfDate))
    db.session.commit()

def getLatestExistingData(mutualFund):
    latestMarketData = MutualFundMarketData.query.filter_by(mutualFundId = mutualFund.getId()).order_by(desc(MutualFundMarketData.marketDate)).first()
    return latestMarketData.getMarketDate()

def getLatestExistingData():
    latestMarketData = MutualFundMarketData.query.order_by(desc(MutualFundMarketData.marketDate)).first()
    return latestMarketData.getMarketDate()

def getLatestDateForDayWiseMFPosition(userId):
    latestDate = MutualFundDayWisePosition.query.filter_by(userId = userId).order_by(desc(MutualFundDayWisePosition.asOfDate)).first()
    if latestDate:
        return latestDate.getAsOfDate()
    return datetime(2018,3,1).date()

def createMutualFundPackage(mutualFundData, asOfDate, userId):   
    mutualFundPackage = MutualFundPackage(asOfDate, userId) 
    mutualFundsMap = {} 
    if mutualFundData["TRANSACTION DATE"].min().date() > asOfDate: return
    for row in range(len(mutualFundData.values)):
        rowItem = mutualFundData.values[row]
        transactDate = rowItem[0]
        if transactDate.date() > asOfDate: continue
        fundName = rowItem[1]
        transactType = rowItem[5]
        investedAmountMultiplier = 1
        sourceScheme, targetScheme = None, None
        investValue = rowItem[6]
        nav = rowItem[8]
        stampDuty = rowItem[11]
        stampDuty = 0 if pd.isna(stampDuty) else stampDuty
        units = rowItem[7]
        if transactType in ["Systematic Transfer In", "Switch In"]:
            sourceScheme = rowItem[13]
        if transactType in ["Systematic Transfer Out", "Switch Out", "Sell"]:
            targetScheme = rowItem[14]
            investedAmountMultiplier = -1
        investmentObject = Investment(transactDate, transactType, investValue * investedAmountMultiplier, units * investedAmountMultiplier, nav, stampDuty, sourceScheme, targetScheme)

        if fundName not in mutualFundsMap:
            mutualFundsMap[fundName] = MutualFund(fundName)
        mutualFundsMap[fundName].addInvestment(investmentObject, investmentObject._transactDate.date() <= asOfDate)
    for mutualFund in mutualFundsMap.values():
        mutualFundPackage.addMutualFund(mutualFund)

    mutualFundPackage.processMutualFundPackage()
    return mutualFundPackage