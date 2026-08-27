from config import db
from sqlalchemy import desc

class EquityDayWisePosition(db.Model):
    __tablename__ = 'Equity_DayWisePosition' 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('USERS.id'), nullable=False)
    equityId = db.Column(db.Integer, db.ForeignKey('EQUITY_MASTER.id'), nullable=False)
    asOfDate = db.Column(db.Date, nullable=False, index=True)
    totalInvestment = db.Column(db.BigInteger, unique=False, nullable=False)  
    currentInvestment = db.Column(db.BigInteger, unique=False, nullable=False)    
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    avgPrice = db.Column(db.Numeric(18, 2), nullable=False)
    dailyChange = db.Column(db.Numeric(18, 2))
    
    def __init__(self, userId, equityId, asOfDate, totalInvestment, currentInvestment, quantity, avgPrice, dailyChange):
        self.userId = userId
        self.equityId = equityId
        self.asOfDate = asOfDate
        self.totalInvestment = totalInvestment
        self.currentInvestment = currentInvestment
        self.quantity = quantity
        self.avgPrice = avgPrice
        self.dailyChange = dailyChange

    def getId(self):
        return self.id

    def getEquityId(self):
        return self.equityId
    
    def getUserId(self):
        return self.userId
    
    def getCurrentInvestment(self):
        return self.currentInvestment
    
    def getTotalInvestment(self):
        return self.totalInvestment
    
    def getAsOfDate(self):
        return self.asOfDate
    
    def getPnL(self):
        return self.currentInvestment - self.totalInvestment
    
    def getQuantity(self):
        return self.quantity
    
    def getAvgPrice(self):
        return self.avgPrice
    
    def getDailyChange(self):
        return self.dailyChange
