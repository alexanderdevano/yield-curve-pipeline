-- compute spreads between key securities

SELECT
    a.date,
    a.yield             AS yield_10y,
    b.yield             AS yield_2y,
    c.yield             AS yield_3m,
    d.yield             AS yield_30y,
    a.yield - b.yield   AS spread_10y_2y,
    a.yield - c.yield   AS spread_10y_3m,
    d.yield - a.yield   AS spread_30y_10y
FROM {{ ref('stg_yield_curve')}} a
JOIN {{ ref('stg_yield_curve')}} b ON a.date = b.date
JOIN {{ ref('stg_yield_curve')}} c ON a.date = c.date
JOIN {{ ref('stg_yield_curve')}} d ON a.date = d.date
WHERE a.maturity = '10_year'
AND b.maturity = '2_year'
AND c.maturity = '3_month'
AND d.maturity = '30_year'
