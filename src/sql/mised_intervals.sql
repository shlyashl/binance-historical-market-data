select  symbol,
        toUnixTimestamp(pocket) * 1000 as time_start,
        toUnixTimestamp(
            pocket + interval 12 hour - interval 1 second
        ) * 1000 as end_time
from
    (
         with
             min(toDate(time_open)) as min_time,
             max(toDate(time_open)) as max_time,
             (max_time - min_time + 1) * 2 as days
         select
             symbol,
             arrayJoin(
                     arrayMap(
                             x -> min_time + interval 12 * x hour,
                             range(toUInt16(days))
                         )
                 ) as pocket
         from raw_bn_1m_candle
         group by symbol
    ) as intervals
    any left join
        (
            select symbol,
                   toStartOfInterval(time_open, interval 12 hour) pocket,
                   count() as cnt
            from raw_bn_1m_candle
            group by symbol, pocket
            order by symbol, pocket
        ) as data using(pocket, symbol)
where cnt = 0
order by symbol, pocket