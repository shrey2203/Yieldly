from config import db
from datetime import datetime

class EquityMaster(db.Model):
    __tablename__ = 'EQUITY_MASTER' 
    id = db.Column(db.Integer, primary_key=True)
    equityShortName = db.Column(db.String(100), nullable=False) 
    equityLongName = db.Column(db.String(100), nullable=False) 
    yearHigh = db.Column(db.BigInteger, nullable=False)
    yearLow = db.Column(db.BigInteger, nullable=False)
    sector = db.Column(db.String(100), nullable=False)  
    lastUpdatedTime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Add this column
    divLastUpdatedTime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Add this column

    dividends = db.relationship('Dividends', backref='equity', lazy=True)
    
    def getId(self):
        return self.id
    
    def getYearHigh(self):
        return self.yearHigh
    
    def getEquityShortName(self):
        return self.equityShortName
    
    def getEquityLongName(self):
        return self.equityLongName

    def getYearLow(self):
        return self.yearLow

    def getSector(self):
        return self.sector
    
    def getLastUpdatedTime(self):
        return self.lastUpdatedTime
    
    def getDivLastUpdatedTime(self):
        return self.divLastUpdatedTime