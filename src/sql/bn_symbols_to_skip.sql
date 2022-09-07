with
    toDate('{}') as ds,
    toDate('{}') as de,
    de - ds as days_in_set
select symbol
from raw_bn_1m_candle
where 1 = 1
  and date between ds and de
group by symbol
having (days_in_set + 1) - uniq(date) = 0
