from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from lxml import etree
import pymysql
import time
import sys


def crawPageSource(url):
	driver = webdriver.Chrome()
	driver.get(url)
	with open("D:/c.txt", "w", encoding="utf-8") as f:
		f.write(driver.page_source)
	driver.close()

def fulledIsNULL():
	connection = pymysql.connect(
		host = "localhost",
		user = "root",
		password = "root1234",
		db = "amazon",
		charset = "utf8mb4"
	)
	with connection.cursor() as cursor:
		sql = "select asin, address from product where fulled is NULL"
		cursor.execute(sql)
		result = cursor.fetchall()
		print(result)

def setChrome():
	driver = webdriver.Chrome()
	driver.get("https://www.amazon.com/")
	element = driver.find_element_by_xpath("//div[@id='nav-global-location-slot']/span/a")
	ActionChains(driver).click(element).perform()
	time.sleep(4)
	input_element = driver.find_element_by_xpath("//input[contains(@class, 'GLUX_Full_Width')]")
	button_element = driver.find_element_by_xpath("//span[@id='GLUXZipUpdate-announce']")
	ActionChains(driver).send_keys_to_element(input_element, "10114").click(button_element).perform()
	time.sleep(5)
	element = driver.find_element_by_xpath("//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']")
	ActionChains(driver).click(element).perform()
	# driver.refresh()
	time.sleep(5)
	driver.get("https://www.amazon.com/TP-Link-wireless-network-Adapter-SoftAP/dp/B008IFXQFU/ref=zg_bs_1266092011_41/132-3182808-8655828")
	time.sleep(10000)

def test():
	# f = sys._getframe().f_code.co_name
	# l = sys._getframe().f_lineno
	# print(f, l)
	log('sssss',sys._getframe().f_code.co_name,sys._getframe().f_lineno)

def log(e, f = sys._getframe().f_code.co_name, l = sys._getframe().f_lineno):
	print(e, f, l)

if __name__ == '__main__':
	# crawPageSource('https://www.amazon.com/2020-American-Certificate-Authenticity-Uncirculated/dp/B087D7NTG2/ref=zg_bs_coins_2?ie=UTF8&language=en_US&psc=1&refRID=KQHB391G1KJF3MW13Q7Q')
	# setChrome()
# 'https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_nav_e_2_1266092011'
# 'https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_pg_2?_encoding=UTF8&pg=2'
	# with open("D:/a.txt", "r", encoding="utf-8") as f:
	# 	p = f.read()
	# page_source = etree.HTML(p)
	# r = page_source.xpath("//a[@id='1dsfd234']")
	# print(r)

#https://www.amazon.com/Best-Sellers-Computers-Accessories-Streaming-Media-Players/zgbs/pc/13447451/ref=zg_bs_nav_pc_3_537316


	test()