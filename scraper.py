import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

visited = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    numWords = word_count(resp)
    print(len(visited))
    return links

def extract_next_links(url, resp):
    nextLinks = set()

    if resp.raw_response:
        soup = BeautifulSoup(resp.raw_response.text, 'lxml')
        for link in soup.findAll('a', attrs={'href': re.compile(r'^https?://')}):
            defragged = link['href'].split('#')[0]

            if defragged not in visited and is_valid(defragged):
                nextLinks.add(defragged)
                visited.add(defragged)

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
    (re.match(r".*\.(ics|cs|informatics|stat)\.uci\.edu$",parsed.netloc.lower()) or re.match(r"today.uci.edu/department/information_computer_sciences(/|$)", parsed.netloc.lower() + parsed.path.lower()))
    
  except TypeError:
    print ("TypeError for ", parsed)
    raise

def word_count(resp):
    if resp.raw_response: # TODO: no raw_response for today.uci.edu...
        html = resp.raw_response.text
        soup = BeautifulSoup(resp.raw_response.text, 'lxml')

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        #print(text)
