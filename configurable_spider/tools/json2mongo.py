import pymongo

def json2mongo(db_name, col_name, json_file):
	client = pymongo.MongoClient('mongodb://localhost:27017/')
	database = client[db_name]
	collection = database[col_name]
	with open(json_file, 'r') as f:
		json_data = f.read()
	collection.insert_one(json_data)


if __name__ == '__main__':
	json2mongo('configurable_spider', 'SpiderConfig', r'')