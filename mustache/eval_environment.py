
class EvalEnvironment(object):
	# TODO: check legality of expression
	def __init__(self, expression ,env):
		self.expression = expression
		self.env = env
	def run(self):
		env = self.env
		return eval(self.expression)