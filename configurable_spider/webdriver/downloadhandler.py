import logging

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

    @defers
    def _download_request(self, request, spider):
        """Download a request URL using webdriver."""
        logging.debug('Downloading %s with webdriver' % request.url)
        request.webdriver.get(request.url)
        return WebdriverResponse(request.url, webdriver=request.webdriver)