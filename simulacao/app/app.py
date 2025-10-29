import os, time, json, sqlite3, threading, logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import paho.mqtt.client as mqtt

# -------------------- Config --------------------
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_SENSORS = os.getenv("MQTT_TOPIC_SENSORS", "fm/+/sensors/#")
MQTT_QOS = int(os.getenv("MQTT_QOS", "0"))
MQTT_TLS = os.getenv("MQTT_TLS", "false").lower() == "true"

DB_PATH = os.getenv("DB_PATH", "queue.db")
EVENT_MAX_BYTES = int(os.getenv("EVENT_MAX_BYTES", "8192"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sensecare-edge")

# -------------------- DB Wrapper --------------------
class DB:
    _lock = threading.Lock()
    _conn: Optional[sqlite3.Connection] = None

    @classmethod
    def conn(cls) -> sqlite3.Connection:
        if cls._conn is None:
            cls._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cls._conn.execute("PRAGMA journal_mode=WAL;")
            cls._conn.execute("PRAGMA synchronous=NORMAL;")
        return cls._conn

    @classmethod
    def init(cls):
        with cls._lock:
            c = cls.conn().cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts INTEGER NOT NULL,
              created_at INTEGER NOT NULL,
              event_json TEXT NOT NULL,
              source TEXT DEFAULT 'api',
              source_topic TEXT,
              synced INTEGER DEFAULT 0,
              synced_at INTEGER
            )""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_events_synced_ts ON events(synced, ts)")
            cls.conn().commit()

    @classmethod
    def enqueue(cls, event: dict, *, source="api", source_topic: Optional[str]=None):
        raw = json.dumps(event, ensure_ascii=False)
        if len(raw.encode("utf-8")) > EVENT_MAX_BYTES:
            raise ValueError("payload too large")
        now_ms = int(time.time() * 1000)
        ts = (
            event.get("timestamp")
            or event.get("ts")
            or now_ms
        )
        with cls._lock:
            cls.conn().execute(
                "INSERT INTO events (ts, created_at, event_json, source, source_topic, synced) "
                "VALUES (?, ?, ?, ?, ?, 0)",
                (int(ts if isinstance(ts, (int, float)) else now_ms), now_ms, raw, source, source_topic),
            )
            cls.conn().commit()

# -------------------- Models --------------------
class Event(BaseModel):
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    totem_id: str = "FM-LOCAL-01"
    session_id: str = "rotating-hash"
    event_type: str
    channel: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)

# -------------------- App --------------------
app = FastAPI(title="Sense&Care Edge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# -------------------- MQTT client --------------------
_mqtt = mqtt.Client()

def _mqtt_connect():
    if MQTT_TLS:
        _mqtt.tls_set()
    _mqtt.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("MQTT connected")
        client.subscribe(MQTT_TOPIC_SENSORS, qos=MQTT_QOS)
    else:
        log.error(f"MQTT connect failed rc={rc}")

def on_disconnect(client, userdata, rc):
    log.warning(f"MQTT disconnected rc={rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        payload = {"raw": msg.payload.decode("utf-8", "ignore")}
    event = {
        "totem_id": "FM-LOCAL-01",
        "session_id": "rotating-hash",
        "event_type": payload.get("event_type", "sensor_event"),
        "channel": "sensor",
        "context": payload.get("context", {}),
        "payload": payload.get("payload", {}),
        "source_topic": msg.topic
    }
    try:
        DB.enqueue(event, source="mqtt", source_topic=msg.topic)
    except Exception as e:
        log.exception(f"enqueue mqtt failed: {e}")

def start_mqtt_forever():
    _mqtt.on_connect = on_connect
    _mqtt.on_disconnect = on_disconnect
    _mqtt.on_message = on_message
    while True:
        try:
            _mqtt_connect()
            _mqtt.loop_forever(retry_first_connection=True)
        except Exception as e:
            log.error(f"MQTT loop error: {e}; retrying in 3s")
            time.sleep(3)

# -------------------- Lifecycle --------------------
@app.on_event("startup")
def startup():
    DB.init()
    threading.Thread(target=start_mqtt_forever, daemon=True).start()
    log.info("Edge started; DB ready and MQTT thread running")

# -------------------- Endpoints --------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/stats")
def stats():
    with DB._lock:
        cur = DB.conn().cursor()
        total = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        pend  = cur.execute("SELECT COUNT(*) FROM events WHERE synced=0").fetchone()[0]
    return {"events_total": total, "events_pending": pend}

@app.post("/events", status_code=201)
def post_event(ev: Event):
    data = ev.dict()
    try:
        DB.enqueue(data, source="api")
        return {"status": "enqueued", "type": ev.event_type}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=413)

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        await ws.send_text("connected")
        while True:
            msg = await ws.receive_text()
            await ws.send_text(f"ack:{msg}")
    except WebSocketDisconnect:
        log.info("websocket disconnected")
    except Exception as e:
        log.error(f"ws error: {e}")
    finally:
        try:
            await ws.close()
        except Exception:
            pass
