import pandas as pd
import prepareSectoralandIndustrialPercentage
import stockRates
import addFinalHoldings 
import addSquaredOffData
import addWatchListData
from addToSheet import *
from scrapping import *
import prepareFinalHoldings
import preparingDetailsMap
import accumulatedBuyTrades
import addAggregatedBuyPositions
import applicationConfig
import addDailyPnl

excel_file = '/Users/bhavya/Downloads/HOLDINGS/SHREY.xlsx'
dataframe = pd.read_excel(excel_file, 0)
args = pd.read_excel(excel_file, 1)

def main():
    allTradedEquities = preparingDetailsMap.prepareAllTradedEquities(dataframe)
    liveQuotesMapScrapping = scrappingData(allTradedEquities)
    if applicationConfig.getAggregatedBuyPosition:
        aggregatedBuyPosition = accumulatedBuyTrades.getAccumulatedBuyTrades(dataframe, args)
        aggregatedBuyPostionData = addAggregatedBuyPositions.addAggregatedBuyPositionsData(aggregatedBuyPosition, liveQuotesMapScrapping)
        addToSheet(excel_file, [aggregatedBuyPostionData[0]] + sorted(aggregatedBuyPostionData[1:-1]) + [aggregatedBuyPostionData[-1]], 'Aggregated Buy')

    finalHoldings = prepareFinalHoldings.prepareFinalHoldingsMap(dataframe)
    # sectoralPercentage, industrialPercentageMap = prepareSectoralandIndustrialPercentage.prepareSectoralandIndustrialPercentageMap(finalHoldings, liveQuotesMapScrapping)

    # if applicationConfig.getDailyPnl:
    #     dailyPnl = prepareFinalHoldings.prepareDailyPnLMap(dataframe)
    #     finalDailyPnlData = addDailyPnl.addDailyPnlData(dailyPnl)
    #     addToSheet(excel_file, finalDailyPnlData, 'Daily PNL')

    finalHoldingsData = addFinalHoldings.addFinalHoldingData(finalHoldings, liveQuotesMapScrapping)
    addToSheet(excel_file, [finalHoldingsData[0]] + sorted(finalHoldingsData[1:-1]) + [finalHoldingsData[-1]], 'Final Holdings')

    squaredOffData = addSquaredOffData.addSquaredOffData(preparingDetailsMap.realisedPnL)
    addToSheet(excel_file, [squaredOffData[0]] + sorted(squaredOffData[1:-1]) + [squaredOffData[-1]], 'Squared Off')

    

if __name__ == "__main__":
    main()

# For LTP after Market Hours, gives instant result.
liveQuotesMap = stockRates.liveRates()