# -*- coding: utf-8 -*-

from typing import Any, Dict, Iterable, Iterator, List, Tuple

import requests
from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class Parser:
    base = ''
    fields: List[Tuple[str, str]] = []
    url = ''

    def __init__(self, *args: Any) -> None:
        super(Parser, self).__init__()
        self.args = args
        if not self.url:
            raise ValueError('Value for url required.')

        r = requests.get(self.url.format(*args))
        r.raise_for_status()

        self.types: Dict[str, Any] = {}
        self.soup = BeautifulSoup(r.text, 'html.parser')

    def parse(self) -> Iterable[Dict[str, Any]]:
        """
        Parse the data from the html page associated with the given URL.
        :return: All the records
        :rtype: Iterable
        """
        for row in self._do_initial_parse():
            yield self.post_process(row)

    def _process_row(self, row, field, selector) -> Any:
        columns = row.select(selector)

        if not columns:
            # Handle missing field
            next_type = self.types.get(field)
            if not next_type:
                # try to guess it
                next_type = selector.split(' > ')[-1].split(':')[0]

            if next_type:
                if next_type == 'a':
                    return {
                        'text': '',
                        'href': ''
                    }
                else:
                    return ''

            return None
        elif len(columns) > 1:
            raise RowMismatchError()

        # grab the first one
        column = columns[0]

        # Check to make sure it's the correct type
        if field in self.types and self.types[field] != column.name:
            raise RowMismatchError()

        self.types[field] = column.name

        if column.name == 'a':
            return {
                'text': column.text,
                'href': column.attrs.get('href')
            }
        elif column.name == 'img':
            return column.attrs.get('src')
        else:
            return column.text

    def _do_initial_parse(self) -> Iterator[Dict[str, Any]]:
        if not self.base:
            raise MissingBaseError()

        # Scrape the fields out of the html
        for row in self.soup.select(self.base):
            next_row: Dict[str, Any] = {}
            for field, selector in self.fields:
                next_field = self._process_row(row, field, selector)
                if next_field:
                    next_row[field] = next_field

            yield next_row

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        You may override this method to do any data post-processing.
        By default this will just return the original row.
        :param row: The list of data that was scraped
        :return: the transformed row
        :rtype: dict
        """
        # pylint: disable=no-self-use
        return row


class NewArrivalsParser(Parser):
    url = 'https://www.beerknurd.com/locations/{}-flying-saucer'
    base = 'div.view-new-arrivals-block > div > table > tbody > tr'
    fields = [
        ('name', 'td.views-field-title'),
        ('date', 'td.views-field-created-1'),
    ]

    def post_process(self, row):
        row['name'] = row['name'].strip()
        row['date'] = row['date'].strip()

        return row


class BridgestoneEventsParser(Parser):
    url = 'https://www.bridgestonearena.com/events'
    base = 'div#list > div > div.info.clearfix'
    fields = [
        ('name', 'h3 > a'),
        ('date', 'div.date'),
    ]

    def post_process(self, row):
        row['name'] = row['name']['text'].strip()
        row['date'] = row['date'].strip()

        return row
