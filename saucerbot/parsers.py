# -*- coding: utf-8 -*-

import abc
import requests
import typing
from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class Parser(abc.ABC):
    def __init__(self) -> None:
        super(Parser, self).__init__()

    @abc.abstractmethod
    def parse(self) -> typing.Iterable[typing.Dict[str, typing.Any]]:
        pass


class KimonoParser(Parser):
    base = ''
    fields: typing.List[typing.Tuple[str, str]] = []
    url = ''

    def __init__(self, *args) -> None:
        super(KimonoParser, self).__init__()
        self.args = args
        if not self.url:
            raise ValueError('Value for url required.')

        r = requests.get(self.url.format(*args))

        self.types: typing.Dict[str, typing.Any] = {}
        self.soup = BeautifulSoup(r.text, 'html.parser')

    def parse(self):
        """
        Parse the data from the html page associated with the given URL.
        :return: All the records
        :rtype: list
        """
        for row in self._do_initial_parse():
            yield self.post_process(row)

    def _do_initial_parse(self) -> typing.Iterator[typing.Dict[str, typing.Any]]:
        if not self.base:
            raise MissingBaseError()

        # Scrape the fields out of the html
        for row in self.soup.select(self.base):
            next_row = {}
            for field, selector in self.fields:
                columns = row.select(selector)

                if len(columns) == 0:
                    # Handle missing field
                    next_type = self.types.get(field)
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
                if field in self.types:
                    if self.types[field] != column.name:
                        raise RowMismatchError()

                self.types[field] = column.name

                if column.name == 'a':
                    next_row[field] = {
                        'text': column.text,
                        'href': column.attrs.get('href')
                    }
                elif column.name == 'img':
                    next_row[field] = column.attrs.get('src')
                else:
                    next_row[field] = column.text

            yield next_row

    def post_process(self, row: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        You may override this method to do any data post-processing.
        By default this will just return the original row.
        :param row: The list of data that was scraped
        :return: the transformed row
        :rtype: dict
        """
        return row


class NewArrivalsParser(KimonoParser):
    url = 'https://www.beerknurd.com/locations/nashville-flying-saucer'
    base = 'div.view-new-arrivals-block > div > table > tbody > tr'
    fields = [
        ('name', 'td.views-field-title'),
        ('date', 'td.views-field-created-1'),
    ]

    def post_process(self, row):
        row['name'] = row['name'].strip()
        row['date'] = row['date'].strip()

        return row


class BridgestoneEventsParser(KimonoParser):

    url = 'https://www.bridgestonearena.com/events'
    base = 'div#list > div > div.info.clearfix'
    fields = [
        ('name', 'h3 > a'),
        ('date', 'div.date')
    ]

    def post_process(self, row):
        row['name'] = row['name']['text'].strip()
        row['date'] = row['date'].strip()

        return row
