from config import db

class EquityMarketData(db.Model):
    __tablename__ = 'EQUITY_MARKET_DATA' 
    id = db.Column(db.Integer, primary_key=True)
    equityId = db.Column(db.Integer, primary_key=False) 
    marketDate = db.Column(db.Date, nullable=False)
    open = db.Column(db.BigInteger, unique=False, nullable=True)
    close = db.Column(db.BigInteger, unique=False, nullable=True)
    low = db.Column(db.BigInteger, unique=False, nullable=True)
    high = db.Column(db.BigInteger, unique=False, nullable=True)

    def getId(self):
        return self.id

    def getEquityId(self):
        return self.equityId

    def getMarketDate(self):
        return self.marketDate

    def getOpen(self):
        return self.open

    def getClose(self):
        return self.close

    def getLow(self):
        return self.low

    def getHigh(self):
        return self.high
