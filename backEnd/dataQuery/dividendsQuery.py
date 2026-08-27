from config import db
from datetime import datetime

class Dividends(db.Model):
    __tablename__ = 'DIVIDENDS' 
    id = db.Column(db.Integer, primary_key=True)
    equityId = db.Column(db.Integer, db.ForeignKey('EQUITY_MASTER.id'), nullable=False)
    payoutDate = db.Column(db.DateTime, nullable=False)
    dividendAmount = db.Column(db.Float, nullable=False)

    
    def getId(self):
        return self.id
    
    def getEquityId(self):
        return self.equityId
    
    def getPayoutDate(self):
        return self.payoutDate
    
    def getEquityLongName(self):
        return self.equityLongName

    def getDividendAmount(self):
        return self.dividendAmount