
import json
import csv
import os
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import psycopg2
import redis

from processing.validation import validate_data
from processing.transformation import transform_data
from processing.anomaly_detection import detect_anomaly


CSV_DIR = Path("data/csv")
CSV_DIR.mkdir(parents=True, exist_ok=True)


# PostgreSQL connection
def connect_db():

    while True:
        try:
            return psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                database="industrial_iot",
                user="iot_user",
                password="iot_password_change_me"
            )

        except Exception as error:
            print("Database waiting:", error)
            time.sleep(3)


db = connect_db()


# Redis connection
cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)


# MQTT connection callback
def on_connect(client, userdata, flags, reason_code, properties):

    print("MQTT Connected")

    client.subscribe("factory/machine/+")

    print("Subscribed to factory/machine/+")


# Receive machine data
def on_message(client, userdata, message):

    try:

        data = json.loads(message.payload.decode())
        data = validate_data(data)

        data = transform_data(data)

        anomaly, reason = detect_anomaly(data)

        temperature = data["temperature"]

        # Step 5: Store data in PostgreSQL
        with db:

            with db.cursor() as cursor:

                cursor.execute("""
                    INSERT INTO machines(machine_id, machine_name)
                    VALUES (%s, %s)
                    ON CONFLICT(machine_id)
                    DO UPDATE SET machine_name = EXCLUDED.machine_name
                """, (
                    data["machine_id"],
                    data.get("machine_name", data["machine_id"])
                ))

                cursor.execute("""
                    INSERT INTO machine_data (
                        machine_id, recorded_at, power, current,
                        temperature, production_count, status,
                        product_name, product_code,
                        stop_reason_code, is_anomaly, anomaly_reason
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    data["machine_id"],
                    data["timestamp"],
                    data.get("power"),
                    data.get("current"),
                    temperature,
                    data["production_count"],
                    data["status"],
                    data.get("product_name"),
                    data.get("product_code"),
                    data.get("stop_reason_code"),
                    anomaly,
                    reason
                ))

        # Step 6: Store latest data in Redis
        cache.set(
            f"machine:{data['machine_id']}:latest",
            json.dumps(data),
            ex=3600
        )

        # Step 7: Store machine-wise data in CSV
        file_path = CSV_DIR / f"{data['machine_id']}.csv"

        fields = [
            "machine_id", "timestamp", "power", "current",
            "temperature", "production_count", "status",
            "product_name", "product_code",
            "stop_reason_code", "is_anomaly", "anomaly_reason"
        ]

        file_exists = file_path.exists()

        with open(file_path, "a", newline="", encoding="utf-8") as file:

            writer = csv.DictWriter(file, fieldnames=fields)

            if not file_exists:
                writer.writeheader()

            row = {key: data.get(key) for key in fields}

            row["is_anomaly"] = anomaly
            row["anomaly_reason"] = reason

            writer.writerow(row)

        print("Data stored:", data["machine_id"])

    except Exception as error:

        print("Processing error:", error)


# MQTT client setup
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="machine_consumer"
)

client.on_connect = on_connect
client.on_message = on_message


# Connect to MQTT broker
while True:

    try:

        client.connect(
            os.getenv("MQTT_HOST", "localhost"),
            1883,
            60
        )

        break

    except Exception as error:

        print("MQTT waiting:", error)
        time.sleep(3)


# Continuously receive messages
client.loop_forever()
