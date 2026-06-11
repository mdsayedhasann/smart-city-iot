import json
import psycopg2
from confluent_kafka import Consumer

# Connect to TimescaleDB
conn = psycopg2.connect(
    host="localhost", port=5432, dbname="smartcity",
    user="cityadmin", password="citypass123",
)
cur = conn.cursor()

# Connect to Kafka and subscribe to the air topic
consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "air-consumer",          # a name for this consumer
    "auto.offset.reset": "earliest",     # read from the start if new
})
consumer.subscribe(["sensor_air"])

print("Consumer running... reading 'sensor_air' from Kafka -> TimescaleDB. Press Ctrl+C to stop.")
count = 0
try:
    while True:
        msg = consumer.poll(1.0)   # wait up to 1 sec for a message
        if msg is None:
            continue
        if msg.error():
            print("Kafka error:", msg.error())
            continue

        # Decode the JSON message
        r = json.loads(msg.value().decode("utf-8"))

        # Insert it into the database
        cur.execute(
            "INSERT INTO raw_air_quality (timestamp, sensor_id, zone_id, co_level, no2_level, pm25_level, o3_level) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (r["timestamp"], r["sensor_id"], r["zone_id"],
             r["co_level"], r["no2_level"], r["pm25_level"], r["o3_level"]),
        )
        conn.commit()
        count += 1
        if count % 4 == 0:
            print(f"saved {count} readings to TimescaleDB so far")
except KeyboardInterrupt:
    print("\nConsumer stopped.")
finally:
    consumer.close()
    cur.close()
    conn.close()