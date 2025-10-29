import os, asyncio, random, string
from datetime import datetime, timezone
import httpx

# ---------------- Config por ENV ----------------
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
SESSIONS = int(os.getenv("SESSIONS", "30"))          # número de sessões a simular
PARALLEL = int(os.getenv("PARALLEL", "3"))           # sessões em paralelo
TOTEM_ID = os.getenv("TOTEM_ID", "FM-LOCAL-01")
LOCALE = os.getenv("LOCALE", "pt-BR")

MODES_POOL = [
    [], ["high_contrast"], ["libras"], ["font_xl"],
    ["high_contrast","libras"], ["libras","font_xl"]
]
CHANNELS = ["touch", "voice", "no_touch"]            # canal principal da sessão
CONTENTS = [
    "rota_acessivel_banheiro", "mapa_principal",
    "ingressos", "alimentacao", "ajuda_acessibilidade"
]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def rand_session_id(n=10):
    alphabet = string.ascii_lowercase + string.digits
    return "sess-" + "".join(random.choice(alphabet) for _ in range(n))

def mk_event(event_type, channel, session_id, context=None, payload=None):
    return {
        "timestamp": now_iso(),
        "totem_id": TOTEM_ID,
        "session_id": session_id,
        "event_type": event_type,
        "channel": channel,
        "context": {"locale": LOCALE, **(context or {})},
        "payload": payload or {}
    }

async def send(client: httpx.AsyncClient, ev: dict):
    try:
        r = await client.post(f"{API_BASE}/events", json=ev, timeout=5.0)
        if r.status_code != 201:
            print(f"[WARN] {ev['event_type']} -> status {r.status_code}: {r.text[:120]}")
        else:
            # print enxuto para não poluir muito o terminal
            print(f"[OK] {ev['event_type']} ({ev['channel']})")
    except httpx.HTTPError as e:
        print(f"[ERR] {ev['event_type']} http error: {e!s}")

async def run_one_session(client: httpx.AsyncClient, idx: int):
    session_id = rand_session_id()
    channel = random.choice(CHANNELS)
    modes = random.choice(MODES_POOL)

    # 1) Consent / preferências
    ev = mk_event("consent_updated", channel, session_id,
                  context={"modes_enabled": modes}, payload={})
    await send(client, ev)
    await asyncio.sleep(random.uniform(0.1, 0.5))

    # 2) Início da interação
    await send(client, mk_event("interaction_started", channel, session_id))
    await asyncio.sleep(random.uniform(0.2, 0.8))

    # 3) Seleção de conteúdo (1 a 3 cliques)
    clicks = random.randint(1, 3)
    for _ in range(clicks):
        content_id = random.choice(CONTENTS)
        await send(client, mk_event("content_selected", channel, session_id,
                                    payload={"content_id": content_id}))
        await asyncio.sleep(random.uniform(0.2, 1.0))

    # 4) Encerramento (com dwell aleatório)
    dwell = random.randint(6000, 30000)
    await send(client, mk_event("interaction_ended", channel, session_id,
                                payload={"dwell_ms": dwell}))
    await asyncio.sleep(random.uniform(0.1, 0.4))

    # 5) Feedback (nem toda sessão envia)
    if random.random() < 0.6:
        csat = random.randint(3, 5)
        comment = "" if random.random() < 0.8 else "Atendimento acessível e claro."
        await send(client, mk_event("feedback_submitted", channel, session_id,
                                    payload={"csat": csat, "comment": comment}))

async def main():
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    async with httpx.AsyncClient(limits=limits, headers={"Content-Type":"application/json"}) as client:
        # executa em lotes para limitar paralelismo
        tasks = []
        for i in range(SESSIONS):
            tasks.append(run_one_session(client, i))
            if len(tasks) >= PARALLEL:
                await asyncio.gather(*tasks)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
