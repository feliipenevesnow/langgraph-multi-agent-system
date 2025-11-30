# Banco Ágil - Agente Bancário Inteligente 🏦

## 1. Visão Geral do Projeto
Este projeto implementa um sistema de atendimento bancário automatizado e inteligente, utilizando uma arquitetura de **Agentes de IA** orquestrados. O sistema simula um atendimento completo, capaz de autenticar usuários, consultar limites, processar solicitações de aumento de crédito (com análise de risco em tempo real), realizar entrevistas financeiras para atualização de score e fornecer cotações de moedas.

O foco principal foi criar uma experiência fluida ("Agentic"), onde o usuário não percebe que está trocando de departamentos (agentes), mantendo o contexto da conversa do início ao fim.

## 2. Arquitetura do Sistema
A solução utiliza uma arquitetura baseada em grafos (**LangGraph**) para orquestrar o fluxo de conversação.

### Componentes Principais:
- **Frontend (Streamlit):** Interface de chat amigável que gerencia o estado da sessão e se comunica com o backend via API REST.
- **Backend (FastAPI):** Expõe o grafo de agentes e gerencia a persistência da sessão.
- **Orquestrador (LangGraph):** O "cérebro" que decide qual agente deve responder com base no estado atual e na intenção do usuário.

### Os Agentes:
1.  **Agente de Triagem (`triage_node`):**
    - Porta de entrada.
    - Responsável pela saudação, coleta de CPF e Data de Nascimento.
    - Realiza a autenticação contra a base de dados (`clientes.csv`).
    - Roteia para outros agentes com base na intenção (Crédito ou Câmbio).
2.  **Agente de Crédito (`credit_node`):**
    - Consulta limite atual.
    - Processa pedidos de aumento de limite.
    - Verifica regras de negócio (Score vs Limite) em `score_limite.csv`.
    - Se o pedido for negado, oferece redirecionamento para o Agente de Entrevista.
3.  **Agente de Entrevista (`interview_node`):**
    - Conduz uma entrevista estruturada para coletar dados financeiros (Renda, Emprego, Despesas, Dívidas).
    - Utiliza LLM para **normalizar** as respostas do usuário (ex: "ganho 5k" -> `5000.0`).
    - Recalcula o Score do cliente com base em uma fórmula ponderada e atualiza a base.
4.  **Agente de Câmbio (`exchange_node`):**
    - Consulta cotações de moedas em tempo real utilizando a **AwesomeAPI**.

## 3. Funcionalidades Implementadas
- ✅ **Autenticação Robusta:** Validação de CPF e Data com lógica de 3 tentativas.
- ✅ **Inteligência de Intenção:** Uso de LLM para entender o que o usuário quer, sem depender de palavras-chave exatas.
- ✅ **Extração de Dados Estruturados:** O sistema extrai CPFs, datas e valores monetários de frases em linguagem natural.
- ✅ **Análise de Crédito Automática:** Aprovação ou rejeição imediata com base no Score.
- ✅ **Entrevista Contextual:** O agente faz perguntas, valida se a resposta faz sentido e atualiza o perfil do cliente.
- ✅ **Cotação em Tempo Real:** Integração com API externa de câmbio.
- ✅ **Interface Chat:** UI limpa com indicador de "digitando" e histórico persistente.

## 4. Desafios Enfrentados e Soluções
### Desafio 1: Manter o Contexto e Estado
**Problema:** Em um chat longo, é difícil saber em que passo da entrevista o usuário está ou se ele já foi autenticado.
**Solução:** Uso do `LangGraph` com um objeto de Estado (`AgentState`) compartilhado. Isso permite que todos os agentes saibam quem é o usuário e qual o próximo passo, sem precisar repassar parâmetros manualmente.

### Desafio 2: Respostas Imprevisíveis do Usuário
**Problema:** O usuário pode responder "sou freela" ou "trabalho por conta" quando perguntado sobre emprego. Regras rígidas (`if x == "autônomo"`) falhariam.
**Solução:** Implementação de uma camada de **Normalização com LLM** (`InterviewNormalization`). O modelo traduz a linguagem natural para os dados técnicos esperados pelo sistema antes de qualquer cálculo.

### Desafio 3: Estabilidade do Frontend (Streamlit)
**Problema:** O chat "piscava" ou duplicava mensagens devido à forma como o Streamlit redesenha a tela a cada interação.
**Solução:** Refatoração para o padrão de renderização otimizado: desenhar o histórico estático primeiro (com chaves únicas) e apenas depois processar a nova entrada, eliminando `st.rerun()` desnecessários.

## 5. Escolhas Técnicas e Justificativas
- **LangGraph:** Escolhido pela capacidade de criar fluxos cíclicos e condicionais complexos, essenciais para um sistema multi-agente onde o usuário pode ir e vir (ex: Crédito -> Entrevista -> Crédito).
- **FastAPI:** Para garantir que o backend seja assíncrono, rápido e desacoplado da interface, permitindo que outros frontends (mobile, web) sejam conectados no futuro.
- **Google Gemini (LLM):** Utilizado pela excelente capacidade de seguir instruções de formato (Structured Output) e custo-benefício.
- **Pydantic:** Para garantir que os dados extraídos pelo LLM sigam estritamente o esquema necessário, evitando erros de tipo no código Python.

## 6. Tutorial de Execução e Testes

### Pré-requisitos
- Python 3.9+
- Chave de API do Google Gemini configurada no arquivo `.env`.

### Passo a Passo
1.  **Configurar o Backend:**
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    ```

2.  **Configurar o Frontend:**
    ```bash
    cd frontend
    pip install -r requirements.txt
    streamlit run app.py
    ```

3.  **Como Testar:**
    - Acesse `http://localhost:8501`.
    - **Autenticação:** Use o CPF `12345678900` e Data `1990-01-01` (ou veja outros em `backend/app/data/clientes.csv`).
    - **Cenário de Aumento:** Peça um aumento de limite alto (ex: "quero 50000"). Se negado, aceite a entrevista.
    - **Entrevista:** Responda as perguntas naturalmente. Ao final, peça o aumento novamente para ver se o Score atualizado ajudou.

## 7. Estrutura Organizada do Código
O projeto segue uma arquitetura modular limpa:

```
/backend
  /app
    /agents       # Lógica específica de cada Agente (Credit, Triage, Interview...)
    /core         # O "Coração" do sistema (Grafo, Configuração de LLM, Utils)
    /data         # Arquivos CSV (Banco de Dados simulado)
    /models       # Schemas Pydantic (Estrutura de dados)
    /tools        # Ferramentas (Acesso a dados, APIs externas)
    main.py       # Ponto de entrada da API
/frontend
  app.py          # Aplicação Streamlit
```
