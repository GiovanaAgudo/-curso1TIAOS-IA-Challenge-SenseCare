"""
Mock Cloud Receiver — Sense&Care
Simula um endpoint HTTP de ingestão de eventos, para testes locais.

Executa um servidor FastAPI simples em :9000 com um endpoint /ingest
que aceita POST {"events": [...]}. Ele imprime os eventos recebidos
e retorna um resumo da operação.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncio

app = FastAPI(title="Mock Cloud Receiver — Sense&Care")

@app.post("/ingest")
async def ingest(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    events = body.get("events", [])
    count = len(events)

    print("\n=== Novo lote recebido ===")
    print(f"Horário: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Eventos: {count}")
    if count:
        sample = events[0]
        print(f"Exemplo: {sample.get('event_type')} (id: {sample.get('totem_id')})")

    # Simula um pequeno atraso de rede
    await asyncio.sleep(0.5)

    return {"status": "ok", "received": count}

@app.get("/health")
async def health():
    return {"ok": True, "msg": "Mock Cloud ativo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
