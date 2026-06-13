{{ config(materialized='table') }}

-- Business Question 5: does traffic correlate with air pollution?
-- Joins hourly traffic and hourly air quality per zone+hour,
-- then measures the correlation per zone.

WITH joined AS (
    SELECT
        t.zone_id,
        t.hour,
        t.total_vehicles,
        a.avg_pm25
    FROM {{ ref('traffic_hourly') }} t
    JOIN {{ ref('air_quality_hourly') }} a
      ON t.zone_id = a.zone_id
     AND t.hour    = a.hour
)

SELECT
    zone_id,
    COUNT(*)                                          AS hours_compared,
    ROUND(AVG(total_vehicles)::numeric, 0)            AS avg_vehicles,
    ROUND(AVG(avg_pm25)::numeric, 2)                  AS avg_pm25,
    ROUND(CORR(total_vehicles, avg_pm25)::numeric, 3) AS traffic_pm25_correlation
FROM joined
GROUP BY zone_id
ORDER BY traffic_pm25_correlation DESC NULLS LAST