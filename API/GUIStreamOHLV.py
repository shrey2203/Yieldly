import yfinance as yf

def streamOHLV(scrip):
    data = yf.download(scrip+".NS", interval="1d", period="1d")
    # print(data.iloc[-1])
    return(data.iloc[-1])