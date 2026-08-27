from selenium.webdriver.common.by import By

def getShareHoldingPattern(driver):
    def getshareHoldingPatternEntity(shareholdingYears, entityID):
        shareHoldingMap = []
        path = "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr[" + str(entityID) + "]/td"
        shareholdingEntity = driver.find_elements(By.XPATH, path)
        for i in range(len(shareholdingYears)):
            
            holding = shareholdingEntity[i].text
            if i == 0:
                shareHoldingMap.append(holding)
                continue
            shareHoldingMap.append(holding)
        return shareHoldingMap

    def getYears(shareHoldingYears):
        years = []
        for i in range(len(shareHoldingYears)):
            year = shareholdingYears[i].text
            years.append(year)
        return years


    shareHoldingPatternMap = []
    shareholdingYears = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/thead[1]/tr[1]/th")
    totalShareHolders = driver.find_elements(By.XPATH, "//section[@id='shareholding']/div[2]/div[1]/table[1]/tbody[1]/tr")
    for i in range(len(totalShareHolders)):
        shareHoldingPatternEntity = getshareHoldingPatternEntity(shareholdingYears, i + 1)
        shareHoldingPatternMap.append(shareHoldingPatternEntity)
    allYears = getYears(shareholdingYears)

    print (shareHoldingPatternMap)
    return allYears, shareHoldingPatternMap
