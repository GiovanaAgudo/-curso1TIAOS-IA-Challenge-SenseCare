Sense&Care — Totem Inteligente de Acessibilidade e Inclusão

1 - O Sense&Care é um totem inteligente acessível projetado para transformar espaços físicos em ambientes verdadeiramente inclusivos.
Integrando voz, toque, LIBRAS, sensores e IA ética, ele oferece uma experiência personalizada, permitindo que qualquer pessoa — com ou sem deficiência — acesse informações e interaja com autonomia.

Este repositório contém uma simulação completa do funcionamento técnico do totem, desde a coleta de dados sensoriais (MQTT) até o processamento no Edge (FastAPI) e sincronização com a nuvem (mock cloud).

2 - Estrutura do Projeto

    simulacao/
    ├── app/              # Edge backend (FastAPI + SQLite + MQTT)
    │   ├── app.py
    │   ├── queue.db
    │   └── requirements.txt
    │
    ├── sims/             # Simuladores (sensores, sessões)
    │   ├── mqtt_publisher.py
    │   └── sessions_generator.py
    │
    └── tools/            # Ferramentas auxiliares
        ├── sync_stub.py
        └── mock_cloud.py


3 - O que está sendo simulado:
Camada	                                Descrição
Edge (app.py)	                        Recebe dados de sensores e interações, salva em SQLite e expõe APIs HTTP/WebSocket.
Simuladores (sims/)	                    Publicam eventos via MQTT e HTTP, representando sensores e interações humanas.
Sync Stub (tools/sync_stub.py)	        Envia os eventos coletados no Edge para um mock de nuvem ou arquivo local.
Mock Cloud (tools/mock_cloud.py)	    API FastAPI simples que simula o backend da nuvem, recebendo eventos e exibindo logs.   


4 - Roteiro de Execução
Siga a ordem abaixo no Powershell para reproduzir toda a simulação (funciona em Windows, macOS e Linux):

    *Instalar dependências*
    cd simulacao/app
    python -m venv .venv
    source .venv/bin/activate      
    # Opção Windows abaixo: 
        py -3 -m venv .venv
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
        .\.venv\Scripts\Activate.ps1
        pip install -r requirements.txt

    *Iniciar o broker MQTT*
    #Instalar Docker
    docker run --name mqtt -p 1883:1883 -d eclipse-mosquitto

    *Subir o backend do totem (Edge)*
    cd ../app
    uvicorn app:app --reload --port 8000
    # Testar: http://localhost:8000/health

    *Simular sensores (MQTT)*
    cd ../sims
    python mqtt_publisher.py

    *Simular sessões de interação (HTTP)*
    cd ../sims
    python sessions_generator.py

    *Rodar o mock da nuvem*
    cd ../tools
    python mock_cloud.py
    # Abre em http://localhost:9000/ingest

    *Sincronizar dados do Edge com a nuvem*
    cd simulacao/tools
    $env:DB_PATH = "..\app\queue.db"
    $env:CLOUD_ENDPOINT = "http://localhost:9000/ingest"
    python sync_stub.py

5 - Tecnologias Principais
    - FastAPI + Uvicorn — backend leve e moderno (Edge)
    - Paho-MQTT — comunicação com sensores via protocolo MQTT
    - HTTPX — simulação de sessões e sincronização
    - SQLite — armazenamento local dos eventos
    - Docker (Mosquitto) — broker MQTT local

6 - Política de Privacidade

O sistema não coleta nenhum dado pessoal identificável.
Todos os eventos são anônimos e usados apenas para métricas de acessibilidade e desempenho.

7 - Autora
Giovana de Oliveira Agudo
Projeto acadêmico desenvolvido no Challenge FlexMedia — FIAP 2025,
Sprint 1: Prototipação de Arquitetura e Estratégia de Dados Simulada,
