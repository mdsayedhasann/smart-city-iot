-- Hourly average air quality per zone
-- Turns thousands of raw 5-second readings into one row per zone per hour.

SELECT
    zone_id,
    date_trunc('hour', timestamp)        AS hour,
    COUNT(*)                             AS reading_count,
    ROUND(AVG(pm25_level)::numeric, 2)   AS avg_pm25,
    ROUND(MAX(pm25_level)::numeric, 2)   AS max_pm25,
    ROUND(AVG(no2_level)::numeric, 2)    AS avg_no2,
    ROUND(AVG(co_level)::numeric, 2)     AS avg_co,
    ROUND(AVG(o3_level)::numeric, 2)     AS avg_o3
FROM raw_air_quality
GROUP BY zone_id, date_trunc('hour', timestamp)
ORDER BY hour, zone_id