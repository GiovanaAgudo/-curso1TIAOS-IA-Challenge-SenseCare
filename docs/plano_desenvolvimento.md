Plano inicial de desenvolvimento e divisão de responsabilidades entre os membros

Objetivo Geral
Garantir que o Sense&Care seja desenvolvido de forma estruturada, ética e colaborativa — com etapas bem definidas, responsabilidades distribuídas e práticas de privacidade e segurança incorporadas desde o início do ciclo de desenvolvimento.

Segurança e Privacidade (LGPD)
Objetivo: assegurar confiança e ética no tratamento dos dados captados pelo sistema, aplicando os princípios da LGPD (Lei Geral de Proteção de Dados).

Atividades:
    Definir como os dados sensíveis e de uso serão protegidos, priorizando a minimização e anonimização.
    Especificar políticas de consentimento e revogação de uso, com registro de consent_updated em cada sessão.
    Implementar camadas de segurança:
        Criptografia em repouso (SQLite cifrado no edge);
        TLS em trânsito (para comunicações MQTT e HTTP);
        Autenticação e controle de acesso (RBAC) nas APIs futuras.
    Garantir conformidade com LGPD e princípios éticos, mantendo logs de auditoria sem exposição de PII (dados pessoais identificáveis).
    Prever direitos do usuário por meio do painel “Seus dados nesta sessão”, permitindo editar ou revogar consentimento.


Estratégia de Desenvolvimento
Objetivo: demonstrar que o time possui estratégia clara, papéis definidos e cronograma bem estruturado para o desenvolvimento incremental da solução.

Atividades:
    Dividir o desenvolvimento em fases:
        Protótipo (Sprint 1): simulação local e integração MQTT/SQLite;
        Integração (Sprint 2): sincronização com backend e APIs REST;
        Testes (Sprint 3): cenários automatizados e monitoramento;
        Entrega (Sprint 4): ajustes finais, dashboards e documentação.
    Definir papéis e responsabilidades entre os integrantes do grupo:
        Arquitetura e integração: configuração de sensores, MQTT e FastAPI;
        Banco e dados: modelagem do queue.db, sync e persistência;
        IA e Análise: criação de lógica de simulação, KPIs e dashboards;
        Documentação e privacidade: LGPD, README e governança dos dados.
    Estimar prazos e dependências, garantindo que os módulos possam ser desenvolvidos em paralelo (Edge, Nuvem e UI).
    Criar um mini cronograma, em formato de checklist semanal, para acompanhar o avanço de cada fase e os responsáveis.


Resultado Esperado
Um plano de desenvolvimento unificado que assegura:
    Execução coordenada entre as áreas técnica e ética;
    Responsabilidade compartilhada no tratamento de dados;
    Entregas incrementais e auditáveis a cada Sprint;
    E conformidade contínua com a LGPD e boas práticas de segurança digital.