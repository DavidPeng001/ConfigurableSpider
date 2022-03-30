import logging
import re
import sys
import chardet

from collections import defaultdict
from lxml.etree import tostring
from lxml.etree import tounicode
from lxml.html import document_fromstring, fragment_fromstring, HTMLParser
from lxml import html
from lxml.html.clean import Cleaner

log = logging.getLogger("htmlparser")

RE_ARTICLE_EXCLUDE = re.compile(r'combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|navbar|sidebar|sponsor|ad-break|agegate|pagination|pager|popup', re.I)
RE_ARTICLE_ALLOW = re.compile(r'and|article|body|column|main|shadow', re.I)
RE_ARTICLE_POSITIVE = re.compile(r'article|body|content|entry|hentry|main|page|pagination|post|text|blog|story|document|section|chapter', re.I)
RE_ARTICLE_NEGATIVE = re.compile(r'combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget', re.I)
RE_PARAGRAPH_FIX = re.compile(r'<(a|blockquote|dl|div|img|ol|p|pre|table|ul)', re.I)

def get_encoding(html: bytes) -> str:
	RE_ENCODING_HTML = re.compile(br'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)
	# eg: <meta charset="gb2312">
	RE_ENCODING_XML = re.compile(br'^<\?xml.*?encoding=["\']*(.+?)["\'>]')
	# eg: <?xml version="1.0" encoding="utf8">

	encoding = RE_ENCODING_HTML.findall(html)
	if not encoding:
		encoding = RE_ENCODING_XML.findall(html)
	if encoding:
		# test declared encoding
		try:
			html.decode(encoding[0].decode())
			# It worked!
			return encoding[0].decode()
			# XXX: allow more than one encoding
		except UnicodeDecodeError:
			pass

	# no declared encoding,  use chardet to judge encoding automatically according to html texts.
	text = re.sub(br'<[^>]+>', b'', html).strip()
	encoding = (chardet.detect(text)['encoding'] or 'utf-8') if len(text) < 10 else 'utf-8'
	return encoding


class HtmlParser:
	# TODO: add xpath parameter to select part of HTML
	def __init__(self, html, min_text_length = 25, retry_length = 250):
		"""
		:param html: str or bytes of the html content. bytes will be decoded automatically.
		:param min_text_length: set to a higher value for more precise detection of longer texts.
		:param retry_length: Set to a lower value for better detection of very small texts.
		"""

		self.min_text_length = min_text_length
		self.min_chinese_length = int(min_text_length/2)
		self.retry_length = retry_length
		if isinstance(html, str):
			self.html = html
			self.encoding = None
		else:
			self.encoding = get_encoding(html) or 'utf-8'
			self.html = html.decode(self.encoding, errors='replace')


	def parse(self, html):
		"""
		Parse and clean HTML, generate DOM structure, return ElementTree.
		"""
		utf8_parser = HTMLParser(encoding='utf-8')
		doc = document_fromstring(html.encode('utf-8', 'replace'), parser=utf8_parser)
		cleaner = Cleaner(scripts=True, javascript=True, comments=True, style=True, links=True, meta=False, frames=False, forms=False)
		doc = cleaner.clean_html(doc)
		# TODO: add make_links_absolute()
		return doc

	def _tags(self, node, *tag_names):
		"""
		Giving ElementTree and tags, traverse the tree, find and return all matched element node
		"""
		for tag_name in tag_names:
			for elem in node.findall('.//%s' % tag_name):
				yield elem

	def _css(self, elem):
		"""
		Return class and id of giving element
		"""
		for css in [elem.get('class', None), elem.get('id', None)]:
			if css:
				yield css

	def _insert_tag(self, parent, tag_name, loc):
		tag = fragment_fromstring('<%s/>' % tag_name)
		parent.insert(loc, tag)
		return tag

	def _get_clean_content(self, elem):
		return re.sub(r'\s+', ' ', elem.text_content() or '')


	def article(self):
		doc = self.parse(self.html)
		self.css_filter(doc)
		self.paragraph_clean(doc)
		scores = self.paragraph_score(doc)
		ranking = sorted(scores.items(), key=lambda x:x[1], reverse=True)
		typical_paragraph = dict(elem=ranking[0][0], score=ranking[0][1])
		res = self.paragraph_expand(scores, typical_paragraph)
		return self._get_clean_content(res)

	def css_filter(self, doc):
		"""
		filter css keyword
		"""
		for elem in self._tags(doc, '*'):
			for css in self._css(elem):
				if RE_ARTICLE_EXCLUDE.search(css) and not RE_ARTICLE_ALLOW.search(css) and elem.tag not in ['html', 'body']:
					elem.drop_tree()

	def paragraph_clean(self, doc):
		"""
		Transform all direct content texts to <p>
		HTML Example:
		<div class="article">            --(1)->     <p class="article">
			(div.text)                   --(2)->     <p> (div.text) </p>
			<tag1> (tag1.text) </tag1>
			(tag1.tail)                  --(3)->     <p> (tag1.tail) </p>
			<tag2> (tag2.text) </tag2>
			(tag2.tail)
		</div>
		"""
		for elem in self._tags(doc, 'div'):
			# (1) if child nodes aren't tags which may contain contents, <div> transform to <p>
			child_list = map(tostring, list(elem))
			child_html = str(b''.join(child_list))
			if not RE_PARAGRAPH_FIX.search(child_html):
				elem.tag = 'p'
			# (2) child node contain contents, div.text transform to <p> and transfer to child node.
			elif elem.text and elem.text.strip():
				p = self._insert_tag(elem, 'p', 0)
				p.text = elem.text
				elem.text = None
				# (3) tail text also transform to <p>
				for pos, child in list(enumerate(elem))[::-1]:
					if child.tail and child.tail.strip():
						p = self._insert_tag(elem, 'p', pos + 1)
						p.text = child.tail
						child.tail = None
					if child.tag == 'br':
						child.drop_tree()

	def paragraph_score(self, doc):
		"""
		score for every <p> & its parent node &its grandparent node.
		total score = (tag score + css score + content score ) * (1 - link density)
		"""
		scores = {}

		for elem in self._tags(doc, 'p', 'pre', 'td'):
			parent_node = elem.getparent()
			if parent_node is None:
				continue
			grand_parent_node = parent_node.getparent()

			content_text = self._get_clean_content(elem)
			content_text_length =len(content_text)
			content_unicode_length = len(content_text.encode())

			if content_unicode_length / content_text_length >= 1.4:
				# mostly Chinese
				if content_text_length < self.min_chinese_length:
					continue
				content_score = 1 + (content_text_length / 8) + (content_unicode_length / 8)
			else:
				# mostly English
				if content_text_length < self.min_text_length:
					continue  # text too short
				content_score = 1 + len(content_text.split()) + min(content_text_length / 100, 3)
			if elem.tag == 'pre':
				content_score = min(content_score, 35)

			if parent_node not in scores:
				scores[parent_node] = self.get_tag_score(parent_node) + self.get_css_score(parent_node) + content_score
			if grand_parent_node is not None and grand_parent_node not in scores:
				scores[grand_parent_node] = self.get_tag_score(grand_parent_node) + self.get_css_score(grand_parent_node) \
											+ content_score / 2.0     # half of grandchild node content score
			pass
		for elem in scores.keys():
			scores[elem] *= 1 - self.get_link_density(elem)

		return scores

	def paragraph_expand(self, scores, typical_paragraph):
		"""
		Typical paragraph can present the style of most article texts.
		Find its siblings node or style-likely node.
		"""
		score_threshold = max(typical_paragraph['score'] * 0.2, 10)    # best score / 5  (lower limit is 10)
		parent = typical_paragraph['elem'].getparent()
		siblings = parent.getchildren() if parent is not None else [typical_paragraph['elem']]

		res = fragment_fromstring("<div/>")
		for sibling in siblings:
			if sibling is typical_paragraph['elem']:
				res.append(sibling)
			elif sibling in scores and scores[sibling] >= score_threshold:
				# Append sibling nodes whose score is above score threshold
				res.append(sibling)
			elif sibling.tag == 'p':
					link_density = self.get_link_density(sibling)
					text_length = len(sibling.text or "")
					if text_length > 80 and link_density < 0.25:
						res.append(sibling)
					elif text_length <= 80 and link_density == 0:
						res.append(sibling)
		# TODO: judge grandfather level sibling
		return res


	def get_css_score(self, elem):
		score = 0
		for css in self._css(elem):
			if RE_ARTICLE_POSITIVE.search(css):
				score += 25
			elif RE_ARTICLE_NEGATIVE.search(css):
				score -= 25

		return score
	def get_tag_score(self, elem):
		score = 0
		tag = elem.tag.lower()
		if tag in ["div", "article"]:
			score += 5
		elif tag in ["pre", "td"]:
			score += 3
		elif tag in ["address", "ol", "ul", "dl", "dd", "dt", "li", "form", "aside"]:
			score -= 3
		elif tag in ["h1", "h2", "h3", "h4", "h5", "h6", "th", "header", "footer", "nav"]:
			score -= 5
		return score

	def get_link_density(self, elem):
		link_length = 0
		for href in self._tags(elem, 'a'):
			link_length += len(self._get_clean_content(href))
		#if len(elem.findall(".//div") or elem.findall(".//p")):
		#    link_length = link_length
		total_length = len(self._get_clean_content(elem))
		return float(link_length) / max(total_length, 1)

if __name__ == '__main__':
	from selenium.webdriver import Chrome
	from selenium.webdriver.chrome.options import Options
	# launcher for Java
	url = sys.argv[1]
	chrome_options = Options()
	chrome_options.add_argument('--headless')
	webdriver = Chrome(options=chrome_options)
	webdriver.get(url)
	html = webdriver.page_source
	webdriver.quit()
	res = HtmlParser(html).article()
	print(res)






