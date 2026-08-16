import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


BROKER = "192.168.1.107"
PORT = 1883
TOPIC = "dadin_kowa/plc/data"
PUBLISH_INTERVAL = 3


def create_telemetry(sequence):
    unit1_mw = 17.20
    unit2_mw = 17.05

    return {
        "seq": sequence,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": "rtd_plc_simulator",
        "unit_id": "PLANT",
        "values": {
            "UNIT1_ACTIVE_POWER_MW": unit1_mw,
            "UNIT2_ACTIVE_POWER_MW": unit2_mw,
            "TOTAL_ACTIVE_POWER_MW": unit1_mw + unit2_mw,

            "UPSTREAM_LEVEL_M": 243.31,
            "TAILRACE_LEVEL_M": 215.30,

            "GRID_FREQUENCY_HZ": 50.00,
            "GRID_VOLTAGE_KV": 132.00,

            "UNIT1_STATUS": "Generating",
            "UNIT2_STATUS": "Generating"
        }
    }


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="rtd_plc_simulator"
    )

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    print("======================================")
    print(" Dadinkowa RTD PLC Simulator")
    print("======================================")
    print(f"MQTT Broker : {BROKER}:{PORT}")
    print(f"MQTT Topic  : {TOPIC}")
    print(f"Interval    : {PUBLISH_INTERVAL} seconds")
    print("Press Ctrl+C to stop.")
    print()

    sequence = 1

    try:
        while True:
            telemetry = create_telemetry(sequence)

            payload = json.dumps(telemetry)

            result = client.publish(
                TOPIC,
                payload,
                qos=1
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"[{sequence}] "
                    f"U1={telemetry['values']['UNIT1_ACTIVE_POWER_MW']:.2f} MW | "
                    f"U2={telemetry['values']['UNIT2_ACTIVE_POWER_MW']:.2f} MW | "
                    f"Total={telemetry['values']['TOTAL_ACTIVE_POWER_MW']:.2f} MW | "
                    f"Upstream={telemetry['values']['UPSTREAM_LEVEL_M']:.2f} m | "
                    f"Tailrace={telemetry['values']['TAILRACE_LEVEL_M']:.2f} m"
                )
            else:
                print(f"[{sequence}] MQTT publish failed: {result.rc}")

            sequence += 1
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()