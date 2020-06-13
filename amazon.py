from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from lxml import etree
import pymysql
import requests
import datetime
import time


# 数据库连接和参数
connection = pymysql.connect(
	host = "localhost",
	user = "root",
	password = "root1234",
	db = "amazon",
	charset = "utf8mb4"
)
# 图片保存文件夹的绝对路径
imageFolder = "C:/Users/ASUS/Desktop/Amazon/image/"
# 启动个人配置的Chrome浏览器
option = webdriver.ChromeOptions()
option.add_argument("--user-data-dir="+
r"C:/Users/ASUS/AppData/Local/Google/Chrome/User Data/")
driver = webdriver.Chrome(chrome_options=option)


def setChrome():
	'''
	因为浏览器打开亚马逊网站的默认收货地址为中国，影响sellers的判断
	所以此方法用于将收货地址改为10114邮编的纽约
	(由于可以启用个人配置的浏览器，此方法弃用)
	'''
	driver.get("https://www.amazon.com/")
	time.sleep(2)
	element = driver.find_element_by_xpath("//div[@id='nav-global-location-slot']/span/a")
	ActionChains(driver).click(element).perform()
	time.sleep(2)
	input_element = driver.find_element_by_xpath("//input[contains(@class, 'GLUX_Full_Width')]")
	button_element = driver.find_element_by_xpath("//span[@id='GLUXZipUpdate-announce']")
	ActionChains(driver).send_keys_to_element(input_element, "10114").click(button_element).perform()
	time.sleep(2)
	element = driver.find_element_by_xpath("//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']")
	ActionChains(driver).click(element).perform()
	time.sleep(4)

def findRank(page_source):
	'''
	在网页源代码中查找商品的排名信息
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Best Sellers Rank":
				ranks = tr.xpath("./td//text()")
				break
		result = []
		for i in ranks:
			if i.strip() and "See Top 100" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		return ranks
	except Exception as e:
		print("findRank1", e)
	try:
		ranks = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul/li[@id='SalesRank']//text()")
		result = []
		for i in ranks:
			if i.strip() and "Amazon Best Sellers Rank" not in i and "See Top 100" not in i and "{" not in i and "}" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		return ranks
	except Exception as e:
		print("findRank2", e)
	try:
		ranks = page_source.xpath("//div[@id='detail-bullets']/table//div[@class='content']/ul/li[@id='SalesRank']//text()")
		result = []
		for i in ranks:
			if i.strip() and "Amazon Best Sellers Rank" not in i and "See Top 100" not in i and "{" not in i and "}" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		return ranks
	except Exception as e:
		print("findRank3", e)
	return []

def findCatalog(page_source):
	'''
	在网页源代码中查找商品所属类别情况
	'''
	try:
		catalog = page_source.xpath("//div[@id='wayfinding-breadcrumbs_feature_div']/ul/li/span/a/text()")
		return [i.strip() for i in catalog]
	except Exception as e:
		print("findCatalog1", e)
	return []

def findBrand(page_source):
	'''
	在网页源代码中查找商品的品牌名称
	'''
	try:
		brand = page_source.xpath("//a[@id='bylineInfo']/text()")[0]
		return brand
	except Exception as e:
		print("findBrand1", e)
	return ""

def findSellers(page_source):
	'''
	在网页源代码中查找并判断商品的销售方式
	'''
	try:
		info = page_source.xpath("//div[@id='merchant-info']/text()")
		sellers = "".join([i.strip() for i in info])
		if "Ships from and sold by Amazon" in sellers:
			return "AMZ"
		if "Ships from and sold by" in sellers:
			return "FBM"
		if "Sold by" in sellers:
			return "FBA"
		return sellers
	except Exception as e:
		print("findSellers1", e)
	return ""

def findSize(page_source):
	'''
	在网页源代码中查找商品尺寸大小
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions" or th.strip() == "Package Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		print("findSize1", e)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions" or th.strip() == "Package Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		print("findSize2", e)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		print("findSize3", e)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Size":
				size = tr.xpath("./td[2]/p/text()")[0]
				return size.strip()
	except Exception as e:
		print("findSize4", e)
	return ""

def findWeight(page_source):
	'''
	在网页源代码中查找商品重量信息
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		print("findWeight1", e)
	try:
		uls = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul")
		for ul in uls:
			th = ul.xpath("./li/b/text()")[0]
			if th.strip() == "Shipping Weight:":
				weight = ul.xpath("./li/text()")[0]
				weight = weight.replace("(", "")
				return weight.strip()
	except Exception as e:
		print("findWeight2", e)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		print("findWeight3", e)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		print("findWeight4", e)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Weight":
				weight = tr.xpath("./td[2]/p/text()")[0]
				return weight.strip()
	except Exception as e:
		print("findWeight5", e)
	try:
		lis = page_source.xpath("//div[@id='detail-bullets']/table//div[@class='content']/ul/li")
		for li in lis:
			b = li.xpath("./b/text()")[0]
			if "Shipping Weight" in b.strip():
				weight = li.xpath("./text()")[0].replace("(", "")
				return weight.strip()
	except Exception as e:
		print("findWeight6", e)
	return ""

def findReleaseData(page_source):
	'''
	在网页源代码中查找商品的上架日期
	'''
	monthDict = {
		"January" : "1",
		"February" : "2",
		"March" : "3",
		"April" : "4",
		"May" : "5",
		"June" : "6",
		"July" : "7",
		"August" : "8",
		"September" : "9",
		"October" : "10",
		"November" : "11",
		"December" : "12"
	}
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Date First Available":
				release_data = tr.xpath("./td//text()")[0]
				month, day, year = release_data.strip().replace(",", " ").split()
				return year+"-"+monthDict[month]+"-"+day
	except Exception as e:
		print("findReleaseData1", e)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Date First Available":
				release_data = tr.xpath("./td//text()")[0]
				month, day, year = release_data.strip().replace(",", " ").split()
				return year+"-"+monthDict[month]+"-"+day
	except Exception as e:
		print("findReleaseData2", e)
	return ""

def getPageSource(url, mod=0):
	'''
	获取指定url链接页面的源代码
	'''
	start_time = time.time()
	driver.get(url)
	try:
		if mod == 0:
			locator = (By.XPATH, "//ul[@id='zg_browseRoot']")
			WebDriverWait(driver, 6, 1).until(EC.presence_of_element_located(locator))
		if mod == 1:
			locator = (By.XPATH, "//div[@id='prodDetails']")
			WebDriverWait(driver, 6, 1).until(EC.presence_of_element_located(locator))
	except Exception as e:
		print("getPageSource1", e)
	try:
		element = driver.find_element_by_xpath("//a[contains(text(), 'Try different image')]")
		ActionChains(driver).click(element).perform()
		return getPageSource(url, mod)
	except Exception as e:
		pass
	end_time = time.time()
	with open("time.txt", "a") as f:
		f.write(str(end_time-start_time)+"\n")
	# time.sleep(1)
	page_source = driver.page_source
	page_source = etree.HTML(page_source)
	return page_source

def fullProductInfo(page_source, asin):
	'''
	首先从页面源代码中查找商品的类别目录、类目层级、品牌名称、销售方式、尺寸大小、重量、上架日期和排名
	然后根据商品的asin将处排名外的信息保存到product表中，排名信息保存到ranking表中
	'''
	catalog = findCatalog(page_source)
	level = len(catalog)
	print(level)
	catalog = ' > '.join(catalog)
	print(catalog)
	brand = findBrand(page_source)
	print(brand)
	sellers = findSellers(page_source)
	print(sellers)
	size = findSize(page_source)
	print(size)
	weight = findWeight(page_source)
	print(weight)
	release_data = findReleaseData(page_source)
	if release_data:
		release_data = "'%s'" % release_data
	else:
		release_data = "NULL"
	print(release_data)
	ranks = findRank(page_source)
	print(ranks)
	if level and catalog and brand and sellers and size and weight and release_data:
		fulled = 1
	else:
		fulled = 0
	try:
		with connection.cursor() as cursor:
			sql = '''update product set level=%d,catalog='%s',brand='%s',
			sellers='%s',size='%s',weight='%s',release_data=%s,fulled=%d,
			update_time=now() where asin='%s' ''' % (level, catalog, brand,
			sellers, size, weight, release_data, fulled, asin)
			cursor.execute(sql)
			for rank in ranks:
				sql = '''insert into ranking(asin, rank_name, rank_number,
				add_time)values('%s','%s',%d,now())''' % (asin, rank[1], int(rank[0]))
				cursor.execute(sql)
	except Exception as e:
		print('fullProductInfo1', e)
	connection.commit()

def crwalList(page_source):
	'''
	获取商品列表中商品的链接、asin、图片链接、评论分数、评论人数、价格和标题，
	先根据asin查询product表中是否已存在此商品，再将不存在的商品信息保存到product表
	'''
	product_list = page_source.xpath("//ol[@id='zg-ordered-list']/li")
	for i, p in enumerate(product_list):
		try:
			address = p.xpath(".//span[contains(@class, 'zg-item')]/a[@class='a-link-normal']/@href")[0]
			address = "https://www.amazon.com" + address
			words = address.split("/")
			asin = words[words.index("dp") + 1]
			image = p.xpath(".//img/@src")[0]
		except Exception as e:
			print("crwalList1", e)
		try:
			review_score = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[1]/@title")[0]
			review_score = float(review_score.split("out")[0])
		except Exception as e:
			review_score = 0
			print("crwalList2", e)
		try:
			review_number = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[2]/text()")[0]
			review_number = review_number.replace(",", "")
			review_number = int(review_number)
		except Exception as e:
			review_number = 0
			print("crwalList3", e)
		try:
			price = p.xpath(".//span[@class='p13n-sc-price']/text()")[0]
			price = float(price.strip()[1:])
		except Exception as e:
			price = -1
			print("crwalList4", e)
		try:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/@title")[0]
		except Exception as e:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/text()")[0]
			print("crwalList5", e)
		title = title.replace("'", r"\'")
		try:
			with connection.cursor() as cursor:
				sql = '''select asin from product where asin='%s' ''' % asin
				result = cursor.execute(sql)
				if result != 1:
					sql = '''insert into product (asin, address, title, image,
					review_number, review_score, price, add_time, update_time)
					values('%s', '%s', '%s', '%s', %d, %f, %f, now(), now())''' % (asin,
					address, title,image.split("/")[-1], review_number,
					review_score, price)
					cursor.execute(sql)
					sql = '''insert into image (link, name) values('%s', '%s')''' %(
					image, image.split("/")[-1])
					cursor.execute(sql)
		except Exception as e:
			print("crwalList6", e)
	connection.commit()

def crawCatalog(url):
	'''
	递归的爬取类别目录和目录商品
	'''
	page_source = getPageSource(url)
	crwalList(page_source)
	next_page_url = page_source.xpath("//li[@class='a-last']/a/@href")[0]
	page_source = getPageSource(next_page_url)
	crwalList(page_source)
	ul = page_source.xpath("//ul[@id='zg_browseRoot']")[0]
	while True:
		r = ul.xpath("./ul")
		if r:
			ul = r[0]
		else:
			break
	select_span = ul.xpath("./li/span[@class='zg_selected']")
	if select_span:
		return
	next_catalog_urls = ul.xpath("./li/a/@href")
	for url in next_catalog_urls:
		crawCatalog(url)

def downloadImage():
	'''
	根据商品的图片链接下载保存到指定文件夹
	'''
	try:
		with connection.cursor() as cursor:
			sql = "select name, link from image where download is NULL"
			cursor.execute(sql)
			result = cursor.fetchall()
			for image in result:
				response = requests.get(image[1])
				with open(imageFolder+image[0], "wb") as f:
					for chunk in response.iter_content(chunk_size=128):
						f.write(chunk)
				sql = "update image set download=1 where name='%s'" % image[0]
				cursor.execute(sql)
			connection.commit()
	except Exception as e:
		print("downloadImage1", e)

def keepa():
	'''
	首先查询数据库中商品上架日期为空的商品，再通过keepa谷歌浏览器插件获取商品的上架日期，更新数据库
	'''
	with connection.cursor() as cursor:
		sql = "select address, asin from product where release_data is NULL"
		cursor.execute(sql)
		result = cursor.fetchall()
	try:
		for i in result:
			driver.get(i[0])
			time.sleep(5)
			driver.switch_to.frame('keepa')
			element = driver.find_element_by_xpath("//table[@class='legendTable']/tbody/tr[last()]/td[2]/table/tbody/tr[last()]/td[2]")
			days = int(element.text.split("(")[1].split("天")[0].strip())
			release_data = (datetime.datetime.now() + datetime.timedelta(days=-days)).strftime("%Y-%m-%d")
			print(i[1], release_data)
			with connection.cursor() as cursor:
				sql = "update product set release_data='%s' where asin='%s'" % (release_data, i[1])
				cursor.execute(sql)
		connection.commit()
	except Exception as e:
		print("keepa1", e)

def work1(urls):
	'''
	根据指定的url列表获取商品信息
	'''
	for url in urls:
		page_source = getPageSource(url)
		crwalList(page_source)

def work2():
	'''
	将product表中fulled字段为NULL的数据信息补充完整
	'''
	try:
		with connection.cursor() as cursor:
			sql = "select asin, address from product where fulled is NULL"
			cursor.execute(sql)
			result = cursor.fetchall()
			for i in result:
				page_source = getPageSource(i[1], mod=1)
				fullProductInfo(page_source, i[0])
	except Exception as e:
		print('work21', e)


if __name__ == '__main__':
	urls = [
	"https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_pg_2?_encoding=UTF8&pg=2"
	]
	url = "https://www.amazon.com/Best-Sellers-Electronics-Audio-Video-Accessories/zgbs/electronics/172532/ref=zg_bs_unv_e_3_10966881_1"
	# work1(urls)
	work2()
	# keepa()
	# crawCatalog(url)