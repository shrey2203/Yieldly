from datetime import datetime

def convertDatetoSimpleDate(date):
    if date == "INCEPTION":
        return date
    formatted_date = date.strftime("%d-%m-%Y")
    return formatted_date


def differenceBetweenDates(date1, date2):
    return (date2 - date1).days


def convertFinalHoldings(finalHoldings, transactionSummary, realtime):
    output = []
    if not realtime:    
        for keys, values in finalHoldings.items():
            temp = {}
            temp["stock"] = keys
            temp["price"] = values[0]
            temp["quantity"] = values[1]
            temp["transactionSummary"] = transactionSummary.get(keys, [])
            output.append(temp)
    else:
        for item in finalHoldings:
            if item[0] in ["TOTAL: ", "EQUITY", "TOTAL"]: 
                continue
            temp = {}
            temp["stock"] = item[0]
            temp["quantity"] = item[1]
            temp["price"] = item[2]
            temp["totalBuy"] = item[3]
            temp["ltp"] = item[4]
            temp["totalValue"] = item[5]
            temp["unrealisedPnL"] = item[6]
            temp["pnlPercent"] = item[7]
            temp["sector"] = item[8]
            temp["industry"] = item[9]
            temp["peRatio"] = item[10]
            temp["yearLow"] = item[11]
            temp["yearHigh"] = item[12]
            temp["dailyChangePercent"] = item[14]
            temp["dailyChange"] = item[15]
            temp["transactionSummary"] = transactionSummary.get(item[0], [])            
            output.append(temp)
    return output