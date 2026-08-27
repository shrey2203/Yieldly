def addAggregatedBuyPositionsData(aggregatedBuyPosition, liveQuotesMap):
    aggregatedBuyPositionsData = [['EQUITY', 'QTY', 'AVERAGE BUY', 'TOTAL BUY', "LTP", "TOTAL VALUE", "UNREALISED P/L", "P/L %", "P/E Ratio", "52W High", "52W Low", "CHIP"]]
    grandTotalBuy, grandTotalValue = 0, 0
    for equity, parameters in aggregatedBuyPosition.items():
        qty = parameters[1]
        averageBuy = parameters[0]
        ltp, unrealisedPnl, totalValue, pnlPercentage = "Not Available", "Not Available", "Not Available", "Not Available"
        peRatio, yearLow, yearHigh, category = "Not Available", "Not Available", "Not Available", "Not Available"
        if equity in liveQuotesMap.keys():
            ltp = liveQuotesMap[equity]["lastPrice"] 
            unrealisedPnl = (ltp - averageBuy) * qty
            totalValue = ltp * qty
            pnlPercentage = 100 * unrealisedPnl/ (qty * averageBuy)
            peRatio = liveQuotesMap[equity]["PE"]
            yearLow = liveQuotesMap[equity]["52w Low"]
            yearHigh = liveQuotesMap[equity]["52w High"]
            category = getCategory(liveQuotesMap[equity]["Indices"])
            grandTotalBuy += averageBuy * qty
            grandTotalValue += totalValue
        aggregatedBuyPositionsData.append([equity, qty, averageBuy, qty * averageBuy, ltp, totalValue, unrealisedPnl, pnlPercentage, peRatio, yearLow, yearHigh, category])
    totalPnl= grandTotalValue - grandTotalBuy
    totalPnlPercentage = (totalPnl * 100)/grandTotalBuy
    aggregatedBuyPositionsData.append(["TOTAL: ", "", "", grandTotalBuy, "", grandTotalValue, totalPnl, totalPnlPercentage, peRatio, yearLow, yearHigh, category])
    return aggregatedBuyPositionsData






def getCategory(data):
    if "NIFTY 50" in data or "NIFTY 100" in data:
        return "LargeCap"
    else:
        return "yet to implement"