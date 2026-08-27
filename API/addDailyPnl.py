import applicationConfig
import preparingDetailsMap
import datetime
from pandas_datareader import data as pdr
import commonUtils

def addDailyPnlData(dailyPnl):
    dailyPnlData = [['Date', 'Invested Amount', 'Portfolio Value', 'Daily Pnl', 'Pnl %', applicationConfig.benchmarkIndex, 'Change in : ' + applicationConfig.benchmarkIndex]]
    today = datetime.date.today()
    previousPresentValue = 0
    if applicationConfig.useBenchmarkIndex:
        benchmarkIndex = applicationConfig.benchmarkIndex
        indexValuePreviousDay = 1
        indexData = pdr.get_data_yahoo(benchmarkIndex, start = datetime.datetime(2020, 1, 1), end = today)
    for date, portfolio in dailyPnl.items():
        investedValue, presentValue = portfolio[0], portfolio[1]
        pnl = presentValue - previousPresentValue
        previousPresentValue = presentValue
        simplifiedDate = datetime.datetime.strptime(commonUtils.convertDatetoSimpleDate(date), '%d-%m-%Y').date()
        if len(indexData[indexData.index.date == simplifiedDate]['Close']) != 0:
            indexValuePresentDay = indexData[indexData.index.date == simplifiedDate]['Close'][0]
        else:
            indexValuePresentDay = indexValuePreviousDay
        changeInIndex = (indexValuePresentDay - indexValuePreviousDay) * 100 / indexValuePreviousDay
        if presentValue != 0:
            dailyPnlData.append([date, investedValue, presentValue, pnl, pnl*100/presentValue, indexValuePresentDay, changeInIndex])
        else:
            dailyPnlData.append([date, investedValue, presentValue, pnl, 0, indexValuePresentDay, changeInIndex])
        indexValuePreviousDay = indexValuePresentDay
    return dailyPnlData