# from nseScrap import *
# import time

# t1 = time.time()
# value = nse_eq('SBIN')['priceInfo']['lastPrice']
# t2  = time.time()
# print (t2-t1 , "seconds", value)


# t1 = time.time()
# value = nse_eq('SBIN')['priceInfo']['lastPrice']
# t2  = time.time()
# print (t2-t1 , "seconds", value)


# # ---------

# from pandas_datareader import data as pdr
# import yfinance as yf
# # yf.pdr_override() # <== that's all it takes :-)
# ticker = yf.Ticker("^NSEI")
# data = ticker.history(period="120mo", interval="1d")
# # [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
# print (data)


# # # --------

# import time
# from datetime import datetime
# while time:
#     time.sleep(6)
#     data=yf.download("TATAMOTORS.NS",interval="1m",period="1d")
#     print(data.index[-1],data.iloc[-1])
#     #  Get the current time
#     current_time = datetime.now()
#     print (current_time)
# # -----------

# # import matplotlib.pyplot as plt
# # data = yf.download("AAPL", start="2020-01-01", end="2021-01-01")
# # data['Close'].plot()
# # plt.title("Apple Stock Prices")
# # plt.show()

# # ------------
import yfinance as yf
import pandas as pd
import numpy as np

def get_nifty_50_metrics():
    # 1. Define the Nifty 50 Tickers (NSE suffix is .NS)
    # Note: List updated for Feb 2026 constituents including recent entrants like Zomato/Trent
    nifty50_tickers = [
        "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
        "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS",
        "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
        "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
        "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
        "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
        "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS",
        "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
        "TATACONSUM.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
        "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS", "ETERNAL.NS"
    ]
    
    benchmark = "^NSEI" # Nifty 50 Index
    risk_free_rate = 0.07 # 7% annual
    
    print("Fetching data for Nifty 50... this may take a moment.")
    
    # 2. Download all data at once for efficiency
    all_tickers = nifty50_tickers + [benchmark]
    data = yf.download(all_tickers, period="1y", interval="1d")['Close']
    
    # 3. Calculate Returns
    returns = data.pct_change().dropna()
    
    results = []
    
    for ticker in nifty50_tickers:
        try:
            stock_ret = returns[ticker]
            bench_ret = returns[benchmark]
            
            # Volatility (Annualized)
            ann_std = stock_ret.std() * np.sqrt(252)
            
            # Beta
            beta = stock_ret.cov(bench_ret) / bench_ret.var()
            
            # Sharpe Ratio
            ann_ret = stock_ret.mean() * 252
            sharpe = (ann_ret - risk_free_rate) / ann_std
            
            results.append({
                "Ticker": ticker.replace(".NS", ""),
                "Beta": round(beta, 2),
                "Volatility": f"{ann_std:.2%}",
                "Sharpe": round(sharpe, 2)
            })
        except Exception as e:
            continue

    # 4. Create DataFrame and Sort by Sharpe Ratio
    df = pd.DataFrame(results)
    return df.sort_values(by="Sharpe", ascending=False)

# Execute
nifty_report = get_nifty_50_metrics()

print("\n--- Nifty 50 Risk-Reward Report (Sorted by Sharpe) ---")
print(nifty_report.to_string(index=False))