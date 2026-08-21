import json
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn


MQTT_BROKER = "192.168.1.107"
MQTT_PORT = 1883
MQTT_TOPIC = "dadin_kowa/plc/data"

app = FastAPI(title="Dadinkowa RTD Backend")

latest_data = {}
data_lock = threading.Lock()


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker: {reason_code}")
    client.subscribe(MQTT_TOPIC, qos=1)
    print(f"Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    global latest_data

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        with data_lock:
            latest_data = payload

        print(
            f"Telemetry received | "
            f"Sequence: {payload.get('seq')}"
        )

    except Exception as e:
        print(f"Telemetry processing error: {e}")


mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="rtd_backend"
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


@app.on_event("startup")
def startup_event():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("RTD backend started")


@app.on_event("shutdown")
def shutdown_event():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


@app.get("/")
def root():
    return {
        "application": "Dadinkowa RTD Backend",
        "status": "running"
    }


@app.get("/api/telemetry")
def get_telemetry():
    with data_lock:
        return latest_data


@app.get("/api/health")
def health():
    with data_lock:
        telemetry_available = bool(latest_data)

    return {
        "status": "ok",
        "telemetry_available": telemetry_available,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/display")
def display():
    return FileResponse("dashboard/index.html")

@app.get("/display/mabon-logo.png")
def mabon_logo():
    return FileResponse("dashboard/mabon-logo.png")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )