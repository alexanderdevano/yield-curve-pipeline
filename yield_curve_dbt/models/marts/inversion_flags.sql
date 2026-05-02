SELECT
    date,
    yield_10y, 
    yield_2y, 
    spread_10y_2y, 
    spread_10y_3m,
    CASE
        WHEN spread_10y_2y < 0 THEN true
        ELSE false
    END AS is_inverted_2y,
    CASE 
        WHEN spread_10y_3m < 0 THEN true
        ELSE false
    END AS is_inverted_3m
FROM {{ ref('yield_spreads')}}
