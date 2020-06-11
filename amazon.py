from selenium import webdriver
from lxml import etree
import pymysql
import requests


connection = pymysql.connect(
	host = "localhost",
	user = "root",
	password = "root1234",
	db = "amazon",
	charset = "utf8mb4"
)
imageFolder = "C:/Users/ASUS/Desktop/Amazon/image/"
driver = webdriver.Chrome()

def findRank(page_source):
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
		pass
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
		pass
	return []

def findCatalog(page_source):
	# 返回的list的长度就level
	try:
		catalog = page_source.xpath("//div[@id='wayfinding-breadcrumbs_feature_div']/ul/li/span/a/text()")
		return [i.strip() for i in catalog]
	except Exception as e:
		pass
	return []

def findBrand(page_source):
	try:
		brand = page_source.xpath("//a[@id='bylineInfo']/text()")[0]
		return brand
	except Exception as e:
		pass
	return ""

def findSellers(page_source):
	# 可以通过判断brand是不是Amazon来判断亚马逊自营
	try:
		info = page_source.xpath("//div[@id='merchant-info']/text()")
		sellers = "".join([i.strip() for i in info])
		if sellers == "Ships from and sold by Amazon.com.":
			return "AMZ"
		if "Ships from and sold by" in sellers:
			return "FBM"
		if "Sold by" in sellers:
			return "FBA"
		return sellers
	except Exception as e:
		pass
	return ""

def findSize(page_source):
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		pass
	return ""

def findWeight(page_source):
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		pass
	try:
		uls = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul")
		for ul in uls:
			th = ul.xpath("./li/b/text()")[0]
			if th.strip() == "Shipping Weight:":
				weight = ul.xpath("./li/text()")[0]
				weight = weight.replace("(", "")
				return weight.strip()
	except Exception as e:
		pass
	return ""

def findReleaseData(page_source):
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
				release_data = release_data.strip().replace(",", " ")
				month, day, year = release_data.split()
				release_data = year+"-"+monthDict[month]+"-"+day
				return release_data
	except Exception as e:
		pass
	return ""

def fullProductInfo(page_source, asin):
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
	try:
		with connection.cursor() as cursor:
			sql = '''update product set level=%d,catalog='%s',brand='%s',
			sellers='%s',size='%s',weight='%s',release_data=%s,fulled=1,
			update_time=now() where asin='%s' ''' % (level, catalog, brand,
			sellers, size, weight, release_data, asin)
			cursor.execute(sql)
			print("update OK")
			for rank in ranks:
				sql = '''insert into ranking(asin, rank_name, rank_number,
				add_time)values('%s','%s',%d,now())''' % (asin, rank[1], int(rank[0]))
				cursor.execute(sql)
			print("rank insert OK")
	except Exception as e:
		print('2', e)
	connection.commit()

def crwalList(page_source):
	product_list = page_source.xpath("//ol[@id='zg-ordered-list']/li")
	for i, p in enumerate(product_list):
		try:
			address = p.xpath(".//span[contains(@class, 'zg-item')]/a[@class='a-link-normal']/@href")[0]
			address = "https://www.amazon.com" + address
			words = address.split("/")
			asin = words[words.index("dp") + 1]
			image = p.xpath(".//img/@src")[0]
		except Exception as e:
			pass
		try:
			review_score = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[1]/@title")[0]
			review_score = float(review_score.split("out")[0])
		except Exception as e:
			review_score = 0
		try:
			review_number = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[2]/text()")[0]
			review_number = review_number.replace(",", "")
			review_number = int(review_number)
		except Exception as e:
			print(e)
			review_number = 0
		try:
			price = p.xpath(".//span[@class='p13n-sc-price']/text()")[0]
			price = float(price.strip()[1:])
		except Exception as e:
			price = -1
		try:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/@title")[0]
		except Exception as e:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/text()")[0]
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
			pass
	connection.commit()

def downloadImage():
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
		pass

def getPageSource(url):
	url = url.split("?")[0] + "?language=en_US"
	driver.get(url)
	page_source = driver.page_source
	page_source = etree.HTML(page_source)
	return page_source

def main(url):
	# page_source = getPageSource(url)
	# crwalList(page_source)
	try:
		with connection.cursor() as cursor:
			sql = "select asin, address from product where fulled is NULL"
			cursor.execute(sql)
			result = cursor.fetchall()
			print(len(result))
			for i in result:
				page_source = getPageSource(i[1])
				fullProductInfo(page_source, i[0])
	except Exception as e:
		print("1", e)


if __name__ == '__main__':
	# with open("D:/a.txt", "r", encoding="utf-8") as f:
	# 	page_source = f.read()
	# page_source = etree.HTML(page_source)
	# result = fullProductInfo(page_source, 'B082YHZLB3')
	# result = findReleaseData(page_source)
	# print(result)
	url = "https://www.amazon.com/Best-Sellers-Electronics-Televisions-Video-Products/zgbs/electronics/1266092011/ref=zg_bs_nav_e_1_e"
	main(url)