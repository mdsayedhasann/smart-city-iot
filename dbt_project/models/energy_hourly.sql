{{ config(materialized='table') }}

-- Hourly energy summary per zone (Business Question 3)

SELECT
    zone_id,
    date_trunc('hour', timestamp)             AS hour,
    COUNT(*)                                  AS reading_count,
    ROUND(SUM(kwh_consumed)::numeric, 1)      AS total_kwh,
    ROUND(AVG(kwh_consumed)::numeric, 1)      AS avg_kwh,
    ROUND(MAX(peak_demand_kw)::numeric, 1)    AS peak_demand_kw
FROM raw_energy
GROUP BY zone_id, date_trunc('hour', timestamp)
ORDER BY hour DESC, zone_id