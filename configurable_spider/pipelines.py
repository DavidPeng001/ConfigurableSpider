# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import redis

from configurable_spider.htmlparser.htmlparser import HtmlParser
from configurable_spider.items import ConfigurableSpiderItem
from configurable_spider.mysql.mysql import submit
from configurable_spider.nlp.vsm import vsm
from lxml import etree

conn = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, db=10)
r = redis.Redis(connection_pool=conn)

class ConfigurableSpiderPipeline(object):
    def process_item(self, item, spider):
        print(item)
        if isinstance(item, ConfigurableSpiderItem):
            url = item['url']
            html = item['html']
            body = item['body']


            if r.sismember("url_set", url):
                r.sadd("url_set", url)
                if body is None or len(body) == 0:
                    body = HtmlParser(html).article()

                weight_dict = spider.weight_dict
                content_threshold = spider.content_threshold
                if vsm(body, weight_dict) > content_threshold:

                    tree = etree.HTML(html)
                    photos = tree.xpath("//img/@src")
                    title = tree.xpath("//title/text()")
                    if len(title) > 0:
                        title = title[0]
                    else:
                        title = "Untitled"

                    submit(title, spider.__getattr__("tag"), body, url, photos)

        return item
                    # arti-parser
                    # upload to db

                    #change running state
                    #





