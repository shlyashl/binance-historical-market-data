from pyaml_env import parse_config

from src.tools import ClickHouse
from src.binance import Binance


def main():
    config = parse_config('config.yml')

    ch = ClickHouse(**config['clickhouse'])

    bn_symbols_to_skip_query = ch.queries['bn_symbols_to_skip'].format(config['binance']['parse_date_start'],
                                                                       config['binance']['parse_date_end'])
    # bn_symbols_to_skip = ch.select(bn_symbols_to_skip_query).symbol.to_list()

    job = Binance(ch, **config['binance'])
    job.execute_job()


if __name__ == '__main__':
    main()
