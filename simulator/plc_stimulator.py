import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


# ============================================================
# MQTT CONFIGURATION
# ============================================================

BROKER = "192.168.1.107"
PORT = 1883
TOPIC = "dadin_kowa/plc/data"

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

    unit1_mw = vary_value(18.50)
    unit2_mw = vary_value(18.50)

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
                vary_value(245.06),

            "TAILRACE_LEVEL_M":
                vary_value(215.78),

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


    # --------------------------------------------------------
    # Connect to MQTT broker
    # --------------------------------------------------------

    try:

        print("======================================")
        print(" Dadinkowa RTD PLC Simulator")
        print("======================================")

        print(
            f"MQTT Broker : {BROKER}:{PORT}"
        )

        print(
            f"MQTT Topic  : {TOPIC}"
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
            BROKER,
            PORT,
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
                TOPIC,
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