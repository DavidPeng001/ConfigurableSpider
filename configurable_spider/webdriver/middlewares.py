import logging
from queue import Queue, Empty

from scrapy.exceptions import NotConfigured
from scrapy.signals import engine_stopped

from configurable_spider.webdriver.http import WebdriverRequest
from configurable_spider.webdriver.manager import WebdriverManager

logger = logging.getLogger('WebdriverSpiderMiddleware')

class WebdriverSpiderMiddleware(object):

	def __init__(self, crawler):
		self.crawler = crawler
		self._manager_queue = Queue()
		self._wait_request = Queue()
		self.crawler.signals.connect(self._check_queue, signal=engine_stopped)

	@classmethod
	def from_crawler(cls, crawler):
		try:
			return cls(crawler)
		except Exception as e:
			raise NotConfigured('WEBDRIVER_BROWSER is misconfigured: %r (%r)' % (crawler.settings.get('WEBDRIVER_BROWSER'), e))

	def process_start_requests(self, start_requests, spider):
		instance_number = getattr(spider, 'webdriver_instances', None)
		if isinstance(instance_number, int) and instance_number > 0:
			self._init_webdriver_queue(instance_number)

		return self._process_requests(start_requests)
		# for request in self._process_requests(start_requests):
		# 	yield request

	def process_spider_output(self, response, result, spider):
		for request in self._process_requests(result):
			yield request
		if isinstance(response.request, WebdriverRequest):
			try:
				next_request = self._wait_request.get_nowait()
			except Empty:
				pass
			else:
				request_result = self._process_request(next_request)
				if request_result is not None:
					yield request_result


	def _init_webdriver_queue(self, instance_number):
		for i in range(instance_number):
			self._manager_queue.put_nowait(WebdriverManager(self.crawler))


	def _process_requests(self, items_or_requests):
		for request in iter(items_or_requests):
			if isinstance(request, WebdriverRequest):
				try:
					current_manager = self._manager_queue.get(True, timeout=10)
				except Empty:
					logger.error('Webdriver manager queue timeout, try later')
					continue    #XXX: try later?
				else:
					self._manager_queue.put_nowait(current_manager)
				request_result = current_manager.acquire(request, self._wait_request)
				if request_result is None:
					continue
				yield request_result

	def _process_request(self, request):
		if isinstance(request, WebdriverRequest):
			try:
				current_manager = self._manager_queue.get(True, timeout=10)
			except Empty:
				logger.error('Webdriver manager queue timeout, try later')
				return
			else:
				self._manager_queue.put_nowait(current_manager)
			request_result = current_manager.acquire(request, self._wait_request)
			return request_result

	def _check_queue(self):
		if not self._wait_request.empty():
			logger.error('Waiting request queue not empty at engine stop.')