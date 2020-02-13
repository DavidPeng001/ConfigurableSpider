from scrapy.exceptions import NotConfigured
from scrapy.signals import engine_stopped
from selenium import webdriver

from configurable_spider.webdriver.http import WebdriverRequest


class WebdriverSpiderMiddleware(object):

	def __init__(self, crawler):
		self.crawler = crawler
		self._settings_browser = crawler.settings.get('WEBDRIVER_BROWSER', None)
		self._settings_options = crawler.settings.get('WEBDRIVER_OPTIONS', [])
		self._user_agent = crawler.settings.get('USER_AGENT', None)
		self._webdriver = None

		# get webdriver browser class
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

	@classmethod
	def from_crawler(cls, crawler):
		try:
			return cls(crawler)
		except Exception as e:
			raise NotConfigured('WEBDRIVER_BROWSER is misconfigured: %r (%r)' % (crawler.settings.get('WEBDRIVER_BROWSER'), e))

	def process_start_requests(self, start_requests, spider):
		for request in start_requests:
			yield self._init_webdriver(request)

	def process_spider_output(self, response, result, spider):
		for request in result:
			yield self._init_webdriver(request)

	def _init_webdriver(self, request):
		if isinstance(request, WebdriverRequest) and request.webdriver is None:
			self._webdriver = self._browser(options=self._webdriver_options)
			self.crawler.signals.connect(self._cleanup, signal=engine_stopped)
			request.webdriver = self._webdriver
		return request

	def _cleanup(self):
		if self._webdriver is not None:
			self._webdriver.quit()
