## 准备

安装Selenium和对应浏览器的Webdriver，并设置环境变量。

## 安装

将 `webdriver` 文件夹放入爬虫项目，与 `spiders` 目录同级。

## 配置

进入项目配置 `settings.py` ，配置下载器与爬虫中间件：

```python
DOWNLOAD_HANDLERS = {
    'http': 'webdriver.downloadhandler.WebdriverDownloadHandler',
    'https': 'webdriver.downloadhandler.WebdriverDownloadHandler',
}

SPIDER_MIDDLEWARES = {
    'webdriver.middlewares.WebdriverSpiderMiddleware': 543,
}
```

按以下格式配置Webdriver对应的浏览器以及其Webdriver参数：

```python
WEBDRIVER_BROWSER = 'Chrome'

WEBDRIVER_OPTIONS = [
	'--debug=true',
	'--load-images=false',
	'--webdriver-loglevel=debug',
	'--headless=true'
]
```

## 使用

在爬虫类中，声明Webdriver的实例数量，即同时并行运行几个浏览器程序， 如：

```python
class TestSpider(scrapy.Spider):
    name = 'test_spider'
    webdriver_instances = 4      # 即同时打开4个浏览器

    def start_requests(self):
        ...
```

发出请求时，使用 `WebdriverRequest` 代替 `scrapy.Request` ：

```python
from scrapyproject.webdriver.http import WebdriverRequest
...
    yield WebdriverRequest(url)
```

若爬取网页为单页应用（SPA），可能在URL地址变更时无法正确加载新内容，此时需要对网页进行刷新，在请求时可添加参数 `refresh=True` ， 如：

```python
yield WebdriverRequest(url, refresh=True)
``` 