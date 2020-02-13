from scrapy import Request
from scrapy.http import TextResponse


class WebdriverRequest(Request):
    # WAITING = None

    def __init__(self, url, webdriver=None, **kwargs):
        super(WebdriverRequest, self).__init__(url, **kwargs)
        self.webdriver = webdriver
        kwargs.setdefault('dont_filter', True)

    def replace(self, *args, **kwargs):
        kwargs.setdefault('webdriver', self.webdriver)
        kwargs.setdefault('dont_filter', True)
        return super(WebdriverRequest, self).replace(*args, **kwargs)


class WebdriverResponse(TextResponse):

    def __init__(self, url, webdriver, **kwargs):
        kwargs.setdefault('body', webdriver.page_source)
        kwargs.setdefault('encoding', 'utf-8')
        super(WebdriverResponse, self).__init__(url, **kwargs)
        self.webdriver = webdriver