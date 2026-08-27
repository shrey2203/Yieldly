import sys
import os
from collections import defaultdict

appserver_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(appserver_path, "API"))

from nseScrap import *
from fetchMarketData import fetchMarketData, getMarketData, addEquities
import applicationConfig

def def_value():
    return defaultdict()


def fetchHeatmap(heatmap):
    heatmapData = defaultdict(def_value)
    heatmap = heatmap.upper()
    heatmapBroadIndices = ["BROAD MARKET INDICES", "SECTORAL INDICES"]
    if heatmap not in heatmapBroadIndices:
        marketData = nseGetStocksInIndex(heatmap)
        for item in marketData['data']:
            if item['symbol'] == heatmap: continue
            heatmapData[item['symbol']] = [item['lastPrice'], item['pChange'], item['change']]
    else:
        allIndicesData = index_info_all()
        for indexData in allIndicesData["data"]:
            if indexData["key"].upper() == heatmap or (heatmap == "BROAD MARKET INDICES" and indexData["key"].upper() == "INDICES ELIGIBLE IN DERIVATIVES"):
                heatmapData[indexData["indexSymbol"]] = [indexData["last"], indexData["percentChange"], indexData["variation"]]
    return heatmapData

