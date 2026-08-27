from config import db
from sqlalchemy import desc

class MutualFundDayWisePosition(db.Model):
    __tablename__ = 'MF_DayWisePosition' 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('USERS.id'), nullable=False)
    mutualFundId = db.Column(db.Integer, db.ForeignKey('MF_MASTER.id'), nullable=False)
    asOfDate = db.Column(db.Date, nullable=False)
    totalInvestment = db.Column(db.BigInteger, unique=False, nullable=False)  
    currentInvestment = db.Column(db.BigInteger, unique=False, nullable=False)    
    
    def __init__(self, userId, mutualFundId, asOfDate, totalInvestment, currentInvestment):
        self.userId = userId
        self.mutualFundId = mutualFundId
        self.asOfDate = asOfDate
        self.totalInvestment = totalInvestment
        self.currentInvestment = currentInvestment

    def getId(self):
        return self.id

    def getMutualFundId(self):
        return self.mutualFundId
    
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
