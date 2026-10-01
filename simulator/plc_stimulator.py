import os
from pathlib import Path
from dotenv import load_dotenv

import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables
load_dotenv(ENV_FILE)


# ============================================================
# MQTT CONFIGURATION
# ============================================================
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

required_vars = {
    "MQTT_BROKER": MQTT_BROKER,
    "MQTT_TOPIC": MQTT_TOPIC,
    "MQTT_USERNAME": MQTT_USERNAME,
    "MQTT_PASSWORD": MQTT_PASSWORD,
}

missing = [name for name, value in required_vars.items() if not value]

if missing:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing)}"
    )


PUBLISH_INTERVAL = 2

# ============================================================
# SIMULATION MODE
# ============================================================
#
# Available modes:
#
# "NORMAL"
# "UNIT1_SHUTDOWN"
# "UNIT2_SHUTDOWN"
# "BOTH_SHUTDOWN"
# "COMMUNICATION_LOST"
#
# Change ONLY TEST_MODE when you want to test a condition.
#
# IMPORTANT:
#
# COMMUNICATION_LOST does NOT publish a special message.
# Instead, the simulator stops publishing telemetry.
# This allows the RTD backend/dashboard to detect a genuine
# communication timeout.
# ============================================================

TEST_MODE = "NORMAL"

VARIATION = 0.02


# ============================================================
# VALUE VARIATION
# ============================================================

def vary_value(nominal):
    """
    Return a value randomly varied by +/- 2%
    from its nominal value.
    """

    variation = random.uniform(
        -VARIATION,
        VARIATION
    )

    return nominal * (1 + variation)


# ============================================================
# CREATE TELEMETRY
# ============================================================

def create_telemetry(sequence):

    # --------------------------------------------------------
    # Normal operating values
    # --------------------------------------------------------

    unit1_mw = vary_value(20.00)
    unit2_mw = vary_value(20.00)

    unit1_status = "Generating"
    unit2_status = "Generating"


    # --------------------------------------------------------
    # Apply simulation condition
    # --------------------------------------------------------

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


    elif TEST_MODE == "COMMUNICATION_LOST":

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # This mode is handled in main().
        #
        # We still return telemetry here so the function
        # remains valid, but main() will NOT publish it.
        # ----------------------------------------------------

        pass


    elif TEST_MODE != "NORMAL":

        print(
            f"WARNING: Unknown TEST_MODE '{TEST_MODE}'"
        )

        print(
            "Falling back to NORMAL mode."
        )


    # --------------------------------------------------------
    # Create telemetry message
    # --------------------------------------------------------

    return {

        "seq": sequence,

        "timestamp_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

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
                vary_value(246.56),

            "TAILRACE_LEVEL_M":
                vary_value(215.15),

            "GRID_FREQUENCY_HZ":
                vary_value(50.00),

            "GRID_VOLTAGE_KV":
                vary_value(132.00),

            "UNIT1_STATUS":
                unit1_status,

            "UNIT2_STATUS":
                unit2_status
        }
    }


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Create MQTT client
    # --------------------------------------------------------

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="rtd_plc_simulator"
    )

    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
#     client.tls_set(
#     ca_certs=r"D:\RTD-project\certs\ca.crt"
# )



    # --------------------------------------------------------
    # Connect to MQTT broker
    # --------------------------------------------------------

    try:

        print("======================================")
        print(" Dadinkowa RTD PLC Simulator")
        print("======================================")

        print(
            f"MQTT Broker : {MQTT_BROKER}:{MQTT_PORT}"
        )

        print(
            f"MQTT Topic  : {MQTT_TOPIC}"
        )

        print(
            f"Interval    : {PUBLISH_INTERVAL} seconds"
        )

        print(
            f"TEST MODE   : {TEST_MODE}"
        )

        print(
            f"Variation   : +/- {VARIATION * 100:.0f}%"
        )

        print(
            "Press Ctrl+C to stop."
        )

        print()


        client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            60
        )

        client.loop_start()


    except Exception as e:

        print(
            f"MQTT connection failed: {e}"
        )

        return


    # --------------------------------------------------------
    # Sequence counter
    # --------------------------------------------------------

    sequence = 1


    try:

        while True:

            # =================================================
            # COMMUNICATION LOST MODE
            # =================================================
            #
            # Do NOT publish telemetry.
            #
            # The last telemetry message remains in the
            # backend, allowing the backend/dashboard to
            # determine that the data has become stale.
            # =================================================

            if TEST_MODE == "COMMUNICATION_LOST":

                print(
                    "COMMUNICATION_LOST | "
                    "Telemetry publishing stopped."
                )

                time.sleep(
                    PUBLISH_INTERVAL
                )

                continue


            # =================================================
            # NORMAL / UNIT SHUTDOWN MODES
            # =================================================

            telemetry = create_telemetry(
                sequence
            )

            payload = json.dumps(
                telemetry
            )


            # ------------------------------------------------
            # Publish telemetry
            # ------------------------------------------------

            result = client.publish(
                MQTT_TOPIC,
                payload,
                qos=1
            )


            # ------------------------------------------------
            # Display result
            # ------------------------------------------------

            if result.rc == mqtt.MQTT_ERR_SUCCESS:

                values = telemetry["values"]

                print(

                    f"[{sequence}] "

                    f"U1="
                    f"{values['UNIT1_ACTIVE_POWER_MW']:.2f} MW "
                    f"({values['UNIT1_STATUS']}) | "

                    f"U2="
                    f"{values['UNIT2_ACTIVE_POWER_MW']:.2f} MW "
                    f"({values['UNIT2_STATUS']}) | "

                    f"Total="
                    f"{values['TOTAL_ACTIVE_POWER_MW']:.2f} MW | "

                    f"Upstream="
                    f"{values['UPSTREAM_LEVEL_M']:.2f} m | "

                    f"Tailrace="
                    f"{values['TAILRACE_LEVEL_M']:.2f} m"

                )


            else:

                print(

                    f"[{sequence}] "
                    f"MQTT publish failed: "
                    f"{result.rc}"

                )


            # ------------------------------------------------
            # Increment sequence
            # ------------------------------------------------

            sequence += 1


            # ------------------------------------------------
            # Wait before next telemetry
            # ------------------------------------------------

            time.sleep(
                PUBLISH_INTERVAL
            )


    except KeyboardInterrupt:

        print(
            "\nSimulator stopped."
        )


    finally:

        client.loop_stop()

        client.disconnect()

        print(
            "MQTT connection closed."
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()