import asyncio
import time
from nseScrap import *
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading
import applicationConfig
import logging
logging.basicConfig(level=logging.INFO)

def def_value():
    return defaultdict()

equitiesData = defaultdict(def_value)
equitiesLock = threading.Lock()
equities = []
fetchThread = None 
stopFetchEvent = threading.Event()

async def getQuote_async(executor, equity):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, nse_eq, equity)

async def scrappingData_async(allTradedEquities):
    print("[" + time.strftime("%Y-%m-%d %H-%M-%S") + "] " + f"Executing Scrapping Data Service in PID: {os.getpid()}")
    start = time.time()
    max_workers = 8
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with equitiesLock:  # Lock while reading equities list
            allTradedEquitiesLocked = list(allTradedEquities) 
        tasks = [getQuote_async(executor, equity) for equity in allTradedEquitiesLocked]
        results = await asyncio.gather(*tasks)

    for result in results:
        if result and 'info' in result:
            try:
                symbol = result['info']['symbol']
                print ("[" + time.strftime("%Y-%m-%d %H-%M-%S") + "] " + "Fetching latest market data for : " + symbol)
                equitiesData[symbol]['lastPrice'] = result['priceInfo']['lastPrice']
                equitiesData[symbol]['Industry'] = result['industryInfo']['industry']
                equitiesData[symbol]['Sector'] = result['industryInfo']['sector']
                equitiesData[symbol]['Macro'] = result['industryInfo']['macro']
                equitiesData[symbol]['PE'] = result['metadata']['pdSymbolPe']
                equitiesData[symbol]['Indices'] = result['metadata']['pdSectorIndAll']
                equitiesData[symbol]['52w Low'] = result['priceInfo']['weekHighLow']['min']
                equitiesData[symbol]['52w High'] = result['priceInfo']['weekHighLow']['max']
                equitiesData[symbol]['dailyChangePercent'] = result['priceInfo']['pChange']
                equitiesData[symbol]['dailyChange'] = result['priceInfo']['change']
                equitiesData[symbol]['timeStamp'] = time.time()
            except KeyError:
                print(f"Error processing {symbol}")

    print("[" + time.strftime("%Y-%m-%d %H-%M-%S") + "] " + f"Total time taken to fetch one batch of market data is : {time.time() - start:.2f} seconds")


def fetchMarketData(equities):
    global fetchThread, stopFetchEvent
    stopFetchEvent.set() 
    if len(equities) == 0: return #initial condition, returning when the service is being initialised.
    
    if fetchThread and fetchThread.is_alive():
        fetchThread.join(timeout = 2)  
    stopFetchEvent.clear() 
    def run():
        if is_market_open() and running_status():  #fetch latest market data only if trading is open.
                print(f"[{time.strftime('%Y-%m-%d %H-%M-%S')}] Market is open. Fetching data continuously...")
                while not stopFetchEvent.is_set():
                    asyncio.run(scrappingData_async(equities))
                    stopFetchEvent.wait(applicationConfig.equitiesMapRefreshFreq / 1000)
        else:
            print(f"[{time.strftime('%Y-%m-%d %H-%M-%S')}] Market is closed. Fetching data once and stopping.")
            asyncio.run(scrappingData_async(equities)) 

    fetchThread = threading.Thread(target=run, daemon=True)

    fetchThread.start()

def executeMarketDataService():
    try:
        with equitiesLock:
            fetchMarketData([])
        
        while True:  
            time.sleep(10)  
            # Keep the main thread alive
            #The main thread is responsible for handling user inputs (e.g., detecting KeyboardInterrupt when you press Ctrl+C to stop the script).
            #If you increase the sleep time too much (e.g., time.sleep(600) or 10 minutes), the script may appear unresponsive for that period.
            #If you press Ctrl+C, Python may take longer to detect it.

    except KeyboardInterrupt:
        stopFetchEvent.set()
        if fetchThread and fetchThread.is_alive():
            fetchThread.join()


def getMarketData():
    return equitiesData


def addEquities(addEquities):
    global fetchThread, equities
    logging.info(f"Before adding, equities = {equities}")
    update_complete = threading.Event()  
    newAdded = False
    with equitiesLock: 
        for equity in addEquities: 
            if equity not in equities:
                newAdded = True
                equities.append(equity)
                print(f"✅ Added new equity: {equity}")
            else:
                print(f"⚠️ Equity {equity} is already being tracked.")
    logging.info(f"After adding, equities = {equities}")
    if newAdded:
        print("🔄 New equities added. Restarting market data fetcher...")
        stopFetchEvent.set()
        if fetchThread and fetchThread.is_alive():
            fetchThread.join(timeout=2) 
        stopFetchEvent.clear()  # Reset stop event
        
        def fetch_and_notify():
            asyncio.run(scrappingData_async(equities))  
            update_complete.set() 

        thread = threading.Thread(target=fetch_and_notify, daemon=True)
        thread.start()
        update_complete.wait() # Block until data is updated
        fetchMarketData(equities)
        print("✅ Market data successfully updated for new equities.")
