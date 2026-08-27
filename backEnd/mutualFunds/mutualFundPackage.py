from mutualFunds.mutualFund import MutualFund
from datetime import timedelta
from dataQuery.mutualFundDayWisePositionQuery import MutualFundDayWisePosition


class MutualFundPackage:
    def __init__(self, asOfDate, userId):
        self._mutualFunds = []
        self._asOfDate = asOfDate
        self._todayPNL = 0
        self._userId = userId

    def addMutualFund(self, mutualFund):
        if isinstance(mutualFund, MutualFund):
            if len(mutualFund.getAllInvestments()) != 0 and mutualFund.getTotalUnits() * 1e8 - 1 > 0:
                self._mutualFunds.append(mutualFund)
        else:
            raise ValueError("Invalid mutual fund object")

    def getTotalInvestedSum(self):
        totalInvestedSum = 0
        for mutualFund in self._mutualFunds:
            totalInvestedSum += mutualFund.getTotalInvestment()
        return totalInvestedSum

    def getTotalCurrentSum(self):
        totalCurrentValueSum = 0
        for mutualFund in self._mutualFunds:
            totalCurrentValueSum += mutualFund.getTotalCurrentValue()
        return totalCurrentValueSum
    
    def getTotalTaxation(self):
        STCG, LTCG = 0, 0
        for mutualFund in self._mutualFunds:
            taxationMap = mutualFund.calculateTaxation()
            LTCG += taxationMap["ltcg"]
            STCG += taxationMap["stcg"]
        return LTCG, STCG
    
    def getTotalCurrentSumAsOfDate(self):
        totalCurrentValueSum = 0
        for mutualFund in self._mutualFunds:
            totalCurrentValueSum += mutualFund.getTotalCurrentValueAsOfDate(self._asOfDate)
        return totalCurrentValueSum
    
    def getTotalUnitsMF(self):
        totalUnits = 0
        for mutualFund in self._mutualFunds:
            totalUnits += mutualFund.getTotalUnits()
        return totalUnits
    
    def getMutualFunds(self):
        return self._mutualFunds
    
    def getAsOfDate(self):
        return self._asOfDate
    
    def computeTodayPNL(self):
        valueDateInvestedValue, valueDateCurrentValue, investedToday = 0, 0, 0
        todayCurrentValue = self.getTotalCurrentSum()
        output = MutualFundDayWisePosition.query.filter_by(asOfDate = self._asOfDate - timedelta(days=1), userId = self._userId).all()
        for mutualFundDayWisePosition in output:
            valueDateInvestedValue += mutualFundDayWisePosition.getTotalInvestment()
            valueDateCurrentValue += mutualFundDayWisePosition.getCurrentInvestment()
        if self._mutualFunds:
            for mutualFund in self._mutualFunds:
                for investment in mutualFund.getAllInvestments():
                    if investment.getTransactDate().date() == self._asOfDate:
                        investedToday += investment.getInvestValue()
        self._todayPNL = todayCurrentValue - valueDateCurrentValue - investedToday
        return self._todayPNL
    
    def processMutualFundPackage(self):
        self.getAsOfDate()
        self.getTotalCurrentSumAsOfDate()
        self.getTotalInvestedSum()
        self.getTotalUnitsMF()

    def to_dict(self):
        totalCurrentValueSum = self.getTotalCurrentSum()
        totalInvestedValueSum = self.getTotalInvestedSum()
        mutualFunds = [fund.to_dict(self._userId, self._asOfDate) for fund in self._mutualFunds]
        ltcg, stcg = self.getTotalTaxation()
        return {
            "asOfDate": self.getAsOfDate(),
            "todayPNL": self.computeTodayPNL(),
            "totalCurrentSum": totalCurrentValueSum,
            "totalInvestedSum": totalInvestedValueSum,
            "mutualFunds": mutualFunds,
            "ltcg" : ltcg,
            "stcg" : stcg
        }
    
    def postPersistingDayWisePosition(self, mutualFundDataAsOfDate):
        for i in range(len(self._mutualFunds)):
            PNL = self._mutualFunds[i].calculateXTDPNL(self._userId, self._asOfDate)
            PNL1D, PNL1M, PNL1Y = PNL['PNL1D'], PNL['PNL1M'], PNL['PNL1Y']
            mutualFundDataAsOfDate['mutualFunds'][i]['PNL1D'] = PNL1D
            mutualFundDataAsOfDate['mutualFunds'][i]['PNL1M'] = PNL1M
            mutualFundDataAsOfDate['mutualFunds'][i]['PNL1Y'] = PNL1Y
        return mutualFundDataAsOfDate