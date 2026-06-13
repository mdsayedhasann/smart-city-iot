# Smart City IoT Pipeline

This project simulates IoT sensor data for a smart city (air quality, traffic, energy) across 4 city zones, streams it through Kafka, stores it in a TimescaleDB time-series database, transforms it with dbt into analytics-ready tables, and visualizes it live in Grafana. It also injects deliberate sensor failures (dead, drifting, and silent sensors) so the monitoring and data-quality checks can be tested.

## Architecture

```
producer.py  ->  Kafka (3 topics)  ->  consumer.py  ->  TimescaleDB (raw tables)  ->  dbt (analytics models)  ->  Grafana
```

- Streaming layer (runs continuously): the producer publishes sensor readings to Kafka topics; the consumer reads them and writes to TimescaleDB.
- Transformation layer (run on demand): dbt aggregates raw readings into hourly summaries, sensor-health metrics, threshold breaches, and cross-sensor correlation.
- A simpler `simulator.py` is also included, which writes directly to TimescaleDB without Kafka (useful for quick tests and replaying the injected failures).

## Install these first (one-time)

1. **Docker Desktop** - https://www.docker.com/products/docker-desktop/ (open it and leave it running)
2. **Python 3.12 or 3.13** - https://www.python.org/downloads/ (tick "Add python.exe to PATH"). Note: dbt does not yet support Python 3.14.
3. **Git** - https://git-scm.com/download/win

## Step 1 - Download the project

```
git clone https://github.com/mdsayedhasann/smart-city-iot.git
cd smart-city-iot
```

## Step 2 - Install the Python libraries

```
python -m pip install psycopg2-binary confluent-kafka
```

(If pip gives an "Access is denied" error, `python -m pip` as shown is the reliable way to install.)

## Step 3 - Start all services

Make sure Docker Desktop is open, then run:

```
docker compose up -d
```

This starts five services:
- TimescaleDB (database) on port 5432
- Grafana (dashboards) on port 3000
- Kafka (event streaming) on port 9092
- Kafka UI on port 8080
- (Grafana, Kafka UI, and dbt docs each use a different port to avoid clashes)

## Step 4 - Create the tables

```
Get-Content setup_tables.sql | docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity
```

(Mac/Linux: `docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity < setup_tables.sql`)

## Step 5 - Run the streaming pipeline

Open two terminals.

Terminal 1 (consumer - reads Kafka, writes to the database):

```
python consumer.py
```

Terminal 2 (producer - publishes readings to Kafka):

```
python producer.py
```

Both print activity every 5 seconds. Press Ctrl+C in each to stop.

## Step 6 - Run the dbt transformations

dbt runs in its own Python sandbox (created with Python 3.12/3.13 because dbt does not support 3.14 yet).

First-time setup:

```
py -3.12 -m venv dbt-venv
.\dbt-venv\Scripts\python.exe -m pip install "dbt-core==1.10.*" "dbt-postgres==1.10.*"
```

Then build the models (from inside the dbt_project folder):

```
cd dbt_project
..\dbt-venv\Scripts\dbt.exe run --profiles-dir .
..\dbt-venv\Scripts\dbt.exe test --profiles-dir .
cd ..
```

This creates the analytics models in the `analytics` schema.

## Step 7 - View the data

- **Kafka UI** - http://localhost:8080 (Topics -> sensor_air -> Messages to see readings flowing through Kafka)
- **Grafana** - http://localhost:3000 (login admin / admin)
  - Add a PostgreSQL data source: Host `timescaledb:5432`, Database `smartcity`, User `cityadmin`, Password `citypass123`, SSL Mode `disable`
  - Example panel query:

```
SELECT "timestamp" AS time, pm25_level, zone_id FROM raw_air_quality WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

- **dbt docs / lineage graph** - from inside dbt_project: `..\dbt-venv\Scripts\dbt.exe docs generate --profiles-dir .` then `..\dbt-venv\Scripts\dbt.exe docs serve --profiles-dir . --port 8081` and open http://localhost:8081

## dbt models (answers the 5 business questions)

| Model | Business Question |
| --- | --- |
| air_quality_hourly | BQ1 - air quality by zone and hour |
| threshold_breaches | BQ1 - hours exceeding the PM2.5 safety limit |
| traffic_hourly | BQ2 - traffic volume and speed by zone |
| energy_hourly | BQ3 - energy consumption and peak demand by zone |
| sensor_health | BQ4 - dead / drifting / silent sensor detection |
| traffic_pollution_correlation | BQ5 - correlation between traffic and pollution |

## Useful commands

- Stop everything (data is kept): `docker compose down`
- Start again later: `docker compose up -d`
- Check a table: `docker exec -it smartcity_timescaledb psql -U cityadmin -d smartcity -c "SELECT COUNT(*) FROM raw_air_quality;"`

## Connection details

- Host: `localhost` (or `timescaledb` from inside Docker)
- Port: `5432`
- Database: `smartcity`
- User: `cityadmin`
- Password: `citypass123`

## What is built so far

- IoT simulator: 3 sensor types, 4 zones with distinct profiles, rush-hour patterns, and 3 injected failures (dead, drifting, silent sensors)
- Kafka streaming for all 3 sensor types (producer -> topics -> consumer)
- TimescaleDB storage with hypertables
- Complete dbt transformation layer: 6 models answering all 5 business questions, 14 data-quality tests, auto-generated docs and lineage graph
- Live Grafana dashboard (air quality)

## Not yet built

- Great Expectations data quality suite
- Airflow orchestration (scheduling the dbt and quality jobs)
- Remaining Grafana dashboards (traffic, energy, sensor health, correlation)
- Project report and remaining diagrams