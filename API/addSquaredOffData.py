import commonUtils

def addSquaredOffData(realisedPnLMap):
    squaredOffData = [['EQUITY', 'QTY', 'BUY DATE', 'BUY PRICE', 'BUY VALUE', 'SELL DATE', 'SELL PRICE', 'SELL VALUE', 'P/L', 'P/L %', 'VERDICT', 'HOLDING DAYS']]
    totalPnl = 0
    for equity, allParameters in realisedPnLMap.items():
        for parameters in allParameters:
            buyDate, sellDate, qty, buyPrice, sellPrice = parameters[0], parameters[1], parameters[2], parameters[3], parameters[4]
            buyValue = buyPrice * qty
            sellValue = sellPrice * qty
            verdict = 'Profit'
            if parameters[4] < parameters[3]: 
                verdict = 'Loss'
            if buyDate == "INCEPTION":
                holdingDays = "Infinity"
            else:
                holdingDays = commonUtils.differenceBetweenDates(buyDate, sellDate)
            if buyPrice == 0:
                squaredOffData.append([equity, qty, commonUtils.convertDatetoSimpleDate(buyDate), buyPrice, buyValue, commonUtils.convertDatetoSimpleDate(sellDate), sellPrice, sellValue, (sellPrice-buyPrice)*qty, "Infinity", verdict, holdingDays])
                continue
            pnl = (sellPrice-buyPrice) * qty
            totalPnl += pnl
            pnlPercentage = 100 * (sellPrice - buyPrice)/buyPrice
            squaredOffData.append([equity, qty, commonUtils.convertDatetoSimpleDate(buyDate), buyPrice, buyValue, commonUtils.convertDatetoSimpleDate(sellDate), sellPrice, sellValue, pnl, pnlPercentage, verdict, holdingDays])
    squaredOffData.append(["TOTAL: ", "", "", "", "", "", "", "", totalPnl, "", "", ""])
    return squaredOffData