# 📊 Sistema de Gestão de Clientes v2.0 (Supabase Edition)

Sistema completo de gestão de clientes desenvolvido em Python com Streamlit, agora com backend **PostgreSQL (Supabase)** para maior segurança e escalabilidade.

[![Streamlit](https://img.shields.io/badge/Streamlit-v1.38+-FF4B4B.svg?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

---

## 🚀 Novidades da Versão 2.0

- **Backend Migrado:** Substituição do SQLite local pelo **PostgreSQL no Supabase**.
- **Busca Melhorada:** Pesquisa de clientes agora é *case-insensitive* (ILIKE).
- **Novo Sistema de Backup:**
  - Exportação e Importação em **JSON** e **CSV**.
  - Backup automático e manual para **Google Drive**.
- **Infraestrutura:** Conexão otimizada via AWS Pooler para maior estabilidade.
- **Notificações por E-mail:**
  - Envio automático de alerta para administrador ao cadastrar novo cliente.
  - Opção de "Receber Atualizações" no cadastro do cliente.
  - Configuração de credenciais SMTP (Gmail) direto na interface.

## 📋 Features

- ✅ **CRUD Completo** de clientes com validação automática (CPF/CNPJ).
- ✅ **Múltiplos Contatos** e endereços por cliente.
- ✅ **Geocodificação** automática de endereços via Nominatim.
- ✅ **Dashboard Analítico** com métricas e visualizações temporais.
- ✅ **Mapas Interativos** com PyDeck (distribuição geográfica).
- ✅ **Restauração Inteligente:** Importação de backups verificando duplicidades.
- ✅ **Integração WhatsApp** com links diretos.
- ✅ **Notificações Automáticas:** Alertas por e-mail para novos cadastros.

## 🏗️ Arquitetura

```mermaid
graph TD
    UI[Streamlit UI] --> Service[Customer Service]
    Service --> Repo[Customer Repository]
    Repo --> DB[(Supabase PostgreSQL)]
    Service --> Backup[Backup Manager]
    Backup --> GDrive[Google Drive API]
```

### Estrutura do Projeto

```
streamlit-customer-app/
├── database_config.py       # Configuração da conexão Supabase/Postgres
├── backup_manager.py        # Gestão de backups (JSON/CSV/Drive)
├── google_drive_service.py  # Integração com API do Google
├── repositories/           
│   └── customer_repository.py # Acesso a dados (SQLModel)
├── services/
│   └── customer_service.py    # Regras de negócio
├── pages/
│   ├── 0_🏠_Dashboard.py
│   ├── 1_📝_Cadastro.py
│   ├── 2_📊_Banco_de_Dados.py
│   └── 5_💾_Backup.py        # Nova interface v2.0
└── Home.py
```

## 📦 Instalação

### Pré-requisitos

- Python 3.10+
- Conta no Supabase (para a string de conexão)
- Credenciais do Google Cloud (para backup no Drive - opcional)

### Passo a Passo

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
   cd streamlit-customer-app
   ```

2. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configuração do Banco de Dados:**
   - O sistema espera uma string de conexão `DATABASE_URL` no arquivo `database_config.py` ou variável de ambiente.
   - Exemplo: `postgresql+psycopg2://USER:PASSWORD@HOST:5432/POSTGRES`

4. **Executar a Aplicação:**

   ```bash
   streamlit run Home.py
   ```

## 🔧 Configuração de Backup (Google Drive)

Para habilitar o backup em nuvem, obtenha o arquivo `credentials.json` no Console do Google Cloud (API Drive) e faça o upload na página de "Backup".

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

## ⚡ Infraestrutura e Manutenção

### Evitar Hibernação (Streamlit Cloud)

O projeto inclui um workflow do GitHub Actions (`.github/workflows/keep_awake.yml`) configurado para evitar que a aplicação entre em modo de hibernação no Streamlit Cloud.

- **Funcionamento:** O workflow executa um `curl` na URL da aplicação diariamente às 12:00 UTC.
- **Configuração:** A URL alvo está definida diretamente no arquivo do workflow.

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
