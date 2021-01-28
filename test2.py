import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

longest_file, max_tokens = '', 0
word_freqs = defaultdict(int)
tokenize_pattern = re.compile(r'[\w]{2,}')

def word_count(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Remove html
    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip()
              for line in lines for phrase in line.split("  "))

    text = '\n'.join(chunk for chunk in chunks if chunk)
    tokens = tokenize_pattern.findall(text)
    print(tokens)

    global max_tokens, longest_file
    for token in tokens:
        word_freqs[token.lower()] += 1

    # Check for new max tokens
    if len(tokens) > max_tokens:
        max_tokens = len(tokens)
        longest_file = url

word_count('https://www.informatics.uci.edu/files/pdf/InformaticsBrochure-March2018')