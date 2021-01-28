from collections import defaultdict

class Results():
	instance = None

	def __init__(self):
		self.longest_file, self.max_tokens = '', 0
		self.word_freqs = defaultdict(int)

	@staticmethod
	def get_instance(self):
		if not instance:
			instance = Results()

		return singleton