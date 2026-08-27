from selenium.webdriver.common.by import By

def getYears(displayYears):
    years = []
    for i in range(len(displayYears)):
        year = displayYears[i].text
        years.append(year)
    return years


def getShareHoldingPattern(driver):
    def getshareHoldingPatternEntity(shareholdingYears, entityID):
        shareHoldingMap = []
        path = "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr[" + str(entityID) + "]/td"
        shareholdingEntity = driver.find_elements(By.XPATH, path)
        for i in range(len(shareholdingYears)):
            holding = shareholdingEntity[i].text
            shareHoldingMap.append(holding)
        return shareHoldingMap
    
    shareHoldingPattern = []
    shareholdingYears = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/thead[1]/tr[1]/th")
    totalShareHolders = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr")
    for i in range(len(totalShareHolders)):
        shareHoldingPatternEntity = getshareHoldingPatternEntity(shareholdingYears, i+1)
        shareHoldingPattern.append(shareHoldingPatternEntity)
    allYears = getYears(shareholdingYears)

    return allYears, shareHoldingPattern


def getQuarterlyResults(driver):
    def getquarterlyResultsElement(quarterlyResultYears, elementID):
        quarterResultElement = []
        div = 2
        if "Profit" not in driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]')[0].text:
            div = 3
        path = "//section[@id='quarters']/div[" + str(div) + "]/table[1]/tbody[1]/tr[" + str(elementID) + "]/td"
        qtrResult = driver.find_elements(By.XPATH, path)
        for i in range(len(quarterlyResultYears)):
            entry = qtrResult[i].text
            quarterResultElement.append(entry)
        return quarterResultElement
    
    quarterlyResultsList = []
    div = 2 # Sometimes when the results are near, div[2] and div[3] change their places.
    if "Profit" not in driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]')[0].text:
        div = 3
    quarterlyResultsYears = driver.find_elements(By.XPATH, "//section[@id='quarters']/div[" + str(div) + "]/table[1]/thead[1]/tr[1]/th")
    quarterlyResults = driver.find_elements(By.XPATH, "//section[@id='quarters']/div[" + str(div) + "]/table[1]/tbody[1]/tr")
    for i in range(len(quarterlyResults)-1):
        quaterlyResultsElement = getquarterlyResultsElement(quarterlyResultsYears, i+1)
        quarterlyResultsList.append(quaterlyResultsElement)
    allYears = getYears(quarterlyResultsYears)
    
    return allYears, quarterlyResultsList

def getQuickInsights(driver):
    data = [['Paramter', 'Value']]
    info_form = driver.find_elements(By.XPATH, "//ul[@id='top-ratios']/li")
    for i in range(1, len(info_form) + 1):
        findKey = "//ul[@id='top-ratios']/li[" + str(i) + "]/span[1]"
        findValue = "//ul[@id='top-ratios']/li[" + str(i) + "]/span[2]"
        key = driver.find_element(By.XPATH, findKey)
        value = driver.find_element(By.XPATH, findValue)
        data.append([key.text, value.text])
    return data

