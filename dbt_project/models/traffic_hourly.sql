{{ config(materialized='table') }}

-- Hourly traffic summary per zone (Business Question 2)

SELECT
    zone_id,
    date_trunc('hour', timestamp)            AS hour,
    COUNT(*)                                 AS reading_count,
    SUM(vehicle_count)                       AS total_vehicles,
    ROUND(AVG(vehicle_count)::numeric, 0)    AS avg_vehicles,
    ROUND(AVG(avg_speed_kmh)::numeric, 1)    AS avg_speed_kmh
FROM raw_traffic
GROUP BY zone_id, date_trunc('hour', timestamp)
ORDER BY hour DESC, zone_id