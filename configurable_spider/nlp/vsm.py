import jieba
import redis
from gensim import corpora, models, similarities


def get_weight_text(wieght_dict):
	weight_sum = 0
	for weight in wieght_dict.values():
		weight_sum += float(weight)
	res = ""
	for term, weight in wieght_dict.items():
		term_num = int(float(weight) / weight_sum * 100)
		term_str = (term + ' ') * term_num
		res += term_str

	return res

def vsm(document, weight_dict):
	conn = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, db=10)
	r = redis.Redis(connection_pool=conn)
	document_words = jieba.lcut(document.strip())
	words = [word for word in document_words if r.sismember('stop_words', word) == 0]
	words_list = [words, [], [], ["考试", "说明"]]

	# turn our tokenized documents into a id <-> term dictionary
	dictionary = corpora.Dictionary(words_list)
	# convert tokenized documents into a document-term matrix
	corpus = [dictionary.doc2bow(words) for words in words_list]
	tfidf = models.TfidfModel(corpus)
	corpus_tfidf = tfidf[corpus]

	vec_bow = dictionary.doc2bow(get_weight_text(weight_dict).split())
	vec_tfidf = tfidf[vec_bow]

	index = similarities.MatrixSimilarity(corpus_tfidf)
	sims = index[vec_tfidf]

	return list(sims)[0]


if __name__ == '__main__':
	weight_dict = {"考研": 0.2, "研究":0.7}
	score = vsm("暨南大学研究生考试招生简章", weight_dict)
	print(score)




