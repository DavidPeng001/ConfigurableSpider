import logging
import copy
import scrapy
from scrapy import cmdline
import pymongo

from configurable_spider.webdriver.http import WebdriverRequest
from mustache.renderer import Renderer, dict2obj, Dictionary

logger = logging.getLogger('spiders.main')

def loop_item(loop_list):
	items = loop_list.pop()
	if len(loop_list) == 0:
		return [[item] for item in items]
	else:
		res = []
		backs = loop_item(loop_list)
		for item in items:
			for back in backs:
				back_list = list(back)
				back_list.append(item)
				res.append(back_list)
		return res


class MainSpider(scrapy.Spider):
	name = None

	def __init__(self, entrance_name, *args, **kwargs):
		super(MainSpider, self).__init__(*args, **kwargs)

		self.client = pymongo.MongoClient('mongodb://localhost:27017/')
		self.database = self.client['configurable_spider']
		self.config_col = self.database['SpiderConfig']

		self.config_dict = self.get_config_from_mongodb(entrance_name)
		self.current_stage = entrance_name

		self.external_params = dict()     # FIXME
		self.next_stage_href = dict()
		self.history_params = dict()

	def start_requests(self, default_url=None):
		renderer = Renderer()
		config = dict2obj(self.config_dict)
		renderer.add('s', copy.deepcopy(config))  # eq: s.request.headers.User-Agent
		for name, history in self.history_params.items():
			renderer.add(name, history)

		# s.header.parameter
		for external in config.header.external:
			renderer.add(external, self.external_params.get(external))

		# s.header.loop
		for items in self._get_loop_item(renderer.render_all(config.header.loop.values())):
			if items is not None:
				for i, key in enumerate(config.header.loop.keys()):
					# TODO: item transfer to Dictionary obj
					renderer.manager.s.header.loop.__setattr__(f'{key}-item', items[i])

			# s.request.url
			url = renderer.render(default_url or config.request.url)
			# s.request.method  # FIXME: only GET method available
			# method = config.request.method
			# s.request.headers
			headers = {header: renderer.render(value) for header, value in config.request.headers.items()}
			# s.request.cookies
			cookies = {cookie: renderer.render(value) for cookie, value in config.request.cookies.items()}

			meta = {
				'renderer': renderer,
				'config': config
			}
			request = WebdriverRequest(url, headers=headers, cookies=cookies, callback=self.parse, meta=meta)
			# renderer.manager.s.__setattr__('_request', copy.deepcopy(request))
			yield request



	def parse(self, response):
		renderer = response.meta.get('renderer', Renderer())
		config = response.meta.get('config', Dictionary())
		# TODO: load response body and cookie to param dict

		# renderer.manager.s.__setattr__('_response', copy.deepcopy(response))
		renderer.manager.s.__setattr__('parser', Dictionary())
		self._parser_recursion(response, renderer, config.parser, renderer.manager.s.parser, None)

		for output in config.output:
			l = self.next_stage_href.setdefault(self.current_stage, dict()).setdefault(output.get('stage'), [])
			l.append(output.get('url', None))

		for stage, href_list in self.next_stage_href.items():

			for href in href_list:
				self.load_next_stage(self.current_stage, renderer.manager.s, stage, href )

		# TODO: finish auto-parser interface

	def load_next_stage(self, previous_stage, previous_s, next_stage, default_url):
		l = self.history_params.setdefault(previous_stage, [])
		l.append(copy.deepcopy(previous_s))
		self.config_dict = self.get_config_from_mongodb(next_stage)
		self.current_stage = next_stage
		self.start_requests(default_url=default_url)


	def get_config_from_mongodb(self, config_name):
		return self.config_col.find_one({'name': config_name})

	def _get_loop_item(self, loop_list):
		# If loop parameter is empty
		if not loop_list:
			return [None]

		return(loop_list)

	def _parser_recursion(self, response, renderer, parser_dict, current_node, node_type):
		"""
		:param response: WebdriverResponse()
		:param renderer: Renderer()
		:param parser_dict: Dictionary()  dict from configfile
		:param current_node: Dictionary()  params dict obj of current node
		:param node_type: str  type of current node
		:return: Dictionary()  params dict obj for upper level node
		"""

		# 0 -> loop
		# 1 -> xpath-loop
		# 2 -> css-loop
		# 3 -> xpath
		# 4 -> css
		# 5 -> xpath-list
		# 6 -> css-list

		for name, value in parser_dict.items():
			current_node.__setattr__(name, Dictionary())
			node = current_node.__getattr__(name)
			if value.type == 0:     # loop

				# multi-condition loop
				# for items in self._get_loop_item(renderer.render_all(value.loop.values())):
				# 	if items is not None:
				# 		for i, key in enumerate(value.loop.keys()):
				# 			node.__setattr__(f'{key}-item', items[i])

				# one condition loop
				loop_list = renderer.render_all(value.loop.values())
				for item in loop_list if len(loop_list) != 0 else [None]:
					if item is not None:
						node.__setattr__('item', item)
					self._parser_recursion(response, renderer, value.child, node, value.type)

			elif value.type == 1 or value.type == 2:        # xpath-loop or css-loop
				super_elem = current_node.elem if (node_type == 1 or node_type == 2) else response
				if value.type == 1:
					for elem in super_elem.xpath(value.xpath):
						node.__setattr__('item', elem)
						self._parser_recursion(response, renderer, value.child, node, value.type)
				else:
					for elem in super_elem.css(value.css):
						node.__setattr__('item', elem)
						self._parser_recursion(response, renderer, value.child, node, value.type)

			elif value.type == 3 or value.type == 4:        # xpath or css
				elem = current_node.elem if (node_type == 1 or node_type == 2) else response
				if value.type == 3:
					parsed_value = elem.xpath(value.xpath).extract_first()
				else:
					parsed_value = elem.css(value.css).extract_first()
				l = current_node.setdefault(name, [])
				l.append(parsed_value)

				if value.next:
					l = self.next_stage_href.setdefault(self.current_stage, dict()).setdefault(value.next, [])
					l.append(parsed_value)

			elif value.type == 5 or value.type == 6:       # xpath-list or css-list
				elem = current_node.elem if (node_type == 1 or node_type == 2) else response
				if value.type == 5:
					parsed_list = elem.xpath(value.xpath).extract()
				else:
					parsed_list = elem.css(value.css).extract()
				l = current_node.setdefault(name, [])
				l.append(parsed_list)

				if value.next:
					l = self.next_stage_href.setdefault(self.current_stage, dict()).setdefault(value.next, [])
					l.extend(parsed_list)





