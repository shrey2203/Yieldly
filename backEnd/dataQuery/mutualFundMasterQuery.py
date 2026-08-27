from config import db
from datetime import datetime

class MutualFundMaster(db.Model):
    __tablename__ = 'MF_MASTER' 
    id = db.Column(db.Integer, primary_key=True)
    mutualFund = db.Column(db.String(100), nullable=False)  
    ISIN = db.Column(db.String(100), nullable=False)
    lastUpdatedTime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Add this column
    dayWisePositionlastUpdatedTime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Add this column


    def getId(self):
        return self.id

    def getMutualFund(self):
        return self.mutualFund

    def getISIN(self):
        return self.ISIN
    
    def getLastUpdatedTime(self):
        return self.lastUpdatedTime
    
    def getDayWisePositionlastUpdatedTime(self):
        return self.dayWisePositionlastUpdatedTime
