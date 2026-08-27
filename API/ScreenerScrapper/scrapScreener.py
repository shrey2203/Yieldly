
from selenium import webdriver
from selenium.webdriver.common.by import By
import addData
import os 
import sys
sys.path.append('/Users/bhavya/Downloads/API')
from addToSheet import *
import applicationConfig

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
if not applicationConfig.openBrowser:
    options.add_argument('headless')
driver = webdriver.Chrome(options=options)
driver.get("https://www.screener.in/login/?")
if applicationConfig.fullScreen:
    driver.fullscreen_window()    

driver.find_element("name", 'username').send_keys(applicationConfig.username)
driver.find_element("name", 'password').send_keys(applicationConfig.password)

button = driver.find_element(By.XPATH, "//button[@class='button-primary']")
driver.execute_script("arguments[0].click();", button)

scrip = ["HAL"]


for i in range(len(scrip)):
    driver.get("https://www.screener.in/company/" + scrip[i])
    file_path = "/Users/bhavya/Downloads/ScreenerOutput/" + scrip[i] + ".xlsx"
    if not os.path.exists(file_path): 
        with open(file_path, 'w') as file: 
            excel_file = "/Users/bhavya/Downloads/ScreenerOutput/" + scrip[i] + ".xlsx"
    else: 
        print(f"The file '{file_path}' already exists.") 
        excel_file = "/Users/bhavya/Downloads/ScreenerOutput/" + scrip[i] + ".xlsx"

if applicationConfig.shareHoldingPattern:
    allYears, shareHoldingPatternMap = addData.getShareHoldingPattern(driver)
    addToSheet(excel_file, [allYears] + shareHoldingPatternMap, "Share Holding Pattern")

if applicationConfig.getQuarterlyResults:
    allYears, quarterlyResultsList = addData.getQuarterlyResults(driver)
    addToSheet(excel_file, [allYears] + quarterlyResultsList, "Quarterly Results")

if applicationConfig.getQuickInsights:
    output = addData.getQuickInsights(driver)
    addToSheet(excel_file, output, "Quick Insights")

