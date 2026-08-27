import prepareFinalHoldings
import math
from datetime import datetime
import pandas as pd
import numpy as np

def getAccumulatedBuyTrades(dataframe, args):
    for header in args.values:
        startDate, endDate =  header[0], header[1]
    if pd.isnull(startDate) and math.isnan(startDate):
        startDate = datetime(2000, 1, 1, 00, 00, 00)
    if pd.isnull(endDate) and math.isnan(endDate):
        endDate = datetime(2099, 1, 1, 00, 00, 00)
    if startDate == "INCEPTION":
        startDate = datetime(2000, 1, 1, 00, 00, 00)
    if endDate == "INCEPTION":
        endDate = datetime(2099, 1, 1, 00, 00, 00)
    if isPandasTimestamp(startDate):
        startDate = startDate.to_pydatetime()
    if isPandasTimestamp(endDate):
        endDate = endDate.to_pydatetime()
    if isNumpyDatetime64(startDate):
        startDate = datetime.utcfromtimestamp(startDate.astype(int) * 1e-9)
    if isNumpyDatetime64(endDate):
        endDate = datetime.utcfromtimestamp(endDate.astype(int) * 1e-9)
    return filterOutBuyTrades(dataframe, startDate, endDate)


def filterOutBuyTrades(dataframe, startDate, endDate):
    df_copy = dataframe.copy(deep=True)
    for index, row in dataframe.iterrows():
        date, e, qty, _ =  row["DATE"], row["EQUITY"], row["QTY"], row["TRADED_AT"]
        if date == "INCEPTION": 
            date = datetime(2000, 1, 1, 00, 00, 00)
        if qty > 0 and startDate <= date and date <= endDate:
            continue
        else:
            df_copy.drop(index, inplace = True)
    return prepareFinalHoldings.prepareFinalHoldingsMap(df_copy)


def isPandasTimestamp(obj):
    return isinstance(obj, pd.Timestamp)

def isNumpyDatetime64(obj):
    return isinstance(obj, np.datetime64)