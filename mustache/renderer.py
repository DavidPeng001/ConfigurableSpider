import re

from mustache.eval_environment import EvalEnvironment

EXPRESSION_RE = re.compile(r'{{(.+?)}}')
PATH_RE = re.compile(r'[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*')


def dict2obj(origin_dict):
	if not isinstance(origin_dict, dict):
		return origin_dict

	dict_obj = Dictionary()
	for key, value in origin_dict.items():
		dict_obj[key] = dict2obj(value)

	return dict_obj




class Renderer(object):
	def __init__(self, manager_dict=None):
		self.manager_dict = manager_dict if manager_dict is not None else dict()
		self._update()

	def add(self, name, value):
		if type(value) == dict:
			self.manager_dict[name] = value
			self._update()
		elif isinstance(value, Dictionary):
			self.manager.__setattr__(name, value)
		else:
			raise TypeError

	def render(self, string):
		repl_list = []
		span_list = []
		for expression in re.finditer(EXPRESSION_RE, string):
			exp = self._path_transfer(expression.groups()[0])
			try:
				result = EvalEnvironment(exp, self.manager).run()
			except Exception:
				raise ExpressionError(expression.groups())
			span = expression.span()
			if not isinstance(result, str):
				if span[1] - span[0] == len(string):
					return result
				else:
					raise ConcatenateError(result)
			else:
				repl_list.append(result)
				span_list.append((span[0], span[1]))

		return self._span_replace(string, repl_list, span_list)

	def render_all(self, strings):
		return [self.render(string) for string in list(strings)]


	def _path_transfer(self, expression):
		"""
		Find dict paths in mustache expression and transfer them executable string.
		"""
		repl_list = []
		span_list = []
		for path in re.finditer(PATH_RE, expression):

			repl_list.append(f'env.{path.group()}')
			span_list.append(path.span())
		return self._span_replace(expression, repl_list, span_list)


	def _span_replace(self, string, repl_list, span_list):
		for i, span in enumerate(span_list[::-1]):
			front_part = string[:span[0]]
			after_part = string[span[1]:]
			string = front_part + repl_list[~i] + after_part
		return string

	def _update(self):
		self.manager = dict2obj(self.manager_dict)


class Dictionary(dict):
	__setattr__ = dict.__setitem__
	__getattr__ = dict.__getitem__


class ExpressionError(Exception):
	def __init__(self, expression):
		self.expression = expression

	def __str__(self):
		return f'{self.expression} cannot be operated correctly'

class ConcatenateError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return f'{self.value} is not str. So it cannot be concatenated with string or other expression'

if __name__ == '__main__':
	test = {
		'key1': 'value1',
		'key2': 'value2',
		'key3': {
			'key4': 'value4',
			'key5': {
				'key6': ['a', 'b', 'v']
			}
		}
	}
	d = dict2obj(test)
	t = d.key3.key5
	t.setdefault('key7', [])

	exit(0)
	r = Renderer()
	r.add('test', test)
	res = r.render('{{test.key3.key5.key6[0]}}')
	print(res)









	# def _update(self, env_dict):
	# 	self.d_dict = dict()
	# 	self.s_dict = self._iterate(env_dict)
	#
	# def _iterate(self, s_dict):
	# 	for key, value in s_dict.items():
	# 		if isinstance(value, Dict):
	# 			s_dict[key] = self._iterate(value)
	# 		else:
	# 			s_dict[key] = self._counter
	# 			self.d_dict[self._counter] = value
	# 			self._counter += 1
	# 	return s_dict
