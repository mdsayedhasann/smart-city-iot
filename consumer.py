import json
import psycopg2
from confluent_kafka import Consumer

conn = psycopg2.connect(
    host="localhost", port=5432, dbname="smartcity",
    user="cityadmin", password="citypass123",
)
cur = conn.cursor()

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "smartcity-consumer",
    "auto.offset.reset": "earliest",
})
consumer.subscribe(["sensor_air", "sensor_traffic", "sensor_energy"])

print("Consumer running... reading all 3 topics -> TimescaleDB. Press Ctrl+C to stop.")
count = 0
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Kafka error:", msg.error())
            continue

        topic = msg.topic()
        r = json.loads(msg.value().decode("utf-8"))

        if topic == "sensor_air":
            cur.execute(
                "INSERT INTO raw_air_quality (timestamp, sensor_id, zone_id, co_level, no2_level, pm25_level, o3_level) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (r["timestamp"], r["sensor_id"], r["zone_id"],
                 r["co_level"], r["no2_level"], r["pm25_level"], r["o3_level"]),
            )
        elif topic == "sensor_traffic":
            cur.execute(
                "INSERT INTO raw_traffic (timestamp, sensor_id, zone_id, vehicle_count, avg_speed_kmh) "
                "VALUES (%s, %s, %s, %s, %s)",
                (r["timestamp"], r["sensor_id"], r["zone_id"],
                 r["vehicle_count"], r["avg_speed_kmh"]),
            )
        elif topic == "sensor_energy":
            cur.execute(
                "INSERT INTO raw_energy (timestamp, sensor_id, zone_id, kwh_consumed, peak_demand_kw) "
                "VALUES (%s, %s, %s, %s, %s)",
                (r["timestamp"], r["sensor_id"], r["zone_id"],
                 r["kwh_consumed"], r["peak_demand_kw"]),
            )

        conn.commit()
        count += 1
        if count % 12 == 0:
            print(f"saved {count} readings across all sensor types")
except KeyboardInterrupt:
    print("\nConsumer stopped.")
finally:
    consumer.close()
    cur.close()
    conn.close()