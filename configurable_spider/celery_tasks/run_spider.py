import json
import logging
import os
import sys
from datetime import datetime

from celery import Celery, Task
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from configurable_spider.mysql.mysql import get_rule, start_running, end_running

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from configurable_spider.spiders.main import MainSpider

app = Celery('run_spider', backend='redis://localhost:6379/11', broker='redis://localhost:6379/11')




#
# class MyTask(Task):
# 	def on_success(self, retval, task_id, args, kwargs):
# 		is_scheduled = kwargs.get("is_scheduled")
# 		table_name = "t_scrapy_task" if not is_scheduled else "t_scrapy_scheduledtask"
# 		end_running(task_id, table_name)
# 		return super(MyTask, self).on_success(retval, task_id, args, kwargs)
#
# 	def on_failure(self, exc, task_id, args, kwargs, einfo):
# 		return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)

@app.task()
def run_spider(task_id, is_scheduled):
	table_name = "t_scrapy_task" if not is_scheduled else "t_scrapy_scheduledtask"
	config_json = get_rule(task_id, table_name)
	if config_json is None:
		return
	config = json.loads(config_json)
	log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..\\log')
	current_time = datetime.now().strftime('%y%m%d-%H%M%S')
	log_file = f'task{task_id}_{current_time}.log'
	logging.info('Log directory: ' + log_dir)
	logging.info('Log file: ' + log_file)

	settings = get_project_settings()
	settings.attributes['LOG_FILE'].__setattr__('value', os.path.join(log_dir, log_file))



	# depth_limit = config.get("common").get("depth_limit")
	# if depth_limit > 0:
	# 	settings.attributes['DEPTH_LIMIT'].__setattr__('value', depth_limit)
	#
	request_interval = config.get("common").get("request_interval")
	if request_interval > 0:
		settings.attributes['DOWNLOAD_DELAY'].__setattr__('value', request_interval)
	#
	retry_times = config.get("common").get("retry_times")
	if retry_times > 0:
		settings.attributes['RETRY_ENABLED'].__setattr__('value', True)
		settings.attributes['RETRY_TIMES'].__setattr__('value', retry_times)

	start_running(task_id, table_name, log_file)

	process = CrawlerProcess(settings)
	process.crawl(MainSpider, config)
	process.start()

def log_scan(log_dir):
	for root, dirs, files in os.walk(log_dir):
		for file_name in files:
			if file_name.endswith('_latest.log'):
				new_name = file_name.replace('_latest.log', '.log')
				try:
					os.rename(os.path.join(log_dir, file_name), os.path.join(log_dir, new_name))
				except PermissionError:
					return False
	return True

if __name__ == '__main__':
	run_spider(7, False)

