## Sense&Care — Totem Inteligente de Acessibilidade e Inclusão

## Sprint 1
## 1 - Introdução e Justificativa do Problema
O Sense&Care nasce da necessidade de transformar espaços físicos em ambientes inclusivos e acessíveis, especialmente em locais públicos, culturais e corporativos.
Pessoas com deficiência visual, auditiva, motora ou múltipla ainda enfrentam barreiras ao buscar informações simples — desde orientações até serviços de atendimento.

O projeto propõe uma solução tecnológica humanizada que une voz, toque, LIBRAS e IA ética, garantindo que qualquer pessoa possa interagir com autonomia, privacidade e conforto.

Descrição da Solução:
O Sense&Care é um totem inteligente de acessibilidade que integra sensores físicos (ESP32), software embarcado (Edge) e uma camada simulada de nuvem.
Ele detecta presença, ajusta luminosidade, interpreta interações e coleta métricas de uso — sempre com anonimização e privacidade por padrão.

A arquitetura desenvolvida nesta Sprint simula todo o fluxo de dados:
Coleta sensorial → Processamento no Edge → Sincronização com a nuvem → Dashboards de acessibilidade.

----

## 2 - Estrutura do Projeto
    SENSE-CARE-CHALLENGE/
    │
    ├── README.md                            # Documento principal do projeto
    │
    ├── /docs                                # Documentação técnica e conceitual
    │   ├── arquitetura.drawio               # Diagrama integrado (link para os outros 3)
    │   ├── escopo.md                        # Definição do problema e proposta
    │   ├── coleta_dados.md                  # Estratégia de coleta, simulação e privacidade
    │   ├── plano_desenvolvimento.md         # LGPD + cronograma + papéis
    │   └── tecnologias.md                   # Linguagens, frameworks e serviços
    │
    ├── /simulacao                           # Scripts e simulações do Sense&Care
    │   ├── /app
    │   │   ├── app.py
    │   │   ├── queue.db
    │   │   ├── queue.db-shm
    │   │   ├── queue.db-wal
    │   │   └── requirements.txt
    │   │
    │   ├── /sims
    │   │   ├── mqtt_publisher.py
    │   │   ├── sessions_generator.py
    │   │
    │   ├── /tools
    │   │   ├── mock_cloud.py
    │   │   └── sync_stub.py
    │   │
    │   └── .env
    │
    └── /diagramas                          
        ├── diag_sensecare_cloud_pipeline.png
        ├── diag_sensecare_hardware.png
        └── diag_sensecare_software_edge.png

----

## 3 - O que está sendo simulado:
Camada	                                Descrição
Edge (app.py)	                        Recebe dados de sensores e interações, salva em SQLite e expõe APIs HTTP/WebSocket.
Simuladores (sims/)	                    Publicam eventos via MQTT e HTTP, representando sensores e interações humanas.
Sync Stub (tools/sync_stub.py)	        Envia os eventos coletados no Edge para um mock de nuvem ou arquivo local.
Mock Cloud (tools/mock_cloud.py)	    API FastAPI simples que simula o backend da nuvem, recebendo eventos e exibindo logs.   

----

## 4 - Roteiro de Execução
Siga a ordem abaixo no Powershell para reproduzir toda a simulação (funciona em Windows, macOS e Linux):

    *Instalar dependências*
    cd simulacao/app
    python -m venv .venv source .venv/bin/activate      
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

----

## 5 - Tecnologias Principais
    - FastAPI + Uvicorn — backend leve e moderno (Edge)
    - Paho-MQTT — comunicação com sensores via protocolo MQTT
    - HTTPX — simulação de sessões e sincronização
    - SQLite — armazenamento local dos eventos
    - Docker (Mosquitto) — broker MQTT local

----

## 6 - Arquitetura (com Diagramas)
Os diagramas completos estão na pasta /diagramas/:
    Hardware Edge – sensores e ESP32 (diag_sensecare_hardware.png)
    Software Edge – processamento local e fila (diag_sensecare_software_edge.png)
    Cloud Pipeline – fluxo até dashboards e relatórios (diag_sensecare_cloud_pipeline.png)

Fluxo resumido:
    Sensores → MQTT Broker → FastAPI (Edge) → SQLite Queue → Sync Stub → Mock Cloud → Dashboards

----

## 7 - Estratégia de Coleta e Segurança
    Nenhum dado pessoal é armazenado.
    IDs são pseudonimizados e rotativos (session_id).
    Eventos: presence_detected, ambient_lux, button_pressed, interaction_started, etc.
    Dados trafegam via TLS e são mantidos localmente apenas até sincronização.
    Retenção:
        events → 12 meses
        aggregates → 24 meses
        logs locais → 90 dias
    Conformidade com LGPD e princípios de privacidade por design.

----

## 8 - Plano de Desenvolvimento
    Sprint 1 – Simulação e arquitetura local (Edge)
        Estruturação dos módulos app/, sims/, tools/
        Criação da fila SQLite e simulação de eventos
    Sprint 2 – Integração com nuvem mock
        Implementar sincronização e mock de armazenamento remoto
    Sprint 3 – Dashboards e análise de dados simulados
        KPIs de acessibilidade e métricas de uso
    Sprint 4 – Testes, documentação e refinamento de IA leve
        Detecção de padrões e insights éticos de interação

----

## 9 - Equipe e Responsabilidades
Integrante	                                        Função	                                        Principais Atividades
Giovana de Oliveira Agudo	                        QA / Arquiteta de desenvolvimento     	        Estrutura do Edge, fila SQLite, testes, roteiros e documentação
Giovana de Oliveira Agudo	                        Colaboração técnica	                            Revisão, validação de arquitetura e ajustes de ambiente

----

## 10 - Política de Privacidade
O sistema não coleta nenhum dado pessoal identificável. Todos os eventos são anônimos e usados apenas para métricas de acessibilidade e desempenho.

## 11 - Autora
Giovana de Oliveira Agudo
Projeto acadêmico desenvolvido no Challenge FlexMedia — FIAP 2025,
Sprint 1: Prototipação de Arquitetura e Estratégia de Dados Simulada,

##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 

## Sprint 2
## Integração, ETL e Dashboard
Nesta Sprint, o projeto evoluiu para integrar sensores, armazenamento local, sincronização simulada em cloud e análise completa de uso do Totem Sense&Care.

## Principais Entregáveis
    - Simulação realista de sessões e eventos (toque, voz, acessibilidade, conteúdo).
    - Banco local SQLite operando como fila de eventos.
    - Pipeline de sincronização entre edge e cloud mock.
    - Modelagem e ETL gerando:
        events_flat.csv
        session_metrics.csv
    -Dashboard analítico em dois formatos:
        dashboard.ipynb
        dashboard_app.py (Streamlit)

## Métricas Monitoradas
    - CSAT médio
    - Tempo de permanência
    - Conteúdos mais acessados
    - Uso de acessibilidade
    - Sessões por canal
    - Relação dwell × satisfação

## Como Executar
1. Rodar simulação
    python sims/sessions_generator.py
    python sims/mqtt_publisher.py

2. Rodar aplicação edge
    python app/app.py

3. Rodar dashboard (Jupyter)
    Abra analysis/dashboard.ipynb

4. Rodar dashboard web (terminal -> cd analysis)
    streamlit run analysis/dashboard_app.py

