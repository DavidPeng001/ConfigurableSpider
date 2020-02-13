import scrapy
import pymongo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class ConfigLoad(scrapy.Spider):
	def __init__(self, entry_name, *args, **kwargs):
		super(ConfigLoad, self).__init__(*args, **kwargs)

		self.client = pymongo.MongoClient('mongodb://localhost:27017/')
		self.database = self.client['configurable_spider']
		self.config_col = self.database['SpiderConfig']
		self.entry_dict = self.config_col.find_one({'name': entry_name})
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--disable-gpu')
		self.driver = webdriver.Chrome(chrome_options=chrome_options)

	def start_requests(self):
		name = self.entry_dict['header']['model_name']
		


