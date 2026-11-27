import json
import time
import random
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_HOST", "localhost")
PORT = 1883

machines = ["MC1001", "MC1002", "MC1003", "MC1004", "MC1005"]

products = [
    ("Industrial Pump", "PRD001"),
    ("Control Panel", "PRD002"),
    ("Motor Assembly", "PRD003")
]

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="machine_simulator"
)

while True:
    try:
        client.connect(BROKER, PORT, 60)
        break
    except Exception as error:
        print("Waiting for MQTT:", error)
        time.sleep(3)

client.loop_start()

status = {machine: 1 for machine in machines}
production = {machine: 100 for machine in machines}

while True:

    for machine in machines:

        if random.random() < 0.05:
            status[machine] = 1 - status[machine]

        product_name, product_code = random.choice(products)

        if status[machine] == 1:
            production[machine] += random.randint(1, 5)
            reason_code = None
        else:
            reason_code = random.choice(
                ["E101", "E102", "E103", "E104"]
            )

        data = {
            "machine_id": machine,
            "machine_name": "Production " + machine,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "power": round(random.uniform(4, 8), 2),
            "current": round(random.uniform(8, 15), 2),
            "temperature": round(random.uniform(35, 70), 2),
            "production_count": production[machine],
            "status": status[machine],
            "product_name": product_name,
            "product_code": product_code,
            "stop_reason_code": reason_code
        }

        topic = f"factory/machine/{machine}"

        client.publish(topic, json.dumps(data), qos=1)

        print("Published:", data)

    time.sleep(5)