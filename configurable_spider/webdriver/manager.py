import logging
# from queue import Queue, Empty

from scrapy.signals import engine_stopped
from selenium import webdriver
from configurable_spider.webdriver.http import WebdriverRequest

logger = logging.getLogger('WebdriverManager')

MAX_POOL_CAPACITY = 5

class WebdriverManager(object):
	def __init__(self, crawler):
		self.crawler = crawler
		self._settings_browser = crawler.settings.get('WEBDRIVER_BROWSER', None)
		self._settings_options = crawler.settings.get('WEBDRIVER_OPTIONS', [])
		self._user_agent = crawler.settings.get('USER_AGENT', None)
		self.request_counter = 0
		# self._wait_queue = Queue()

		# get webdriver browser
		if not self._settings_browser:
			self._settings_browser = 'Chrome'
		module = __import__('selenium.webdriver', fromlist=[self._settings_browser])
		self._browser = getattr(module, self._settings_browser)

		# get webdriver options obj
		if issubclass(self._browser, (webdriver.Chrome, webdriver.Firefox, webdriver.Ie)):
			module = __import__('selenium.webdriver', fromlist=[self._settings_browser + 'Options'])
			self._options = getattr(module, self._settings_browser + 'Options')
			self._webdriver_options = self._options()
			for option in self._settings_options:
				self._webdriver_options.add_argument(option)
		# build a new webdriver instance
		self.webdriver = self._browser(options=self._webdriver_options)
		self.crawler.signals.connect(self._cleanup, signal=engine_stopped)


	def acquire(self, request, wait_request):
		if isinstance(request, WebdriverRequest):
			if self.request_counter < MAX_POOL_CAPACITY:
				self.request_counter += 1
				request.manager = self
				return request
			else:
				wait_request.put_nowait(request)

	# def release(self):
	# 	try:
	# 		request = self.wait_queue.get_nowait()
	# 	except Empty:
	# 		return
	# 	return self.acquire(request)

	def _cleanup(self):
		"""Clean up when the scrapy engine stops."""
		if self.webdriver is not None:
			self.webdriver.quit()



