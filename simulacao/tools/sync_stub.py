"""
Sync Stub — Sense&Care
Lê eventos pendentes (synced=0) do queue.db em lotes, 'envia' para a nuvem
(CLOUD_ENDPOINT) ou salva em arquivo JSONL (OUTPUT_FILE) e marca synced=1.

Env vars:
  DB_PATH=queue.db
  BATCH_SIZE=200
  MAX_PER_RUN=0        # 0 = sem limite (roda tudo)
  CLOUD_ENDPOINT=      # ex: https://mock.cloud/ingest  (se vazio, usa OUTPUT_FILE)
  CLOUD_TIMEOUT=5
  OUTPUT_FILE=./synced_events.jsonl
  DRY_RUN=false        # true = não marca synced
  LOOP=false           # true = roda em loop
  LOOP_INTERVAL=5      # segundos entre ciclos
"""

import os, sqlite3, json, time, logging
from datetime import datetime, timezone

import contextlib
try:
    import httpx
except Exception:
    httpx = None

DB_PATH       = os.getenv("DB_PATH", "queue.db")
BATCH_SIZE    = int(os.getenv("BATCH_SIZE", "200"))
MAX_PER_RUN   = int(os.getenv("MAX_PER_RUN", "0"))
CLOUD_ENDPOINT= os.getenv("CLOUD_ENDPOINT", "").strip()
CLOUD_TIMEOUT = float(os.getenv("CLOUD_TIMEOUT", "5"))
OUTPUT_FILE   = os.getenv("OUTPUT_FILE", "./synced_events.jsonl")
DRY_RUN       = os.getenv("DRY_RUN", "false").lower() == "true"
LOOP          = os.getenv("LOOP", "false").lower() == "true"
LOOP_INTERVAL = float(os.getenv("LOOP_INTERVAL", "5"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sync-stub")

def utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def fetch_batch(con, limit):
    cur = con.cursor()
    cur.execute("""
        SELECT id, ts, event_json
        FROM events
        WHERE synced=0
        ORDER BY ts ASC
        LIMIT ?
    """, (limit,))
    return cur.fetchall()

def mark_synced(con, ids):
    if not ids: return
    cur = con.cursor()
    now_ms = int(time.time() * 1000)
    qmarks = ",".join("?" for _ in ids)
    cur.execute(f"UPDATE events SET synced=1, synced_at=? WHERE id IN ({qmarks})", (now_ms, *ids))
    con.commit()

def send_to_cloud(payloads):
    """Envia lista de eventos para endpoint HTTP (JSON). Retorna True/False."""
    if not CLOUD_ENDPOINT:
        return False
    if httpx is None:
        raise RuntimeError("httpx não instalado. pip install httpx")
    try:
        with httpx.Client(timeout=CLOUD_TIMEOUT) as client:
            r = client.post(CLOUD_ENDPOINT, json={"events": payloads})
            if r.status_code // 100 == 2:
                return True
            log.warning("cloud status=%s body=%s", r.status_code, r.text[:200])
            return False
    except Exception as e:
        log.error("cloud error: %s", e)
        return False

def append_jsonl(file_path, payloads):
    with open(file_path, "a", encoding="utf-8") as f:
        for p in payloads:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

def run_once():
    total_synced = 0
    with contextlib.closing(get_conn()) as con:
        processed = 0
        while True:
            left = MAX_PER_RUN - processed if MAX_PER_RUN else BATCH_SIZE
            if left <= 0: break
            batch_size = min(BATCH_SIZE, left) if MAX_PER_RUN else BATCH_SIZE

            rows = fetch_batch(con, batch_size)
            if not rows:
                break

            ids = [r["id"] for r in rows]
            payloads = []
            for r in rows:
                try:
                    ev = json.loads(r["event_json"])
                except Exception:
                    ev = {"_corrupt": r["event_json"]}
                # acrescenta metadados de sync (úteis no mock/dashboard)
                ev["_synced_at"] = utc_iso()
                ev["_source_ts"] = r["ts"]
                payloads.append(ev)

            sent_ok = False
            if CLOUD_ENDPOINT:
                sent_ok = send_to_cloud(payloads)
            if not CLOUD_ENDPOINT or not sent_ok:
                append_jsonl(OUTPUT_FILE, payloads)
                sent_ok = True  # consideramos OK ao persistir no JSONL

            if sent_ok and not DRY_RUN:
                mark_synced(con, ids)
                total_synced += len(ids)

            processed += len(rows)
            log.info("lote processado: %s eventos (acumulado=%s)", len(rows), processed)

    return total_synced

def main():
    log.info("Sync stub iniciado | db=%s | endpoint=%s | file=%s | dry_run=%s",
             DB_PATH, CLOUD_ENDPOINT or "(jsonl)", OUTPUT_FILE, DRY_RUN)
    if LOOP:
        while True:
            synced = run_once()
            if synced == 0:
                time.sleep(LOOP_INTERVAL)
            else:
                # se sincronizou algo, tenta de novo logo (pode haver mais páginas)
                time.sleep(0.2)
    else:
        synced = run_once()
        log.info("Concluído. Eventos sincronizados: %s", synced)

if __name__ == "__main__":
    main()
