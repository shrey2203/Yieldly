import requests
import time

def liveRates():
    start_time = time.time()
    url = "https://latest-stock-price.p.rapidapi.com/any"
    headers = {
	    "X-RapidAPI-Key": "671bea463emshd2e61a404773865p17d0e0jsn4585d68bc4b9",
	    "X-RapidAPI-Host": "latest-stock-price.p.rapidapi.com"
    }
    liveQuotesList = requests.get(url, headers=headers)
    liveQuotesListJson = liveQuotesList.json()
    liveQuotesMap = {}
    for equityDetails in range(len(liveQuotesListJson)):
        liveQuotesMap[liveQuotesListJson[equityDetails]["symbol"]] = liveQuotesListJson[equityDetails]
    end_time = time.time()
    elapsed_time = end_time - start_time
    print ("Time taken to fetch rates is : " + str(elapsed_time))
    print (liveQuotesMap["M&M"])
    return liveQuotesMap

# liveRates()


