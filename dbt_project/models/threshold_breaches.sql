-- Flags each hour where a zone's average PM2.5 exceeds the WHO safety limit.
-- Builds on the hourly model we already made.

WITH hourly AS (
    SELECT * FROM analytics.air_quality_hourly
) 

SELECT
    zone_id,
    hour,
    avg_pm25,
    35.0                                 AS threshold,
    avg_pm25 - 35.0                      AS amount_over,
    'PM2.5'                              AS pollutant
FROM hourly
WHERE avg_pm25 > 35.0
ORDER BY hour DESC, zone_id