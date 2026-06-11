-- Traffic sensors: vehicle counts and average speed
CREATE TABLE IF NOT EXISTS raw_traffic (
    timestamp      TIMESTAMPTZ NOT NULL,
    sensor_id      TEXT NOT NULL,
    zone_id        TEXT NOT NULL,
    vehicle_count  INTEGER,
    avg_speed_kmh  DOUBLE PRECISION
);
SELECT create_hypertable('raw_traffic', 'timestamp');

-- Energy sensors: electricity consumption per district
CREATE TABLE IF NOT EXISTS raw_energy (
    timestamp       TIMESTAMPTZ NOT NULL,
    sensor_id       TEXT NOT NULL,
    zone_id         TEXT NOT NULL,
    kwh_consumed    DOUBLE PRECISION,
    peak_demand_kw  DOUBLE PRECISION
);
SELECT create_hypertable('raw_energy', 'timestamp');