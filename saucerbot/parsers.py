# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class Parser(object):

    def __init__(self):
        super(Parser, self).__init__()

    def parse(self):
        raise NotImplementedError()


class KimonoParser(Parser):
    """

    """
    base = ''
    fields = ()
    url = ''

    def __init__(self, *args):
        super(KimonoParser, self).__init__()
        self.args = args
        if not self.url:
            raise ValueError('Value for url required.')

        r = requests.get(self.url.format(*args))

        self.soup = BeautifulSoup(r.text, 'html.parser')

    def parse(self):
        """
        Parse the data from the html page associated with the given URL.
        :return: All the records
        :rtype: list
        """
        rows = []
        types = {}

        if not self.base:
            raise MissingBaseError()

        # Scrape the fields out of the html
        for row in self.soup.select(self.base):
            next_row = {}
            for field, selector in self.fields:
                columns = row.select(selector)

                if len(columns) == 0:
                    # Handle missing field
                    next_type = types.get(field)
                    if not next_type:
                        # try to guess it
                        next_type = selector.split(' > ')[-1].split(':')[0]
                    if next_type:
                        if next_type == 'a':
                            next_row[field] = {
                                'text': '',
                                'href': ''
                            }
                        else:
                            next_row[field] = ''
                    continue
                elif len(columns) > 1:
                    raise RowMismatchError()

                # grab the first one
                column = columns[0]

                # Check to make sure it's the correct type
                if field in types:
                    if types[field] != column.name:
                        raise RowMismatchError()

                types[field] = column.name

                if column.name == 'a':
                    next_row[field] = {
                        'text': column.text,
                        'href': column.attrs.get('href')
                    }
                elif column.name == 'img':
                    next_row[field] = column.attrs.get('src')
                else:
                    next_row[field] = column.text

            rows.append(next_row)

        # Scan through a second time in case the fields were not discernable the first time through
        for row in rows:
            missing = False
            for field, selector in self.fields:
                if field not in row:
                    missing = True
                    if types[field] == 'a':
                        row[field] = {
                            'text': '',
                            'href': ''
                        }
                    else:
                        row[field] = ''
            if not missing:
                # All the fields were intact, so we're done
                break

        return self.post_process(rows)

    def post_process(self, data):
        """
        You may override this method to do any data post-processing.
        By default this will just return the original list.
        :param data: The list of data that was scraped
        :return: the transformed data
        :rtype: list
        """
        return data


class NewArrivalsParser(KimonoParser):
    url = 'https://www.beerknurd.com/locations/nashville-flying-saucer'
    base = 'div.view-new-arrivals-block > div > table > tbody > tr'
    fields = (
        ('name',        'td.views-field-title'),
        ('date',        'td.views-field-created-1'),
    )

    def post_process(self, data):
        for item in data:
            item['name'] = item['name'].strip()
            item['date'] = item['date'].strip()

        return data
