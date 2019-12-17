# -*- coding: utf-8 -*-

from typing import Any, Dict, Iterable, Iterator, List, Tuple

import requests
from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class HtmlContentProvider:

    def __init__(self, url: str, *args: Any) -> None:
        self.url = url.format(*args)
        self.soup = None

    def get_content(self) -> BeautifulSoup:
        if not self.soup:
            r = requests.get(self.url)
            r.raise_for_status()
            self.soup = BeautifulSoup(r.text, 'html.parser')
        return self.soup


class Parser:
    base = ''
    fields: List[Tuple[str, str]] = []

    def __init__(self, provider: HtmlContentProvider) -> None:
        super(Parser, self).__init__()
        if not provider:
            raise ValueError('Value for provider required.')

        self.provider = provider
        self.types: Dict[str, Any] = {}

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
        for row in self.provider.get_content().select(self.base):
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

    @staticmethod
    def create_new_arrivals_provider(*args: Any) -> HtmlContentProvider:
        return HtmlContentProvider(NewArrivalsParser.url.format(*args))


class BridgestoneEventsParser(Parser):
    base = 'div#list > div > div.info.clearfix'
    fields = [
        ('link', 'h3 > a'),
        ('date', 'div.date'),
    ]

    def post_process(self, row):
        result = {
            'details': row['link']['href'],
            'name': row['link']['text'].strip(),
            'date': row['date'].strip()
        }
        return result


class BridgestoneEventTimeParser(Parser):
    base = "div#content > div > div#column_1 > div.leftColumn > div.event_showings " \
           "> ul.list.clearfix > li.listItem"
    fields = [
        ("time", "div.flex-wrap > div.border-wrap > div.date > div.cal > span.time-stamp")
    ]

    def post_process(self, row):
        row['time'] = row['time'].strip()
        return row

    @staticmethod
    def create_event_time_provider(event: Dict[str, Any]) -> HtmlContentProvider:
        return HtmlContentProvider(event['details'])
