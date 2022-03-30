import redis

conn = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, db=10)
r = redis.Redis(connection_pool=conn)

with open('ChineseStopWords.txt', 'r', encoding='utf-8') as f:
	content = f.read()
	words = content.split('\n')
for word in words:
	r.sadd('stop_words', word)
print('Redis importing finished')