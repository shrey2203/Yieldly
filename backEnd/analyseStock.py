# import numpy as np
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# import sys
# sys.path.append('/Users/bhavya/Downloads/API')
# from addToSheet import *
# import applicationConfig


# class AnalyseStock:
#     def __init__(self, stock):
#         self.stock = stock.upper()
#         self.fiiHolding = None
#         self.diiHolding = None
#         self.rsi = None
#         self.eps = None
#         self.support_resistance = None
#         self.pe_ratio = None
#         self.fibonacci = None

#     def getShareHoldingPattern(self, driver):
#         def getshareHoldingPatternEntity(shareholdingYears, entityID):
#             shareHoldingMap = []
#             path = "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr[" + str(entityID) + "]/td"
#             shareholdingEntity = driver.find_elements(By.XPATH, path)
#             for i in range(len(shareholdingYears)):
#                 holding = shareholdingEntity[i].text
#                 shareHoldingMap.append(holding)
#             return shareHoldingMap
        
#         shareHoldingPattern = []
#         shareholdingYears = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/thead[1]/tr[1]/th")
#         totalShareHolders = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr")
#         for i in range(len(totalShareHolders)):
#             shareHoldingPatternEntity = getshareHoldingPatternEntity(shareholdingYears, i+1)
#             shareHoldingPattern.append(shareHoldingPatternEntity)
#         allYears = self.getYears(shareholdingYears)
#         for item in shareHoldingPattern:
#             if item[0] == "FIIs +" and len(item) > 3:
#                 lastHolding = float(item[-1].replace("%", ""))
#                 secondLastHolding = float(item[-2].replace("%", ""))
#                 if lastHolding > secondLastHolding:
#                     self.fiiHolding = "⬆" + str(round(lastHolding - secondLastHolding, 3)) + "%"
#                 else:
#                     self.fiiHolding = "⬇" + str(round(lastHolding - secondLastHolding, 3)) + "%"
#             elif item[0] == "DIIs +" and len(item) > 3:
#                 lastHolding = float(item[-1].replace("%", ""))
#                 secondLastHolding = float(item[-2].replace("%", ""))
#                 if lastHolding > secondLastHolding:
#                     self.diiHolding = "⬆" + str(round(lastHolding - secondLastHolding, 3)) + "%"
#                 else:
#                     self.diiHolding = "⬇" + str(round(lastHolding - secondLastHolding, 3)) + "%"
#         return [self.fiiHolding, self.diiHolding]

#     def fetchStockAnalysisData(self, stock):
#         options = webdriver.ChromeOptions()
#         options.add_experimental_option("detach", True)
#         if not applicationConfig.openBrowser:
#             options.add_argument('headless')
#         driver = webdriver.Chrome(options=options)
#         driver.get("https://www.screener.in/login/?")
#         if applicationConfig.fullScreen:
#             driver.fullscreen_window()    

#         # driver.find_element("name", 'username').send_keys(applicationConfig.username)
#         # driver.find_element("name", 'password').send_keys(applicationConfig.password)

#         # button = driver.find_element(By.XPATH, "//button[@class='button-primary']")
#         # driver.execute_script("arguments[0].click();", button)

#         driver.get("https://www.screener.in/company/" + stock)
#         return self.getShareHoldingPattern(driver)



    
#     def calculate_rsi(self, closing_prices, period=14):
#         """
#         Calculate the Relative Strength Index (RSI).
#         :param closing_prices: List of closing prices.
#         :param period: Lookback period for RSI calculation.
#         """
#         deltas = np.diff(closing_prices)
#         gains = np.where(deltas > 0, deltas, 0)
#         losses = np.where(deltas < 0, -deltas, 0)
        
#         avg_gain = np.mean(gains[:period])
#         avg_loss = np.mean(losses[:period])
        
#         if avg_loss == 0:
#             self.rsi = 100
#         else:
#             rs = avg_gain / avg_loss
#             self.rsi = 100 - (100 / (1 + rs))
        
#         return self.rsi
    
#     def calculate_eps(self, net_income, total_shares):
#         """
#         Calculate Earnings Per Share (EPS).
#         :param net_income: Net income of the company.
#         :param total_shares: Total outstanding shares.
#         """
#         self.eps = net_income / total_shares if total_shares else "Invalid Data"
#         return self.eps

#     def calculate_support_resistance(self, price_data):
#         """
#         Calculate support and resistance levels based on recent high and low prices.
#         :param price_data: List of historical prices.
#         """
#         self.support_resistance = {
#             "support": min(price_data[-10:]),
#             "resistance": max(price_data[-10:])
#         }
#         return self.support_resistance

#     def calculate_pe_ratio(self, market_price, eps):
#         """
#         Calculate Price-to-Earnings (P/E) Ratio.
#         :param market_price: Current market price of the stock.
#         :param eps: Earnings per share.
#         """
#         self.pe_ratio = market_price / eps if eps > 0 else "N/A"
#         return self.pe_ratio
    
#     def calculate_fibonacci_levels(self, high, low):
#         """
#         Calculate Fibonacci retracement levels.
#         :param high: Highest price.
#         :param low: Lowest price.
#         """
#         diff = high - low
#         levels = {
#             "23.6%": high - (diff * 0.236),
#             "38.2%": high - (diff * 0.382),
#             "50.0%": high - (diff * 0.500),
#             "61.8%": high - (diff * 0.618),
#             "78.6%": high - (diff * 0.786)
#         }
#         self.fibonacci = levels
#         return self.fibonacci
    
#     def getYears(self, displayYears):
#         years = []
#         for i in range(len(displayYears)):
#             year = displayYears[i].text
#             years.append(year)
#         return years
    

# # Example Usage
# if __name__ == "__main__":
#     stock_analyzer = AnalyseStock("AAPL")
#     print(stock_analyzer.calculate_rsi([150, 152, 148, 147, 149, 151, 153, 155, 157, 156, 154]))
#     print(stock_analyzer.calculate_fii_holding({"AAPL": "12.5%"}))
#     print(stock_analyzer.calculate_eps(5000000, 1000000))
#     print(stock_analyzer.calculate_support_resistance([140, 142, 144, 145, 146, 148, 149, 150, 151, 153]))
#     print(stock_analyzer.calculate_pe_ratio(150, 5))
#     print(stock_analyzer.calculate_fibonacci_levels(160, 140))


import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import applicationConfig

class AnalyseStock:
    def __init__(self, stock):
        self.stock = stock.upper()
        self.fiiHolding = None
        self.diiHolding = None
        self.rsi = None
        self.eps = None
        self.supportResistance = None
        self.peRatio = None
        self.fibonacci = None

    def getShareHoldingPattern(self, driver):
        try:
            # Find the table rows
            rows = driver.find_elements(By.XPATH, "//section[@id='shareholding']//table[1]/tbody/tr")
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if not cols: continue
                
                entityName = cols[0].text
                # We need at least 3 columns to compare last two quarters
                if len(cols) < 3: continue 

                def parsePercent(val):
                    try:
                        return float(val.replace("%", "").strip())
                    except ValueError:
                        return 0.0

                lastVal = parsePercent(cols[-1].text)
                prevVal = parsePercent(cols[-2].text)
                diff = round(lastVal - prevVal, 3)
                trend = "⬆" if diff > 0 else "⬇"
                formattedVal = f"{trend}{abs(diff)}%"

                if "FIIs" in entityName:
                    self.fiiHolding = formattedVal
                elif "DIIs" in entityName:
                    self.diiHolding = formattedVal
            
            return [self.fiiHolding, self.diiHolding]
        except Exception as e:
            print(f"Error scraping holdings: {e}")
            return [None, None]

    def fetchStockAnalysisData(self, stock):
        options = webdriver.ChromeOptions()
        if not applicationConfig.openBrowser:
            options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=options)
        try:
            # Screener.in URL structure
            driver.get(f"https://www.screener.in/company/{stock}/consolidated/")
            raw_quarterly_df = self.get_full_financials(driver)
            health_report = self.analyze_quarterly_results(raw_quarterly_df)
            print("-" * 30)
            print(f"📊 QUARTERLY HEALTH CHECK: {stock}")
            print("-" * 30)
            for metric, value in health_report.items():
                print(f"{metric}: {value}")
            print("-" * 30)
            holdings = self.getShareHoldingPattern(driver)
            return holdings
        finally:
            driver.quit() # Always close the driver

    def calculateRsi(self, prices, period=14):
        if len(prices) < period: return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avgGain = np.mean(gains[:period])
        avgLoss = np.mean(losses[:period])
        
        if avgLoss == 0:
            self.rsi = 100
        else:
            rs = avgGain / avgLoss
            self.rsi = 100 - (100 / (1 + rs))
        return round(self.rsi, 2)

    def calculateFibonacciLevels(self, high, low):
        diff = high - low
        self.fibonacci = {
            "23.6%": round(high - (diff * 0.236), 2),
            "38.2%": round(high - (diff * 0.382), 2),
            "50.0%": round(high - (diff * 0.500), 2),
            "61.8%": round(high - (diff * 0.618), 2)
        }
        return self.fibonacci

    def calculateSupportResistance(self, prices):
        # Using a 10-period window as per your original logic
        recent_data = prices[-10:]
        self.supportResistance = {
            "support": min(recent_data),
            "resistance": max(recent_data)
        }
        return self.supportResistance
    
    def get_full_financials(self, driver):
        # This grabs ALL tables on the page as DataFrames
        tables = pd.read_html(driver.page_source)
        
        # Usually:
        # tables[0] = Peer Comparison
        # tables[1] = Quarterly Results
        # tables[2] = Profit & Loss
        # tables[3] = Balance Sheet
        
        quarterly_results = tables[1]
        return quarterly_results
    
    def analyze_quarterly_results(self, quarterly_df):
        try:
            quarterly_df = quarterly_df.set_index(quarterly_df.columns[0]).T           
            quarterly_df.columns = quarterly_df.columns.str.replace(r'[\xa0+]', '', regex=True).str.strip()
            print(f"DEBUG: Cleaned Columns -> {quarterly_df.columns.tolist()}") 
            for col in quarterly_df.columns:
                series = quarterly_df[col].astype(str).str.replace(',', '').str.replace('%', '')
                quarterly_df[col] = pd.to_numeric(series, errors='coerce')
            target_col = None
            possible_names = ['Sales', 'Revenue', 'Interest Earned', 'Total Income']
            for name in possible_names:
                if name in quarterly_df.columns:
                    target_col = name
                    break
            if not target_col:
                return {"Error": f"Could not find Top Line. Available: {list(quarterly_df.columns)}"}
            # 4. PERFORM ANALYSIS (Using the found column)
            recent_data = quarterly_df.tail(5)
            latest_q = recent_data.iloc[-1]
            last_year_q = recent_data.iloc[-5]
            sales_yoy = ((latest_q[target_col] - last_year_q[target_col]) / last_year_q[target_col]) * 100
            np_yoy = ((latest_q['Net Profit'] - last_year_q['Net Profit']) / last_year_q['Net Profit']) * 100
            # Handle OPM (It might be missing for Banks)
            opm = f"{latest_q.get('OPM', 'N/A')}%"

            return {
                "Metric Used": target_col,
                "Latest Quarter": recent_data.index[-1],
                "Top-Line Growth (YoY)": f"{sales_yoy:.2f}%",
                "Net Profit Growth (YoY)": f"{np_yoy:.2f}%",
                "Margins": opm
            }

        except Exception as e:
            return {"Error": f"Analysis Failed: {str(e)}"}

# Example Usage
if __name__ == "__main__":
    # Note: Ensure applicationConfig has openBrowser = True/False
    analyzer = AnalyseStock("RELIANCE") 
    
    # Example Technicals
    prices = [2400, 2420, 2380, 2390, 2410, 2450, 2460, 2480, 2500, 2510, 2530, 2550, 2580, 2600, 2620]
    print(f"RSI: {analyzer.calculateRsi(prices)}")
    print(f"Fibonacci: {analyzer.calculateFibonacciLevels(2620, 2400)}")
    print(f"S/R Levels: {analyzer.calculateSupportResistance(prices)}")