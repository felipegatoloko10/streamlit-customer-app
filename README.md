# 📊 Sistema de Gestão de Clientes v2.0 (Supabase Edition)

Sistema completo de gestão de clientes desenvolvido em Python com Streamlit, agora com backend **PostgreSQL (Supabase)** e **Robô de Atendimento WhatsApp** com Inteligência Artificial (Google Gemini).

[![Streamlit](https://img.shields.io/badge/Streamlit-v1.38+-FF4B4B.svg?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Bot-25D366.svg?style=flat&logo=whatsapp&logoColor=white)](#-robô-de-atendimento-whatsapp)
[![Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4.svg?style=flat&logo=google&logoColor=white)](https://aistudio.google.com)

---

## 🚀 Novidades da Versão 2.0

- **Backend Migrado:** Substituição do SQLite local pelo **PostgreSQL no Supabase**.
- **Busca Melhorada:** Pesquisa de clientes agora é *case-insensitive* (ILIKE).
- **🤖 Robô de Atendimento WhatsApp (NOVO):**
  - Bot inteligente que responde clientes automaticamente via WhatsApp.
  - Integração com **Google Gemini AI** para respostas humanizadas.
  - Rate limiting inteligente (por minuto e por dia) para respeitar limites do plano gratuito.
  - Fallback automático entre modelos Gemini quando um atinge a cota.
  - Deduplicação de mensagens em 2 camadas (memória + banco de dados).
  - Filtro anti-spam para evitar respostas duplicadas.
  - Dashboard completo de controle, configuração e monitoramento.
- **Integração WhatsApp (Evolution API):**
  - Deploy via Docker na Oracle Cloud (grátis para sempre).
  - Envio de mensagens e criação de instâncias via API.
- **Novo Sistema de Backup:**
  - Exportação e Importação em **JSON** e **CSV**.
  - Backup automático e manual para **Google Drive**.
- **Infraestrutura:** Conexão otimizada via AWS Pooler para maior estabilidade.
- **Notificações por E-mail:**
  - Envio automático de alerta para administrador ao cadastrar novo cliente.
  - Configuração de credenciais SMTP (Gmail) direto na interface.

## 📋 Features

- ✅ **CRUD Completo** de clientes com validação automática (CPF/CNPJ).
- ✅ **Múltiplos Contatos** e endereços por cliente.
- ✅ **Geocodificação** automática de endereços via Nominatim.
- ✅ **Dashboard Analítico** com métricas e visualizações temporais.
- ✅ **Mapas Interativos** com PyDeck (distribuição geográfica).
- ✅ **Restauração Inteligente:** Importação de backups verificando duplicidades.
- ✅ **🤖 Robô de Atendimento WhatsApp** com IA (Google Gemini).
- ✅ **Notificações Automáticas:** Alertas por e-mail para novos cadastros.

---

## 🏗️ Arquitetura Geral

```mermaid
graph TD
    UI[Streamlit UI] --> Service[Customer Service]
    Service --> Repo[Customer Repository]
    Repo --> DB[(Supabase PostgreSQL)]
    Service --> Backup[Backup Manager]
    Backup --> GDrive[Google Drive API]
    
    UI --> DashBot[Dashboard - Aba Bot]
    DashBot --> BotEngine[Bot Engine Thread]
    BotEngine --> EvoService[Evolution Service]
    EvoService --> EvoAPI[Evolution API - Docker]
    EvoAPI --> WhatsApp((WhatsApp))
    BotEngine --> BotIntel[Bot Intelligence]
    BotIntel --> Gemini[Google Gemini AI]
```

### Estrutura do Projeto

```
streamlit-customer-app/
├── database_config.py            # Configuração da conexão Supabase/Postgres
├── database.py                   # Funções de acesso ao banco (clientes + chat)
├── backup_manager.py             # Gestão de backups (JSON/CSV/Drive)
├── google_drive_service.py       # Integração com API do Google
├── integration_services.py       # Serviços de integração (e-mail, cloud status)
├── bot_config.json               # ⚙️ Configuração do robô (chaves, status)
├── run_bot_engine.bat            # 🦇 Script para rodar o bot standalone
├── repositories/           
│   └── customer_repository.py    # Acesso a dados (SQLModel)
├── services/
│   ├── customer_service.py       # Regras de negócio
│   ├── bot_engine.py             # 🤖 Motor do robô (polling, deduplicação)
│   ├── bot_intelligence.py       # 🧠 IA do robô (Gemini, rate limiting)
│   └── evolution_service.py      # 📱 Wrapper da Evolution API (WhatsApp)
├── pages/
│   ├── 0_🏠_Dashboard.py         # Dashboard + Aba de controle do Bot
│   ├── 1_📝_Cadastro.py
│   ├── 2_📊_Banco_de_Dados.py
│   ├── 3_💰_Calculadora_de_Preços.py
│   ├── 4_💸_Emitir_NFS-e.py
│   └── 5_💾_Backup.py
├── DEPLOY_ORACLE_CLOUD.md        # 📖 Guia completo de deploy na Oracle Cloud
└── Home.py                       # Página principal
```

---

# 🤖 Robô de Atendimento WhatsApp

## A Ideia

A ideia do robô nasceu da necessidade de **atender clientes automaticamente via WhatsApp 24 horas por dia, 7 dias por semana**, sem depender de um humano online o tempo todo. O bot:

1. **Recebe** mensagens dos clientes via WhatsApp.
2. **Entende** a mensagem usando IA (Google Gemini).
3. **Responde** automaticamente de forma profissional e humanizada.
4. **Registra** todo o histórico de conversas no banco de dados.

### Componentes Principais

| Componente | Arquivo | Função |
|---|---|---|
| **Motor do Bot** | `services/bot_engine.py` | Loop de polling que busca novas mensagens a cada 15s |
| **Inteligência IA** | `services/bot_intelligence.py` | Gera respostas usando Google Gemini com controle de cota |
| **Serviço WhatsApp** | `services/evolution_service.py` | Wrapper da API Evolution para enviar/receber mensagens |
| **Configuração** | `bot_config.json` | Chaves de API, URL do servidor, status on/off |
| **Dashboard** | `pages/0_🏠_Dashboard.py` | Interface de controle (aba "🤖 Bot Atendimento") |

---

## 📦 Guia Completo: Como Configurar do Zero

### Pré-requisitos

- **Python 3.10+** instalado
- **Docker** e **Docker Compose** instalados
- Uma conta no **[Supabase](https://supabase.com)** (banco de dados)
- Uma conta no **[Google AI Studio](https://aistudio.google.com)** (chave Gemini, gratuita)
- Um servidor Linux com IP público (recomendado: **Oracle Cloud Always Free**)
- Um **celular** com WhatsApp ativo para escanear o QR Code

---

### ETAPA 1: Clonar e Instalar o Projeto

```bash
# 1. Clone o repositório
git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
cd streamlit-customer-app

# 2. (Recomendado) Crie um ambiente virtual
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### ETAPA 2: Configurar o Banco de Dados (Supabase)

1. Acesse o [Supabase](https://supabase.com) e crie um novo projeto.
2. Vá em **Settings > Database** e copie a **Connection String** (URI).
3. Configure a variável `DATABASE_URL` no arquivo `database_config.py`:

   ```python
   # Exemplo:
   DATABASE_URL = "postgresql+psycopg2://postgres.abc123:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
   ```

4. Execute o app uma vez para criar as tabelas automaticamente:

   ```bash
   streamlit run Home.py
   ```

---

### ETAPA 3: Subir a Evolution API (Servidor WhatsApp)

A Evolution API é o servidor que conecta seu bot ao WhatsApp. Ela roda em **Docker** e precisa de um servidor com IP público.

> **💡 Recomendação:** Use a **Oracle Cloud Always Free** para hospedar de graça para sempre. Veja o guia completo em [`DEPLOY_ORACLE_CLOUD.md`](DEPLOY_ORACLE_CLOUD.md).

#### 3.1. Preparar o Servidor

Acesse sua VPS (Oracle Cloud, AWS, DigitalOcean, etc.) via SSH:

```bash
ssh -i "sua-chave.key" ubuntu@IP_DO_SEU_SERVIDOR
```

Instale o Docker:

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

#### 3.2. Criar os Arquivos de Configuração

```bash
# Criar pasta do projeto
mkdir evolution-api && cd evolution-api
```

**Crie o arquivo `.env`:**

```bash
nano .env
```

Cole o seguinte conteúdo (ajuste `SERVER_URL` e `AUTHENTICATION_API_KEY`):

```env
# SERVER_URL = O IP PÚBLICO do seu servidor
SERVER_URL=http://SEU_IP_PUBLICO

# Essas são suas credenciais de acesso — MUDE a API_KEY!
CORS_ORIGIN=*
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS,PATCH
CORS_CREDENTIALS=true
PORT=8080
LOG_LEVEL=INFO

# Autenticação — GERE SUA PRÓPRIA CHAVE (ex: um UUID aleatório)
AUTHENTICATION_API_KEY=SUA-CHAVE-SECRETA-AQUI
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

# Banco de dados (PostgreSQL interno do Docker)
DATABASE_ENABLED=true
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://evolution:evolution@evolution_postgres:5432/evolution
DATABASE_CLIENT_NAME=evolution_exchange

# Redis (cache)
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=redis://evolution_redis:6379/1
CACHE_REDIS_PREFIX_KEY=evolution
CACHE_REDIS_SAVE_INSTANCES=false
CACHE_REDIS_TTL=604800

# Desabilitados
S3_ENABLED=false
MINIO_ENABLED=false
CHATWOOT_ENABLED=false
TYPEBOT_ENABLED=false
OPENAI_ENABLED=false
DIFY_ENABLED=false
```

**Crie o arquivo `docker-compose.yaml`:**

```bash
nano docker-compose.yaml
```

Cole o conteúdo:

```yaml
version: "3.8"

services:
  api:
    container_name: evolution_api
    image: atendai/evolution-api:v2.2.2
    restart: always
    depends_on:
      - redis
      - evolution-postgres
    ports:
      - "8080:8080"
    volumes:
      - evolution_instances:/evolution/instances
    networks:
      - evolution-net
    env_file:
      - .env

  frontend:
    container_name: evolution_frontend
    image: evoapicloud/evolution-manager:latest
    restart: always
    ports:
      - "8081:80"
    networks:
      - evolution-net

  redis:
    container_name: evolution_redis
    image: redis:latest
    restart: always
    command: >
      redis-server --port 6379 --appendonly yes
    volumes:
      - evolution_redis:/data
    networks:
      - evolution-net

  evolution-postgres:
    container_name: evolution_postgres
    image: postgres:15
    restart: always
    env_file:
      - .env
    command:
      - postgres
      - -c
      - max_connections=1000
      - -c
      - listen_addresses=*
    environment:
      - POSTGRES_DB=${POSTGRES_DATABASE:-evolution}
      - POSTGRES_USER=${POSTGRES_USERNAME:-evolution}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-evolution}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - evolution-net

volumes:
  evolution_instances:
  evolution_redis:
  postgres_data:

networks:
  evolution-net:
    driver: bridge
```

#### 3.3. Subir os Containers

```bash
docker compose up -d
```

Verifique se está rodando:

```bash
docker ps
```

Você deve ver 4 containers rodando: `evolution_api`, `evolution_frontend`, `evolution_redis` e `evolution_postgres`.

#### 3.4. Liberar Portas no Firewall

Na **Oracle Cloud**, libere as portas `8080` e `8081` nas **Security Lists** da sua VPC. Na VPS, também limpe as regras do iptables:

```bash
sudo iptables -F
sudo netfilter-persistent save
```

#### 3.5. Criar Instância e Escanear QR Code

1. Acesse o **Evolution Manager** em `http://SEU_IP:8081` no navegador.
2. Conecte ao servidor: URL = `http://SEU_IP:8080`, Token = sua `AUTHENTICATION_API_KEY`.
3. **Crie uma nova instância** (nome sugerido: `BotFeh`).
4. Um **QR Code** aparecerá — escaneie com o WhatsApp do celular que será usado como bot.
5. Quando aparecer status **"open"**, o WhatsApp está conectado!

---

### ETAPA 4: Obter a Chave do Google Gemini (IA)

1. Acesse o [Google AI Studio](https://aistudio.google.com).
2. Clique em **"Get API Key"**.
3. Crie uma nova chave API (é grátis no plano free tier).
4. Copie a chave — você vai precisar na próxima etapa.

> **Limites do Plano Gratuito:**
>
> - ~15 requisições por minuto
> - ~1.500 requisições por dia
> - O bot gerencia esses limites automaticamente com rate limiting e fallback de modelos.

---

### ETAPA 5: Configurar o Bot no Dashboard

1. **Inicie o app Streamlit:**

   ```bash
   streamlit run Home.py
   ```

2. Navegue até **Dashboard** → aba **"🤖 Bot Atendimento"**.

3. Expanda **"Configurações da API"** e preencha:

   | Campo | Valor |
   |---|---|
   | **Evolution API URL** | `http://SEU_IP:8080` |
   | **Evolution API Token** | A `AUTHENTICATION_API_KEY` do `.env` |
   | **Evolution Instance Name** | O nome da instância criada (ex: `BotFeh`) |
   | **Gemini API Key** | A chave que você obteve no passo anterior |

4. Clique em **"Salvar Configurações"**.

5. **Ative o Toggle "Bot Ativo"** — o bot começará a rodar imediatamente!

---

### ETAPA 6: Testar o Bot

1. De **outro celular** (não o que escaneou o QR), envie uma mensagem para o número do WhatsApp do bot.
2. Aguarde ~15 segundos (tempo de polling).
3. O bot deve responder automaticamente!
4. No Dashboard, você verá:
   - **Status "🟢 Bot Rodando"**
   - **Logs em tempo real** com as mensagens processadas
   - **Últimas Conversas** com o histórico de chat
   - **Uso do Gemini** com calls/minuto e calls/dia

---

## 🔧 Como o Robô Funciona (Detalhes Técnicos)

### Fluxo de Funcionamento

```mermaid
sequenceDiagram
    participant Cliente as 📱 Cliente WhatsApp
    participant Evo as 🖥️ Evolution API (Docker)
    participant Bot as 🤖 Bot Engine (Python)
    participant AI as 🧠 Gemini AI
    participant DB as 🗄️ Banco de Dados

    loop A cada 15 segundos
        Bot->>Evo: Buscar mensagens recentes (polling)
        Evo-->>Bot: Lista de mensagens
        
        Bot->>Bot: Filtrar (apenas msgs dos últimos 2 min)
        Bot->>Bot: Deduplicar (cache memória + DB)
        Bot->>Bot: Filtro anti-spam (mesmo texto < 30s)
        
        Bot->>DB: Salvar mensagem do cliente
        Bot->>AI: Gerar resposta (com contexto)
        AI-->>Bot: Resposta gerada
        Bot->>Evo: Enviar resposta ao cliente
        Evo->>Cliente: Mensagem de volta
        Bot->>DB: Salvar resposta do bot
    end
```

### Motor do Bot (`bot_engine.py`)

O motor do bot roda como uma **thread daemon** dentro do processo do Streamlit. Principais características:

- **Polling a cada 15 segundos** — busca novas mensagens na Evolution API.
- **Filtragem temporal** — só processa mensagens dos últimos 2 minutos (ignora histórico antigo).
- **Deduplicação em 2 camadas:**
  - **Memória** — set de últimos 500 IDs (rápido, sem acessar banco).
  - **Banco de dados** — verificação persistente como fallback.
- **Anti-spam** — ignora se o mesmo número mandar a mesma mensagem em menos de 30 segundos.
- **Auto-diagnóstico** — verifica a cada ciclo se a instância WhatsApp está conectada.
- **Recarregamento dinâmico** — recarrega `bot_config.json` a cada loop (mudanças no Dashboard são aplicadas sem reiniciar).
- **Singleton thread-safe** — garante que apenas UMA instância do bot roda por vez, eliminando threads "zumbis".

### Inteligência Artificial (`bot_intelligence.py`)

A IA do bot usa o **Google Gemini** com proteções robustas:

- **Rate limiting local** antes de chamar a API:
  - Máximo de 13 calls/minuto (limite real: 15).
  - Máximo de 1.400 calls/dia (limite real: 1.500).
- **Fallback automático de modelos:** Se um modelo atinge a cota (`limit: 0`), troca automaticamente para o próximo na lista:
  1. `gemini-1.5-flash` (padrão)
  2. `gemini-2.0-flash`
  3. `gemini-1.5-flash-8b`
- **Cooldown inteligente:** Quando recebe erro 429, extrai o `retry_delay` da resposta e aguarda automaticamente.
- **System Prompt** configurado como recepcionista/assistente virtual: profissional, curto e objetivo — adequado para WhatsApp.
- **Retorna `None`** em vez de mensagem de erro quando há rate limit — evita mandar "Desculpe..." ao cliente.

### Serviço Evolution (`evolution_service.py`)

Wrapper simples que encapsula as chamadas HTTP para a Evolution API v2:

- `check_connection()` — verifica se a instância WhatsApp está "open".
- `send_message(phone, message)` — envia texto via `POST /message/sendText`.
- `get_recent_messages(count)` — busca mensagens via `POST /chat/findMessages`.

---

## 📧 Configuração de E-mail

O sistema suporta envio de notificações via SMTP (focado no Gmail).

1. Acesse a página **💾 Backup**.
2. Vá até a seção **Configuração de Notificações por E-mail**.
3. Insira seu e-mail e a **Senha de App** (gerada nas configurações de segurança do Google).
4. O sistema salvará as credenciais localmente em `email_config.json`.

### Configuração via Streamlit Secrets (Recomendado para Cloud)

Para maior segurança, especialmente no **Streamlit Cloud**, você pode configurar as credenciais usando `Secrets`.

1. **Localmente:** Crie/edite o arquivo `.streamlit/secrets.toml`:

    ```toml
    [email_config]
    sender_email = "seu-email@gmail.com"
    password = "sua-senha-de-app"
    smtp_server = "smtp.gmail.com"
    smtp_port = "587"
    app_base_url = "https://seu-app.streamlit.app"
    ```

2. **No Streamlit Cloud:**
    - Vá nas configurações do seu app.
    - Cole o conteúdo acima na área de **Secrets**.

> **Nota:** Se as configurações estiverem presentes nos Secrets, o arquivo `email_config.json` será ignorado e a edição via interface será desabilitada.

---

## 🔧 Configuração de Backup (Google Drive)

Para habilitar o backup em nuvem, obtenha o arquivo `credentials.json` no Console do Google Cloud (API Drive) e faça o upload na página de "Backup".

---

## ⚡ Infraestrutura e Manutenção

### Evitar Hibernação (Streamlit Cloud)

O projeto inclui um workflow do GitHub Actions (`.github/workflows/keep_awake.yml`) configurado para evitar que a aplicação entre em modo de hibernação no Streamlit Cloud.

- **Funcionamento:** O workflow executa um `curl` na URL da aplicação diariamente às 12:00 UTC.
- **Configuração:** A URL alvo está definida diretamente no arquivo do workflow.

### Rodar o Bot Standalone (sem Streamlit)

Se quiser rodar o bot sem o Streamlit (ex: em um servidor dedicado), use:

```bash
# No Windows:
run_bot_engine.bat

# No Linux/Mac:
python services/bot_engine.py
```

> O bot lê o `bot_config.json` para pegar as chaves de API e configurações. Certifique-se de preencher este arquivo antes de rodar.

---

## 🩺 Troubleshooting (Problemas Comuns)

| Problema | Causa Provável | Solução |
|---|---|---|
| Bot não responde | Instância WhatsApp desconectada | Reescanear QR Code no Manager (`http://IP:8081`) |
| "Chave Gemini não configurada" | Chave vazia no Dashboard | Ir no Dashboard > Bot > Configurações e preencher |
| Rate limit / cooldown | Muitas mensagens em pouco tempo | O bot gerencia automaticamente; aguardar o cooldown |
| "limit: 0" no log | Modelo esgotou a cota free | O bot troca de modelo automaticamente (fallback) |
| Msgs antigas sendo respondidas | Filtro de tempo não aplicado | Verificar se o clock do servidor está correto |
| Container Docker parou | Erro na VPS | `docker compose up -d` para reiniciar |

---

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---
**Desenvolvido por Felipe Gato Loko**
