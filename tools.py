from selenium import webdriver
from lxml import etree
import pymysql


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

if __name__ == '__main__':
	# crawPageSource('https://www.amazon.com/2020-American-Certificate-Authenticity-Uncirculated/dp/B087D7NTG2/ref=zg_bs_coins_2?ie=UTF8&language=en_US&psc=1&refRID=KQHB391G1KJF3MW13Q7Q')
	fulledIsNULL()