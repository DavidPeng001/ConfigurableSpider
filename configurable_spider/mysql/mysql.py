from datetime import datetime

import pymysql

conn = pymysql.connect("112.126.90.201", "root", "90201", "news")
cursor = conn.cursor()

def connect_mysql():
	conn = pymysql.connect("112.126.90.201", "root", "90201", "news")
	cursor = conn.cursor()
	return conn, cursor


def get_rule(task_id, table_name):
	conn, cursor = connect_mysql()
	sql = f'select rule from {table_name} where id = {str(task_id)}'
	cursor.execute(sql)
	res = cursor.fetchone()
	conn.commit()
	if len(res) > 0:
		return res[0]
	else:
		return None

def start_running(task_id, table_name, log_file):
	conn, cursor = connect_mysql()
	current_time = datetime.now().strftime('%y/%m/%d/%H/%M/%S')
	sql = f'update {table_name} set lastruntime = "{current_time}" , is_running = 1 , log = "{log_file}" where id = {str(task_id)}'
	cursor.execute(sql)
	conn.commit()
	return

def end_running(task_id, table_name):
	conn, cursor = connect_mysql()
	sql = f'update {table_name} set is_running = 0 where id = {str(task_id)}'
	cursor.execute(sql)
	conn.commit()


def submit(title, tag, body, url, photos):
	conn, cursor = connect_mysql()
	current_time = datetime.now().strftime('%y/%m/%d/%H/%M/%S')
	body.replace('"', "'")
	photo0 = f'"{photos[0]}"' if len(photos) > 0 else 'null'
	photo1 = f'"{photos[1]}"' if len(photos) > 1 else 'null'
	photo2 = f'"{photos[2]}"' if len(photos) > 2 else 'null'
	photo3 = f'"{photos[3]}"' if len(photos) > 3 else 'null'
	photo4 = f'"{photos[4]}"' if len(photos) > 4 else 'null'

	sql = f'insert into t_download_news values (null ,"{body}", "{current_time}", {photo0}, {photo1} ,{photo2} ,{photo3} ,{photo4}, "{url}", "未编辑", "{tag}", "{title}", null)'
	print(sql)
	cursor.execute(sql)
	conn.commit()

	return


if __name__ == '__main__':
	res = get_rule(1, 't_scrapy_task')
	print(res)