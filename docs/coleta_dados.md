## Sprint 1
## Explicação da estratégia de Dados — simulada

1. Objetivo
Demonstrar como o Sense&Care capta, trata e transforma dados em informações úteis — com privacidade por padrão, seguindo princípios de anonimização, minimização e consentimento explícito — e como esse fluxo será simulado tecnicamente nesta Sprint.

2. Coleta de Dados (por Fonte/Sensor)
Consentimento & Preferências
Eventos:
 consent_updated → define modos ativos (voz, LIBRAS, alto contraste, sem toque, idioma).

Cada sessão gera um session_id rotativo e respeita o opt-in/opt-out informado localmente.

Interação de Interface (UI)
Eventos:
    interaction_started / interaction_ended
    screen_view
    content_selected
    feedback_submitted

Usados para medir tempo de engajamento e avaliar a usabilidade das rotas acessíveis.

Voz (STT/TTS)
Eventos:
    stt_intent (texto interpretado da fala — áudio nunca armazenado)
    tts_played (referência da fala sintetizada)

Sensores ESP32
Eventos simulados via mqtt_publisher.py:
    presence_detected → PIR
    distance_cm → ToF ou ultrassônico
    ambient_lux → LDR
    button_pressed → botoeira acessível

Esses dados validam o funcionamento dos sensores e sua integração com o backend.

Saúde do Dispositivo
Eventos:
    device_heartbeat
    network_status
    queue_size

Permitem monitorar status do totem e volume de eventos pendentes no SQLite local.

Observação: nenhum dado pessoal, imagem ou áudio bruto é armazenado. Todos os identificadores são pseudonimizados por sessão e descartados após o uso.

3. Armazenamento e Processamento
No Edge (Local)
    Banco SQLite (queue.db) atua como fila local de eventos, com suporte a sincronização via sync_stub.py.
    Eventos são armazenados temporariamente até o envio à nuvem.
    Aplicadas etapas de:
        Normalização
        Minimização
        Pseudonimização (session_id rotativo por sessão)


Na Nuvem (futura implementação)
Destinos previstos: Firestore / DynamoDB
Estruturas:
    events (granular)
    sessions (agregado)
    device_status
    aggregates_hourly e aggregates_daily

Regras de acesso serão baseadas em RBAC com logging de auditoria completo.

4. Esquema Base de Evento (JSON)
    {
    "event_id": "uuid",
    "timestamp": "2025-10-29T22:15:00Z",
    "totem_id": "FM-LOCAL-01",
    "session_id": "rotating-hash",
    "event_type": "presence_detected",
    "channel": "sensor",
    "context": {
        "presence": true,
        "ambient_lux": 120,
        "locale": "pt-BR",
        "modes_enabled": ["high_contrast", "libras"]
    },
    "payload": {
        "content_id": "rota_acessivel_banheiro",
        "dwell_ms": 0
    }
    }

O event_id é gerado automaticamente no publisher, garantindo rastreabilidade por evento.

5. Estratégia de Análise (IA Leve + Regras)
Regras no Edge
    Ajuste automático de brilho conforme ambient_lux.
    Aumento do tempo de foco quando o perfil declara baixa visão.
    Sugerir rotas acessíveis baseadas em preferências de mobilidade.
    Alertas locais quando sensores falham ou fila local excede limite.

IA (Local ou Nuvem)
    Classificação simples de intenções STT (“banheiro acessível”, “mapa”, “ajuda”).
    Recomendação de conteúdos por co-ocorrência de consultas.
    Experimentos A/B de layout acessível (ordem de botões, contraste).

KPIs Derivados
    Taxa de Atração → Interação
    Dwell time médio
    Modos de acessibilidade utilizados
    Rotas mais acessadas
    CSAT/NPS Acessibilidade
    Falhas de rede/offline
    Tempo médio de sincronização da fila (queue.db → API)

6. Plano de Simulação (Sprint 1)
Como Simular:

    Publicação MQTT fake:
        mqtt_publisher.py envia presence_detected, ambient_lux e button_pressed para tópicos /fm/zoo01/sensors/...

    Eventos de UI:
        Enviados via Postman para POST /events e WebSocket /realtime.

    Sessões sintéticas:
        sessions_generator.py cria 300–1000 sessões/dia variando:
            canal (toque/voz)
            modos (LIBRAS, alto contraste)
            duração média
            rota acessada
    Dashboards:
        Visualização de KPIs simulados via Grafana ou Looker Studio, conectando aggregates_hourly.

7. Privacidade, Segurança e Retenção
    Sem biometria, imagem ou áudio persistido.
    TLS em trânsito; SQLite cifrado em repouso (criptografia local).
    Retenção de dados:
        events: 12 meses
        aggregates: 24 meses
        device_logs: 90 dias
    Painel de controle de sessão (“Seus dados nesta sessão”) permite editar ou revogar consentimento.


8. Dicionário de Dados (Resumo)
Campo                       Tipo / Exemplo              Descrição
session_id                  hash rotativo               Identifica sessão pseudonimizada
event_id                    UUID                        ID único do evento
event_type                  string                      Tipo de evento gerado
timestamp                   ISO 8601                    Data/hora UTC
channel                     string                      sensor / touch / voice / libras
modes_enabled[]             lista                       Modos de acessibilidade ativos
content_id                  string                      Conteúdo exibido / rota acessada
dwell_ms                    número                      Tempo de permanência
ambient_lux                 número                      Nível de luminosidade (LDR)
device_status               string                      online / offline / erro
csat                        número                      Satisfação do usuário (1–5)

9. Conclusão
A simulação atual comprova a viabilidade técnica da arquitetura de dados do Sense&Care — com:
    fluxo realista de coleta via MQTT e HTTP,
    fila local confiável (queue.db),
    sincronização bem-sucedida via sync_stub.py,
    e geração de eventos auditáveis com preservação total da privacidade.


##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 

## Sprint 2
## Fluxo de Dados Sense&Care – Sprint 2

O fluxo completo simula o ciclo real do Totem Flexmedia:

1. Entrada — Captação de Interações
    Os eventos são gerados por sensores simulados:
        - toque
        - voz
        - seleção de conteúdo
        - feedbacks
        - ativação de acessibilidade
        - início/fim de sessão

    Cada evento possui:
        - event_type  
        - timestamp  
        - session_id  
        - payload  
        - context  
        - modes_enabled  

2. Processamento — Edge (app.py)
    - Normalização do payload
    - Mapear eventos em estruturas padrão
    - Persistir em SQLite local (queue.db)
    - Preparar dados para sincronização

3. Sincronização — Stub Cloud
    sync_stub.py envia lotes para a cloud simulada
    mock_cloud.py recebe e valida

    Garante confiabilidade mínima da ingestão

4. ETL — Camada analítica
    No notebook etl_events.ipynb:
        - Explora payloads complexos
        - Extrai métricas por sessão (dwell, csat, eventos)
        - Remove duplicações
        - Padroniza formato de datas

    Resulta em:
        - analysis/exports/events_flat.csv  
        - analysis/exports/session_metrics.csv  
- 
5. Saída — Visualização
    Os dados são utilizados no dashboard (Jupyter e Streamlit):
        - KPIs
        - gráficos
        - análises automáticas