from flask import Flask, redirect, url_for, render_template, request
from amazon import *
import datetime
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

@app.route('/', methods=["GET", "POST"])
def index():
	if request.method == "POST":
		setup = request.form.get("setup")
		
		url = request.form["url"]
		number = request.form["number"]
		status_data = get_status()
		if status_data["start_time"] == "" and url != "" and number != "":
			status_data["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
			status_data["work_statu"] = "商品列表爬取"
			set_status(**status_data)
			crawCatalog(url=url,max_level=int(number))
			status_data["work_statu"] = "单个商品爬取"
			set_status(**status_data)
			work2()
			status_data["work_statu"] = "keepa补充信息"
			set_status(**status_data)
			keepa()
			status_data["work_statu"] = "图片下载"
			set_status(**status_data)
			downloadImage()
			status_data["work_statu"] = "Excel下载"
			set_status(**status_data)
			resultOfHTML()
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

		return render_template("index.html", status_data=status_data)

