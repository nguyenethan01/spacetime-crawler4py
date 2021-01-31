from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
import scraper


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)

    f = open('results.txt', 'w')
    f.write(f'1) {len(scraper.visited)}\n')
    f.write(f'2) {scraper.longest_file}: {scraper.max_tokens}\n')
    f.write(f'4) {scraper.ics_subs}')
    f.close()
    
    f = open('wordfreqs.txt', 'w')
    for item in sorted(scraper.word_freqs.items(), reverse=True, key=lambda x: x[1]):
        f.write(f'{item}\n')
    f.close()

    f = open('visited.txt', 'w')
    f.write(f'{scraper.visited}')
    f.close()