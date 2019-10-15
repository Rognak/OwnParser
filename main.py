import requests
import re
from bs4 import BeautifulSoup
from config import *
import sys
import os


class Parser():
    """
    This class is responsible for parsing and preparing html data.
    It wraps an bs4 object and cleans it by given strategy.
    -------------
    PUBLIC METHODS:
    main_content(density, soup, force) -> main function
    get_html(url) -> get raw html after preprocessing

    PRIVATE METHODS:
    preprocess(html) -> html cleaning with regexp
    calc_depth(node) -> calculates depth of each node at the current tree level
    calc_density(nodes) -> saving calc_depth results as dict
    """

    def __init__(self, config):
        # setting the configuration
        self.config = config

    def get_html(self, url):
        """
        [PUBLIC]
        This function makes a request by given url and preprocess the data
        -----------
        inputs:
           url: string

        returns:
           html: string
        """

        # request and preprocessing
        with requests.Session() as session:
            session.headers = {'User-Agent': 'Mozilla/5.0'}
            request = session.get(url)
            html = self._prepocess(request.text)

        return html

    def _prepocess(self, html):
        """
        [PRIVATE]
        This function is for preprocessing purposes. It uses regexp mechanism for preparing html.
        ------------
           inputs:
              html: string

           returns:
              html: string
        """

        # applying regexp patterns from config
        patterns = [re.compile(p) for p in self.config.pre_processing]

        for pattern in patterns:
            html = re.subn(pattern, '', html)[0]

        return html

    def _calc_depth(self, node):
        """
        [PRIVATE]
        This function calculates the density (depth) of each node at the level
        -----------
           inputs:
              node: bs4 node

           returns:
              depth: list or null
        """

        # depth calculating
        if hasattr(node, "contents") and node.contents:
            return max([self._calc_depth(child) for child in node.contents]) + 1
        else:
            return 0

    def _calc_density(self, nodes):
        """
        [PRIVATE]
        This function calculates the density (depth) of each node at the level
        -------------
            inputs:
            nodes: bs4 node

            :returns
            node_density: dict
        """

        # node density dict
        node_density = {}

        # main loop
        for node in nodes:
            density = self._calc_depth(node)
            node_density.update({node: density})

        return node_density

    def main_content(self, density=None, soup=None, forced=False):
        """
        [PUBLIC]
        This is the class main function. The algorithm recursively goes through the nodes
         and removes those branches that are less than a certain coefficient, calculated depending on a given strategy
         --------------
         inputs:
            density: dict -> calculated from private self-titled function
            soup: bs4 object -> BeatifullSoup parser instance
            forced: bool -> if True, watching the <p> tag intensely

        returns:
            soup: bs4 object -> after all processing
        """

        # strategy from config
        strategy = self.config.STRATEGY
        coef = self.config.CUSTOM_COEFF

        # entry point of recursive func
        if density is None:
            # get children of root (1)
            children = soup.find_all(True, recursive=False)
            # density calculation  (2)
            density = self._calc_density(children)
            self.main_content(density=density, soup=soup, forced=forced)

        if strategy is not None:

            for node in density.keys():

                # repeating (1) and (2)
                childs = node.find_all(True, recursive=False)
                density = self._calc_density(childs)

                # coefficient calculation by given strategy
                if strategy == 'AVG':

                    # preventing divizion by zero
                    if len(density.values()) == 0:
                        continue
                    else:
                        avg = sum(density.values()) / len(density.values())

                elif strategy == 'CUSTOM':
                    avg = sum(density.values()) * coef

                # preventing "dict size changed" error
                keys = list(density.keys())

                # main loop
                for node in keys:

                    # preventing <p> and <h> tags deleting (don't watching depth itself)
                    if node.name == 'p' or node.name == 'h1' or node.name == 'h2':
                        continue

                    if node.h1:
                        continue

                    # don't dele\te <p> tags if node has at least 3 tags
                    if forced:
                        if len(node.find_all('p')) > 3:
                            continue

                    # node deleting
                    if density[node] < avg:
                        node.decompose()

                # go through recursion
                for node in density.keys():
                    self.main_content(density, soup=soup, forced=forced)

        return soup


class Formatter(Config):
    """
    This class represents a simple text formatter. It formats text by given length and writes to file
    ----------
    PUBLIC METHODS:
    prepare_text(soup, max_length) -> post-processing
    write_file(text) -> creates dirs and file

    PRIVATE METHODS:
    domain_name(url) -> extracts domain name
    get_url(urls, domain) -> puts url's into brackets []
    add_urls(text, prepared_urls) -> add's prepared urls into raw html text
    """

    def __init__(self, domain):
        # setting full url
        self.domain = domain

    def _domain_name(self, url):
        """
        [PRIVATE]
        This function extracts domain name from url
          -----------
          inputs:
              url: string

          returns:
              url: string
        """
        # get short domain name
        return re.match(r'http(s)?://', url).group() + url.split("//")[-1].split("/")[0]


    def _get_urls(self, urls, domain):
        """
        [PRIVATE]
        This function gets urls from html and puts them into brackets
        ---------
        inputs:
            urls: list -> list of urls in the page
            domain: string

        returns:
           r_urls: dict -> full-url: description
        """

        # defining the dict
        r_urls = {}

        # get short domain name
        domain = self._domain_name(domain)

        # putting into brackets
        for url in urls:
            if ("http" or "htpps") not in url['href']:
                href = '[' + domain + url['href'] + ']'
                r_urls.update({href: url.text})
            else:
                href = '[' + url['href'] + ']'
                r_urls.update({href: url.text})

        return r_urls

    def _add_urls(self, text, prepared_urls):
        """
        [PRIVATE]
        This function adds prepared urls into raw html text
        -----------
        inputs:
           text: string -> html text
           prepared_urls: dict -> urls after _get_urls()

        returns:
           text: string -> text with urls
        """

        for url in prepared_urls.keys():
            text = re.sub(prepared_urls[url], prepared_urls[url] + ' ' + url, text)
        return text

    def prepare_text(self, soup, max_length=Config.MAX_LENGTH):
        """
        [PUBLIC]
        This is post-processing function. It clears html of extra indentation, tabs and etc. After that it edits
        text by given length.
        -----------
           inputs:
              soup: bs4 object -> instance after pre-processing.
              max_length: int -> max row's length

           returns:
              new_string: string -> write ready text
        """

        # get all paragraphs and urls
        paragr = soup.find_all('p')
        urls = soup.find_all('a')

        # html post-processing
        string = soup.text
        string = string.replace('\n', '')
        string = string.strip()
        string = string.replace(r'\s+', ' ')

        # separating paragraph's
        for p in paragr:
            if p.text == '':
                continue
            string = string.replace(p.text.strip(), '\n' + p.text.strip() + '\n')

        # get and add urls to text
        prepared_urls = self._get_urls(urls, self.domain)
        text_with_urls = self._add_urls(string, prepared_urls)

        # main regexp
        sp2 = re.findall(r"(\[(https?://[^\s]+)\]|[\w]+|[\s.,!?;\()-])", text_with_urls)

        length = 1
        new_string = ''

        # text edit by given length
        for word in sp2:
            w = word[0]
            if length == 1:
                w = word[0].lstrip()
            length += len(word[0])

            if w == '\n':
                new_string += '\n'
                length = 1

            if length > max_length:
                new_string += '\n'
                new_string += w
                length = len(w) + 1

            elif length == max_length:
                new_string += w + '\n'
                length = 1

            else:
                new_string += w

        return new_string.replace('\n\n\n', '\n')

    def write_file(self, text):
        """
        [PUBLIC]
        This function creates dir's and writes text to file after post-processing
        -------------
        inputs:
           text: string -> text after post-processing
        """

        # auto-generating file path
        file_name = re.sub(r"http(s)?://(www\.)?", '', self.domain)
        file_name = re.sub(r'.(s)?html|/$', '', file_name)

        # get dir from string
        dir = os.path.dirname(file_name)

        # create directory if it does not exist
        if not os.path.exists(dir):
            os.makedirs(dir)

        # writing to file
        with open(file_name + '.txt', 'w') as f:
            f.write(text)


if __name__ == '__main__':

    # args reading (or waiting for user input otherwise)
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input('Please, enter url: ')

    # defining parser
    parser = Parser(config=Config)

    # get html
    html = parser.get_html(url)

    # defining soup object
    soup = BeautifulSoup(html, 'lxml')

    # pre-processed soup
    clean_soup = parser.main_content(soup=soup, forced=True)

    # defining the formatter
    formatter = Formatter(domain=url)

    # post-processed text
    clean_text = formatter.prepare_text(clean_soup)

    # writing to file
    formatter.write_file(clean_text)
