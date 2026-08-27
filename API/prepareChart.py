from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()
data = pdr.get_data_yahoo("TATAMOTORS.NS", period="120mo",interval="1d")
# [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
print ((data))
# for index, row in data.iterrows():
#     print(index, row['Open'])
#     break

# import finplot as fplt
# import yfinance
# df = yfinance.download('TATAMOTORS.NS')
# fplt.candlestick_ochl(df[['Open', 'Close', 'High', 'Low']])
# fplt.show()