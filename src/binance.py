# -*- coding: utf-8 -*-
from datetime import datetime, timezone
import traceback
from itertools import product
import json

from datetime import timedelta
import requests
import pandas as pd
import asyncio
import aiohttp

from src.tools import logger, try_again


class Binance:
    def __init__(self, ch_conn, symbols_to_skip=None, **kwargs):
        self._tickers_url = kwargs['api_tickers_url']
        self.ch_conn = ch_conn
        self.klines_url = kwargs['api_klines_url']
        self.date_start = datetime.strptime(kwargs['parse_date_start'], '%Y-%m-%d')
        self.date_end = datetime.strptime(kwargs['parse_date_end'], '%Y-%m-%d')
        self.symbols_to_skip = symbols_to_skip
        self.symbols = self._get_tickers()
        self.intervals = self._get_dt_intervals()
        self.tasks_description = [[e[0], *e[1]] for e in product(self.symbols, self.intervals)]
        self._ioloop = asyncio.get_event_loop()
        self._max_rps = asyncio.Semaphore(15)

    def _get_tickers(self) -> list:
        response = requests.get(url=self._tickers_url)
        assets_raw = json.loads(response.text)

        coin_symbols = [coin['symbol'] for coin in assets_raw
                        if coin['symbol'].endswith('USDT')
                        and not any(f in coin['symbol'] for f in ['BCHSVUSDT', 'UP', 'DOWN'] + self.symbols_to_skip)]

        logger.debug(f'{coin_symbols=}')
        return coin_symbols

    def _get_dt_intervals(self) -> list:
        starts = pd.date_range(self.date_start, self.date_end + timedelta(days=1), freq='12H')
        zipped_intervals = zip(starts[:-1], starts[1:])

        intervals = [[str(int(i[0].replace(tzinfo=timezone.utc).timestamp() * 1000)),
                      str(int(i[1].replace(tzinfo=timezone.utc).timestamp() * 1000) - 1000)] for i in zipped_intervals]

        logger.debug(f'{intervals=}')
        return intervals

    @try_again
    async def _get_candle_data(self, symbol: str, ts_start: str, ts_end: str):
        url = self.klines_url.format(symbol, ts_start, ts_end)

        async with aiohttp.ClientSession() as session:
            async with self._max_rps, session.get(url) as response:
                response_json = await response.json()
                await asyncio.sleep(0.1)

        assert response_json or response_json == [], f'Empty data: {url}'

        if not response_json:
            logger.warning(f'Recived empty response from binance: {url=}')

        data = []
        for candle in response_json:
            try:
                time_open = datetime.utcfromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            except:
                print(candle, '!!!!!')
                exit()
            time_close = datetime.utcfromtimestamp(candle[6] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            opening_price_in_usd = candle[1]
            highest_price_in_usd = candle[2]
            the_lowest_price_in_usd = candle[3]
            closing_price_in_usd = candle[4]
            volume_in_usd = candle[7]
            volume_in_coins = candle[5]
            volume_in_coins_when_taker_buy_coins = candle[9]
            volume_in_usd_when_taker_sell_coins = candle[10]
            transactions_per_minute = candle[8]

            data.append(
                [symbol, time_open, time_close, opening_price_in_usd, highest_price_in_usd, the_lowest_price_in_usd,
                 closing_price_in_usd, volume_in_usd, volume_in_coins, volume_in_coins_when_taker_buy_coins,
                 volume_in_usd_when_taker_sell_coins, transactions_per_minute])

        df = pd.DataFrame(
            data, columns=[
                'symbol', 'time_open', 'time_close', 'opening_price_in_usd', 'highest_price_in_usd',
                'the_lowest_price_in_usd', 'closing_price_in_usd', 'volume_in_usd', 'volume_in_coins',
                'volume_in_coins_when_taker_buy_coins', 'volume_in_usd_when_taker_sell_coins',
                'transactions_per_minute'])

        await self.ch_conn.insert(df)

        logger.info(f'Data inserted into for task {symbol=} {ts_start=} {ts_end=}')

    async def _tasks_loop(self):
        tasks = {asyncio.ensure_future(self._get_candle_data(*task)): task for task in self.tasks_description}
        pending = set(tasks.keys())

        num_times_called = 0
        while pending:
            finished, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_EXCEPTION)
            for task in finished:
                try:
                    task.result()
                except:
                    num_times_called += 1
                    logger.info("Unexpected error: {}".format(traceback.format_exc()))
                    logger.info(f'Err task: {tasks[task]}')
                    if num_times_called >= 100000:
                        self._ioloop.stop()

                    new_task = asyncio.ensure_future(self._get_candle_data(*tasks[task]))
                    tasks[new_task] = tasks[task]
                    pending.add(new_task)
        logger.info('Job done')

    def execute_job(self):
        return self._ioloop.run_until_complete(self._tasks_loop())

