d:
cd D:\DCC\PythonDemo\ConfigurableSpider
celery -A configurable_spider.celery_tasks.run_spider worker -l info -P gevent