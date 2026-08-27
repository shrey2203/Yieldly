import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from nseScrap import *

finalHolding = ['M&M', 'RELIANCE', 'INFY', 'TCS']

def getQuote(equity):
    scrappedData = nse_eq(equity)
    return scrappedData

start = time.time()
max_workers = 4
processes = []
with ThreadPoolExecutor(max_workers) as executor:
    print ('max workers - ' + str(max_workers))
    for equity in finalHolding:
        processes.append(executor.submit(getQuote, equity))

for task in as_completed(processes):
    print(task.result()['priceInfo']['open'])


print(f'Time taken: {time.time() - start}')