import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "192.168.1.107"
PORT = 1883
TOPIC = "dadin_kowa/plc/data"

seq = 1

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="rtd_plc_simulator"
)

client.connect(BROKER, PORT, 60)
client.loop_start()

print("PLC simulator started.")
print(f"Publishing to {TOPIC}")
print("Press Ctrl+C to stop.")

try:
    while True:

        # Simulated Dadinkowa plant values
        unit1_mw = 17.20
        unit2_mw = 17.05

        values = {
            "UNIT1_ACTIVE_POWER_MW": unit1_mw,
            "UNIT2_ACTIVE_POWER_MW": unit2_mw,
            "TOTAL_ACTIVE_POWER_MW": unit1_mw + unit2_mw,

            "UPSTREAM_LEVEL_M": 243.31,
            "TAILRACE_LEVEL_M": 215.30,

            "GRID_FREQUENCY_HZ": 50.00,
            "GRID_VOLTAGE_KV": 132.00,

            "UNIT1_STATUS": 1,
            "UNIT2_STATUS": 1,

            "PLANT_STATUS": 1
        }

        payload = {
            "seq": seq,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source": "rtd_plc_simulator",
            "unit_id": "PLANT",
            "stale_sources": [],
            "values": values
        }

        client.publish(
            TOPIC,
            json.dumps(payload),
            qos=1
        )

        print(json.dumps(payload, indent=2))

        seq += 1
        time.sleep(5)

except KeyboardInterrupt:
    print("\nPLC simulator stopped.")

finally:
    client.loop_stop()
    client.disconnect()