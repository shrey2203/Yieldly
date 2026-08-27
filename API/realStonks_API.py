# import requests

# url = "https://realstonks.p.rapidapi.com/ADANIENT"

# headers = {
# 	"X-RapidAPI-Key": "671bea463emshd2e61a404773865p17d0e0jsn4585d68bc4b9",
# 	"X-RapidAPI-Host": "realstonks.p.rapidapi.com"
# }

# response = requests.get(url, headers=headers)

# print(response.json())


# import requests

# url = "https://latest-stock-price.p.rapidapi.com/any"

# headers = {
# 	"X-RapidAPI-Key": "671bea463emshd2e61a404773865p17d0e0jsn4585d68bc4b9",
# 	"X-RapidAPI-Host": "latest-stock-price.p.rapidapi.com"
# }

# response = requests.get(url, headers=headers)

# print(response.json())


# import requests

# url = "https://yahoo-finance15.p.rapidapi.com/api/v1/markets/insider-trades"

# headers = {
# 	"X-RapidAPI-Key": "671bea463emshd2e61a404773865p17d0e0jsn4585d68bc4b9",
# 	"X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com"
# }

# response = requests.get(url, headers=headers)

# print(response.json())




# Stockvider end of day historical data
import requests

url = "https://stockvider.p.rapidapi.com/NASDAQ/AAPL/EOD"

querystring = {"start_date":"2024-01-19","end_date":"2024-01-20"}

headers = {
	"X-RapidAPI-Key": "671bea463emshd2e61a404773865p17d0e0jsn4585d68bc4b9",
	"X-RapidAPI-Host": "stockvider.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())