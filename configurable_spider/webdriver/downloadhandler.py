import logging
import time

from scrapy.utils.decorators import inthread,  defers
from scrapy.utils.misc import load_object

from configurable_spider.webdriver.http import WebdriverRequest, WebdriverResponse

FALLBACK_HANDLER = 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler'

class WebdriverDownloadHandler(object):

    def __init__(self, settings):
        self._enabled = settings.get('WEBDRIVER_BROWSER') is not None
        self._fallback_handler = load_object(FALLBACK_HANDLER)(settings)

    def download_request(self, request, spider):
        """Return the result of the right download method for the request."""
        if self._enabled and isinstance(request, WebdriverRequest):
            download = self._download_request
        else:
            download = self._fallback_handler.download_request
        return download(request, spider)

    @inthread
    def _download_request(self, request, spider):
        """Download a request URL using webdriver."""
        logging.debug('Webdriver download %s' % request.url)
        request.manager.webdriver.get(request.url)
        if request.refresh:
            request.manager.webdriver.refresh()
        if request.manager.request_counter > 0:
            request.manager.request_counter -= 1
        time.sleep(1)
        return WebdriverResponse(request.url, request.manager.webdriver.page_source)
