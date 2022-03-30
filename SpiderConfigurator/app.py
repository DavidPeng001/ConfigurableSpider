import json
import os

from flask import Flask, render_template, jsonify, request
import redis

from configurable_spider.celery_tasks.run_spider import run_spider
from configuration_validator.validator import Validator

app = Flask(__name__)
conn = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True)

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

def json_str_check(json_str):
	if not json_str:
		return '{}'
	try:
		json.loads(json_str)
	except Exception:
		return False
	return json_str



@app.route('/scrapyconfig/submitstage', methods=['POST'])
def stage_submit():
	r = redis.Redis(connection_pool=conn)
	json_dict = json.loads(request.get_data())
	name = json_dict.get('name')
	if name is None:
		return 'name not found', 400

	parser = parser_list2dict(list(json_dict['parser']))
	json_dict['parser'] = parser
	r.hset('spider_stage', name, request.get_data())
	r.hset('spider_config', name, json.dumps(json_dict))

	return 'success', 200

@app.route('/scrapyconfig/allstage', methods=['GET'])
def all_stage():
	r = redis.Redis(connection_pool=conn)
	names = r.hkeys('spider_stage')
	return jsonify(names)

@app.route('/scrapyconfig/loadstage', methods=['GET'])
def load_stage():
	r = redis.Redis(connection_pool=conn)
	name = request.args.get('name')
	if name is None:
		return 'name not found', 400
	stage = r.hget('spider_stage', name) or '{"error": "Stage not found"}'
	config = r.hget('spider_config', name) or '{"error": "Config not found. Check stage settings again."}'
	validation = r.hget('spider_config_validator', name) or 'Validator not found. Please validate config first.'

	return jsonify([stage, config, validation])

@app.route('/scrapyconfig/validate', methods=['GET'])
def config_validate():
	r = redis.Redis(connection_pool=conn)
	name = request.args.get('name')
	if name is None:
		return 'name not found', 400
	config = r.hget('spider_config', name)
	if config is None:
		return 'config not found', 400
	validator = Validator()
	config, validator_log = validator.validator(json.loads(config), int(request.args.get('mode') or 0))
	print(json.dumps(config))
	r.hset('spider_config', name, json.dumps(config))
	r.hset('spider_config_validator', name, validator_log)
	return 'success', 200

@app.route('/scrapyconfig/deletestage', methods=['GET'])
def delete_stage():
	r = redis.Redis(connection_pool=conn)
	name = request.args.get('name')
	if name is None:
		return 'name not found', 400
	r.hdel('spider_stage', name)
	r.hdel('spider_config', name)
	r.hdel('spider_config_validator', name)
	return 'success', 200


@app.route('/scrapyconfig/allentrance', methods=['GET'])
def all_entrance():
	r = redis.Redis(connection_pool=conn)
	entrances = r.hkeys('spider_entrance')
	return jsonify(entrances)

@app.route('/scrapyconfig/loadentrance', methods=['GET'])
def load_entrance():
	r = redis.Redis(connection_pool=conn)
	entrance = request.args.get('entrance')
	if entrance is None:
		return 'entrance not found', 400
	entrance_config = r.hget('spider_entrance', entrance)
	if entrance_config is None:
		return 'entrance_config not found', 400
	return jsonify(json.loads(entrance_config))

@app.route('/scrapyconfig/saveentrance', methods=['POST'])
def save_entrance():
	r = redis.Redis(connection_pool=conn)
	print(request.get_data())
	json_dict = json.loads(request.get_data())
	stage_name = json_dict.get('stage_name')
	if stage_name is None:
		return 'stage_name not found', 400
	config = r.hget('spider_config', stage_name)
	if config is None:
		return 'config not found', 400
	external = json_str_check(json_dict.get('external'))
	if not external:
		return 'External json decode fail', 400
	json_dict['external'] = external

	entrance_name = json_dict.pop('entrance_name')
	if entrance_name is None:
		return 'entrance_name not found', 400
	r.hset('spider_entrance', entrance_name, json.dumps(json_dict))
	return 'success', 200

@app.route('/scrapyconfig/runentrance', methods=['POST'])
def save_run_entrance():
	r = redis.Redis(connection_pool=conn)
	json_dict = json.loads(request.get_data())
	stage_name = json_dict.get('stage_name')
	if stage_name is None:
		return 'stage_name not found', 400
	config = r.hget('spider_config', stage_name)
	if config is None:
		return 'config not found', 400
	external = json_str_check(json_dict.get('external'))
	if not external:
		return 'External json decode fail', 400
	json_dict['external'] = external
	entrance_name = json_dict.pop('entrance_name')
	if entrance_name is None:
		return 'entrance_name not found', 400
	r.hset('spider_entrance', entrance_name, json.dumps(json_dict))
	status = run_spider.delay(entrance_name, stage_name=stage_name, entrance_external=json.loads(external))
	print(status)
	return 'success', 200

@app.route('/scrapyconfig/deleteentrance', methods=['GET'])
def delete_entrance():
	r = redis.Redis(connection_pool=conn)
	entrance = request.args.get('entrance')
	if entrance is None:
		return 'entrance not found', 400
	delete_status = r.hdel('spider_entrance', entrance)
	if delete_status == 0:
		return 'entrance delete fail', 400
	return 'success', 200

@app.route('/scrapyconfig/entrancelog', methods=['GET'])
def get_latest_log():
	entrance = request.args.get('entrance')
	if entrance is None:
		return 'entrance not found', 400
	log_dir = os.path.abspath(r'../configurable_spider/log')
	for root, dirs, files in os.walk(log_dir):
		for file_name in files:
			if file_name.startswith(entrance) and file_name.endswith('_latest.log'):
				with open(os.path.join(log_dir, file_name), 'r', encoding='utf-8') as f:
					log_str = f.read()
					return log_str, 200
	return 'No latest log.', 200



@app.route('/scrapyconfig/homepage')
def homepage():
	return render_template('configurator.html')

@app.route('/scrapyconfig/oldpage')
def oldpage():
	return render_template('table_config.html')

if __name__ == '__main__':
	app.jinja_env.auto_reload = True
	app.config['TEMPLATES_AUTO_RELOAD'] = True
	app.DEBUG = True
	app.run()
