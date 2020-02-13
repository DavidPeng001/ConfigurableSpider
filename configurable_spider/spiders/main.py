import logging

import scrapy
import pymongo

from mustache.renderer import Renderer, dict2obj

logger = logging.getLogger('spiders.main')

class MainSpider(scrapy.Spider):
	name = None

	def __init__(self, entrance_name, *args, **kwargs):
		super(MainSpider, self).__init__(*args, **kwargs)

		self.client = pymongo.MongoClient('mongodb://localhost:27017/')
		self.database = self.client['configurable_spider']
		self.config_col = self.database['SpiderConfig']
		self.entrance_dict = self.config_col.find_one({'name': entrance_name})

		self.external_parameter = dict()
		# FIXME

	def start_requests(self):
		renderer = Renderer()
		entrance = dict2obj(self.entrance_dict)
		renderer.add('s', entrance)  # eq: s.request.headers.User-Agent

		# s.header.parameter
		for external in entrance.header.external:
			renderer.add(external, self.external_parameter.get(external))

		# s.header.loop
		for items in self._get_loop_item(list(entrance.header.loop.values())):
			for i, key in enumerate(list(entrance.header.loop.keys())):
				# TODO: item transfer to Dictionary obj
				renderer.manager.s.header.loop.__setattr__(f'{key}-item', items[i])

			# s.request




	def _get_loop_item(self, loop_list):
		items = loop_list.pop()
		if len(loop_list) == 0:
			return [[item] for item in items]
		else:
			res = []
			backs = self._get_loop_item(loop_list)
			for item in items:
				for back in backs:
					back_list = list(back)
					back_list.append(item)
					res.append(back_list)
			return res










