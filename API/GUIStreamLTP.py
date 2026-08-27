import yfinance as yf

def streamLTP(scrip):
    # t1 = time.time()
    # value = nse_eq(scrip)
    # t2 = time.time()
    # print ("Time taken to fetch : ", scrip, " was ", t2-t1, " seconds")
    # return value['priceInfo']['lastPrice']
    data = yf.download(scrip+".NS", interval="1m", period="1d")
    # print(data.iloc[-1])
    return(data.iloc[-1,3])


def streamStaleLTP(scrip):
    data = yf.download(scrip+".NS", interval="30m", period="1d")
    return(data.iloc[-1,3])