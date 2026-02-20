# 🚀 Guia de Deploy na Oracle Cloud (Always Free)

Este guia vai te ajudar a hospedar sua **Evolution API** gratuitamente e para sempre na Oracle Cloud.

---

## 🏗️ Passo 1: Criar sua Conta e VPS (Máquina Virtual)

1. **Acesse:** [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) e crie sua conta.
   - *Nota:* Eles pedem cartão de crédito para verificação de identidade, mas **não cobram** se você selecionar os recursos "Always Free".
2. **No Painel (Console):**
   - Vá em **"Create a VM instance"**.
   - **Name:** `evolution-api` (ou o que preferir).
   - **Image:** `Ubuntu 22.04` ou `24.  04` (Canonical Ubuntu).
   - **Shape (Importante):** Selecione **Ampere (Arm)** -> **VM.Standard.A1.Flex**.
     - Configure para **2 a 4 OCPUs** e **12GB a 24GB de RAM** (Isso tudo é grátis!).
3. **Networking (Rede):**
   - Certifique-se de que "Assign a public IPv4 address" esteja marcado.
4. **SSH Keys:**
   - Faça o download da chave privada (`ssh-key-timestamp.key`) e guarde bem! Você vai precisar dela para entrar na máquina.
5. **Criar:** Clique em **Create**.

---

## 🔓 Passo 2: Liberar Portas (Firewall da Oracle)

A Oracle bloqueia tudo por padrão. Você precisa liberar as portas **8080** (API) e **8081** (Gerenciador).

1. Na página da sua Instância, clique no link da **Subnet** (em "Primary VNIC").
2. Clique na **Security List** (ex: `Default Security List for...`).
3. Adicione uma **Ingress Rule**:
   - **Source CIDR:** `0.0.0.0/0` (Qualquer lugar da internet)
   - **IP Protocol:** TCP
   - **Destination Port Range:** `8080,8081`
   - **Description:** Evolution API Ports
4. Clique em **Add Ingress Rules**.

---

## 💻 Passo 3: Acessar a VPS e Instalar Docker

Se você usa Windows, use o **PowerShell** ou **Putty**.
Caminho da chave no comando (exemplo):

```powershell
ssh -i "C:\Caminho\Para\Sua\Chave.key" ubuntu@IP_DA_SUA_VPS
```

*(Substitua `IP_DA_SUA_VPS` pelo IP Público que aparece no painel da Oracle)*

### No terminal da VPS, rode os comandos

1. **Atualizar sistema e firewall interno:**

   ```bash
   sudo apt update && sudo apt upgrade -y
   # Limpa regras de firewall do Ubuntu que podem bloquear conexões
   sudo iptables -F 
   sudo netfilter-persistent save
   ```

2. **Instalar Docker:**

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   ```

---

## 📦 Passo 4: Subir a Evolution API

1. **Crie uma pasta para o projeto:**

   ```bash
   mkdir evolution-api
   cd evolution-api
   ```

2. **Crie o arquivo `.env`:**
   Execute:

   ```bash
   nano .env
   ```

   Cole o conteúdo abaixo (Ajuste o `API_KEY` para algo seguro!):

   ```env
   SERVER_URL=http://localhost:8080
   CORS_ORIGIN=*
   CORS_METHOD=GET,POST,PUT,DELETE,OPTIONS
   PORT=8080
   AUTHENTICATION_API_KEY=SUA_SENHA_SEGURA_AQUI
   DATABASE_ENABLED=true
   DATABASE_CONNECTION_URI=postgresql://evolution:evolution@evolution_postgres:5432/evolution
   CACHE_REDIS_URI=redis://evolution_redis:6379/1
   ```

   *(Para salvar no nano: `Ctrl+O`, `Enter`, `Ctrl+X`)*

3. **Crie o arquivo `docker-compose.yaml`:**
   Execute:

   ```bash
   nano docker-compose.yaml
   ```

   Cole o conteúdo do arquivo `docker-compose.oracle.yaml` que criei no seu projeto (estará nos seus arquivos locais também).

   **Conteúdo Resumido para Copiar/Colar:**

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
         - "8080:8080" # Exposed to 0.0.0.0 via default
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
         - "8081:80" # Manager on port 8081
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

4. **Rodar tudo!**

   ```bash
   docker compose up -d
   ```

---

## 🔗 Passo 5: Conectar no Streamlit e Criar WhatsApp

1. Acesse `http://IP_DA_SUA_VPS:8081` (Manager) em seu navegador.
   - Conecte sua instância.
   - Pegue o **QR Code** e leia com seu celular.
   - Copie a **ApiKey**.

2. Volte para o seu **App Streamlit** (Dashboard > Bot Atendimento).
3. Configure:
   - **URL:** `http://IP_DA_SUA_VPS:8080`
   - **Token:** A chave que você definiu.

**Pronto! Seu WhatsApp estará rodando na nuvem 24/7 de graça.**
