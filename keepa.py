from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from lxml import etree
import time
import datetime

driver = webdriver.Chrome()
option = webdriver.ChromeOptions()
option.add_argument("--user-data-dir="+
r"C:/Users/ASUS/AppData/Local/Google/Chrome/User Data/")
driver = webdriver.Chrome(chrome_options=option)

'''
driver.get("https://www.amazon.com/Echo-Dot/dp/B07FZ8S74R/ref=zg_bs_electronics_home_2")
#locator = (By.XPATH, "//div[@id='keepaContainer']/iframe")
#WebDriverWait(driver, 20, 1).until(EC.presence_of_element_located(locator))
page = etree.HTML(driver.page_source)
iframe_src = page.xpath("//div[@id='keepaContainer']/iframe/@src")[0]
#print(iframe_src)
driver.get(iframe_src)
locator = (By.XPATH, "//div[@class='tickLabel']")
WebDriverWait(driver, 20, 1).until(EC.presence_of_element_located(locator))

#element = driver.find_element_by_xpath("//div[@id='priceHistory']")
#ActionChains(driver).move_to_element(element)
element = driver.find_element_by_xpath("//div[contains(@class, 'graph')]//div[contains(@class, 'xAxis')]/div[@class='tickLabel'][1]")
#element = driver.find_element_by_xpath("//div[@id='graph']/canvas[@class='flot-base']")
width = element.size['width']
ActionChains(driver).move_to_element(element).move_by_offset(-(width//2+3), 0).perform()
#time.sleep(6)

page = etree.HTML(driver.page_source)
start_data = page.xpath("//div[@class='flotToolTipsPlaceholder']/div[@id='flotTipDate']/text()")
print(start_data)

driver.close()
'''

#"//table[@class='legendTable']/tbody/tr[last()]/td[2]/table/tbody/tr[last()]/td[2]/text()"
def keepa(url):
	driver.get(url)
	time.sleep(5)
	driver.switch_to.frame('keepa')
	element = driver.find_element_by_xpath("//table[@class='legendTable']/tbody/tr[last()]/td[2]/table/tbody/tr[last()]/td[2]")
	days = int(element.text.split("(")[1].split("天")[0].strip())
	release_data = (datetime.datetime.now() + datetime.timedelta(days=-days)).strftime("%Y-%m-%d")
	print(release_data)

if __name__ == '__main__':
	url = "https://www.amazon.com/Carhartt-Workwear-Pocket-Short-Sleeve-T-Shirt/dp/B0007XB2Y8/ref=zg_bs_fashion_home_1"
	keepa(url)