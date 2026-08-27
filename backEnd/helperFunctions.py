from config import db
from sqlalchemy import desc

from dataQuery.userQuery import User
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.equityDayWisePositionQuery import EquityDayWisePosition
from datetime import datetime, timedelta


def getUserId(username):
    allUsersQueried = User.query.all()
    for user in allUsersQueried:
        if username.lower() == user.getUserName().lower(): 
            username = user.getId()
            return user.getId()
        
def getLatestExistingEquityMarketData():
    latestMarketData = EquityMarketData.query.order_by(desc(EquityMarketData.marketDate)).first()
    return latestMarketData.getMarketDate()


def getLatestDateForDayWiseEquityPosition(userId):
    latestDate = EquityDayWisePosition.query.filter_by(userId = userId).order_by(desc(EquityDayWisePosition.asOfDate)).first()
    if latestDate:
        return latestDate.getAsOfDate()
    return datetime(2018,1,1).date()