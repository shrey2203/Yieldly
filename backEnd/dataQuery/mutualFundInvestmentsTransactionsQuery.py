from config import db

class MutualFundInvestmentsTransactions(db.Model):
    __tablename__ = 'MF_INVESTMENTS_TRANSACTIONS' 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, unique=False, nullable=False)
    transactionDate = db.Column(db.Date, nullable=False)
    mutualFundId = db.Column(db.Integer, db.ForeignKey('MF_MASTER.id'), nullable=False)
    transactionType = db.Column(db.String(100), nullable=False) 
    amount = db.Column(db.BigInteger, unique=False, nullable=False)
    units = db.Column(db.BigInteger, unique=False, nullable=False)
    nav = db.Column(db.BigInteger, unique=False, nullable=False)
    stampDuty = db.Column(db.BigInteger, unique=False, nullable=False)
    totalAmount = db.Column(db.BigInteger, unique=False, nullable=False)

    def __init__(self, userId, mutualFundId, transactionDate, transactionType, amount, units, nav, stampDuty, totalAmount):
        self.userId = userId
        self.mutualFundId = mutualFundId
        self.transactionDate = transactionDate
        self.transactionType = transactionType
        self.amount = amount
        self.units = units
        self.nav = nav
        self.stampDuty = stampDuty
        self.totalAmount = totalAmount


    def getId(self):
        return self.id

    def getTransactionDate(self):
        return self.transactionDate

    def getMutualFundId(self):
        return self.mutualFundId

    def getTransactionType(self):
        return self.transactionType

    def getAmount(self):
        return self.amount

    def getUnits(self):
        return self.units

    def getNav(self):
        return self.nav
    
    def getStampDuty(self):
        return self.stampDuty
    
    def getTotalAmount(self):
        return self.totalAmount