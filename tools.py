from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from lxml import etree
import pymysql
import traceback
import time
import sys
import os


def crawPageSource(url):
	driver = webdriver.Chrome()
	driver.get(url)
	# with open("D:/c.txt", "w", encoding="utf-8") as f:
	# 	f.write(driver.page_source)
	# driver.close()
	driver.execute_script("window.scrollBy(0, 1000)")
	time.sleep(10000)

def dbtest():
	connection = pymysql.connect(
		host = "localhost",
		user = "root",
		password = "root1234",
		db = "amazon",
		charset = "utf8mb4"
	)
	with connection.cursor() as cursor:
		# sql = "select link, name from image"
		# cursor.execute(sql)
		# result = cursor.fetchall()
		# for i in result:
		# 	sql = "update product set image='%s' where image='%s'" % (i[0], i[1])
		# 	cursor.execute(sql)
		# connection.commit()
		sql = "select image from product"
		cursor.execute(sql)
		result = cursor.fetchall()
		print(len(result))
		for i in result:
			# weight = i[1]
			# if "ounces" in weight:
			# 	weight = str(round(float(weight.replace("ounces", "").strip())*28.35, 2)) + " 克"
			# if "pounds" in weight:
			# 	weight = str(round(float(weight.replace("pounds", "").strip())*453.59, 2)) + " 克"
			# sql = "update product set weight='%s' where asin='%s'" %(weight, i[0])
			# cursor.execute(sql)
			# connection.commit()
			file_name = os.path.join("image", i[0].split("/")[-1])
			if not os.path.exists(file_name):
				print(i[0])

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
	try:
		int('1.02')
	except Exception as e:
		# print(str(e))
		# print(type(str(e)))
		# print(traceback.format_exc())
		save_log()
		# pass
		# print(traceback.format_exception)
		# exc_type, exc_value, exc_traceback = sys.exc_info()
		# print(exc_traceback.tb_lineno)
		# print(exc_type, exc_value, exc_traceback, sep="\n")
		# error = traceback.format_exception(exc_type, exc_value, exc_traceback)
		# print(error[1])
		# print(error[2])
		# print(len(error))
	# log('sssss',sys._getframe().f_code.co_name,sys._getframe().f_lineno)
	try:
		1/0
	except Exception as e:
		save_log()

def log():
	# try:
	# 	for i in range(10):
	# 		print(i)
	# 		if i == 5:
	# 			raise Exception("yyy")
	# except Exception as e:
	# 	print(i, e)
	# try:
	# 	exc_type, exc_value, exc_traceback = sys.exc_info()
	# 	error = traceback.format_exception(exc_type, exc_value, exc_traceback)
	# 	print(error[1], error[2])
	# except Exception as e:
	# pass
	exc_type, exc_value, exc_traceback = sys.exc_info()

	print(type(exc_traceback.tb_frame.f_code.co_name))

def save_log():
	e_type, e_value, e_traceback = sys.exc_info()
	error_type = e_type.__name__
	error_message = str(e_value).replace("'", r"\'")
	file_name = e_traceback.tb_frame.f_code.co_filename
	function_name = e_traceback.tb_frame.f_code.co_name
	line_number = e_traceback.tb_lineno
	# print(type(line_number))
	print(error_type, error_message, file_name, function_name, line_number, sep="\n")

def writeExcel():

		import xlsxwriter
		 
		 
		# 创建一个新Excel文件并添加一个工作表。
		workbook = xlsxwriter.Workbook('images.xlsx')
		worksheet = workbook.add_worksheet()
		 
		# 加宽第一列使文本更清晰。
		worksheet.set_column('A:A', 30)
		 
		# 插入一张图片。
		worksheet.write('A2', '向单元格插入一张图片：')
		worksheet.insert_image('B2', '1.jpg')
		 
		# 插入一张位偏移图片。
		worksheet.write('A12', '插入一张位偏移图片：')
		worksheet.insert_image('B12', '1.jpg', {'x_offset': 15, 'y_offset': 10})
		 
		# 插入一张缩放了的图片。
		worksheet.write('A23', '插入一张缩放了的图片：')
		worksheet.insert_image('B23', '1.jpg', {'x_scale': 0.5, 'y_scale': 0.5})
		 
		workbook.close()
# sys.setrecursionlimit(5)
def demo(n=0, m=2):
	if n == m:
		return
	for i in range(3):
		print(n, i)
		demo(n=n+1)

if __name__ == '__main__':
	crawPageSource('https://www.amazon.com/2020-American-Certificate-Authenticity-Uncirculated/dp/B087D7NTG2/ref=zg_bs_coins_2?ie=UTF8&language=en_US&psc=1&refRID=KQHB391G1KJF3MW13Q7Q')
	# setChrome()
# 'https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_nav_e_2_1266092011'
# 'https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_pg_2?_encoding=UTF8&pg=2'
	# with open("D:/a.txt", "r", encoding="utf-8") as f:
	# 	p = f.read()
	# page_source = etree.HTML(p)
	# r = page_source.xpath("//a[@id='1dsfd234']")
	# print(r)

#https://www.amazon.com/Best-Sellers-Computers-Accessories-Streaming-Media-Players/zgbs/pc/13447451/ref=zg_bs_nav_pc_3_537316
	# writeExcel()
	# demo()
	# test()
	# print(sys._getframe().f_lineno)
	# print(type(sys._getframe().f_lineno))
	# log()

'''
Amazon Devices & Accessories
Amazon Launchpad
Amazon Pantry
Appliances
Apps & Games
Arts, Crafts & Sewing
Audible Books & Originals
Automotive
Baby
Beauty & Personal Care
Books
CDs & Vinyl
Camera & Photo
Cell Phones & Accessories
Clothing, Shoes & Jewelry
Collectible Currencies
Computers & Accessories
Digital Music
Electronics
Entertainment Collectibles
Gift Cards
Grocery & Gourmet Food
Handmade Products
Health & Household
Home & Kitchen
Industrial & Scientific
Kindle Store
Kitchen & Dining
Magazine Subscriptions
Movies & TV
Musical Instruments
Office Products
Patio, Lawn & Garden
Pet Supplies
Software
Sports & Outdoors
Sports Collectibles
Tools & Home Improvement
Toys & Games
Video Games
'''