import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from configuration_validator.validator import Validator


def parser_list2dict(parsers, loc='s.parser'):
	nodes = list(list_filter(parsers, loc, 'loc'))
	result_dict = dict()
	for node in nodes:
		node_type = node['type']
		result = dict(type=node_type)

		if node_type.startswith('xpath'):
			result['xpath'] = node['value']
		elif node_type.startswith('css'):
			result['css'] = node['value']
		else:
			result['loop'] = node['value']

		if node_type in ['xpath-loop', 'css-loop', 'loop']:
			child = parser_list2dict(parsers, node['loc'] + '.' + node['name'])
			result['child'] = child
		else:
			result['next'] = node.get('next')

		result_dict.setdefault(node['name'], result)
	return result_dict

def list_filter(str_list, target, key):
	for s in str_list:
		if s[key] == target:
			yield s

def config_parser(original_config):
	config_dict = json.loads(original_config)
	stages = []
	for stage in config_dict.get('stages'):
		stage['parser'] = parser_list2dict(list(stage.get('parser')))
		stages.append(stage)
	config_dict['stages'] = stages
	return json.dumps(config_dict)

if __name__ == '__main__':
	# launcher for Java 
	# input_list = sys.argv[1:]
	# input = ' '.join(input_list)
	with open("D:\\DCC\\PythonDemo\\ConfigurableSpider\\configuration_validator\\tmp.json", 'r', encoding='utf-8') as f:
		input = f.read()
	config = config_parser(input)
	config, log = Validator().validate(json.loads(config), mode=1)
	config = json.dumps(config)
	print(config)
	print(log)
