#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys

from flask.cli import cli


def main():
    os.environ.setdefault('FLASK_APP', 'saucerbot')
    os.environ.setdefault('FLASK_DEBUG', '1')

    args = sys.argv[1:]

    cli.main(args=args)


if __name__ == '__main__':
    main()
