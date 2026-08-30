def addFinalHoldingData(finalHoldingsData, liveQuotesMap, equityMasterCache):
    headers = [
        'EQUITY', 'QTY', 'AVERAGE BUY', 'TOTAL BUY', "LTP", "TOTAL VALUE", 
        "UNREALISED P/L", "P/L %", "SECTOR", "INDUSTRY", "P/E Ratio", 
        "52W High", "52W Low", "CHIP", "DAILY CHANGE PERCENT", "DAILY CHANGE"
    ]
    finalHoldingData = [headers]
    grandTotalBuy, grandTotalValue = 0, 0
    def get_sector_from_cache(stock_name):
        for equity_obj in equityMasterCache.values():
            if equity_obj.equityShortName == stock_name:
                return getattr(equity_obj, 'sector', 'Other') 
        return "Other"

    for equity, parameters in finalHoldingsData.items():
        qty = parameters[1]
        averageBuy = parameters[0]
        
        # Initialize defaults
        ltp = 0
        unrealisedPnl = 0
        totalValue = 0
        pnlPercentage = 0
        
        # Fetch Sector from DB Cache first (More reliable than scraper)
        sector = get_sector_from_cache(equity)
        industry = "Other"
        
        peRatio = 0
        yearLow = 0
        yearHigh = 0
        category = ""
        dailyChangePercent = 0
        dailyChange = 0
        if equity in liveQuotesMap:
            stock_data = liveQuotesMap[equity]
            ltp = stock_data.get("lastPrice", 0)
            last_close = stock_data.get("lastClose", ltp)
            unrealisedPnl = (ltp - averageBuy) * qty
            totalValue = ltp * qty            
            if averageBuy != 0:
                pnlPercentage = (unrealisedPnl / (qty * averageBuy)) * 100
            if sector == "Other":
                sector = stock_data.get('Sector', stock_data.get('Industry', 'Other'))
            
            industry = stock_data.get('Industry', 'Other')
            yearLow = stock_data.get("52w Low", 0)
            yearHigh = stock_data.get("52w High", 0)
            
            if last_close != 0:
                dailyChangePercent = ((ltp - last_close) / last_close) * 100
                dailyChange = (ltp - last_close) * qty
        else:
            ltp = averageBuy
            totalValue = qty * averageBuy
            unrealisedPnl = 0
            pnlPercentage = 0

        grandTotalBuy += (averageBuy * qty)
        grandTotalValue += totalValue

        finalHoldingData.append([
            equity, qty, averageBuy, qty * averageBuy, ltp, totalValue, 
            unrealisedPnl, round(pnlPercentage, 2), sector, industry, 
            peRatio, yearHigh, yearLow, category, dailyChangePercent, dailyChange
        ])
    totalPnl = grandTotalValue - grandTotalBuy
    totalPnlPercentage = (totalPnl * 100) / grandTotalBuy if grandTotalBuy != 0 else 0
    finalHoldingData.append([
        "TOTAL", "", "", grandTotalBuy, "", grandTotalValue, 
        totalPnl, totalPnlPercentage, "", "", "", "", "", "", "", ""
    ]) 
    return finalHoldingData

def getCategory(data):
    if "NIFTY 50" in data or "NIFTY 100" in data:
        return "LargeCap"
    else:
        return "yet to implement"