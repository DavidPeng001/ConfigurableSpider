import re
import json
import logging
from copy import deepcopy
from datetime import datetime

import redis
import scrapy

# from configurable_spider.mysql.mysql import end_running
from scrapy import Request

from configurable_spider.htmlparser.htmlparser import HtmlParser
from configurable_spider.items import ConfigurableSpiderItem
from configurable_spider.mysql.mysql import submit
from configurable_spider.nlp.vsm import vsm
from configurable_spider.webdriver.http import WebdriverRequest
from mustache.renderer import Renderer, dict2obj, Dictionary

RE_LEGAL_URL = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

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




def is_legal_url(url):
	return re.match(RE_LEGAL_URL, url) != None

class MainSpider(scrapy.Spider):
	name = 'main_spider'
	webdriver_instances = 4

	# @classmethod
	# def from_crawler(cls, crawler, *args, **kwargs):
	# 	spider = cls(*args, **kwargs)
	# 	spider._set_crawler(crawler)
	# 	return spider

	def __init__(self, config, *args, **kwargs):
		super(MainSpider, self).__init__(*args, **kwargs)

		conn = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, db=10)
		self.r = redis.Redis(connection_pool=conn)

		self.header_log_print(config)
		self.config = config
		self.tag = self.config.get("tag")
		self.is_static = self.config.get("common").get("is_static", False)
		depth_limit = int(self.config.get("common").get("depth_limit"))
		self.depth_limit = depth_limit if depth_limit > 0 else 5

		# explorer_processes = self.config.get("common").get("explorer_processes")
		# MainSpider.webdriver_instances = explorer_processes if 0 < explorer_processes < 10 else 4

		self.title_threshold = float(self.config.get("filter").get("title_threshold", 0),)
		self.content_threshold = float(self.config.get("filter").get("content_threshold", 0))
		self.weight_dict = self.config.get("filter").get("weight_dict")

		self.start_stage_dict = self.config.get("stages")[0]
		self.start_stage = self.start_stage_dict.get("name")

		self.external_params = dict(e= json.loads(self.config.get("common").get("external_def")) if self.config.get("common").get("external_def") !='' else {})
		self.next_stage_href = dict()
		self.history_params = dict()

	def header_log_print(self, config):
		print('\n-------- SPIDER PARAMS --------\n')
		print(f'Rule:  {config}')
		print('\n-------------------------------\n')


	def start_requests(self, default_url=None, stage_dict=None, stage_name=None):
		current_stage_dict = stage_dict if stage_dict is not None else self.start_stage_dict
		current_stage_name = stage_name if stage_name is not None else self.start_stage
		current_stage_id = datetime.now().strftime('%y%m%d%H%M%S')
		renderer = Renderer()
		config = dict2obj(current_stage_dict)
		renderer.add('s', deepcopy(config))  # eq: s.request.headers.User-Agent
		for name, history in self.history_params.items():
			renderer.add(name, history[-1])

		# s.header.external
		renderer.add('e', self.external_params.get('e', dict()))
		for external in config.header.external:
			renderer.add(external, self.external_params.get(external))

		# s.header.loop
		for items in self._get_loop_item(renderer.render_all(config.header.loop.values())):  # TODO: type check
			if items is not None:
				for i, key in enumerate(config.header.loop.keys()):
					# TODO: item transfer to Dictionary obj
					renderer.manager.s.header.loop.__setattr__(f'{key}_item', items[i])

			# s.request.url
			url = renderer.render(default_url or config.request.url)

			# s.request.headers
			headers = {header: renderer.render(value) for header, value in config.request.headers.items()}
			# s.request.cookies
			cookies = {cookie: renderer.render(value) for cookie, value in config.request.cookies.items()}

			meta = {
				'renderer': renderer,
				'config': config,
				'current_stage_dict': current_stage_dict,
				'current_stage_name': current_stage_name,
				'current_stage_id': current_stage_id,
				'depth': 0
			}
			if self.is_static:
				request = Request(url, headers=headers, cookies=cookies, callback=self.parse, meta=meta)
			else:
				request = WebdriverRequest(url, headers=headers, cookies=cookies, callback=self.parse, meta=meta, refresh=config.need_refresh)
			# renderer.manager.s.__setattr__('_request', copy.deepcopy(request))
			yield request

	def get_next_requests(self, default_url=None, stage_dict=None, stage_name=None):
		current_stage_dict = stage_dict if stage_dict is not None else self.start_stage_dict
		current_stage_name = stage_name if stage_name is not None else self.start_stage
		current_stage_id = datetime.now().strftime('%y%m%d%H%M%S')
		renderer = Renderer()
		config = dict2obj(current_stage_dict)
		renderer.add('s', deepcopy(config))  # eq: s.request.headers.User-Agent
		request_list = []
		for name, history in self.history_params.items():
			renderer.add(name, history[-1])

		# s.header.external
		renderer.add('e', self.external_params.get('e', dict()))
		for external in config.header.external:
			renderer.add(external, self.external_params.get(external))

		# s.header.loop
		for items in self._get_loop_item(renderer.render_all(config.header.loop.values())):  # TODO: type check
			if items is not None:
				for i, key in enumerate(config.header.loop.keys()):
					# TODO: item transfer to Dictionary obj
					renderer.manager.s.header.loop.__setattr__(f'{key}_item', items[i])

			# s.request.url
			url = renderer.render(default_url or config.request.url)

			# s.request.headers
			headers = {header: renderer.render(value) for header, value in config.request.headers.items()}
			# s.request.cookies
			cookies = {cookie: renderer.render(value) for cookie, value in config.request.cookies.items()}

			meta = {
				'renderer': renderer,
				'config': config,
				'current_stage_dict': current_stage_dict,
				'current_stage_name': current_stage_name,
				'current_stage_id': current_stage_id
			}
			if self.is_static:
				request = WebdriverRequest(url, headers=headers, cookies=cookies, callback=self.parse, meta=meta)
			else:
				request = WebdriverRequest(url, headers=headers, cookies=cookies, callback=self.parse, meta=meta, refresh=config.need_refresh)
			# renderer.manager.s.__setattr__('_request', copy.deepcopy(request))
			request_list.append(request)
		return request_list


	def parse(self, response):
		renderer = response.meta.get('renderer', Renderer())
		config = response.meta.get('config', Dictionary())
		depth = response.meta.get('depth') + 1
		current_stage_dict = response.meta.get('current_stage_dict')
		current_stage_name = response.meta.get('current_stage_name')
		current_stage_id = response.meta.get('current_stage_id')


		# renderer.manager.s.__setattr__('_response', copy.deepcopy(response))
		renderer.manager.s.__setattr__('parser', Dictionary())
		self._parser_recursion(response, renderer, config.parser, renderer.manager.s.parser, None)

		body = None
		if config.auto_parse_body == True:
			body = ''
		else:
			if config.body_parser is not None and config.body_parser.strip() != '':
				result_list = response.xpath(config.body_parser).extract()
				body_list = [s.strip() for s in result_list if s.strip() != '']
				body = "\n".join(body_list)

		if body is not None:
			self.save_into_db(body=body, response=response)

		if depth <= self.depth_limit:
			for next_stage, href_list in self.next_stage_href.get(current_stage_id, {}).items():
				if next_stage is None or next_stage.strip() == '':
					continue
				for href in href_list:
					href = response.urljoin(href)
					request_list = self.load_next_stage(current_stage_name, renderer.manager.s, next_stage, href )
					for request in request_list:
						request.meta['depth'] = depth
						yield request



	def load_next_stage(self, previous_stage, previous_s, next_stage, default_url):
		l = self.history_params.setdefault(previous_stage, [])
		l.append(deepcopy(previous_s))
		next_stage_dict = self.get_stage(next_stage)
		next_stage_name = next_stage
		request_list = self.get_next_requests(default_url=default_url, stage_dict=next_stage_dict, stage_name=next_stage_name)
		return request_list
		# XXX: use celery to manager new spider stage

	def save_into_db(self, response, body):
		if not self.r.sismember("url_set", response.url):
			self.r.sadd("url_set", response.url)
		# if True:
			if body is None or len(body) == 0:
				body = HtmlParser(response.body).article()

			weight_dict = self.weight_dict
			content_threshold = self.content_threshold
			sim = vsm(body, weight_dict)
			is_pass = sim >= content_threshold
			logger.info(f'URL {response.url} Content similarity {sim}, {"pass" if is_pass else "not relative"}')
			if is_pass:

				photos = response.xpath("//img/@src").extract()
				title = response.xpath("//title/text()").extract_first()
				if title is None or title.strip == '' :
					title = "Untitled"

				submit(title, self.tag, body, response.url, photos)

	def get_stage(self, stage_name):
		for index, stage in enumerate(self.config.get("stages")):
			if stage["name"] == stage_name:
				return self.config.get("stages")[index]

	def _get_loop_item(self, loop_list):
		# If loop parameter is empty
		if not loop_list:
			return [None]

		return loop_item(loop_list)

	def title_judge(self, href_content):
		sim = vsm(href_content, self.weight_dict)
		res = sim >= self.title_threshold
		logger.info(f'Title {href_content} similarity {sim}, {"pass" if res else "not relative"}')
		return res

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
			if value.type == 'loop':     # loop

				# multi-condition loop
				# for items in self._get_loop_item(renderer.render_all(value.loop.values())):
				# 	if items is not None:
				# 		for i, key in enumerate(value.loop.keys()):
				# 			node.__setattr__(f'{key}-item', items[i])

				# one condition loop
				loop_list = renderer.render(value.loop)
				if not isinstance(loop_list, list):
					logger.error(f'Rendered {name}.loop is not list')
				for item in loop_list if len(loop_list) != 0 else [None]:
					if item is not None:
						node.__setattr__('item', item)          # FIXME: maybe elem?
					self._parser_recursion(response, renderer, value.child, node, value.type)

			elif value.type in ['xpath-loop', 'css-loop']:        # xpath-loop or css-loop
				upper_elem = current_node.elem if (node_type in ['xpath-loop', 'css-loop']) else response

				if value.type == 'xpath-loop':
					for elem in upper_elem.xpath(value.xpath):
						node.__setattr__('elem', elem)
						self._parser_recursion(response, renderer, value.child, node, value.type)
				else:
					for elem in upper_elem.css(value.css):
						node.__setattr__('elem', elem)
						self._parser_recursion(response, renderer, value.child, node, value.type)

			elif value.type in ['xpath', 'css']:        # xpath or css
				elem = current_node.elem if (node_type in ['xpath-loop', 'css-loop']) else response
				if value.type == 'xpath':
					selectors = elem.xpath(value.xpath)
					if value.next and selectors[0].root.tag == 'a':
						if self.title_judge(selectors[0].root.text_content()):
							# FIXME: is href empty or not abs address
							parsed_value = selectors[0].attrib['href']
						else:
							continue
					else:
						parsed_value = elem.xpath(value.xpath).extract_first()
				else:
					selectors = elem.css(value.css)
					if value.next and selectors[0].root.tag == 'a':
						if self.title_judge(selectors[0].root.text_content()):
							parsed_value = selectors[0].attrib['href']
						else:
							continue
					else:
						parsed_value = elem.css(value.css).extract_first()
				print(parsed_value)
				l = current_node.setdefault(name, [])
				if not isinstance(l, list):
					l = []
				l.append(parsed_value)

				if value.next:
					next_stage = renderer.render(value.next)
					if not isinstance(next_stage, str):
						continue
					l = self.next_stage_href.setdefault(response.meta.get('current_stage_id'), dict()).setdefault(next_stage , [])
					l.append(parsed_value)

			elif value.type in ['xpath-list', 'css-list']:       # xpath-list or css-list
				elem = current_node.elem if (node_type in ['xpath-loop', 'css-loop']) else response
				if value.type == 'xpath-list':
					parsed_list = []
					if value.next:
						for selector in elem.xpath(value.xpath):
							if  selector.root.tag == 'a':
								if self.title_judge(selector.root.text_content()):
									parsed_value = selector.attrib['href']
									parsed_list.append(parsed_value)
						if parsed_list == []:
							parsed_list = elem.xpath(value.xpath).extract()
					else:
						parsed_list = elem.xpath(value.xpath).extract()
				else:
					parsed_list = []
					if value.next:
						for selector in elem.css(value.css):
							if selector.root.tag == 'a':
								if self.title_judge(selector.root.text_content()):
									parsed_value = selector.attrib['href']
									parsed_list.append(parsed_value)
						if parsed_list == []:
							parsed_list = elem.css(value.css).extract()
					else:
						parsed_list = elem.css(value.css).extract()
				l = current_node.setdefault(name, [])
				if not isinstance(l, list):
					l = []
				l.extend(parsed_list)

				if value.next:
					l = self.next_stage_href.setdefault(response.meta.get('current_stage_id'), dict()).setdefault(value.next, [])
					l.extend(parsed_list)
					pass

