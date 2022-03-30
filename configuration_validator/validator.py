import copy
import io
import json
import logging
import sys

logger = logging.getLogger('validator')
logger.setLevel('DEBUG')

class Validator():
	def __init__(self):
		self.log_capture_string = io.StringIO()
		ch = logging.StreamHandler(self.log_capture_string)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		ch.setFormatter(formatter)
		ch.setLevel('DEBUG')
		logger.addHandler(ch)

	def validate(self, config, mode=0):
		stages = []
		is_pass = True
		logger.info(f'Validation initiate with mode {"CHECK" if mode == 0 else "CORRECT"}.')
		for stage in config.get('stages'):

			stage, stage_pass = self.stage_validator(stage, mode)
			stages.append(stage)
			if not stage_pass:
				is_pass = False
		config['stages'] = stages
		config['validation_pass'] = is_pass

		return config, self.get_log()

	def stage_validator(self, stage, mode):
		self.warning_counter = 0
		self.error_counter = 0
		self.mode = mode  # 0 -> check mode  1 -> correct mode

		origin_stage = stage
		stage = copy.deepcopy(stage)

		stage_name = stage.get('name', 'Untitled Stage')
		logger.info(f'Stage {stage_name} validation start.')
			
		# check header

		if self.judge(stage, 'header', name='header', type=dict, default={
			'external': [],
			'loop': {}
		}):
			header = stage.get('header')
			self.judge(header, 'external', name='header.external', type=list, default=[])
			self.judge(header, 'loop', name='header.loop', type=dict, default={})

		# check request

		if self.judge(stage, 'request', name='request', type=dict, necessity=True):
			request = stage.get('request')
			self.judge(request, 'url', name='request.url', type=str, necessity=True)
			self.judge(request, 'method', name='request.method', type=str, default='GET')
			self.judge(request, 'headers', name='request.headers', type=dict, default={})
			self.judge(request, 'cookies', name='request.cookies', type=dict, default={})

		# check parser

		if self.judge(stage, 'parser', name='request', type=dict, necessity=True):
			parser = stage.get('parser')
			self.parser_check(parser)

		# check output

		# check booleans
		# self.judge(stage, 'auto_parse', name='auto_parse', type=bool, default=False)
		self.judge(stage, 'remove_repeats', name='remove_repeats', type=bool, default=True)
		self.judge(stage, 'need_refresh', name='need_refresh', type=bool, default=False)

		if self.warning_counter == 0 and self.error_counter == 0:
			logger.info(f'Stage {stage_name} validation pass.')
		else:
			logger.info(f'Stage {stage_name} validation end. Result:  Error: {self.error_counter}  Warning: {self.warning_counter}')


		if self.error_counter > 0:
			is_pass = False
		else:
			if mode == 0 and self.warning_counter > 0:
				is_pass = False
			else:
				is_pass = True

		if is_pass == True and mode == 1:
			return stage, is_pass
		else:
			return origin_stage, is_pass

	def judge(self, parent, key, name='unknown module', type=None, default=None, necessity=False):
		obj = parent.get(key)
		if obj is None:
			if necessity:
				logger.error(f'Necessary part {name} lose')
				self.error_counter += 1
			else:
				logger.warning(f'{name} lose')
				self.warning_counter += 1
				if self.mode == 1:
					parent.setdefault(key, default)
					logger.info(f'Autofill {name} with default')
		elif (not isinstance(obj, type)) if type is not None else False:
			logger.error(f'{name} type error')
			self.error_counter += 1
		else:
			return True

		return False

	def parser_check(self, parser):
		for name, value in parser.items():
			if self.judge(parser, name, name=f'parser-{name}', type=dict, necessity=True):
				parser_type = value.get('type')
				if self.judge(value, 'type', name=f'parser-{name}.type', type=str, necessity=True):
					if parser_type == 'loop':
						# value['type'] = 0
						self.judge(value, 'loop', name=f'parser-{name}.loop', type=str, necessity=True)
						if self.judge(value, 'child', name=f'parser-{name}.child', type=dict, default={}):
							self.parser_check(value['child'])
					elif parser_type == 'xpath-loop':
						# value['type'] = 1
						self.judge(value, 'xpath', name=f'parser-{name}.xpath', type=str, necessity=True)
						if self.judge(value, 'child', name=f'parser-{name}.child', type=dict, default={}):
							self.parser_check(value['child'])
					elif parser_type == 'css-loop':
						# value['type'] = 2
						self.judge(value.get('css'), name=f'parser-{name}.css', type=str, necessity=True)
						if self.judge(value, 'child', name=f'parser-{name}.child', type=dict, default={}):
							self.parser_check(value['child'])
					elif parser_type == 'xpath':
						# value['type'] = 3
						self.judge(value, 'xpath', name=f'parser-{name}.xpath', type=str, necessity=True)
					elif parser_type == 'css':
						# value['type'] = 4
						self.judge(value, 'css', name=f'parser-{name}.css', type=str, necessity=True)
					elif parser_type == 'xpath-list':
						# value['type'] = 5
						self.judge(value, 'xpath', name=f'parser-{name}.xpath', type=str, necessity=True)
					elif parser_type == 'css-list':
						# value['type'] = 6
						self.judge(value, 'css', name=f'parser-{name}.css', type=str, necessity=True)
					else:
						logger.warning(f'Unknown parser type \'{parser_type}\'')

	def get_log(self):
		log_contents = self.log_capture_string.getvalue()
		self.log_capture_string.close()
		return log_contents


if __name__ == '__main__':
	# launcher for Java
	input = sys.argv[1]
	config_dict = json.loads(input)
	config, log = Validator().validate(config_dict, mode=1)
	print(json.dumps(config))
	print(log)
