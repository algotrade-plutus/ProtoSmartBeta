"""
SQL query
"""

DAILY_DATA_QUERY = """
    select extract(year from datetime - interval '12 month'), datetime, tickersymbol, price
    from quote.close
    where datetime between %s and %s and length(tickersymbol) = 3 and tickersymbol <> 'SPX'
    order by datetime, tickersymbol
"""

FINANCIAL_INFO_QUERY = """
    with ticker as (
        select t.tickersymbol 
        from quote.ticker t
        where t.exchangeid = 'HSX' and t.instrumenttype = 'stock'
    )

    select i.year, i.tickersymbol, i.value, i.code
    from financial.info i join ticker t on i.tickersymbol = t.tickersymbol
    where i.year between %s and %s and i.code in %s and i.quarter = 0
    order by i.year, i.tickersymbol, i.code
"""

INDEX_QUERY = """
    select o.datetime, o.price as op, c.price as cp
    from quote.open o join quote.close c
    on o.tickersymbol = c.tickersymbol and o.datetime = c.datetime
    where o.tickersymbol = 'VNINDEX' and o.datetime between %s and %s
    order by o.datetime
"""
