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

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) and \
            (re.match(r".*\.(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc.lower()) or re.match(
                r"today.uci.edu/department/information_computer_sciences(/|$)", parsed.netloc.lower() + parsed.path.lower()))

    except TypeError:
        print("TypeError for ", parsed)
        raise
simhashes = {'a': 674161246, 'b': 674161246}
def check_dup(url):
    simhash = simhashes[url]
    print(simhash)

    for _url, _hash in simhashes.items():
        if url == _url: continue

        curr_hash = simhash

        total = 0
        for i in range(32):
            print(curr_hash, _hash)
            print(curr_hash & 1 == _hash & 1)
            if curr_hash & 1 == _hash & 1:
                total += 1
            curr_hash >>= 1
            _hash >>= 1
        print(_url, total, total / 32)
        if total / 32 >= 0.9:
            return True
    
    return False

print(check_dup('b'))