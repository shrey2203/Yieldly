from mutualFunds.investment import Investment
import requests
import time
from datetime import date, timedelta, datetime
from dataQuery.mutualFundMarketDataQuery import MutualFundMarketData
from dataQuery.mutualFundDayWisePositionQuery import MutualFundDayWisePosition
from sqlalchemy import desc
from dataQuery.mutualFundMasterQuery import MutualFundMaster
import state
import financialMath


class MutualFund:
    def __init__(self, name):
        self._name = name
        self._investments = [] 
        self._mutualFundCurrentValue = 0
        self._mutualFundInvestedValue = 0
        self._mutualFundNAV = 0
        self._mutualFundUnits = 0

    def getFundName(self):
        return self._name
    
    def addInvestment(self, investment):
        if isinstance(investment, Investment):
            self._investments.append(investment)
        else:
            raise ValueError("Invalid investment object")
        
    def addInvestment(self, investment, isEligible = True):
        if isinstance(investment, Investment) and isEligible:
            self._investments.append(investment)
        if not isinstance(investment, Investment):
            raise ValueError("Invalid investment object")
        else: return

    def getTotalInvestment(self):
        if self._mutualFundInvestedValue != 0: return self._mutualFundInvestedValue
        investSum = 0
        for investment in self._investments:
            investSum += investment.getInvestValue() + investment.getStampDuty()
        self._mutualFundInvestedValue = investSum
        return self._mutualFundInvestedValue
    
    def getProfitLoss(self):
        pnl = 0
        for investment in self._investments:
            pnl += investment.getProfitLoss()
        return pnl

    def getTotalCurrentValue(self):
        # latestNAV = 0
        latestNAV = self.latestMutualFundNAV(self._name)
        self._mutualFundNAV = latestNAV
        currentSum = 0 
        for investment in self._investments:
            investment.setCurrentNAV(latestNAV)
            investment.setCurrentValue(investment.getUnits() * latestNAV)
            investment.setProfitLoss((investment.getUnits() * latestNAV) - investment.getInvestValue())
            currentSum += investment.getCurrentValue()
        self._mutualFundCurrentValue = currentSum
        return self._mutualFundCurrentValue
    
    def getTotalCurrentValueAsOfDate(self, asOfDate):
        if self._mutualFundCurrentValue != 0: return self._mutualFundCurrentValue
        NAV = self.getMutualFundNAV(self._name, asOfDate)
        self._mutualFundNAV = NAV
        currentSum = 0 
        for investment in self._investments:
            investment.setCurrentNAV(NAV)
            investment.setCurrentValue(investment.getUnits() * NAV)
            investment.setProfitLoss((investment.getCurrentValue()) - investment.getInvestValue())
            currentSum += investment.getCurrentValue()
        self._mutualFundCurrentValue = currentSum
        return self._mutualFundCurrentValue
    
    def getCurentMutualFundNAV(self):
        return 0
    
    def getXTDPNL(self, navType, mutualFundName, userId, asOfDate):
        mutualFund = MutualFundMaster.query.filter_by(mutualFund = mutualFundName).first()
        match navType:
            case "dtd":
                investedToday = 0
                for investment in self.getAllInvestments():
                    if investment.getTransactDate().date() == asOfDate:
                        investedToday += investment.getInvestValue()
                output = (MutualFundDayWisePosition.query.filter_by(mutualFundId=mutualFund.getId(), userId = userId).order_by(desc(MutualFundDayWisePosition.asOfDate)).limit(2).all())
                if len(output) < 2:
                    print ("Investment in fund: " +  mutualFund.getMutualFund() + " was done as of T-1")
                    return output[0].getCurrentInvestment() - output[0].getTotalInvestment()
                secondLatestPNL = output[1]
                return self.getTotalCurrentValue() - secondLatestPNL.getCurrentInvestment() - investedToday
            case "mtd":
                # today = date.today()
                firstDayOfMonth = asOfDate.replace(day=1)
                monthStartPNL = (MutualFundDayWisePosition.query.filter(MutualFundDayWisePosition.asOfDate == firstDayOfMonth, MutualFundDayWisePosition.mutualFundId == mutualFund.getId(), MutualFundDayWisePosition.userId == userId))
                backtrack = firstDayOfMonth
                while not monthStartPNL:
                    backtrack = backtrack - timedelta(days=1)
                    monthStartPNL = (MutualFundDayWisePosition.query.filter(MutualFundDayWisePosition.asOfDate == backtrack, MutualFundDayWisePosition.mutualFundId == mutualFund.getId(), MutualFundDayWisePosition.userId == userId))
                    if backtrack.month != firstDayOfMonth.month:
                        raise ValueError("Unable to find valid MTD start PNL")
                if len(monthStartPNL.all()) == 0:
                    return (self.getTotalCurrentValue() - self.getTotalInvestment())
                return (self.getTotalCurrentValue() - self.getTotalInvestment()) - (monthStartPNL.first().getCurrentInvestment() - monthStartPNL.first().getTotalInvestment())
            case "ytd":
                # today = date.today()
                firstDayOfMonth = asOfDate.replace(day=1)
                firstDayOfYear = firstDayOfMonth.replace(month=1)
                yearStartPNL = (MutualFundDayWisePosition.query.filter(MutualFundDayWisePosition.asOfDate == firstDayOfYear, MutualFundDayWisePosition.mutualFundId == mutualFund.getId(), MutualFundDayWisePosition.userId == userId))
                backtrack = firstDayOfYear
                while not yearStartPNL:
                    backtrack = backtrack - timedelta(days=1)
                    yearStartPNL = (MutualFundDayWisePosition.query.filter(MutualFundDayWisePosition.asOfDate == backtrack, MutualFundDayWisePosition.mutualFundId == mutualFund.getId(), MutualFundDayWisePosition.userId == userId))
                    if backtrack.year != firstDayOfYear.year:
                        raise ValueError("Unable to find valid YTD start PNL")
                if len(yearStartPNL.all()) == 0:
                    return (self.getTotalCurrentValue() - self.getTotalInvestment())
                return (self.getTotalCurrentValue() - self.getTotalInvestment()) - (yearStartPNL.first().getCurrentInvestment() - yearStartPNL.first().getTotalInvestment())
            case _:
                raise ValueError(f"Invalid NAV type: {navType}")
            
    def getXTDNAV(self, navType, mutualFundName):
        mutualFund = MutualFundMaster.query.filter_by(mutualFund = mutualFundName).first()
        match navType:
            case "dtd":
                lastTwo = (MutualFundMarketData.query.filter_by(mutualFundId=mutualFund.getId()).order_by(desc(MutualFundMarketData.marketDate)).limit(2).all())
                if len(lastTwo) < 2:
                    raise ValueError("Not enough market data for DTD calculation")
                secondLatest = lastTwo[1]
                return secondLatest.getNav()
            case "mtd":
                today = date.today()
                firstDayOfMonth = today.replace(day=1)
                monthStartNav = (MutualFundMarketData.query.filter_by(mutualFundId=mutualFund.getId(), marketDate=firstDayOfMonth).first())
                backtrack = firstDayOfMonth
                while not monthStartNav:
                    backtrack = backtrack - timedelta(days=1)
                    monthStartNav = (MutualFundMarketData.query.filter_by(mutualFundId=mutualFund.getId(), marketDate=backtrack).first())
                    if backtrack.month != firstDayOfMonth.month:
                        raise ValueError("Unable to find valid MTD start NAV")
                return monthStartNav.getNav()
            case _:
                raise ValueError(f"Invalid NAV type: {navType}")


    def getTotalUnits(self):
        if self._mutualFundUnits != 0: return self._mutualFundUnits
        investUnits = 0
        for investment in self._investments:
            investUnits += investment.getUnits()
        self._mutualFundUnits = investUnits
        return investUnits

    def setTotalUnits(self, value):
        self._mutualFundUnits = value
    
    def getAverageNav(self):
        investSum = self.getTotalInvestment()
        totalUnits = self.getTotalUnits()

        if totalUnits == 0:
            return None

        return investSum / totalUnits

    
    def getAllInvestments(self):
        return self._investments
    
    def getAbsPNLPercentage(self):
        return financialMath.calculate_abs_return(self.getProfitLoss(), self.getTotalInvestment())
    
    def getMaxHoldingDays(self):
        return max((inv.getHoldingDays() for inv in self._investments), default=0)
    
    def getCAGR(self):
        return financialMath.calculate_cagr(self.getTotalInvestment(), self.getTotalCurrentValue(), self.getMaxHoldingDays())

    def getXIRR(self, asOfDate=None):
        if not self._investments:
            return 0.0
        
        currentVal = self.getTotalCurrentValue()
        totalInvested = self.getTotalInvestment()
        
        if totalInvested <= 0 or currentVal <= 0:
            return 0.0

        # Build raw date & cashflow pairs (negative for purchases)
        cashflows = []
        for inv in self._investments:
            cost = inv.getInvestValue() + inv.getStampDuty()
            if cost > 0:
                cashflows.append((inv.getTransactDate(), -float(cost)))

        if not cashflows:
            return 0.0

        eval_date = asOfDate if asOfDate else date.today()
        cashflows.append((eval_date, float(currentVal)))

        return financialMath.calculate_xirr(cashflows, as_of_date=eval_date, fallback_cagr=True)

    
    def to_dict(self, userId, asOfDate):
        investments = [inv.to_dict() for inv in self._investments]
        tax_data = self.calculateTaxation()
        return {
            "name": self._name,
            "totalInvestment": self.getTotalInvestment(),
            "totalCurrentValue": self.getTotalCurrentValue(),
            "totalUnits": self.getTotalUnits(),
            "mutualFundNAV": self._mutualFundNAV,
            "PNL1D": 0,
            "PNL1M": 0,
            "PNL1Y": 0,
            "averageNav": self.getAverageNav(),
            "investments": investments,
            "holdingDays": max((inv.getHoldingDays() for inv in self._investments), default=0),
            "absPNLPercentage": self.getAbsPNLPercentage(),
            "cagr": self.getCAGR(),
            "xirr": self.getXIRR(asOfDate),
            "ltcg": tax_data["ltcg"],
            "stcg": tax_data["stcg"]
        }
    
    def calculateXTDPNL(self, userId, asOfDate):
        return {
            "PNL1D": self.getXTDPNL("dtd", self._name, userId, asOfDate),
            "PNL1M": self.getXTDPNL("mtd", self._name, userId, asOfDate),
            "PNL1Y": self.getXTDPNL("ytd", self._name, userId, asOfDate)
        }
    
    def calculateTaxation(self):
        ltcg, stcg = 0, 0
        for inv in self._investments:
            # Standard 1-year threshold for Equity
            if inv.getHoldingDays() > 365:
                ltcg += inv.getProfitLoss()
            else:
                stcg += inv.getProfitLoss()
        return {"ltcg": ltcg, "stcg": stcg}
        
    
    def latestMutualFundNAV(self, mutualFundName):
        # mutualFundAPIMap = {}
        # mutualFundAPIMap["Quant Flexi Cap Fund (G)"] = 109830
        # mutualFundAPIMap["HDFC NIFTY200 Momentum 30 Index Fund Reg (G)"] = 152429
        # mutualFundAPIMap["HDFC Small Cap Fund (G)"] = 130502
        # mutualFundAPIMap["HDFC Large And Mid Cap Fund Reg (G)"] = 130496
        # mutualFundAPIMap["Nippon India Multi Cap Fund (G)"] = 101161
        # mutualFundAPIMap["Nippon India Growth Fund (G)"] = 100377
        # mutualFundAPIMap["Nippon India Growth Mid Cap Fund (G)"] = 118668
        # mutualFundAPIMap["Invesco India PSU Equity Fund (G)"] = 112171
        # mutualFundAPIMap["SBI Automotive Opportunities Fund Reg (G)"] = 152658
        # mutualFundAPIMap["PGIM India Flexi Cap Fund (G)"] = 133836
        # mutualFundAPIMap["Parag Parikh Flexi Cap Fund Reg (G)"] = 122640
        # mutualFundAPIMap["Aditya Birla SL Frontline Equity Fund Reg (G)"] = 103174
        # mutualFundAPIMap["Mirae Asset Large & Midcap Fund Reg (G)"] = 112932
        # mutualFundAPIMap["Mirae Asset Large Cap Fund Reg (G)"] = 107578
        # mutualFundAPIMap["Kotak Flexi Cap Fund Reg (G)"] = 112090
        # mutualFundAPIMap["Mirae Asset Ultra Short Duration Fund Reg (G)"] = 148530
        # mutualFundAPIMap["Mirae Asset Global X Artificial Intelligence & Technology E T F FoF Reg (G)"] = 150596
        # mutualFundAPIMap["Mirae Asset Multicap Fund Reg (G)"] = 151812
        # mutualFundAPIMap["Quant Small Cap Fund (G)"] = 100177
        # mutualFundAPIMap["Quant Large and Mid Cap Fund (G)"] = 104513
        # mutualFundAPIMap["SBI PSU Fund Reg (G)"] = 113099
        # mutualFundAPIMap["Invesco India Infrastructure Fund (G)"] = 106654
        # mutualFundAPIMap["HDFC Defence Fund Reg (G)"] = 151751
        # mutualFundAPIMap["ICICI Pru Energy Opp Fund Reg (G)"] = 152726
        # mutualFundAPIMap["Motilal Oswal Nifty India Defence Index Fund Reg (G)"] = 152711
        # mutualFundAPIMap["Kotak Nifty Next 50 Index Fund Reg (G)"] = 148743
        # mutualFundAPIMap["Tata Digital India Fund Reg Plan (G)"] = 135799
        # mutualFundAPIMap["Motilal Oswal Midcap Fund Reg (G)"] = 127039






        # start_time = time.time()
        # url = "https://api.mfapi.in/mf/" + str(mutualFundAPIMap[mutualFundName]) + "/latest"
        # mutualFundFetch = requests.get(url)
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print ("Time taken to fetch rates is : " + str(elapsed_time) + " for MF : " + mutualFundName)
        # mutualFundFetchJson = mutualFundFetch.json()
        # return float(mutualFundFetchJson['data'][0]['nav'])

        fundData = state.mutualFundMarketDataCache.get(mutualFundName)
        if fundData:
            return state.mutualFundMarketDataCache[mutualFundName]['nav']
        mutualFund = MutualFundMaster.query.filter_by(mutualFund = mutualFundName).first()
        latestMarketData = MutualFundMarketData.query.filter_by(mutualFundId = mutualFund.getId()).order_by(desc(MutualFundMarketData.marketDate)).first()
        return latestMarketData.getNav()
    
    def getMutualFundNAV(self, mutualFundName, asOfDate):
        mutualFund = MutualFundMaster.query.filter_by(mutualFund = mutualFundName).first()
        marketData = MutualFundMarketData.query.filter_by(mutualFundId = mutualFund.getId(), marketDate = asOfDate).first()
        while True:
            marketData = MutualFundMarketData.query.filter_by(mutualFundId = mutualFund.getId(), marketDate = asOfDate).first()
            if marketData:
                return marketData.getNav()
            if asOfDate > date(2024, 6, 4) and asOfDate < date(2024,6, 12) and mutualFundName == 'SBI Automotive Opportunities Fund Reg (G)':
                return 10.0
            if asOfDate == date(2023, 8, 21) and mutualFundName == 'Mirae Asset Multicap Fund Reg (G)':
                return 10.0
            if asOfDate == date(2023, 8, 21) and mutualFundName == 'Mirae Asset Multicap Fund Reg (G)':
                return 10.0
            if asOfDate == date(2024, 7, 21) and mutualFundName == 'ICICI Pru Energy Opportunities Fund Reg (G)':
                return 10.0
            asOfDate = asOfDate - timedelta(days=1)


