import os
import pkg_resources
from io import BytesIO
import sys

from dotenv import load_dotenv
from pyaml_env import parse_config

from src.tools import ClickHouse
from src.binance import Binance


def main(parse_date_start: str = None, parse_date_end: str = None):
    load_dotenv(pkg_resources.resource_filename(__name__, '/.env'))
    config = parse_config(pkg_resources.resource_filename(__name__, '/config.yml'))

    if parse_date_start and parse_date_end:
        config['binance']['parse_date_start'] = parse_date_start
        config['binance']['parse_date_end'] = parse_date_end

    ch = ClickHouse(**config['clickhouse'])

    bn_symbols_to_skip_query = ch.queries['bn_symbols_to_skip'].format(
        config['binance']['parse_date_start'],
        config['binance']['parse_date_end'])

    bn_symbols_to_skip = ch.select(bn_symbols_to_skip_query).symbol.to_list()

    job = Binance(ch, bn_symbols_to_skip, **config['binance'])
    job.execute_job()


if __name__ == '__main__':
    main('2022-12-27', '2022-12-27')
