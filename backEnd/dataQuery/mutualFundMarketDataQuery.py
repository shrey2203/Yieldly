from config import db
from sqlalchemy import desc

class MutualFundMarketData(db.Model):
    __tablename__ = 'MF_MARKET_DATA' 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mutualFundId = db.Column(db.Integer, db.ForeignKey('MF_MASTER.id'), nullable=False)
    marketDate = db.Column(db.Date, nullable=False)
    nav = db.Column(db.BigInteger, unique=False, nullable=False)    
    
    def __init__(self, mutualFundId, marketDate, nav):
        self.mutualFundId = mutualFundId
        self.marketDate = marketDate
        self.nav = nav

    def getId(self):
        return self.id

    def getMutualFundId(self):
        return self.mutualFundId

    def getMarketDate(self):
        return self.marketDate

    def getNav(self):
        return self.nav
    
    # @staticmethod
    # def getLatestByMutualFund(mutualFundId):
    #     return MutualFundMarketData.query \
    #         .filter_by(mutualFundId=mutualFundId) \
    #         .order_by(desc(MutualFundMarketData.marketDate)) \
    #         .first()