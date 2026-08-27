def addFinalHoldingData(finalHoldingsData, liveQuotesMap):
    finalHoldingData = [['EQUITY', 'QTY', 'AVERAGE BUY', 'TOTAL BUY', "LTP", "TOTAL VALUE", "UNREALISED P/L", "P/L %", "SECTOR", "INDUSTRY", "P/E Ratio", "52W High", "52W Low", "CHIP", "DAILY CHANGE PERCENT", "DAILY CHANGE"]]
    grandTotalBuy, grandTotalValue = 0, 0
    for equity, parameters in finalHoldingsData.items():
        qty = parameters[1]
        averageBuy = parameters[0]
        ltp, unrealisedPnl, totalValue, pnlPercentage, sector, industry = "Not Available", "Not Available", "Not Available", "Not Available", "Not Available", "Not Available"
        peRatio, yearLow, yearHigh, category, dailyChangePercent, dailyChange = "Not Available", "Not Available", "Not Available", "Not Available", "Not Available", "Not Available"
        try:
            if equity in liveQuotesMap.keys():
                ltp = liveQuotesMap[equity]["lastPrice"] 
                unrealisedPnl = (ltp - averageBuy) * qty
                totalValue = ltp * qty
                if averageBuy == 0: #case of a demerger
                    pnlPercentage = 0
                else:
                    pnlPercentage = 100 * unrealisedPnl/ (qty * averageBuy)
                sector = ""
                industry = liveQuotesMap[equity]['Industry']
                peRatio = ""
                yearLow = liveQuotesMap[equity]["52w Low"]
                yearHigh = liveQuotesMap[equity]["52w High"]
                category = ""
                dailyChangePercent = (liveQuotesMap[equity]["lastPrice"] - liveQuotesMap[equity]["lastClose"]) *100 / liveQuotesMap[equity]["lastClose"]
                dailyChange = (liveQuotesMap[equity]["lastPrice"] - liveQuotesMap[equity]["lastClose"]) * qty
                grandTotalBuy += averageBuy * qty
                grandTotalValue += totalValue
        
                finalHoldingData.append([equity, qty, averageBuy, qty * averageBuy, ltp, totalValue, unrealisedPnl, round(pnlPercentage, 2), sector, industry, peRatio, yearLow, yearHigh, category, dailyChangePercent, dailyChange])
        except:
            continue
        totalPnl= grandTotalValue - grandTotalBuy
        if grandTotalBuy == 0:
            totalPnlPercentage = (totalPnl * 100)/1
        else:
            totalPnlPercentage = (totalPnl * 100)/grandTotalBuy
    finalHoldingData.append(["TOTAL: ", "", "", grandTotalBuy, "", grandTotalValue, totalPnl, totalPnlPercentage, peRatio, yearLow, yearHigh, category])
    return finalHoldingData    



def getCategory(data):
    if "NIFTY 50" in data or "NIFTY 100" in data:
        return "LargeCap"
    else:
        return "yet to implement"

