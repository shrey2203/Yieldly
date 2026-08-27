def addWatchListData(finalHoldings, liveQuotesMap):
    watchListData = [["EQUITY", "LTP", "OPEN", "DAY LOW", "DAY HIGH", "VOLUME"]]
    for equity in finalHoldings.keys():
        ltp = "Not Available"
        open = "Not Available"
        dayLow = "Not Available"
        dayHigh = "Not Available"
        volume = "Not Available"
        if equity in liveQuotesMap.keys():
            ltp = liveQuotesMap[equity]["lastPrice"]
            open = liveQuotesMap[equity]["open"]
            dayLow = liveQuotesMap[equity]["dayLow"]
            dayHigh = liveQuotesMap[equity]["dayHigh"]
            volume = liveQuotesMap[equity]["totalTradedVolume"]
        watchListData.append([equity, ltp, open, dayLow, dayHigh, volume])
    return watchListData