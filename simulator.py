import psycopg2
import random
import time
import math
from datetime import datetime, timezone

# ---- Zone personalities -----------------------------------------------------
# Each zone has baseline values for every sensor type.
ZONES = {
    "zone_a": {  # highway-adjacent: dirty air, heavy traffic
        "air":     {"co": 0.5, "no2": 50, "pm25": 30, "o3": 55},
        "traffic": {"vehicles": 400, "speed": 45},
        "energy":  {"kwh": 120, "peak": 80},
    },
    "zone_b": {  # city centre
        "air":     {"co": 0.4, "no2": 40, "pm25": 25, "o3": 60},
        "traffic": {"vehicles": 300, "speed": 35},
        "energy":  {"kwh": 200, "peak": 140},
    },
    "zone_c": {  # industrial: dirtiest air, high energy
        "air":     {"co": 0.6, "no2": 45, "pm25": 40, "o3": 50},
        "traffic": {"vehicles": 250, "speed": 50},
        "energy":  {"kwh": 350, "peak": 260},
    },
    "zone_d": {  # residential park: clean air, light traffic
        "air":     {"co": 0.3, "no2": 25, "pm25": 15, "o3": 65},
        "traffic": {"vehicles": 120, "speed": 30},
        "energy":  {"kwh": 90, "peak": 55},
    },
}

# ---- Deliberate sensor failures (the project asks for these) -----------------
# These names get special broken behaviour so our quality checks can catch them later.
DEAD_SENSOR  = "sensor_air_zone_b_01"   # always returns zero (hardware failure)
DRIFT_SENSOR = "sensor_air_zone_d_01"   # values creep upward over time (drift)
drift_multiplier = 1.0                  # grows each loop for the drift sensor


def rush_hour_factor(hour):
    # Peaks around 8am and 6pm, dips at night.
    return 1 + 0.4 * math.sin((hour - 6) / 24 * 2 * math.pi) \
             + 0.4 * math.sin((hour - 18) / 12 * 2 * math.pi)


def make_air(zone_id, base, hour):
    factor = rush_hour_factor(hour)
    sensor_id = f"sensor_air_{zone_id}_01"

    # Failure: dead sensor always reports zero
    if sensor_id == DEAD_SENSOR:
        return (datetime.now(timezone.utc), sensor_id, zone_id, 0.0, 0.0, 0.0, 0.0)

    # Failure: drift sensor reads higher and higher
    drift = drift_multiplier if sensor_id == DRIFT_SENSOR else 1.0

    return (
        datetime.now(timezone.utc), sensor_id, zone_id,
        round(max(0, random.gauss(base["co"], 0.1) * factor * drift), 2),
        round(max(0, random.gauss(base["no2"], 8) * factor * drift), 1),
        round(max(0, random.gauss(base["pm25"], 6) * factor * drift), 1),
        round(max(0, random.gauss(base["o3"], 10)), 1),
    )


def make_traffic(zone_id, base, hour):
    factor = rush_hour_factor(hour)
    vehicles = int(max(0, random.gauss(base["vehicles"], 40) * factor))
    # More traffic -> slower average speed
    speed = round(max(5, random.gauss(base["speed"], 6) / max(0.5, factor)), 1)
    return (datetime.now(timezone.utc), f"sensor_traffic_{zone_id}_01", zone_id, vehicles, speed)


def make_energy(zone_id, base, hour):
    factor = rush_hour_factor(hour)
    kwh = round(max(0, random.gauss(base["kwh"], 20) * factor), 1)
    peak = round(max(0, random.gauss(base["peak"], 15) * factor), 1)
    return (datetime.now(timezone.utc), f"sensor_energy_{zone_id}_01", zone_id, kwh, peak)


conn = psycopg2.connect(
    host="localhost", port=5432, dbname="smartcity",
    user="cityadmin", password="citypass123",
)
cur = conn.cursor()

print("Full simulator running (air + traffic + energy)... press Ctrl+C to stop.")
loop_count = 0
try:
    while True:
        hour = datetime.now(timezone.utc).hour

        # Drift sensor creeps up 2% each loop
        drift_multiplier = 1.0 + (loop_count * 0.02)

        # Failure: zone_c air sensor goes SILENT for loops 5..15 (network outage)
        silent = (5 <= loop_count <= 15)

        for zone_id, base in ZONES.items():
            air_sensor = f"sensor_air_{zone_id}_01"
            if not (silent and zone_id == "zone_c"):
                cur.execute(
                    "INSERT INTO raw_air_quality (timestamp, sensor_id, zone_id, co_level, no2_level, pm25_level, o3_level) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    make_air(zone_id, base["air"], hour),
                )

            cur.execute(
                "INSERT INTO raw_traffic (timestamp, sensor_id, zone_id, vehicle_count, avg_speed_kmh) "
                "VALUES (%s, %s, %s, %s, %s)",
                make_traffic(zone_id, base["traffic"], hour),
            )
            cur.execute(
                "INSERT INTO raw_energy (timestamp, sensor_id, zone_id, kwh_consumed, peak_demand_kw) "
                "VALUES (%s, %s, %s, %s, %s)",
                make_energy(zone_id, base["energy"], hour),
            )

        conn.commit()
        loop_count += 1
        note = "  (zone_c air SILENT)" if silent else ""
        print(f"loop {loop_count:>3} | inserted air+traffic+energy for all zones{note}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    cur.close()
    conn.close()