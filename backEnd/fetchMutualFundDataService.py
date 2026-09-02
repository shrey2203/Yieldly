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
from dataQuery.mutualFundInvestmentsTransactionsQuery import MutualFundInvestmentsTransactions
from updateDayWisePositionMF import updateMutualFundDayWisePositionData
import applicationConfig
from dataQuery.userQuery import User
from flask import request, jsonify
# mutualFundPackage = MutualFundPackage(datetime.date(datetime.now()))

def def_value():
    return defaultdict(list)

def fetchMutualFund(mutualFundRawData, userId, reset = False):
    startTime = time.time()
    allUsersQueried = User.query.all()
    user = None
    for u in allUsersQueried:
        if str(userId).lower() == u.getUserName().lower(): 
            user = u
            break
            
    if not user:
        # Fallback to first user or dummy object
        user = allUsersQueried[0] if allUsersQueried else User(username=userId, panNumber=userId, emailAddress=f"{userId}@yieldly.com")

    global mutualFundPackage
    if not reset:
        return mutualFundPackage.to_dict()   

    if str(userId).upper() == 'COMBINED':
        import updateDayWisePositionMF
        import helperFunctions
        from autoDiscoveryService import backfill_combined_positions
        asOfDate = getLatestExistingData()
        all_individual_users = User.query.filter(User.username.in_(['Shrey', 'Monica', 'Yogesh', 'Bhavya'])).all()
        needs_sync = False
        for ind_user in all_individual_users:
            ind_latest = updateDayWisePositionMF.getLatestDateForDayWiseMFPosition(ind_user.getId())
            if ind_latest is None or ind_latest < asOfDate:
                needs_sync = True
                try:
                    ind_df = helperFunctions.getUserMutualFundDataFrame(ind_user.getUserName())
                    init(ind_user)
                    ind_pkg = MutualFundPackage(asOfDate, ind_user.getId())
                    for r in range(len(ind_df.values)):
                        rItem = ind_df.values[r]
                        tDate, fName, tType = rItem[0], rItem[1], rItem[5]
                        iMult = -1 if tType in ["Systematic Transfer Out", "Switch Out", "Sell"] else 1
                        sScheme = rItem[13] if tType in ["Systematic Transfer In", "Switch In"] else None
                        tScheme = rItem[14] if tType in ["Systematic Transfer Out", "Switch Out", "Sell"] else None
                        sDuty = 0 if pd.isna(rItem[11]) else rItem[11]
                        invObj = Investment(tDate, tType, rItem[6] * iMult, rItem[7] * iMult, rItem[8], sDuty, sScheme, tScheme)
                        if fName not in ind_pkg._mutualFundsMap:
                            ind_pkg.addMutualFund(MutualFund(fName))
                        ind_pkg._mutualFundsMap[fName].addInvestment(invObj)
                    updateDayWisePositionMF.updateMutualFundDayWisePositionData(ind_user.getId(), ind_pkg, ind_df, False)
                except Exception as e:
                    print(f"Error auto-syncing MF for {ind_user.getUserName()}: {e}")
        if needs_sync:
            backfill_combined_positions()

    init(user)
    # oneTimeFunction(mutualFundRawData, user.getId())

    asOfDate = getLatestExistingData()
    mutualFundPackage = MutualFundPackage(asOfDate, user.getId()) 
    mutualFundsMap = {} 

    for row in range(len(mutualFundRawData.values)):
        rowItem = mutualFundRawData.values[row]
        transactDate = rowItem[0]
        fundName = rowItem[1]
        transactType = rowItem[5]
        investedAmountMultiplier = 1
        sourceScheme, targetScheme = None, None
        investValue = rowItem[6]
        units = rowItem[7]
        nav = rowItem[8]
        stampDuty = rowItem[11]
        stampDuty = 0 if pd.isna(stampDuty) else stampDuty
        if transactType in ["Systematic Transfer In", "Switch In"]:
            sourceScheme = rowItem[13]
        if transactType in ["Systematic Transfer Out", "Switch Out", "Sell"]:
            targetScheme = rowItem[14]
            investedAmountMultiplier = -1
        investmentObject = Investment(transactDate, transactType, investValue * investedAmountMultiplier, units * investedAmountMultiplier, nav, stampDuty, sourceScheme, targetScheme)

        if fundName not in mutualFundsMap:
            mutualFundsMap[fundName] = MutualFund(fundName)

        mutualFundsMap[fundName].addInvestment(investmentObject)
    for mutualFund in mutualFundsMap.values():
        mutualFundPackage.addMutualFund(mutualFund)

    mutualFundDataAsOfDate = mutualFundPackage.to_dict()
    updateMutualFundDayWisePositionData(user.getId(), mutualFundPackage, mutualFundRawData, applicationConfig.backFillDayWisePositionMF)
    mutualFundDataAsOfDateUpdated = mutualFundPackage.postPersistingDayWisePosition(mutualFundDataAsOfDate)
    
    if str(userId).upper() == 'COMBINED':
        output = MutualFundDayWisePosition.query.filter_by(userId=1).all()
    else:
        output = MutualFundDayWisePosition.query.filter_by(userId=user.getId()).all()
        
    mutualFundDayWiseCurrentAndTotalValue = {}
    for fund in output:
        d_key = str(fund.getAsOfDate())
        if d_key not in mutualFundDayWiseCurrentAndTotalValue:
            mutualFundDayWiseCurrentAndTotalValue[d_key] = {'currentInvestment': 0, 'totalInvestment': 0}
        mutualFundDayWiseCurrentAndTotalValue[d_key]['currentInvestment'] += fund.getCurrentInvestment()
        mutualFundDayWiseCurrentAndTotalValue[d_key]['totalInvestment'] += fund.getTotalInvestment()
    mutualFundDataAsOfDateUpdated['mutualFundDayWiseCurrentAndTotalValue'] = mutualFundDayWiseCurrentAndTotalValue

    endTme = time.time()
    elapsedTime = endTme - startTime
    print ("Time taken load the Page for Mutual Funds is : " + str(elapsedTime))
    return mutualFundDataAsOfDateUpdated

def oneTimeFunction(mutualFundRawData, userId):
    for row in range(len(mutualFundRawData.values)):
        rowItem = mutualFundRawData.values[row]
        transactDate = rowItem[0]
        fundName = rowItem[1]
        transactType = rowItem[5]
        investValue = rowItem[6]
        units = rowItem[7]
        nav = rowItem[8]
        stampDuty = rowItem[11]
        totalAmount = rowItem[6]
        stampDuty = 0 if pd.isna(stampDuty) else stampDuty
        output = MutualFundMaster.query.filter_by(mutualFund = fundName).all()
        if len(output) != 0:
            newEntry = MutualFundInvestmentsTransactions(userId, output[0].getId(), transactDate, transactType, investValue, units, nav, stampDuty, totalAmount)
            db.session.add(newEntry)
        else:
            print ("Fund Reference Data is missing (https://www.mfapi.in), create a manual entry to fetch data for : " + fundName + "  Query is -->    INSERT INTO MF_MASTER VALUES (28, '" + fundName + "'150736, '2026-01-01 00:00:00.000', '2026-01-01 00:00:00.000')")
    db.session.commit()


def init(user):
    IsNewInvestments = checkIfNewInvestments(user)
    if IsNewInvestments: updateMutualFundData(withTimeContrainst=True)
    # updateMutualFundDataCustom("ICICI Pru Energy Opportunities Fund Reg (G)", datetime(2024, 7, 25, 0, 0, 0).date())

def checkIfNewInvestments(user):
    newInvestments = False
    latestInvestmentTransaction = getLatestInvestmentTransaction(user)
    if len(latestInvestmentTransaction.all()) == 0:
        latestInvestmentTransactionDate = datetime.strptime('01/01/2018', '%d/%m/%Y').date()
        newInvestments = True
    excelPath = '/Users/bhavya/Downloads/HOLDINGS/' + str(user.getUserName()) + '_MF.xlsx'
    dataframe = pd.read_excel(excelPath, 0)
    
    for _ in dataframe.values:
        transactionDates = dataframe.sort_values("TRANSACTION DATE")
        if (len(transactionDates) > 0 and len(latestInvestmentTransaction.all()) > 0):
            if transactionDates.iloc[:, 0].max().date() > latestInvestmentTransaction.first().getTransactionDate():
                newInvestments = True
                print ("There are some new Investments")
                break
    latestExistingData = def_value()
    if newInvestments:
        if len(latestInvestmentTransaction.all()) == 0:
            dataframe = dataframe[dataframe["TRANSACTION DATE"] >= pd.Timestamp(latestInvestmentTransactionDate)] 
        else:
            latestInvestmentTransactionforADate = getLatestInvestmentTransactionForADate(user, latestInvestmentTransaction.first().getTransactionDate())
            for i in latestInvestmentTransactionforADate.all():
                latestExistingData[latestInvestmentTransaction.first().getTransactionDate()].append(i.getMutualFundId())
            dataframe = dataframe[dataframe["TRANSACTION DATE"] >= pd.Timestamp(latestInvestmentTransaction.first().getTransactionDate())] 
        # Automatically discover and seed any newly added mutual funds from Excel
        from autoDiscoveryService import auto_discover_mutual_fund
        for row in dataframe.values:
            f_name = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else None
            if f_name and not MutualFundMaster.query.filter_by(mutualFund=f_name).first():
                auto_discover_mutual_fund(f_name)

        mutualFundMasters = MutualFundMaster.query.all()
        mutualFundMastersMap = {}
        for mutualFund in mutualFundMasters:
            mutualFundMastersMap[mutualFund.getMutualFund()] = mutualFund.getId()
        newInvestmentsList = []
        for i in dataframe.values:
            fund_name = i[1]
            mf_id = mutualFundMastersMap.get(fund_name)
            if not mf_id:
                auto_mf = auto_discover_mutual_fund(fund_name)
                if auto_mf:
                    mf_id = auto_mf.getId()
                    mutualFundMastersMap[fund_name] = mf_id
            if not mf_id:
                continue
            date, mf = i[0].date(), mf_id
            if date in latestExistingData and mf in latestExistingData[date]:
                continue
            newInvestmentsList.append(i)
        for row in newInvestmentsList:
            transactDate = row[0]
            fundName = row[1]
            transactType = row[5]
            investValue = row[6]
            units = row[7]
            nav = row[8]
            stampDuty = row[11]
            totalAmount = row[6]
            stampDuty = 0 if pd.isna(stampDuty) else stampDuty
            output = MutualFundMaster.query.filter_by(mutualFund = fundName).all()
            if not output:
                new_mf = auto_discover_mutual_fund(fundName)
                if new_mf:
                    output = [new_mf]
            if len(output) != 0:
                newEntry = MutualFundInvestmentsTransactions(user.getId(), output[0].getId(), transactDate, transactType, investValue, units, nav, stampDuty, totalAmount)
                db.session.add(newEntry)
            else:
                print(f"[AutoDiscovery] Could not resolve scheme code for '{fundName}'")
        db.session.commit()
    return newInvestments

def updateMutualFundData(withTimeContrainst):
    todayDateTime = datetime.now()
    mutualFundMasters = MutualFundMaster.query.all()
    for mutualFund in mutualFundMasters:
        lastUpdatedTime = mutualFund.getLastUpdatedTime()
        refreshFreqMF = applicationConfig.refreshFrequencyMF
        if withTimeContrainst and todayDateTime - lastUpdatedTime < timedelta(hours=refreshFreqMF): 
            print("The difference is less than " + str(refreshFreqMF) + " hours for " + mutualFund.getMutualFund() + ", not updating mutual fund data")
            continue
        startTime = time.time()
        latestExisitingDate = getLatestExistingData(mutualFund)
        url = "https://api.mfapi.in/mf/" + mutualFund.getISIN()
        mutualFundFetch = requests.get(url)
        mutualFundFetchJson = mutualFundFetch.json()
        for data in mutualFundFetchJson['data']:
            marketDate = datetime.strptime(data['date'], "%d-%m-%Y").date()
            if marketDate <= latestExisitingDate: break
            nav = data['nav']
            newEntry = MutualFundMarketData(
                    mutualFundId = mutualFund.getId(), 
                    marketDate = marketDate,
                    nav = nav
                )
            db.session.add(newEntry)
        mutualFund.lastUpdatedTime = todayDateTime 
        endTme = time.time()
        elapsedTime = endTme - startTime
        print ("Time taken to fetch MF NAV data is : " + str(elapsedTime) + " for MF : " + mutualFund.getMutualFund())
        db.session.commit()

def updateMutualFundDataCustom(mutualFund, latestExisitingDate):
    mutualFundMasters = MutualFundMaster.query.all()
    for i in mutualFundMasters:
        if i.getMutualFund() == mutualFund:
            todayDateTime = datetime.now()
            startTime = time.time()
            url = "https://api.mfapi.in/mf/" + i.getISIN()
            mutualFundFetch = requests.get(url)
            mutualFundFetchJson = mutualFundFetch.json()
            for data in mutualFundFetchJson['data']:
                marketDate = datetime.strptime(data['date'], "%d-%m-%Y").date()
                if marketDate <= latestExisitingDate: break
                nav = data['nav']
                newEntry = MutualFundMarketData(
                        mutualFundId = i.getId(), 
                        marketDate = marketDate,
                        nav = nav
                    )
                db.session.add(newEntry)
            i.lastUpdatedTime = todayDateTime 
            endTme = time.time()
            elapsedTime = endTme - startTime
            print ("Time taken to fetch MF NAV data is : " + str(elapsedTime) + " for MF : " + i.getMutualFund())
            db.session.commit()

def getLatestExistingData(mutualFund=None):
    if mutualFund:
        latestMarketData = MutualFundMarketData.query.filter_by(mutualFundId = mutualFund.getId()).order_by(desc(MutualFundMarketData.marketDate)).first()
    else:
        latestMarketData = MutualFundMarketData.query.order_by(desc(MutualFundMarketData.marketDate)).first()
    if latestMarketData:
        return latestMarketData.getMarketDate()
    else:
        return (datetime.today() - timedelta(days=100)).date()

def getLatestInvestmentTransaction(user):
    queryOutput = MutualFundInvestmentsTransactions.query.filter_by(userId=user.getId()).order_by(desc(MutualFundInvestmentsTransactions.transactionDate))
    if queryOutput:
        return queryOutput
    print ("No Existing data present for investment transactions")
    return None

def getLatestInvestmentTransactionForADate(user, transactionDate):
    queryOutput = MutualFundInvestmentsTransactions.query.filter_by(userId=user.getId(), transactionDate=transactionDate).order_by(desc(MutualFundInvestmentsTransactions.transactionDate))
    if queryOutput:
        return queryOutput
    print ("No Existing data present for investment transactions")
    return None