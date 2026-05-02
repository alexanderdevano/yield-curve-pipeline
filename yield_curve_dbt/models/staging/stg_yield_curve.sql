-- clean and cast raw FRED data
-- remove missing values and casts types properly

SELECT
    CAST(date AS DATE) AS date,
    value               AS yield,
    maturity, 
    series_id, 
    pulled_at
FROM {{ source('yield_curve', 'observations')}}
WHERE value IS NOT NULL