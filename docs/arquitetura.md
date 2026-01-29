## Sprint 1
## Esboço da arquitetura da solução

## Componentes físicos (edge & periféricos)
    Totem (mini-PC/Raspberry + tela touch + áudio + botoeira acessível)
    ESP32/ESP32-CAM com sensores: PIR/ToF (presença/distância), LDR (luminosidade), botão físico (modo sem toque)
    Câmera opcional (desabilitada por padrão; só com opt-in explícito)
    Rede: Ethernet/PoE preferencial; Wi-Fi/LTE como fallback

## Linguagens e frameworks
    Frontend (Interface do Totem): JavaScript – React + Next.js (PWA) com VLibras, ARIA/WCAG, Service Worker e IndexedDB
    Backend/Edge: Python – FastAPI (+ MQTT client, WebSockets, fila local SQLite)
    Sensores/IoT: ESP32 (Arduino/ESP-IDF) com MQTT/HTTP
    Voz: Whisper/Vosk (STT) no edge + Web Speech API ou Coqui TTS (TTS)
    Nuvem: GCP (Cloud Run, Firestore, Looker Studio) ou AWS (Lambda, DynamoDB, Grafana/QuickSight)

## Pipeline de dados 
coleta → transmissão → armazenamento → análise → dashboard

## Coleta (dispositivo/ESP32)
    presence_detected, button_pressed, ambient_lux → publicados em MQTT

## Transmissão (edge FastAPI)
    Consome MQTT e eventos da UI (HTTP/WebSocket), aplica regras de consentimento & acessibilidade
    Enfileira em SQLite (modo offline) e envia acks à UI

## Armazenamento (nuvem)
    Eventos anônimos enviados via HTTPS para Firestore/DynamoDB
    Conteúdos estáticos e configurações versionadas (CDN/Storage)

## Análise
    Agregações por totem/horário: dwell time, modos de acessibilidade usados, trilhas consultadas, CSAT

## Dashboard
    Looker/Grafana com painéis: Atração→Interação, Acessibilidade (uso de LIBRAS, alto contraste, sem toque), Fluxo por hora, Feedback/NPS


## Eventos principais:
    presence_detected
    consent_updated
    interaction_started/ended
    accessibility_mode_enabled
    stt_transcript_ready
    tts_played
    nav_route_requested
    feedback_submitted
    sync_ok.

## Papel da IA
    No edge (ético e leve):
        STT/TTS para diálogo acessível
        Recomendação de rotas/conteúdos baseada em preferências declaradas (sem PII)
        Ajustes contextuais (ex.: brilho por LDR; tempo de foco por perfil)


    Na nuvem (agregado):
        Análise de engajamento e A/B de fluxos (ex.: ordem dos botões de acessibilidade)
        Opcional: previsão de horários mais calmos (sem dados pessoais)


Não há biometria/reconhecimento pessoal. Qualquer uso de câmera exige opt-in explícito e trabalha apenas com buckets amplos, sem persistir imagem

## Diagramas (anexos na pasta /diagramas)
    /diag_sensecare_hardware.png
    /diag_sensecare_software_edge.png
    /diag_sensecare_cloud_pipeline.png

## Nuvem
    Edge → Firestore/DynamoDB → Looker/Grafana

## Legenda de privacidade
    ícones para dados anônimos, criptografado, offline queue

##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 

## Sprint 2
##  Arquitetura Implementada

A arquitetura do Sense&Care nesta Sprint 2 evoluiu para integrar coleta de dados, processamento, armazenamento, ETL, análise estatística e visualização. O objetivo é simular o funcionamento real do Totem Flexmedia, demonstrando como sensores, software embarcado e camadas de cloud podem trabalhar juntas.

A solução é composta por cinco módulos principais:

1. Simulação de Sensores (Hardware Virtual)
    - Scripts em sims/ geram eventos representando interações reais: toque, voz, feedbacks, CSAT, navegação, seleção de conteúdo e modos de acessibilidade.
    - O arquivo sessions_generator.py simula sessões completas.
    - O arquivo mqtt_publisher.py simula a publicação dos eventos via MQTT.

2. Edge Software (Totem Local)
    - O módulo app/app.py atua como “software embarcado” do totem.
    - Recebe eventos dos sensores simulados.
    - Normaliza, autentica e grava em banco local SQLite (queue.db).
    - Controla sincronização com cloud via stub (sync_stub.py).

3. Cloud Mock + APIs
    - tools/mock_cloud.py simula o backend real da Flexmedia.
    - Recebe dados sincronizados e valida a estrutura de eventos.

4. ETL e Modelagem de Dados
    - Os dados brutos (events.csv + raw_events) são transformados no notebook analysis/etl_events.ipynb.

    - São criados dois datasets finais:
        events_flat.csv – granularidade de evento
        session_metrics.csv – granularidade de sessão

    - A modelagem segue a lógica “Star Schema”:
        Fato: eventos e métricas de sessão
        Dimensões: conteúdo, modo de acessibilidade, canal

5. Dashboard e Análises
    - Dois formatos de dashboard foram criados:
        dashboard.ipynb – painel Jupyter com KPIs e gráficos
        dashboard_app.py – dashboard interativo Streamlit

    - Principais métricas:
        CSAT médio
        Dwell time
        Sessões por canal
        Conteúdos mais acessados
        Uso de acessibilidade
        Relação dwell × satisfação
