import prepareFinalHoldings
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from nseScrap import *
from scrapping import *
from collections import defaultdict


def def_value(): 
    return defaultdict()
equitiesData = defaultdict(def_value) 

def getQuote(equity):
    scrappedData = nse_eq(equity)
    return scrappedData

def scrappingData(allTradedEquities):
    start = time.time()
    max_workers = 7
    processes = []
    with ThreadPoolExecutor(max_workers) as executor:
        print ('Workers assigned for multithreading are: ' + str(max_workers))
        for equity in allTradedEquities:
            processes.append(executor.submit(getQuote, equity))

    for task in as_completed(processes):
        result = task.result()
        try:
            equitiesData[result['info']['symbol']]['lastPrice'] = result['priceInfo']['lastPrice']
            equitiesData[result['info']['symbol']]['Industry'] = result['industryInfo']['industry']
            equitiesData[result['info']['symbol']]['Sector'] = result['industryInfo']['sector']
            equitiesData[result['info']['symbol']]['Macro'] = result['industryInfo']['macro']
            equitiesData[result['info']['symbol']]['PE'] = result['metadata']['pdSymbolPe']
            equitiesData[result['info']['symbol']]['Indices'] = result['metadata']['pdSectorIndAll']
            equitiesData[result['info']['symbol']]['52w Low'] = result['priceInfo']['weekHighLow']['min']
            equitiesData[result['info']['symbol']]['52w High'] = result['priceInfo']['weekHighLow']['max']
        except:
            print("Getting Error While Fetching.")
    print ('Total time taken to scrap data is: ' + str(time.time() - start))
    return equitiesData
    
# symbol = "SBIN"
# series = "EQ"
# start_date = "08-06-2021"
# end_date ="14-06-2021"
# print(nse_nifty50())