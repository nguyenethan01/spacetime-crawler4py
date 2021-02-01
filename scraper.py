import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict
from nltk.corpus import stopwords
from utils.download import download
from protego import Protego

# For tokenising
tokenize_pattern = re.compile(r'[a-zA-Z0-9]{2,}')
cached_stopwords = set(stopwords.words('english'))

# For storing robots.txt parsers
robots = {}

# For duplicate detection
simhashes = {}
THRESHOLD = 0.9

# For answering questions 
visited = set()
longest_file, max_tokens = '', 0
word_freqs = defaultdict(int)
ics_subs = defaultdict(int)

def scraper(url, resp, config):
    # Ignore error status codes
    if resp.status < 200 or resp.status > 399:
        return []

    curr_word_freqs = word_count(resp, url)

    # Check for near dups
    simhash = compute_simhash(curr_word_freqs)
    if check_dup(url, simhash): return []

    links = extract_next_links(url, resp, config)
    return links

def extract_next_links(url, resp, config):
    next_links = set()

    # Ignore if no data
    if resp.raw_response:
        soup = BeautifulSoup(resp.raw_response.text, 'lxml')

        for link in soup.findAll('a', attrs={'href': True}):
            defragged = urldefrag(link['href'])[0]
            
            # Handle relative urls
            defragged = urljoin(url, defragged)

            # Fetch robots.txt if not found yet
            defragged_parsed = urlparse(defragged)
            fetch_robots(defragged_parsed, config, next_links)
            
            # Add to next_links if valid and robots.txt permits
            if defragged not in visited and is_valid(defragged) and \
                    (not robots[defragged_parsed.netloc] or robots[defragged_parsed.netloc].can_fetch(defragged, '*')):
                add_link(next_links, defragged)
 
    return list(next_links)

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

# Tokenises, gets frequencies
def word_count(resp, url):
    if not resp.raw_response:
        return {}
    
    html = resp.raw_response.text
    soup = BeautifulSoup(html, 'lxml')

    # Remove html noise
    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip()
                for line in lines for phrase in line.split("  "))

    text = '\n'.join(chunk for chunk in chunks if chunk)

    # Get tokens
    tokens = tokenize_pattern.findall(text)

    # Check for new max tokens
    global max_tokens, longest_file
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

# Adds the subdomain to the recorded list if a subdomain of ics.uci.edu
def add_subdomain(url):
    parsed = urlparse(url)
    out = re.match(r'(?P<subdomain>.*)\.ics\.uci\.edu$', parsed.netloc.lower())
    if out:
        ics_subs[out.group('subdomain')] += 1

# Adds the link to next_links, visited, and ics_subs if relevant
def add_link(next_links, defragged):
    next_links.add(defragged)
    visited.add(defragged)
    add_subdomain(defragged)

# ------------------------------------- Duplicate detection

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

    for _url, _hash in simhashes.items():
        if url == _url: continue

        curr_hash = simhash

        total = 0
        for i in range(32):
            if curr_hash & 1 == _hash & 1:
                total += 1
            curr_hash >>= 1
            _hash >>= 1
        if total / 32 >= THRESHOLD:
            return True
    
    simhashes[url] = simhash
    return False

# ---------------------------------- Robots.txt

def fetch_robots(url_parsed, config, next_links):
    if url_parsed.netloc not in robots:
        curr_robots = download(url_parsed.scheme + '://' + url_parsed.netloc + '/robots.txt', config)
        if 200 <= curr_robots.status < 400 and curr_robots.raw_response:
            robots[url_parsed.netloc] = Protego.parse(curr_robots.raw_response.text)

            # Get sites from sitemap
            check_sitemaps(url_parsed, config, next_links)
        else:
            robots[url_parsed.netloc] = False

def check_sitemaps(url_parsed, config, next_links):
    sitemaps = robots[url_parsed.netloc].sitemaps
    for sitemap in sitemaps:
        curr_sitemap = download(sitemap, config)
        if 200 <= curr_sitemap.status < 400 and curr_sitemap.raw_response:
            sitemap_soup = BeautifulSoup(curr_sitemap.raw_response.text, 'lxml')
            locs = sitemap_soup.find_all('loc')

            for loc in locs:
                loc_defragged = urldefrag(loc.text)[0]
                if loc_defragged not in visited and is_valid(loc_defragged):
                    add_link(next_links, loc_defragged)
    
    
# today.uci.edu/robots.txt is not accessible through cache, so manually add it
with open('today_robots.txt') as f:
    robots['today.uci.edu'] = Protego.parse(f.read())