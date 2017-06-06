from requests_futures.sessions import FuturesSession
from concurrent.futures import TimeoutError
from requests.adapters import HTTPAdapter
from requests import exceptions as rze
from parsel import Selector
from pprint import pprint
from requests import (
    Session,
    Request
)
import logging
import hashlib
import regex
import time
import yaml
import sys
import os


class ObjectStore(dict):

    """Provides dictionary with values also accessible by attribute

    """

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class PhilosophyCrawl(object):

    def __init__(self, config):
        self._session = None
        self._adapter = None
        self.holy_grail_count = 0
        self.cyclic_count = 0
        self.dead_end_count = 0
        self.visited = {}
        self.depth_dict = {}
        self.url_depth_map = {}
        self.config = ObjectStore(config)
        self.logger = self._get_logger(__file__,
                                       self.config.log_file
                                       ) if self.config.log_to_file \
            else self._get_logger(__file__)

    def _get_logger(self, filename, log_file=None):
        logger = logging.getLogger(filename)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel = logging.FileHandler(log_file) if log_file else \
            logging.StreamHandler(sys.stdout)
        channel.setLevel(logging.DEBUG)
        channel.setFormatter(formatter)
        logger.addHandler(channel)

        return logger

    def _remove_select_parentheses(self, html_content):
        paren_count = 0
        bracket_count = 0
        cleaned_string = ""
        for c in html_content:
            if c == '<':
                bracket_count += 1
            elif c == '>':
                bracket_count -= 1
            elif c == '(' and bracket_count == 0:
                paren_count += 1
            elif c == ')' and bracket_count == 0:
                paren_count -= 1
                continue
            if paren_count == 0:
                cleaned_string += c
        return cleaned_string

    def _sanitize(self, html_content):
        sanitized_html_content = regex.sub(
            self.config.italic_pattern, '', html_content)
        return self._remove_select_parentheses(sanitized_html_content)

    def _get_hashed(self, word):
        """Get a 6-character hash

        """
        h = hashlib.sha256(word)

        return h.digest().encode('base64')[:6]

    def _prepare_request(self, url):
        """Prepped request

        """
        return self.session.prepare_request(Request('GET',  url))

    def _scrape(self, url):
        """Scrape the url content

        """
        resp = self.session.get(url)
        try:
            response = resp.result(self.config.timeout)
        except TimeoutError:
            self.logger.debug(
                'Skipping {} because of timeout error'.format(url))
            return

        if response.status_code != 200:
            self.logger.debug(
                'Bad status code. Skipping {}'.format(url))

            return

        url, content = response.url, response.content.decode('utf8')

        if self.status == self.config.begin_status:
            if url in self.visited:
                return

            self.parent_url = response.url
            self.depth = 0
            self.visited[self.parent_url] = {}

        self._parse(url, content)

    def _get_next_url(self, html_content):
        """Get the next url from the html content

        """
        next_url = None
        sanitized_html_content = self._sanitize(html_content)

        next_url_match = regex.search(
            self.config.href_pattern, sanitized_html_content)
        if next_url_match:
            next_url = next_url_match.group(0).split('#')[0]

        return next_url

    def _parse(self, current_url, content):
        """Parse the html content and recurse if and when needed

        """
        hashed_current_url = self._get_hashed(current_url)

        html_paragraphs = Selector(text=content).xpath(
            self.config.paragraph_pattern).extract()

        next_url = None
        for html_paragraph_content in html_paragraphs:
            next_url = self._get_next_url(html_paragraph_content)
            if next_url:
                break

        if not next_url:
            html_list_content = ''.join(Selector(text=content).xpath(
                self.config.list_pattern).extract())
            next_url = self._get_next_url(html_list_content)

        if not next_url:
            self.depth += 1
            self.dead_end_count += 1
            self.status = self.config.dead_end_status

            return

        next_url = ''.join((self.config.base_url, next_url))
        hashed_next_url = self._get_hashed(next_url)

        # if a page links to another page in its path or to itself we have
        # found a cycle
        if next_url in self.visited[
                self.parent_url] or hashed_next_url == \
                hashed_current_url:
            self.depth = -1
            self.cyclic_count += 1
            self.status = self.config.cyclic_status

            return

        # if the next page is philosophy there is no need to request it - it
        # marks the end of our search - the holy grail
        if next_url == self.holy_grail:
            # we are at the end of our search - report the depth of the root
            # page from the philosophy page
            self.depth += 1
            self.visited[
                self.parent_url][current_url] = self.depth
            self.holy_grail_count += 1
            self.depth += 1
            self.status = self.config.success_status

            return

        if self.parent_url != current_url:
            self.depth += 1
            self.visited[
                self.parent_url][current_url] = self.depth

        if self.config.optimized and next_url in self.url_depth_map:
            self.depth += self.url_depth_map[next_url]
            self.holy_grail_count += 1
            self.status = self.config.success_status

            return

        self.status = self.config.in_progress_status
        self._scrape(next_url)

    def _write_to_file(self, content, file_name, is_list=False, append=False):
        """Write to external file

        """
        mode = 'a' if append else 'w'
        with open(file_name, mode) as f:
            if is_list:
                for line in content:
                    f.write(line)
            else:
                f.write(content)

    def _setup_status_logs(self):
        self.status_logs = {
            self.config.success_status: 'crawl of {0} lead to philosophy '
            'after {1} hops'.format(self.parent_url, self.depth),
            self.config.dead_end_status: 'crawl of {0} lead to a dead end '
            .format(self.parent_url),
            self.config.cyclic_status: 'crawl of {0} lead to a cycle '
            .format(self.parent_url, self.depth),
        }

    def _crawl(self):
        while self.holy_grail_count < self.config.article_limit:
            self.status = self.config.begin_status
            self._scrape(self.config.random_article_url)
            self._setup_status_logs()
            self.logger.debug(self.status_logs[self.status])

            self.visited[
                self.parent_url]['depth'] = self.depth

            if self.config.optimized:
                self.url_depth_map[self.parent_url] = self.depth
                if self.depth > 1:
                    self.url_depth_map.update(dict([(key, self.depth - value
                                                     ) for key,
                                                    value in self.visited[
                        self.parent_url].iteritems()]))

            if self.depth > 1:
                try:
                    self.depth_dict[self.depth] += 1
                except KeyError:
                    self.depth_dict[self.depth] = 1

        total_count = self.holy_grail_count + \
            self.dead_end_count + self.cyclic_count
        self.percentage_reached_philosophy = round(float(
            self.holy_grail_count)/total_count * 100, 2)

    def crawl(self):
        self._crawl()

        self.logger.debug(
            'percentage pages leading to philosophy - {0}'.format(
                self.percentage_reached_philosophy))
        self.logger.debug(
            'path length distribution of {0} pages - {1}'.format(
                self.config.article_limit, self.depth_dict))

        if not self.config.optimized:
            self.logger.debug('to reduce the number of http requests '
                              'enable the `optimized` flag in '
                              'config.yaml file')
        else:
            self.logger.debug('this run is already optimized to '
                              'reduce the number of http requests')

        if self.config.print_trail:
            pprint(self.visited)
            if self.config.optimized:
                pprint(self.url_depth_map)

    @property
    def holy_grail(self):
        """A funny name for the philosophy page url

        """
        return ''.join((self.config.base_url, self.config.final_node))

    @property
    def adapter(self):
        """Transport Adapter

        """
        if not self._adapter:
            self._adapter = HTTPAdapter(max_retries=self.config.max_retries)

        return self._adapter

    @property
    def session(self):
        """Persistent HTTP Connection

        """
        if not self._session:
            self._session = FuturesSession()
            self._session.mount(self.config.session_mount_url, self.adapter)

        return self._session

    @property
    def hashed_parent_url(self):
        """6-character Hashed URL

        """
        return self._get_hashed(self.parent_url)


def timefunc(f):
    def f_timer(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print 'Philosophy Crawler', 'took', round(end - start, 2), 'secs'
        return result
    return f_timer


@timefunc
def main():
    config_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'data', 'config.yaml'))

    with open(config_file, 'r') as f:
        config = yaml.load(f)

    config['log_file'] = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'data', config['log_file_name']))

    PhilosophyCrawl(config).crawl()

    if config['log_to_file']:
        print 'log file available here: {0}'.format(config['log_file'])

if __name__ == '__main__':
    main()
