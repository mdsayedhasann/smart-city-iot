import json
import random
import time
import math
from datetime import datetime, timezone
from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": "localhost:9092"})

# Each zone has baseline values for every sensor type
ZONES = {
    "zone_a": {  # highway-adjacent
        "air":     {"co": 0.5, "no2": 50, "pm25": 30, "o3": 55},
        "traffic": {"vehicles": 400, "speed": 45},
        "energy":  {"kwh": 120, "peak": 80},
    },
    "zone_b": {  # city centre
        "air":     {"co": 0.4, "no2": 40, "pm25": 25, "o3": 60},
        "traffic": {"vehicles": 300, "speed": 35},
        "energy":  {"kwh": 200, "peak": 140},
    },
    "zone_c": {  # industrial
        "air":     {"co": 0.6, "no2": 45, "pm25": 40, "o3": 50},
        "traffic": {"vehicles": 250, "speed": 50},
        "energy":  {"kwh": 350, "peak": 260},
    },
    "zone_d": {  # residential park
        "air":     {"co": 0.3, "no2": 25, "pm25": 15, "o3": 65},
        "traffic": {"vehicles": 120, "speed": 30},
        "energy":  {"kwh": 90, "peak": 55},
    },
}

def rush_hour_factor(hour):
    return 1 + 0.4 * math.sin((hour - 6) / 24 * 2 * math.pi) \
             + 0.4 * math.sin((hour - 18) / 12 * 2 * math.pi)

def make_air(zone_id, base, now, factor):
    return {
        "timestamp": now.isoformat(),
        "sensor_id": f"sensor_air_{zone_id}_01",
        "zone_id": zone_id,
        "co_level":   round(max(0, random.gauss(base["co"], 0.1) * factor), 2),
        "no2_level":  round(max(0, random.gauss(base["no2"], 8) * factor), 1),
        "pm25_level": round(max(0, random.gauss(base["pm25"], 6) * factor), 1),
        "o3_level":   round(max(0, random.gauss(base["o3"], 10)), 1),
    }

def make_traffic(zone_id, base, now, factor):
    vehicles = int(max(0, random.gauss(base["vehicles"], 40) * factor))
    speed = round(max(5, random.gauss(base["speed"], 6) / max(0.5, factor)), 1)
    return {
        "timestamp": now.isoformat(),
        "sensor_id": f"sensor_traffic_{zone_id}_01",
        "zone_id": zone_id,
        "vehicle_count": vehicles,
        "avg_speed_kmh": speed,
    }

def make_energy(zone_id, base, now, factor):
    return {
        "timestamp": now.isoformat(),
        "sensor_id": f"sensor_energy_{zone_id}_01",
        "zone_id": zone_id,
        "kwh_consumed":   round(max(0, random.gauss(base["kwh"], 20) * factor), 1),
        "peak_demand_kw": round(max(0, random.gauss(base["peak"], 15) * factor), 1),
    }

print("Producer running... publishing air + traffic + energy to Kafka. Press Ctrl+C to stop.")
try:
    while True:
        now = datetime.now(timezone.utc)
        factor = rush_hour_factor(now.hour)
        for zone_id, base in ZONES.items():
            producer.produce("sensor_air",     value=json.dumps(make_air(zone_id, base["air"], now, factor)).encode("utf-8"))
            producer.produce("sensor_traffic", value=json.dumps(make_traffic(zone_id, base["traffic"], now, factor)).encode("utf-8"))
            producer.produce("sensor_energy",  value=json.dumps(make_energy(zone_id, base["energy"], now, factor)).encode("utf-8"))
        producer.flush()
        print(f"{datetime.now().strftime('%H:%M:%S')}  published air+traffic+energy for all zones")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nProducer stopped.")