import financialMath
from datetime import date

class Investment:
    def __init__(self, transactDate, transactType, investValue, units, nav, stampDuty, sourceScheme, targetScheme):
        self._transactDate = transactDate
        self._transactType = transactType
        self._investValue = investValue
        self._units = units
        self._nav = nav
        self._stampDuty = stampDuty
        self._sourceScheme = sourceScheme
        self._targetScheme = targetScheme
        self._currentNAV = None
        self._currentValue = None
        self._profitLoss = None
        self._holdingDays = self.getHoldingDays()
        self._absPNLPercentange = None
        self._cagr = None

    def getTransactDate(self):
        return self._transactDate

    def setTransactDate(self, value):
        self._transactDate = value

    def getTransactType(self):
        return self._transactType

    def setTransactType(self, value):
        self._transactType = value

    def getInvestValue(self):
        return self._investValue

    def setInvestValue(self, value):
        if value < 0:
            raise ValueError("Investment value cannot be negative")
        self._investValue = value

    def getUnits(self):
        return self._units

    def setUnits(self, value):
        if value < 0:
            raise ValueError("Units cannot be negative")
        self._units = value

    def getNav(self):
        return self._nav

    def setNav(self, value):
        if value <= 0:
            raise ValueError("NAV must be positive")
        self._nav = value

    def getStampDuty(self):
        return self._stampDuty

    def setStampDuty(self, value):
        if value < 0:
            raise ValueError("Stamp duty cannot be negative")
        self._stampDuty = value

    def getCurrentNAV(self):
        return self._currentNAV

    def setCurrentNAV(self, value):
        self._currentNAV = value

    def getCurrentValue(self):
        return self._currentValue

    def setCurrentValue(self, value):
        self._currentValue = value

    def getProfitLoss(self):
        return self._profitLoss

    def setProfitLoss(self, value):
        self._profitLoss = value 

    def getHoldingDays(self):
        return financialMath.calculate_holding_days(self._transactDate)
    
    def getAbsPNLPercentange(self):
        return financialMath.calculate_abs_return(self._profitLoss, self._investValue)
    
    def getcagr(self):
        return financialMath.calculate_cagr(self._investValue, self._currentValue, self._holdingDays)
    
    def isLongTermOrShortTerm(self):
        return financialMath.get_tax_holding_type(self._holdingDays)

    def to_dict(self):
        return {
            "transactDate": str(self._transactDate),
            "transactType": self._transactType,
            "investValue": self._investValue,
            "units": self._units,
            "nav": self._nav,
            "stampDuty": self._stampDuty,
            "currentNAV" : self._currentNAV,
            "currentValue" : self._currentValue,
            "profitLoss" : self._profitLoss,
            "holdingDays" : self._holdingDays,
            "absPNLPercentange" : self.getAbsPNLPercentange(),
            "cagr" : self.getcagr(),
            "taxation" : self.isLongTermOrShortTerm()
        }