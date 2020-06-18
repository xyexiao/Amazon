from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from lxml import etree
import pymysql
import xlsxwriter
import traceback
import requests
import datetime
import time
import sys
import os


# 数据库连接和参数
def setDB():
	connection = pymysql.connect(
		host = "localhost",
		user = "root",
		password = "root1234",
		db = "amazon",
		charset = "utf8mb4"
	)
	return connection
connection = setDB()
# 图片保存文件夹的名称
imageFolder = "image"
# 线程池最大线程数
max_download_thread = 10
# 启动个人配置的Chrome浏览器
def createDriver():
	option = webdriver.ChromeOptions()
	option.add_argument("--user-data-dir="+
	r"C:/Users/ASUS/AppData/Local/Google/Chrome/User Data/")
	option.add_argument("--ignore-certificate-errors")
	driver = webdriver.Chrome(chrome_options=option)
	return driver
# driver = setChrome()

def save_log(source_from):
	e_type, e_value, e_traceback = sys.exc_info()
	error_type = e_type.__name__
	error_message = str(e_value).replace("'", r"\'")
	file_name = e_traceback.tb_frame.f_code.co_filename.replace("\\", r"\\")
	function_name = e_traceback.tb_frame.f_code.co_name
	line_number = e_traceback.tb_lineno
	sql = '''insert into error_log (source_from, error_type, error_message, file_name, function_name,
	line_number, add_time) values ('%s','%s', '%s', '%s', '%s', %d, now())''' % (source_from, 
	error_type, error_message, file_name,function_name, line_number)
	with connection.cursor() as cursor:
		cursor.execute(sql)
	connection.commit()

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

def findRank(page_source, asin):
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
		ranks = [[i[0].replace(",", ""), i[1]] for i in ranks]
		return ranks
	except Exception as e:
		save_log(asin)
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
		save_log(asin)
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
		save_log(asin)
	return []

def findCatalog(page_source, asin):
	'''
	在网页源代码中查找商品所属类别情况(已弃用)
	'''
	try:
		catalog = page_source.xpath("//div[@id='wayfinding-breadcrumbs_feature_div']/ul/li/span/a/text()")
		return [i.strip() for i in catalog]
	except Exception as e:
		save_log(asin)
	return []

def findBrand(page_source, asin):
	'''
	在网页源代码中查找商品的品牌名称
	'''
	try:
		brand = page_source.xpath("//a[@id='bylineInfo']/text()")[0]
		return brand
	except Exception as e:
		save_log(asin)
	return ""

def findSellers(page_source, asin):
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
		save_log(asin)
	return ""

def findSize(page_source, asin):
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
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions" or th.strip() == "Package Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Size":
				size = tr.xpath("./td[2]/p/text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin)
	return ""

def findWeight(page_source, asin):
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
		save_log(asin)
	try:
		uls = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul")
		for ul in uls:
			th = ul.xpath("./li/b/text()")[0]
			if th.strip() == "Shipping Weight:":
				weight = ul.xpath("./li/text()")[0]
				weight = weight.replace("(", "")
				return weight.strip()
	except Exception as e:
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Weight":
				weight = tr.xpath("./td[2]/p/text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin)
	try:
		lis = page_source.xpath("//div[@id='detail-bullets']/table//div[@class='content']/ul/li")
		for li in lis:
			b = li.xpath("./b/text()")[0]
			if "Shipping Weight" in b.strip():
				weight = li.xpath("./text()")[0].replace("(", "")
				return weight.strip()
	except Exception as e:
		save_log(asin)
	return ""

def findReleaseData(page_source, asin):
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
		save_log(asin)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Date First Available":
				release_data = tr.xpath("./td//text()")[0]
				month, day, year = release_data.strip().replace(",", " ").split()
				return year+"-"+monthDict[month]+"-"+day
	except Exception as e:
		save_log(asin)
	return ""

def getPageSource(driver, url, mod=0):
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
		if mod == 2:
			body_height = driver.find_element_by_xpath("//body").size["height"]
			while 1:
				driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
				time.sleep(1)
				new_body_height = driver.find_element_by_xpath("//body").size["height"]
				if new_body_height == body_height:
					break
				body_height = new_body_height
			while 1:
				products = driver.find_elements_by_xpath("//div[@class='c011']")
				print(">>>>>>>",len(products))
				if len(products) == 50:
					break
				time.sleep(2)
	except Exception as e:
		save_log(url)
	try:
		element = driver.find_element_by_xpath("//a[contains(text(), 'Try different image')]")
		ActionChains(driver).click(element).perform()
		return getPageSource(driver, url, mod)
	except Exception as e:
		pass
	page_source = driver.page_source
	page_source = etree.HTML(page_source)
	return page_source

def fullProductInfo(page_source, asin):
	'''
	首先从页面源代码中查找商品的品牌名称、销售方式、尺寸大小、重量、上架日期和排名
	然后根据商品的asin将处排名外的信息保存到product表中，排名信息保存到ranking表中
	'''
	brand = findBrand(page_source, asin)
	brand = brand.replace("'", r"\'")
	print('\n品牌名称:', brand)
	sellers = findSellers(page_source, asin)
	print('销售方式:', sellers)
	size = findSize(page_source, asin)
	size = size.replace("'", r"\'")
	if "inches" in size:
		size = " x ".join([str(round(float(i.strip())*2.54, 2)) for i in size.replace("inches", "").split("x")]) + " 厘米"
	print('尺寸:', size)
	weight = findWeight(page_source, asin)
	weight = weight.replace("'", r"\'")
	if "ounces" in weight:
		weight = str(round(float(weight.replace("ounces", "").strip())*28.35, 2)) + " 克"
	if "pounds" in weight:
		weight = str(round(float(weight.replace("pounds", "").strip())*453.59, 2)) + " 克"
	print('重量:', weight)
	release_data = findReleaseData(page_source, asin)
	if release_data:
		release_data = "'%s'" % release_data
	else:
		release_data = "NULL"
	print('上架日期:', release_data)
	ranks = findRank(page_source, asin)
	print('排名:', ranks)
	if all([brand, sellers, size, weight, release_data]):
		fulled = 1
	else:
		fulled = 0
	try:
		with connection.cursor() as cursor:
			sql = '''update product set brand='%s',sellers='%s',size='%s',
			weight='%s',release_data=%s,fulled=%d,update_time=now() where asin='%s' '''% (
			brand,sellers, size, weight, release_data, fulled, asin)
			cursor.execute(sql)
			for rank in ranks:
				sql = '''insert into ranking(asin, rank_name, rank_number,
				add_time)values('%s','%s',%d,now())''' % (asin, rank[1].replace("'", r"\'"), int(rank[0]))
				cursor.execute(sql)
	except Exception as e:
		save_log(asin)
	connection.commit()

def crwalList(page_source, catalog):
	'''
	获取商品列表中商品的链接、asin、图片链接、评论分数、评论人数、价格和标题，
	先根据asin查询product表中是否已存在此商品，再将不存在的商品信息保存到product表
	'''
	product_list = page_source.xpath("//ol[@id='zg-ordered-list']/li")
	catalog = [i.replace("'", r"\'") for i in catalog]
	for i, p in enumerate(product_list):
		address = p.xpath(".//span[contains(@class, 'zg-item')]/a[@class='a-link-normal']/@href")
		if address:
			address = "https://www.amazon.com" + address[0]
			words = address.split("/")
			asin = words[words.index("dp") + 1]
		else:
			address = asin = ""
		image = p.xpath(".//img/@src")
		image = image[0] if image else ""
		review_score = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[1]/@title")
		review_score = float(review_score[0].split("out")[0]) if review_score else 0
		review_number = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[2]/text()")
		review_number = int(review_number[0].replace(",", "")) if review_number else 0
		price = p.xpath(".//span[@class='p13n-sc-price']/text()")
		multiple = 1 if len(price)>1 else 0
		price = float(price[0].replace(",", "").strip()[1:]) if price else 0
		title = p.xpath(".//div[@class='p13n-sc-truncated']/@title")
		title = title[0] if title else p.xpath(".//div[@class='p13n-sc-truncated']/text()")
		title = title[0] if title else ""
		title = title.replace("'", r"\'")
		try:
			with connection.cursor() as cursor:
				sql = '''select asin from product where asin='%s' ''' % asin
				result = cursor.execute(sql)
				if result != 1:
					sql = '''insert into product (asin, address, title, image,
					review_number, review_score, price, multiple, level, catalog, add_time, update_time)
					values('%s', '%s', '%s', '%s', %d, %f, %f, %d, %d, '%s', now(), now())''' % (asin,
					address, title,image, review_number, review_score, price, multiple, len(catalog), ">".join(catalog))
					cursor.execute(sql)
		except Exception as e:
			save_log(asin)
		connection.commit()

def crawByQuickView(page_source, catalog):
	'''
	获取商品列表中商品的链接、asin、图片链接、评论分数、评论人数、价格、标题、品牌、销售方式、尺寸、重量、上架日期和排名，
	先根据asin查询product表中是否已存在此商品，再将不存在的商品信息保存到product表
	'''
	pass

def crawCatalog(driver, url, max_level=2, now_level=0):
	'''
	递归的爬取类别目录和目录商品
	'''
	if max_level == now_level:
		return
	page_source = getPageSource(driver, url)
	catalog = []
	ul = page_source.xpath("//ul[@id='zg_browseRoot']")[0]
	while True:
		r = ul.xpath("./ul")
		if r:
			catalog.append(" ".join(ul.xpath("./li//text()")).replace("‹", "").strip())
			ul = r[0]
		else:
			break
	select_span = ul.xpath("./li/span[@class='zg_selected']/text()")
	if select_span:
		catalog.append(select_span[0].strip())
	print(catalog)
	crwalList(page_source, catalog)
	next_page_url = page_source.xpath("//li[@class='a-last']/a/@href")[0]
	page_source = getPageSource(driver, next_page_url)
	crwalList(page_source, catalog)
	if select_span:
		return
	next_catalog_urls = ul.xpath("./li/a/@href")
	for url in next_catalog_urls:
		crawCatalog(driver, url, max_level, now_level=now_level+1)

def download(url):
	headers = {
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
		"Accept-encoding": "gzip, deflate, br",
		"Accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
		"Cache-control": "max-age=0",
		"Sec-fetch-dest": "document",
		"Sec-fetch-mode": "navigate",
		"Sec-fetch-site": "none",
		"Sec-fetch-user": "?1",
		"Upgrade-insecure-requests": "1",
		"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36 Edg/83.0.478.45"
	}
	file_name = url.split("/")[-1]
	file_name = os.path.join(imageFolder, file_name)
	if os.path.exists(file_name):
		return
	response = requests.get(url, headers=headers)
	with open(file_name, "wb") as f:
		for chunk in response.iter_content(chunk_size=128):
			f.write(chunk)

def downloadImage():
	'''
	根据商品的图片链接下载保存到指定文件夹
	'''
	if not os.path.exists(imageFolder):
		os.mkdir(imageFolder)
	with connection.cursor() as cursor:
		sql = "select image from product"
		cursor.execute(sql)
		images = cursor.fetchall()
	pool = ThreadPoolExecutor(max_workers=max_download_thread)
	for image in images:
		pool.submit(download, image[0])
	pool.shutdown()

def resultOfHTML():
	bigCatalog = ['Amazon Devices & Accessories', 'Amazon Launchpad', 'Amazon Pantry', 'Appliances',
	'Apps & Games', 'Arts, Crafts & Sewing', 'Audible Books & Originals', 'Automotive', 'Baby',
	'Beauty & Personal Care', 'Books', 'CDs & Vinyl', 'Camera & Photo', 'Cell Phones & Accessories',
	'Clothing, Shoes & Jewelry', 'Collectible Currencies', 'Computers & Accessories', 'Digital Music',
	'Electronics', 'Entertainment Collectibles', 'Gift Cards', 'Grocery & Gourmet Food',
	'Handmade Products', 'Health & Household', 'Home & Kitchen', 'Industrial & Scientific',
	'Kindle Store', 'Kitchen & Dining', 'Magazine Subscriptions', 'Movies & TV', 'Musical Instruments',
	'Office Products', 'Patio, Lawn & Garden', 'Pet Supplies', 'Software', 'Sports & Outdoors',
	'Sports Collectibles', 'Tools & Home Improvement', 'Toys & Games', 'Video Games']
	with connection.cursor() as cursor:
		sql = '''select image,asin,review_number,review_score,price,level,catalog,title,brand,sellers,
		size,weight,address,release_data from product where fulled=1 limit 50'''
		cursor.execute(sql)
		result = cursor.fetchall()
		with open("%s.html"%datetime.datetime.now().strftime("%Y-%m-%d"), "w", encoding="utf-8") as f:
			f.write('''<table border="1" cellpadding="0" cellspacing="0"><thead><td>图片</td><td>编号</td>
			<td>评论人数</td><td>评论分数</td><td>价格</td><td>类目层级</td><td>类别目录</td><td>标题</td>
			<td>品牌名称</td><td>销售方式</td><td>尺寸</td><td>重量</td><td>页面地址</td><td>上架日期</td>
			</thead><tbody>''')
			for p in result:
				f.write('''<tr><td><img src="%s"></td><td>%s</td><td>%d</td><td>%.1f</td><td>%.2f</td><td>%d</td>
				<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href="%s"
				target="_blank">详情</a></td><td>%s</td></tr>''' % p)
			f.write("</tbody></table>")

def resultOfExcel(start_time, sql=""):
	with connection.cursor() as cursor:
		sql = sql if sql else '''select image,asin,review_number,review_score,price,level,catalog,title,
		brand,sellers,size,weight,address,release_data from product where update_time>"%s" ''' % start_time
		cursor.execute(sql)
		result = cursor.fetchall()
		workbook = xlsxwriter.Workbook('%s.xlsx'%datetime.datetime.strptime(start_time,
		"%Y-%m-%d %H:%M").strftime("%Y-%m-%d_%H_%M"))
		worksheet = workbook.add_worksheet()
		worksheet.set_column('A:A', 27.8)
		worksheet.set_column('B:B', 15)
		worksheet.set_column('G:G', 30)
		worksheet.set_column('H:H', 30)
		worksheet.set_column('I:I', 17)
		worksheet.set_column('K:K', 28)
		worksheet.set_column('L:L', 10)
		fromat1 = workbook.add_format({"text_wrap":1})
		fromat2 = workbook.add_format({"num_format":"yyyy-mm-dd"})
		worksheet.write("A1", "图片")
		worksheet.write("B1", "编号")
		worksheet.write("C1", "评论人数")
		worksheet.write("D1", "评论分数")
		worksheet.write("E1", "价格")
		worksheet.write("F1", "类目层级")
		worksheet.write("G1", "类别目录")
		worksheet.write("H1", "标题")
		worksheet.write("I1", "品牌名称")
		worksheet.write("J1", "销售方式")
		worksheet.write("K1", "尺寸")
		worksheet.write("L1", "重量")
		worksheet.write("M1", "页面地址")
		worksheet.write("N1", "上架日期")
		for i, p in enumerate(result):
			worksheet.set_row(i+1, 152)
			worksheet.insert_image('A'+str(i+2), os.path.join(imageFolder, p[0].split("/")[-1]))
			worksheet.write('B'+str(i+2), p[1])
			worksheet.write('C'+str(i+2), p[2])
			worksheet.write('D'+str(i+2), p[3])
			worksheet.write('E'+str(i+2), p[4])
			worksheet.write('F'+str(i+2), p[5])
			worksheet.write('G'+str(i+2), p[6], fromat1)
			worksheet.write('H'+str(i+2), p[7], fromat1)
			worksheet.write('I'+str(i+2), p[8])
			worksheet.write('J'+str(i+2), p[9])
			worksheet.write('K'+str(i+2), p[10])
			worksheet.write('L'+str(i+2), p[11])
			worksheet.write('M'+str(i+2), p[12], fromat1)
			worksheet.write('N'+str(i+2), str(p[13]))
		workbook.close()


def keepa(driver):
	'''
	首先查询数据库中商品上架日期为空的商品，再通过keepa谷歌浏览器插件获取商品的上架日期，更新数据库
	'''
	with connection.cursor() as cursor:
		sql = "select address, asin from product where release_data is NULL"
		cursor.execute(sql)
		result = cursor.fetchall()
		for i in result:
			try:
				driver.get(i[0])
				driver.execute_script("window.scrollBy(0, 700)")
				locator = (By.XPATH, "//div[@id='keepaContainer']")
				WebDriverWait(driver, 15, 1).until(EC.presence_of_element_located(locator))
				driver.switch_to.frame('keepa')
				locator = (By.XPATH, "//div[@id='priceHistory']")
				WebDriverWait(driver, 15, 1).until(EC.presence_of_element_located(locator))
				time.sleep(1)
				element = driver.find_element_by_xpath("//table[@class='legendTable']/tbody/tr[last()]/td[2]/table/tbody/tr[last()]/td[2]")
				days = int(element.text.split("(")[1].split("天")[0].strip())
				release_data = (datetime.datetime.now() + datetime.timedelta(days=-days)).strftime("%Y-%m-%d")
				print(i[1], release_data)
				with connection.cursor() as cursor:
					sql = "update product set release_data='%s' where asin='%s'" % (release_data, i[1])
					cursor.execute(sql)
				connection.commit()
			except Exception as e:
				save_log(i[1])

def work1(driver, urls):
	'''
	根据指定的url列表获取商品信息
	'''
	for url in urls:
		page_source = getPageSource(driver, url)
		crwalList(page_source)

def work2(driver):
	'''
	将product表中fulled字段为NULL的数据信息补充完整
	'''
	try:
		with connection.cursor() as cursor:
			sql = "select asin, address from product where fulled is NULL"
			cursor.execute(sql)
			result = cursor.fetchall()
			for i in result:
				page_source = getPageSource(driver, i[1], mod=1)
				fullProductInfo(page_source, i[0])
	except Exception as e:
		save_log(i[0])


if __name__ == '__main__':
	urls = [
	"https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_pg_2?_encoding=UTF8&pg=2"
	]
	url = "https://www.amazon.com/Best-Sellers-Health-Personal-Care/zgbs/hpc/ref=zg_bs_nav_0"
	driver = createDriver()
	p = getPageSource(driver,url,mod=2)
	with open("D:/k.txt", "w", encoding="utf-8") as f:
		f.write(p)
	# work1(driver, urls)
	# work2(driver)
	# keepa(driver)
	# crawCatalog(driver, url)
	# resultOfHTML()
	# downloadImage()
	# resultOfExcel(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
