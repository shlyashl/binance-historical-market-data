from pyaml_env import parse_config

from src.tools import logger, ClickHouse
from src.binance import Benance


def main():
    config = parse_config('config.yml')

    ch = ClickHouse(**config['clickhouse'])

    bn_symbols_to_skip_query = ch.queries['bn_symbols_to_skip'].format(config['binance']['parse_date_start'],
                                                                       config['binance']['parse_date_end'])
    bn_symbols_to_skip = ch.select(bn_symbols_to_skip_query).symbol.to_list()

    job = Benance(ch, bn_symbols_to_skip, **config['binance'])
    job.execute_job()


if __name__ == '__main__':
    main()
