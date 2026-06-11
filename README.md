# Smart City IoT Simulator + Live Dashboard

This project simulates IoT sensor data for a smart city (air quality, traffic, energy) across 4 city zones, stores it in a TimescaleDB time-series database, and visualizes it live in Grafana. It also injects deliberate sensor failures (dead, drifting, and silent sensors) so our monitoring can be tested.

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

## Step 2 — Install the Python library

```
pip install psycopg2-binary
```

If `pip` is not recognized, use:

```
py -m pip install psycopg2-binary
```

## Step 3 — Start the database and Grafana

Make sure Docker Desktop is open, then run:

```
docker compose up -d
```

The first time, this downloads the TimescaleDB and Grafana images (wait a minute or two). It starts two containers: the database and Grafana.

## Step 4 — Create the tables

This sets up the three hypertables (`raw_air_quality`, `raw_traffic`, `raw_energy`):

```
Get-Content setup_tables.sql | docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity
```

On Mac/Linux use this instead:

```
docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity < setup_tables.sql
```

## Step 5 — Run the simulator

```
python simulator.py
```

It inserts data for all zones every 5 seconds. Around loop 6 you will see a `(zone_c air SILENT)` note — that is a deliberate "network outage" failure. Let it run for a minute or two, then press **Ctrl+C** to stop.

## Step 6 — Open Grafana

In a browser, go to **http://localhost:3000** and log in:

- Username: `admin`
- Password: `admin`

(Set a new password when asked.)

## Step 7 — Connect Grafana to the database

Left menu → **Connections → Data sources → Add data source → PostgreSQL**. Fill in:

- **Host URL:** `timescaledb:5432`
- **Database:** `smartcity`
- **Username:** `cityadmin`
- **Password:** `citypass123`
- **TLS/SSL Mode:** `disable`

Click **Save & test** — you should see a green "Database Connection OK".

## Step 8 — Build a live chart

Go to **Dashboards → New → New dashboard → Add visualization**, pick the PostgreSQL data source, switch the query editor to **Code**, and paste:

```
SELECT "timestamp" AS time, pm25_level, zone_id FROM raw_air_quality WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

Set the time range to **Last 15 minutes** and click **Run query**. A live pollution chart appears.

## Useful commands

- Stop everything (data is kept): `docker compose down`
- Start again later: `docker compose up -d`

## Connection details

- Host: `localhost` (or `timescaledb` from inside Docker)
- Port: `5432`
- Database: `smartcity`
- User: `cityadmin`
- Password: `citypass123`

## What is built so far

- IoT simulator: 3 sensor types, 4 zones with distinct profiles, rush-hour patterns, and 3 injected failures (dead, drifting, silent sensors)
- TimescaleDB storage with hypertables
- Live Grafana dashboard

**Not yet built:** Kafka streaming layer, dbt aggregations, Great Expectations checks, Airflow orchestration, full set of dashboards.