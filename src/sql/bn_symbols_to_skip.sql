with
    toDate('{}') as ds,
    toDate('{}') as de
select symbol
from raw_bn_1m_candle
where 1 = 1
  and date between ds and de
group by symbol
having de - min(toDate(time_open)) + 1 = uniq(toDate(time_open))