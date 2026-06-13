# Smart City IoT Monitoring Pipeline

A complete data-engineering pipeline that simulates a smart city's IoT sensors (air quality, traffic, energy) across 4 zones, streams the data through Kafka, stores it in TimescaleDB, transforms it with dbt, and shows it live on Grafana dashboards. It also injects deliberate sensor failures (dead, drifting, silent) so the monitoring can be tested.

This README is written so that anyone can clone the repo and get the whole thing running and visible on their own machine, step by step. Just follow it top to bottom.

---

## Architecture

```
producer.py  ->  Kafka (3 topics)  ->  consumer.py  ->  TimescaleDB  ->  dbt models  ->  Grafana dashboards
```

Everything runs in Docker except the Python scripts and dbt, which run on your machine.

---

## 1. Install the required software (one time)

Install these three first. Accept the default options unless noted.

1. **Docker Desktop** - https://www.docker.com/products/docker-desktop/
   - On Windows it will set up WSL2 automatically; just accept the prompts and restart if asked.
   - After installing, OPEN Docker Desktop and leave it running (you should see the whale icon steady in your taskbar). Nothing below works unless Docker Desktop is open.
2. **Python 3.12 or 3.13** - https://www.python.org/downloads/
   - IMPORTANT: on the first install screen, tick the box "Add python.exe to PATH".
   - Do NOT use Python 3.14 - dbt does not support it yet. 3.12 or 3.13 is required.
3. **Git** - https://git-scm.com/download/win

To confirm they installed, open a new terminal (PowerShell on Windows) and run each line - you should get a version number, not an error:

```
docker --version
python --version
git --version
```

---

## 2. Download the project

In a terminal, run:

```
git clone https://github.com/mdsayedhasann/smart-city-iot.git
cd smart-city-iot
```

You are now inside the project folder. Run all later commands from here unless told otherwise.

---

## 3. Install the Python libraries

```
python -m pip install psycopg2-binary confluent-kafka
```

(If you see an "Access is denied" error, the `python -m pip` form shown above is the reliable way - use it instead of plain `pip`.)

---

## 4. Start all the services (database, Kafka, Grafana)

With Docker Desktop open, run:

```
docker compose up -d
```

The first time, this downloads several images and takes a few minutes. When done you have five services running:

| Service | What it is | Opens at |
| --- | --- | --- |
| TimescaleDB | the database | port 5432 (no web page) |
| Kafka | event streaming | port 9092 (no web page) |
| Kafka UI | view Kafka messages | http://localhost:8080 |
| Grafana | the dashboards | http://localhost:3000 |

Check they are running:

```
docker ps
```

You should see `smartcity_timescaledb`, `smartcity_kafka`, `smartcity_kafka_ui`, and `smartcity_grafana`.

---

## 5. Create the database tables

```
Get-Content setup_tables.sql | docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity
```

(On Mac/Linux use: `docker exec -i smartcity_timescaledb psql -U cityadmin -d smartcity < setup_tables.sql`)

This creates three tables: raw_air_quality, raw_traffic, raw_energy.

---

## 6. Start the data flowing (two terminals)

The pipeline needs two scripts running at the same time, so open TWO terminals.

Terminal 1 - the consumer (reads from Kafka, writes to the database). Start this one first:

```
python consumer.py
```

Terminal 2 - open a new terminal (in VS Code: Terminal > New Terminal), then the producer (creates sensor readings and sends them to Kafka):

```
python producer.py
```

Both print a line every 5 seconds. Leave them running while you use the dashboards. Press Ctrl+C in each to stop later.

Tip: there is also `python simulator.py`, which writes straight to the database without Kafka - handy for a quick test, but the producer + consumer pair is the real pipeline.

---

## 7. Build the dbt analytics models

dbt runs in its own small Python environment (because dbt needs Python 3.12/3.13).

First-time setup (creates the environment and installs dbt):

```
py -3.12 -m venv dbt-venv
.\dbt-venv\Scripts\python.exe -m pip install "dbt-core==1.10.*" "dbt-postgres==1.10.*"
```

(If `py -3.12` errors, use whichever 3.12/3.13 you have, e.g. `py -3.13 -m venv dbt-venv`.)

Then build and test the models:

```
cd dbt_project
..\dbt-venv\Scripts\dbt.exe run --profiles-dir .
..\dbt-venv\Scripts\dbt.exe test --profiles-dir .
cd ..
```

This creates 6 analytics models in the `analytics` schema and runs 14 data-quality tests.

---

## 8. See the dashboards in Grafana

Open your browser at **http://localhost:3000**

Log in:
- Username: `admin`
- Password: `admin`
(It may ask you to set a new password - set anything, or skip if allowed.)

### Connect Grafana to the database (one time)

1. Left menu: Connections > Data sources > Add data source > PostgreSQL
2. Fill in EXACTLY these values:

| Field | Value |
| --- | --- |
| Host URL | `timescaledb:5432` |
| Database | `smartcity` |
| Username | `cityadmin` |
| Password | `citypass123` |
| TLS/SSL Mode | `disable` |

3. Click "Save & test" - you should see a green "Database Connection OK".

(Use `timescaledb:5432` as the host, NOT localhost - inside Docker the containers find each other by name.)

### Build a dashboard panel

Dashboards > New > New dashboard > Add visualization > pick the PostgreSQL data source > switch the query editor to "Code" > paste a query below > set the time range (top-right) to "Last 15 minutes" > Run query > Save.

Make sure the producer and consumer (Step 6) are running so there is live data.

Queries for the 5 dashboards:

Air quality (PM2.5 by zone):
```
SELECT "timestamp" AS time, pm25_level, zone_id FROM raw_air_quality WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

Traffic (vehicle count by zone):
```
SELECT "timestamp" AS time, vehicle_count, zone_id FROM raw_traffic WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

Energy (consumption by zone):
```
SELECT "timestamp" AS time, kwh_consumed, zone_id FROM raw_energy WHERE "timestamp" > NOW() - INTERVAL '1 hour' ORDER BY "timestamp";
```

Sensor health (use the Table visualization, not Time series):
```
SELECT sensor_id, recent_readings, recent_avg_pm25, health_status FROM analytics.sensor_health ORDER BY health_status;
```

Traffic vs pollution correlation (use the Table visualization):
```
SELECT zone_id, hours_compared, avg_vehicles, avg_pm25, traffic_pm25_correlation FROM analytics.traffic_pollution_correlation ORDER BY traffic_pm25_correlation DESC NULLS LAST;
```

You can also view raw Kafka messages at http://localhost:8080 (Topics > sensor_air > Messages).

---

## All the passwords and connection details (in one place)

These are set in `docker-compose.yml` and are fine for local/classroom use.

| Thing | Value |
| --- | --- |
| Database name | `smartcity` |
| Database user | `cityadmin` |
| Database password | `citypass123` |
| Database host (from your machine) | `localhost`, port `5432` |
| Database host (from inside Docker, e.g. Grafana) | `timescaledb`, port `5432` |
| Grafana URL | http://localhost:3000 |
| Grafana login | `admin` / `admin` |
| Kafka UI URL | http://localhost:8080 |
| Kafka (from your machine) | `localhost:9092` |

Note: storing passwords in the repo is fine for a class project on a local machine, but in a real deployment these would be kept in environment variables / a secrets manager, never committed.

---

## Everyday commands

| To do this | Run |
| --- | --- |
| Stop everything (data is kept) | `docker compose down` |
| Start everything again | `docker compose up -d` |
| Check the database row count | `docker exec -it smartcity_timescaledb psql -U cityadmin -d smartcity -c "SELECT COUNT(*) FROM raw_air_quality;"` |
| Rebuild dbt models | `cd dbt_project` then `..\dbt-venv\Scripts\dbt.exe run --profiles-dir .` |

---

## dbt models (answer the 5 business questions)

| Model | Business Question |
| --- | --- |
| air_quality_hourly | BQ1 - air quality by zone and hour |
| threshold_breaches | BQ1 - hours over the PM2.5 safety limit |
| traffic_hourly | BQ2 - traffic volume and speed by zone |
| energy_hourly | BQ3 - energy consumption and peak demand by zone |
| sensor_health | BQ4 - dead / drifting / silent sensor detection |
| traffic_pollution_correlation | BQ5 - traffic vs pollution correlation |

---

## What is built

- IoT simulator: 3 sensor types, 4 zones, rush-hour patterns, 3 injected failures
- Kafka streaming for all 3 sensor types
- TimescaleDB storage with hypertables
- dbt transformation layer: 6 models, 14 tests, docs + lineage graph
- 5 Grafana dashboards (one per business question)

## Not yet built

- Great Expectations data-quality suite
- Airflow orchestration (scheduling the dbt and quality jobs)
- Project report and remaining diagrams

---

## Troubleshooting

- "cannot connect to the Docker daemon" -> Docker Desktop is not open. Open it and wait for the whale icon to be steady.
- Grafana shows "No data" -> make sure the producer AND consumer are running, and the time range is "Last 15 minutes".
- Grafana data source error "no default database" -> you have two PostgreSQL data sources; use the one whose Host is `timescaledb:5432` and Database is `smartcity`.
- `pip` "Access is denied" -> use `python -m pip install ...` instead.
- dbt crashes on install -> you are probably on Python 3.14; create the venv with Python 3.12 or 3.13.