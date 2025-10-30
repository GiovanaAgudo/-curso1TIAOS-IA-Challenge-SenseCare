Definição das tecnologias que serão utilizadas
Arquitetura Técnica e Tecnologias Definidas

Camada: Frontend (Interface do Totem)
Tecnologia: JavaScript – React + Next.js (PWA)      
Por quê / Observações: UI acessível, responsiva, fácil de internacionalizar; roda em Chromium kiosk; cache offline via Service Worker; integração direta com VLibras e atalhos de acessibilidade.

Camada: Voz (STT/TTS) 
Tecnologia: ASR no backend (Python + Whisper/Vosk) e TTS no navegador (Web Speech API) ou Coqui TTS via backend  
Por quê / Observações: Mantém dados de áudio locais/edge; baixa latência.

Camada: LIBRAS
Tecnologia: VLibras (widget JS) ou Hand Talk (se houver licença)
Por quê / Observações: Biblioteca brasileira, simples de embutir no React.

Camada: Backend/Edge
Tecnologia: Python (FastAPI) ou Node.js (Express)     
Por quê / Observações: Orquestração de sensores, eventos, consentimento e envio à nuvem.

Camada: Sensores
Tecnologia: ESP32/ESP32-CAM (PIR/ToF/LDR/botão) + MQTT/HTTP
Por quê / Observações: Dispara presença, ajusta brilho, habilita “sem toque”.

Camada: Nuvem
Tecnologia: GCP (Cloud Run, Firestore, Looker) ou AWS (Lambda, DynamoDB, QuickSight/Grafana)     
Por quê / Observações: Telemetria anônima e dashboards.


Fluxo Simplificado de Integração Tecnológica 
Detecção & Acordo de Uso
    ESP32 (PIR/ToF) detecta presença → envia presence_detected via MQTT ao Edge (FastAPI/MQTT client).
    PWA (React/Next) desperta “modo atração”.
    Tela Consent-First: usuário escolhe modos de acessibilidade (alto contraste, fonte XL, LIBRAS, sem toque) e canais (voz/toque).
    Edge registra consent_updated (anônimo) e retorna política ativa para o frontend.


Interação no Totem (PWA)
    Interface reage às preferências (tema acessível, foco ampliado, botões grandes).
    LIBRAS via widget VLibras (toggle acessível).
    Voz:
        STT: áudio é enviado do PWA ao Edge (FastAPI) para Whisper/Vosk.
        TTS: resposta por Web Speech API (local) ou Coqui TTS via Edge quando necessário.
    Sem toque: navegação por voz + botoeira (GPIO→ESP32→Edge→PWA via WebSocket).


Orquestração no Edge (Python/FastAPI)
    Recebe eventos do PWA (HTTP/WebSocket) e dos ESP32 (MQTT).
    Aplica regras de personalização (perfil declarado) e limpeza/anonimização de dados.
    Mantém fila local (SQLite) para modo offline e envia acks ao PWA (UX responsiva).


Persistência & Nuvem
    Edge envia eventos anônimos para Firestore/DynamoDB (via HTTPS).
    Looker/Grafana consome agregados para dashboards (modos acessibilidade, dwell, rotas consultadas, CSAT).
    PWA mantém cache (IndexedDB + Service Worker) para conteúdo e preferências por sessão.


Recuperação & Continuidade
    Se cair a rede: Edge grava tudo localmente (fila cifrada) e PWA opera com conteúdo em cache.
    Quando a rede volta: sincronização de eventos pendentes → confirmação de entrega → limpeza segura

Resumo dos Requisitos Funcionais e Não Funcionais
Requisitos Funcionais
    O sistema deve detectar a presença do usuário por sensores (PIR/ToF) e ativar o modo de interação.
    Deve oferecer múltiplos modos de acesso: voz, toque, LIBRAS e modo sem toque.
    Deve permitir navegação acessível com tradução em LIBRAS, leitura em voz alta e alto contraste.
    Deve coletar dados anônimos de uso e acessibilidade, enviando-os à nuvem de forma segura.
    Deve apresentar dashboards com métricas de engajamento e acessibilidade para os gestores.
    Deve funcionar em modo offline, com sincronização automática ao restabelecer conexão.


Requisitos Não Funcionais
    Acessibilidade: conformidade com WCAG 2.1 e uso de tecnologias inclusivas (VLibras, TTS).
    Privacidade: nenhuma coleta de dados pessoais; anonimização e consentimento explícito.
    Disponibilidade: funcionamento contínuo com recuperação automática de falhas.
    Desempenho: resposta em tempo real (<1s para ações locais).
    Escalabilidade: arquitetura modular, compatível com múltiplos ambientes (museus, hospitais etc.).
    Segurança: comunicação criptografada (TLS/AES-256) e controle de logs.