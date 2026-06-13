{{ config(materialized='table') }}

-- Sensor health based on the LAST 200 readings per sensor (recent behaviour),
-- so recent failures aren't hidden by old healthy data.

WITH ranked AS (
    SELECT
        sensor_id,
        zone_id,
        pm25_level,
        timestamp,
        ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY timestamp DESC) AS rn
    FROM raw_air_quality
),

recent AS (
    SELECT sensor_id, zone_id, pm25_level
    FROM ranked
    WHERE rn <= 200            -- only the most recent 200 readings
),

per_sensor AS (
    SELECT
        sensor_id,
        zone_id,
        COUNT(*)                              AS recent_readings,
        ROUND(AVG(pm25_level)::numeric, 2)    AS recent_avg_pm25,
        ROUND(MAX(pm25_level)::numeric, 2)    AS recent_max_pm25
    FROM recent
    GROUP BY sensor_id, zone_id
),

fleet AS (
    SELECT
        AVG(recent_avg_pm25)    AS fleet_avg,
        STDDEV(recent_avg_pm25) AS fleet_stddev
    FROM per_sensor
)

SELECT
    p.sensor_id,
    p.zone_id,
    p.recent_readings,
    p.recent_avg_pm25,
    CASE
        WHEN p.recent_avg_pm25 = 0 THEN 'CRITICAL - dead (reads zero)'
        WHEN p.recent_avg_pm25 > f.fleet_avg + f.fleet_stddev THEN 'WARNING - drift (abnormally high)'
        ELSE 'HEALTHY'
    END AS health_status
FROM per_sensor p
CROSS JOIN fleet f
ORDER BY health_status, p.sensor_id