import os
import json
import time
import uuid
import random
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

# ---------------------- Configuração via ENV / defaults ----------------------
MQTT_HOST          = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT          = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TLS           = os.getenv("MQTT_TLS", "0") in ("1", "true", "True")
MQTT_QOS           = int(os.getenv("MQTT_QOS", "0"))  # 0/1/2
TOPIC_BASE         = os.getenv("TOPIC_BASE", "fm/zoo01")
TOTEM_ID           = os.getenv("TOTEM_ID", "FM-LOCAL-01")
SESSION_ID         = os.getenv("SESSION_ID", "rotating-hash")

HEARTBEAT_EVERY    = float(os.getenv("HEARTBEAT_EVERY", "10"))  # s
PUBLISH_INTERVAL   = float(os.getenv("PUBLISH_INTERVAL", "2.0")) # s
MAX_EVENTS         = int(os.getenv("MAX_EVENTS", "0"))  # 0 = infinito

LOG_LEVEL          = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("publisher")


# ----------------------------- Utilitários -----------------------------------
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def mk_event(event_type: str, context=None, payload=None, channel="sensor") -> dict:
    """Evento com ID e metadados padronizados."""
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "totem_id": TOTEM_ID,
        "session_id": SESSION_ID,
        "event_type": event_type,
        "channel": channel,
        "context": context or {},
        "payload": payload or {},
    }


def topic(path: str) -> str:
    return f"{TOPIC_BASE}/{path}"


# ------------------------------ MQTT -----------------------------------------
client = mqtt.Client()

def connect():
    # Last Will (se cair sem encerrar, fica 'offline')
    client.will_set(
        topic("status"),
        json.dumps({"status": "offline"}),
        qos=MQTT_QOS,
        retain=True,
    )
    if MQTT_TLS:
        # usa CA do sistema; para CA customizada, setar client.tls_set(cafile=...)
        client.tls_set()
        log.info("MQTT com TLS habilitado")

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    # Sinaliza 'online' (retain=True p/ monitores)
    client.publish(topic("status"), json.dumps({"status": "online"}), qos=MQTT_QOS, retain=True)


def disconnect_gracefully():
    try:
        client.publish(topic("status"), json.dumps({"status": "offline"}), qos=MQTT_QOS, retain=True)
    except Exception:
        pass
    try:
        client.loop_stop()
        client.disconnect()
    except Exception:
        pass


def pub(path: str, obj: dict):
    client.publish(topic(path), json.dumps(obj), qos=MQTT_QOS, retain=False)


# --------------------------------- Main --------------------------------------
def main():
    connect()
    log.info("Simulator started: host=%s port=%s base=%s", MQTT_HOST, MQTT_PORT, TOPIC_BASE)

    last_hb = 0.0
    count   = 0

    try:
        while True:
            now = time.time()

            # Heartbeat periódico
            if now - last_hb >= HEARTBEAT_EVERY:
                hb = {"ts": now_iso(), "queue": 0}
                pub("status/heartbeat", mk_event("heartbeat", channel="system", payload=hb))
                last_hb = now

            # Sensores simulados
            presence  = random.random() < 0.6
            lux       = random.randint(50, 400)
            distance  = random.randint(30, 200)

            pub("sensors/presence", mk_event("presence_detected", context={"presence": presence}))
            pub("sensors/lux",      mk_event("ambient_lux", payload={"lux": lux}))
            pub("sensors/distance", mk_event("distance_cm", payload={"cm": distance}))

            # Botão (10% de chance)
            if random.random() < 0.10:
                pub("sensors/button", mk_event("button_pressed", payload={"button": "access"}))

            count += 4
            log.info("published batch (presence,lux,distance[,button])")

            if MAX_EVENTS and count >= MAX_EVENTS:
                log.info("MAX_EVENTS reached (%s). Exiting.", count)
                break

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        log.info("Interrupted by user (Ctrl+C).")
    finally:
        disconnect_gracefully()
        log.info("MQTT stopped.")


if __name__ == "__main__":
    main()
