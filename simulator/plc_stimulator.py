import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


BROKER = "192.168.1.107"
PORT = 1883
TOPIC = "dadin_kowa/plc/data"
PUBLISH_INTERVAL = 3

# ============================================================
# SIMULATION MODE
# ============================================================
# Available modes:
#
# "NORMAL"
# "UNIT1_SHUTDOWN"
# "UNIT2_SHUTDOWN"
# "BOTH_SHUTDOWN"
#
# Change ONLY this value when you want to test a condition.
# ============================================================

TEST_MODE = "NORMAL"


def create_telemetry(sequence):

    # Normal operating values
    unit1_mw = 17.20
    unit2_mw = 17.05

    unit1_status = "Generating"
    unit2_status = "Generating"

    # ========================================================
    # Apply simulation condition
    # ========================================================

    if TEST_MODE == "UNIT1_SHUTDOWN":

        unit1_mw = 0.00
        unit1_status = "Shutdown"

    elif TEST_MODE == "UNIT2_SHUTDOWN":

        unit2_mw = 0.00
        unit2_status = "Shutdown"

    elif TEST_MODE == "BOTH_SHUTDOWN":

        unit1_mw = 0.00
        unit2_mw = 0.00

        unit1_status = "Shutdown"
        unit2_status = "Shutdown"

    elif TEST_MODE != "NORMAL":

        print(f"WARNING: Unknown TEST_MODE '{TEST_MODE}'")
        print("Falling back to NORMAL mode.")

    # ========================================================
    # Create telemetry message
    # ========================================================

    return {
        "seq": sequence,

        "timestamp_utc":
            datetime.now(timezone.utc).isoformat(),

        "source":
            "rtd_plc_simulator",

        "unit_id":
            "PLANT",

        "values": {

            "UNIT1_ACTIVE_POWER_MW":
                unit1_mw,

            "UNIT2_ACTIVE_POWER_MW":
                unit2_mw,

            "TOTAL_ACTIVE_POWER_MW":
                unit1_mw + unit2_mw,

            "UPSTREAM_LEVEL_M":
                243.31,

            "TAILRACE_LEVEL_M":
                215.30,

            "GRID_FREQUENCY_HZ":
                50.00,

            "GRID_VOLTAGE_KV":
                132.00,

            "UNIT1_STATUS":
                unit1_status,

            "UNIT2_STATUS":
                unit2_status
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
    print(f"TEST MODE   : {TEST_MODE}")
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

                values = telemetry["values"]

                print(
                    f"[{sequence}] "
                    f"U1={values['UNIT1_ACTIVE_POWER_MW']:.2f} MW "
                    f"({values['UNIT1_STATUS']}) | "
                    f"U2={values['UNIT2_ACTIVE_POWER_MW']:.2f} MW "
                    f"({values['UNIT2_STATUS']}) | "
                    f"Total={values['TOTAL_ACTIVE_POWER_MW']:.2f} MW | "
                    f"Upstream={values['UPSTREAM_LEVEL_M']:.2f} m | "
                    f"Tailrace={values['TAILRACE_LEVEL_M']:.2f} m"
                )

            else:

                print(
                    f"[{sequence}] "
                    f"MQTT publish failed: {result.rc}"
                )

            sequence += 1

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:

        print("\nSimulator stopped.")

    finally:

        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
