from scrapping import *
import matplotlib.pyplot as plt
import numpy as np

def def_value(): 
    return 0

def prepareSectoralandIndustrialPercentageMap(finalHoldings, liveQuotesMapScrapping):
    sectoralPercentageMap = defaultdict(def_value) 
    industrialPercentageMap = defaultdict(def_value) 
    for equity, holding in finalHoldings.items():
        if equity in liveQuotesMapScrapping:
            sector = liveQuotesMapScrapping[equity]['Sector']
            sectoralPercentageMap[sector] += holding[0] * holding[1]
            industry = liveQuotesMapScrapping[equity]['Industry']
            industrialPercentageMap[industry] = holding[0] * holding[1]
    y = np.array([])
    mylabels = []
    for a, b in industrialPercentageMap.items():
        y = np.append(y, b)
        mylabels.append(a)
    plt.pie(y, labels = mylabels)
    # plt.legend()
    plt.show()
    return sectoralPercentageMap, industrialPercentageMap