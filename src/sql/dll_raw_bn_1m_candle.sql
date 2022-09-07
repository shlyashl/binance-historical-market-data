create table raw_bn_1m_candle
(   symbol String,
    time_open DateTime,
    time_close DateTime,
    opening_price_in_usd Float64,
    highest_price_in_isd Float64,
    the_lowest_price_in_usd Float64,
    closing_price_in_usd Float64,
    volume_in_usd Float64,
    volume_in_coins Float64,
    volume_in_coins_when_taker_buy_coins Float64,
    volume_in_usd_when_taker_sell_coins Float64,
    transactions_per_minute UInt16,
    _version       DateTime materialized now(),
    date Date alias toDate(time_open)
)   engine = ReplacingMergeTree(_version)
        partition by toYYYYMM(time_open)
        order by (symbol, time_open)
