import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict
from nltk.corpus import stopwords
# from results import Results

tokenize_pattern = re.compile(r'[a-zA-Z0-9]{2,}')
cached_stopwords = set(stopwords.words('english'))

visited = set()
simhashes = {}
THRESHOLD = 0.9

longest_file, max_tokens = '', 0
word_freqs = defaultdict(int)
ics_subs = defaultdict(int)

def scraper(url, resp):
    # Ignore error status codes
    if resp.status < 200 or resp.status > 399:
        return []

    curr_word_freqs = word_count(resp, url)

    # Check for near dups
    simhash = compute_simhash(curr_word_freqs)
    if check_dup(url, simhash): return []
    # print(simhashes[url])

    links = extract_next_links(url, resp)
    # print(len(visited))
    # print('\n', sorted(word_freqs.items(), reverse=True, key=lambda x: x[1])[:10], '\n')
    # print(ics_subs)
    return links

def extract_next_links(url, resp):
    nextLinks = set()

    # Ignore if no data
    if resp.raw_response:
        soup = BeautifulSoup(resp.raw_response.text, 'lxml')
        for link in soup.findAll('a', attrs={'href': True}):
            defragged = urldefrag(link['href'])[0]

            # Handle relative urls
            defragged = urljoin(url, defragged)

            if defragged not in visited and is_valid(defragged):
                nextLinks.add(defragged)
                visited.add(defragged)
                add_subdomain(defragged)

    return list(nextLinks)

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


def word_count(resp, url):
    if resp.raw_response:  # TODO: no raw_response for today.uci.edu...
        html = resp.raw_response.text
        soup = BeautifulSoup(html, 'lxml')

        # Remove html
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip()
                  for line in lines for phrase in line.split("  "))

        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Get tokens
        tokens = tokenize_pattern.findall(text)

        global max_tokens, longest_file
        # Check for new max tokens
        if len(tokens) > max_tokens:
            max_tokens = len(tokens)
            longest_file = url
            
        # Get word frequencies
        curr_word_freqs = defaultdict(int)
        for token in tokens:
            curr_word_freqs[token.lower()] += 1
            if token.lower() not in cached_stopwords:
                word_freqs[token.lower()] += 1
        
        return curr_word_freqs
    
    return {}

def add_subdomain(url):
    parsed = urlparse(url)
    out = re.match(r'(?P<subdomain>.*)\.ics\.uci\.edu$', parsed.netloc.lower())
    if out:
        ics_subs[out.group('subdomain')] += 1

def compute_simhash(word_freqs):
    token_hashes = {token: hash(token) for token in word_freqs}
    vec = [0] * 32
    
    for token, _hash in token_hashes.items():
        for i in range(len(vec)-1, -1, -1):
            # Add 1 if right-most bit is 1, subtract 1 if 0
            right = _hash & 1
            vec[i] += 1 if right else -1
            _hash >>= 1
    
    fingerprint = 0
    for bit in vec:
        if bit > 0:
            fingerprint = (fingerprint << 1) | 1
        else:
            fingerprint <<= 1
    
    return fingerprint

def check_dup(url, simhash):
    # print(simhash)

    for _url, _hash in simhashes.items():
        if url == _url: continue

        curr_hash = simhash

        total = 0
        for i in range(32):
            if curr_hash & 1 == _hash & 1:
                total += 1
            curr_hash >>= 1
            _hash >>= 1
        # print(_url, total / 32)
        if total / 32 >= THRESHOLD:
            return True
    
    simhashes[url] = simhash
    return False
    