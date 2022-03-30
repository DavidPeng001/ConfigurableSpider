from scrapy import Request
from scrapy.http import TextResponse


class WebdriverRequest(Request):
    # WAITING = None, refresh=False

    def __init__(self, url, refresh=False,**kwargs):
        super(WebdriverRequest, self).__init__(url, **kwargs)
        self.dont_filter = True
        self.refresh = refresh

    def replace(self, *args, **kwargs):
        kwargs.setdefault('dont_filter', True)
        kwargs.setdefault('refresh', False)
        return super(WebdriverRequest, self).replace(*args, **kwargs)


class WebdriverResponse(TextResponse):

    def __init__(self, url, body, **kwargs):
        kwargs.setdefault('body', body)
        kwargs.setdefault('encoding', 'utf-8')
        super(WebdriverResponse, self).__init__(url, **kwargs)

