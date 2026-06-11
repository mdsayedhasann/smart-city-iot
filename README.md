# Smart City IoT Pipeline

This project simulates IoT sensor data for a smart city (air quality, traffic, energy) across 4 city zones, streams it through Kafka, stores it in a TimescaleDB time-series database, and visualizes it live in Grafana. It also injects deliberate sensor failures (dead, drifting, and silent sensors) so our monitoring can be tested.

## Architecture (so far)

```
producer.py  ->  Kafka (sensor_air topic)  ->  consumer.py  ->  TimescaleDB  ->  Grafana
```

There are two ways data currently reaches the database:
- `simulator.py` writes readings directly to TimescaleDB (the original simple version).
- `producer.py` + `consumer.py` use the proper Kafka streaming flow (producer publishes to Kafka, consumer reads and writes to the database).

## Install these first (one-time)

1. **Docker Desktop** — https://www.docker.com/products/docker-desktop/ (open it and leave it running)
2. **Python 3.11+** — https://www.python.org/downloads/ (tick **"Add python.exe to PATH"** during install)
3. **Git** — https://git-scm.com/download/win

## Step 1 — Download the project

Open PowerShell and run (replace the URL with our repo link if different):

```
git clone https://github.com/mdsayedhasann/smart-city-iot.git
cd smart-city-iot
```

## Step 2 — Install the Python libraries

```
python -m pip install psycopg2-binary confluent-kafka
```

(If `pip` gives an "Access is denied" error, `python -m pip` as shown above is the reliable way to install.)

## Step 3 — Start all services

Make sure Docker Desktop is open, then run:

```
docker compose up -d
```

The first time, this downloads the images (wait a few minutes). It starts four services:
- TimescaleDB (database) on port 5432
- Grafana (dashboards) on port 3000
- Kafka (event streaming) on port 9092
- Kafka UI on port 8080

## Step 4 — Create the tables

This sets up the hypertables (`raw_air_quality`, `raw_traffic`, `raw_energy`):

```
Get-Content setup_tables.sql | docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity
```

On Mac/Linux use this instead:

```
docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity < setup_tables.sql
```

## Step 5 — Run the streaming pipeline (Kafka version)

Open **two** terminals.

Terminal 1 — start the consumer (reads Kafka, writes to the database):

```
python consumer.py
```

Terminal 2 — start the producer (publishes sensor readings to Kafka):

```
python producer.py
```

Both print activity every 5 seconds. Press **Ctrl+C** in each to stop.

*(Alternatively, `python simulator.py` runs the simpler direct-to-database version without Kafka.)*

## Step 6 — See the data

- **Kafka UI** — http://localhost:8080 → Topics → `sensor_air` → Messages tab (see readings flowing through Kafka)
- **Grafana** — http://localhost:3000 (login `admin` / `admin`)
  - Connect a PostgreSQL data source: Host `timescaledb:5432`, Database `smartcity`, User `cityadmin`, Password `citypass123`, SSL Mode `disable`
  - Build a panel with this query:

```
SELECT "timestamp" AS time, pm25_level, zone_id FROM raw_air_quality WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

## Useful commands

- Stop everything (data is kept): `docker compose down`
- Start again later: `docker compose up -d`
- Check row count: `docker exec -it smartcity_timescaledb psql -U cityadmin -d smartcity -c "SELECT COUNT(*) FROM raw_air_quality;"`

## Connection details

- Host: `localhost` (or `timescaledb` from inside Docker)
- Port: `5432`
- Database: `smartcity`
- User: `cityadmin`
- Password: `citypass123`

## What is built so far

- IoT simulator: 3 sensor types, 4 zones with distinct profiles, rush-hour patterns, and 3 injected failures (dead, drifting, silent sensors)
- Kafka streaming for air quality (producer -> topic -> consumer)
- TimescaleDB storage with hypertables
- Live Grafana dashboard

## Not yet built

- Kafka streaming for traffic and energy (currently only air quality)
- dbt aggregations (hourly/daily summaries, sensor health, threshold breaches)
- Great Expectations data quality checks
- Airflow orchestration
- Full set of 5 Grafana dashboards