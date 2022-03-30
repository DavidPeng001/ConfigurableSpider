import os
import sys
import time


sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from configurable_spider.celery_tasks.run_spider import run_spider
from configurable_spider.mysql.mysql import end_running



if __name__ == '__main__':
	task_id = sys.argv[1]
	status = sys.argv[2]
	# task_id = 4
	# status = 0
	is_scheduled = int(status) == 1
	result = run_spider.delay(int(task_id), is_scheduled)
	while not result.ready():
		time.sleep(10)
	table_name = "t_scrapy_task" if not is_scheduled else "t_scrapy_scheduledtask"
	end_running(int(task_id), table_name)