from flask import Flask, redirect, url_for, render_template, request, send_from_directory
from multiprocessing import Process
from amazon import *
import datetime
import threading
import pymysql
import json



# start_time = ""
# work_statu = ""
# crawl_product_number = 0

app = Flask(__name__)

def get_status():
	with open("status.json", "r") as f:
		status_data = json.load(f)
	return status_data

def set_status(start_time,work_statu,crawl_product_number):
	status_data = {
		"start_time": start_time,
		"work_statu": work_statu,
		"crawl_product_number": crawl_product_number
	}
	with open("status.json", "w") as f:
		json.dump(status_data, f)

set_status("","",0)

def setup1(url, number):
	try:
		driver = createDriver()
		crawCatalog(driver, url=url,max_level=int(number))
		status_data = get_status()
		status_data["work_statu"] = "单个商品爬取"
		status_data["crawl_product_number"] = 0
		set_status(**status_data)
	except Exception as e:
		save_log("web")
	finally:
		driver.quit() 

def setup2():
	try:
		driver = createDriver()
		work2(driver)
		status_data = get_status()
		status_data["work_statu"] = "keepa补充信息"
		status_data["crawl_product_number"] = 0
		set_status(**status_data)
	except Exception as e:
		save_log("web")
	finally:
		driver.quit()

def setup3():
	try:
		driver = createDriver()
		keepa(driver)
		status_data = get_status()
		status_data["work_statu"] = "图片下载"
		status_data["crawl_product_number"] = 0
		set_status(**status_data)
	except Exception as e:
		save_log("web")
	finally:
		driver.quit()

def setup4():
	try:
		downloadImage()
		status_data = get_status()
		status_data["work_statu"] = "Excel生成"
		status_data["crawl_product_number"] = 0
		set_status(**status_data)
	except Exception as e:
		save_log("web")

@app.route('/', methods=["GET", "POST"])
def index():
	if request.method == "POST":
		setup = request.form.get("setup", "0")
		setup = int(setup)
		if setup == 1:
			url = request.form.get("url", "")
			number = request.form.get("number", "")
			status_data = get_status()
			if status_data["start_time"] == "" and url != "" and number != "":
				status_data["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
				status_data["work_statu"] = "商品列表爬取"
				set_status(**status_data)
				threading.Thread(target=setup1, args=(url, number)).start()
		if setup == 2:
			threading.Thread(target=setup2).start()
		if setup == 3:
			threading.Thread(target=setup3).start()
		if setup == 4:
			Process(target=setup4).start()
		if setup == 5:
			try:
				status_data = get_status()
				start_time = status_data["start_time"]
				resultOfExcel(start_time)
				status_data["start_time"] = ""
				status_data["work_statu"] = ""
				status_data["crawl_product_number"] = 0
				set_status(**status_data)
				file_name = '%s.xlsx'%datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d_%H_%M")
				return send_from_directory("", file_name,as_attachment=True)
			except Exception as e:
				save_log("web")
		if setup == 9:
			review_number_min = request.form.get("review_number_min", "")
			review_number_max = request.form.get("review_number_max", "")
			review_number_sql = " review_number>"+review_number_min if review_number_min else ""
			review_number_sql = " review_number<"+review_number_max if review_number_max else review_number_sql
			review_number_sql = " review_number between %s and %s "%(review_number_min,
			review_number_max) if (review_number_min and review_number_max) else review_number_sql
			review_score_min = request.form.get("review_score_min", "")
			review_score_max = request.form.get("review_score_max", "")
			review_score_sql = " review_score>"+review_score_min if review_score_min else ""
			review_score_sql = " review_score<"+review_score_max if review_score_max else review_score_sql
			review_score_sql = " review_score between %s and %s "%(review_score_min,
			review_score_max) if (review_score_min and review_score_max) else review_score_sql
			price_min = request.form.get("price_min", "")
			price_max = request.form.get("price_max", "")
			price_sql = " price>"+price_min if price_min else ""
			price_sql = " price<"+price_max if price_max else price_sql
			price_sql = " price between %s and %s "%(price_min,
			price_max) if (price_min and price_max) else price_sql
			release_data_min = request.form.get("release_data_min", "")
			release_data_max = request.form.get("release_data_max", "")
			release_data_sql = " release_data>'%s'"%release_data_min if release_data_min else ""
			release_data_sql = " release_data<'%s'"%release_data_max if release_data_max else release_data_sql
			release_data_sql = " release_data between '%s' and '%s' "%(release_data_min,
			release_data_max) if (release_data_min and release_data_max) else release_data_sql
			sellers = request.form.getlist("sellers")
			sellers = ["'%s'"%i for i in sellers]
			sellers_sql = " sellers in ("+",".join(sellers)+")" if len(sellers)>1 else ""
			sellers_sql = " sellers=%s"%sellers[0] if len(sellers)==1 else sellers_sql
			key_word = request.form.get("key_word", "")
			key_word_sql = " (catalog like '%%%s%%' or title like '%%%s%%' or brand like '%%%s%%')" % (
			key_word, key_word, key_word) if key_word else ""
			# print(
			# 	"\nreview_number_min:",review_number_min,
			# 	"\nreview_number_max:",review_number_max,
			# 	"\nreview_score_min:",review_score_min,
			# 	"\nreview_score_max:",review_score_max,
			# 	"\nprice_min:",price_min,
			# 	"\nprice_max:",price_max,
			# 	"\nrelease_data_min:",release_data_min,
			# 	"\nrelease_data_max:",release_data_max,
			# 	"\nsellers:",sellers,
			# 	"\nkey_word:",key_word
			# )
			sqls = (review_number_sql, review_score_sql, price_sql, release_data_sql, sellers_sql, key_word_sql)
			sqls = " and ".join([i for i in sqls if i])
			fulled_sql = " and fulled is not NULL" if sqls else " fulled is not NULL"
			sql = '''select image,asin,review_number,review_score,price,level,catalog,title,brand,sellers,
			size,weight,address,release_data from product where %s %s''' % (sqls, fulled_sql)
			start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
			try:
				resultOfExcel(start_time, sql)
			except Exception as e:
				save_log("web")
			file_name = '%s.xlsx'%datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M").strftime("%Y-%m-%d_%H_%M")
			return send_from_directory("", file_name,as_attachment=True)
		return redirect(url_for('index'))

	if request.method == "GET":
		status_data = get_status()
		#查数据库更新
		if status_data["start_time"] != "":
			if status_data["work_statu"] == "商品列表爬取":
				sql = "select count(*) from product where update_time>'%s'" % status_data["start_time"]
				with connection.cursor() as cursor:
					cursor.execute(sql)
					result = cursor.fetchone()[0]
				status_data["crawl_product_number"] = result
				set_status(**status_data)
			if status_data["work_statu"] == "单个商品爬取":
				sql = "select count(*) from product where update_time>'%s' and fulled is not NULL" % status_data["start_time"]
				with connection.cursor() as cursor:
					cursor.execute(sql)
					result = cursor.fetchone()[0]
				status_data["crawl_product_number"] = result
				set_status(**status_data)
			if status_data["work_statu"] == "keepa补充信息":
				sql = "select count(*) from product where update_time>'%s' and release_data is NULL" % status_data["start_time"]
				with connection.cursor() as cursor:
					cursor.execute(sql)
					result = cursor.fetchone()[0]
				status_data["crawl_product_number"] = -result
				set_status(**status_data)
			if status_data["work_statu"] == "图片下载":
				sql = "select image from product where update_time>'%s'" % status_data["start_time"]
				with connection.cursor() as cursor:
					cursor.execute(sql)
					result = cursor.fetchall()
				image_number = 0
				for i in result:
					file_name = i[0].split("/")[-1]
					file_name = os.path.join(imageFolder, file_name)
					if os.path.exists(file_name):
						image_number += 1
				status_data["crawl_product_number"] = image_number
				set_status(**status_data)

		return render_template("index.html", status_data=status_data)
