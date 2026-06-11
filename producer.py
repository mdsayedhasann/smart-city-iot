import json
import random
import time
import math
from datetime import datetime, timezone
from confluent_kafka import Producer

# Connect to Kafka (running in Docker, reachable on localhost:9092)
producer = Producer({"bootstrap.servers": "localhost:9092"})

ZONES = {
    "zone_a": {"co": 0.5, "no2": 50, "pm25": 30, "o3": 55},  # highway-adjacent
    "zone_b": {"co": 0.4, "no2": 40, "pm25": 25, "o3": 60},  # city centre
    "zone_c": {"co": 0.6, "no2": 45, "pm25": 40, "o3": 50},  # industrial
    "zone_d": {"co": 0.3, "no2": 25, "pm25": 15, "o3": 65},  # residential park
}

def rush_hour_factor(hour):
    return 1 + 0.4 * math.sin((hour - 6) / 24 * 2 * math.pi) \
             + 0.4 * math.sin((hour - 18) / 12 * 2 * math.pi)

def make_air(zone_id, base):
    now = datetime.now(timezone.utc)
    factor = rush_hour_factor(now.hour)
    return {
        "timestamp": now.isoformat(),
        "sensor_id": f"sensor_air_{zone_id}_01",
        "zone_id": zone_id,
        "co_level":   round(max(0, random.gauss(base["co"], 0.1) * factor), 2),
        "no2_level":  round(max(0, random.gauss(base["no2"], 8) * factor), 1),
        "pm25_level": round(max(0, random.gauss(base["pm25"], 6) * factor), 1),
        "o3_level":   round(max(0, random.gauss(base["o3"], 10)), 1),
    }

print("Producer running... publishing to Kafka topic 'sensor_air'. Press Ctrl+C to stop.")
try:
    while True:
        for zone_id, base in ZONES.items():
            reading = make_air(zone_id, base)
            # Send the reading as JSON to the 'sensor_air' topic
            producer.produce("sensor_air", value=json.dumps(reading).encode("utf-8"))
        producer.flush()   # make sure messages are sent
        print(f"{datetime.now().strftime('%H:%M:%S')}  published {len(ZONES)} readings to Kafka")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nProducer stopped.")