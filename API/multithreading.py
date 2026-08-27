import requests
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

def multiThreadingEquity(finalHoldings):
    start = time.time()
    max_workers = 4
    processes = []
    with ThreadPoolExecutor(max_workers) as executor:
        print ('Workers assigned for multithreading are: ' + str(max_workers))
        for equity in finalHoldings:
            processes.append(executor.submit(getQuote, equity))

    for task in as_completed(processes):
        result = task.result()
        equitiesData[result['info']['symbol']]['lastPrice'] = result['priceInfo']['lastPrice']
    return equitiesData

# print(f'Time taken: {time.time() - start}')



