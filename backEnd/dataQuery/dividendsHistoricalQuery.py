from config import db
from datetime import datetime

class DividendsHistorical(db.Model):
    __tablename__ = 'DIVIDENDS_HISTORICAL' 
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('USERS.id'), nullable=False)
    equityId = db.Column(db.Integer, db.ForeignKey('EQUITY_MASTER.id'), nullable=False)
    payoutDate = db.Column(db.DateTime, nullable=False)
    dividendPerShare = db.Column(db.Numeric(18, 4), nullable=False)
    quantityHeld = db.Column(db.Numeric(18, 4), nullable=False)
    totalDividendAmount = db.Column(db.Numeric(18, 2), nullable=False)
    
    def getId(self):
        return self.id
    
    def getUserId(self):
        return self.userId
    
    def getEquityId(self):
        return self.equityId
    
    def getPayoutDate(self):
        return self.payoutDate

    def getQuantityHeld(self):
        return self.quantityHeld
    
    def getDividendPerShare(self):
        return self.dividendPerShare
    
    def getTotalDividendAmount(self):
        return self.totalDividendAmount