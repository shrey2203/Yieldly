from preparingDetailsMap import *
import applicationConfig
import matplotlib.pyplot as plt 

def prepareFinalHoldingsMap(dataframe, portfolioAsOnDate):
    # global finalHoldings
    finalHoldings = {}
    # Preparing a map - date:trades.
    dateTradewiseDetailsMap = preparedateTradewiseDetailsMap(dataframe, portfolioAsOnDate)
    # Preparing a map - equity:trades on all dates.
    equityFinalHoldings = prepareEquityFinalHoldingsMap(dateTradewiseDetailsMap)

    # Preparing Final Holdings
    finalHoldings = prepareAggregatedHoldings(equityFinalHoldings)
    return finalHoldings

def prepareDailyPnLMap(dataframe, portfolioAsOnDate):
    # Preparing a day wise pnl
    dateTradewiseDetailsMap = preparedateTradewiseDetailsMap(dataframe, portfolioAsOnDate)
    dailyPnl = prepareDailyPnl(dataframe, dateTradewiseDetailsMap)
    dates = list(dailyPnl.keys())      
    prices = list(dailyPnl.values())
    # plt.plot(dates, prices, '-')
    # plt.show()
    return dailyPnl