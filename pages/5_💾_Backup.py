import streamlit as st
import os
import shutil
import datetime
import google_drive_service
import backup_manager

st.set_page_config(page_title="Backup e Restauração", layout="wide")
st.title("💾 Backup e Restauração de Dados")
st.info("Gerencie cópias de segurança locais e em nuvem do seu banco de dados.")

DB_FILE = 'customers.db'

# --- Seção 1: Backup e Restauração Local ---
with st.expander("1. Backup e Restauração Local (Manual)", expanded=False):
    st.subheader("Criar e Baixar um Backup Local")
    st.write(f"Clique no botão abaixo para baixar uma cópia de segurança do seu banco de dados para o seu computador.")
    
    try:
        with open(DB_FILE, "rb") as fp:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"backup_{DB_FILE}_{timestamp}.db"
            st.download_button(
                label="Baixar Cópia de Segurança Local",
                data=fp,
                file_name=backup_filename,
                mime="application/octet-stream",
                use_container_width=True
            )
    except FileNotFoundError:
        st.warning(f"O arquivo do banco de dados (`{DB_FILE}`) ainda não existe. Cadastre um cliente para criá-lo.")

# --- Seção 2: Backup em Nuvem (Google Drive) ---
with st.expander("2. Backup em Nuvem (Google Drive)", expanded=True):
    st.header("Gerenciamento de Backup na Nuvem")
    
    # Verifica se o arquivo credentials.json existe. É pré-requisito para tudo.
    creds_exist = os.path.exists(google_drive_service.CREDENTIALS_FILE)
    
    try:
        authenticated_email = google_drive_service.get_authenticated_user_email() if creds_exist else None

        if authenticated_email:
            st.success(f"Conectado ao Google Drive como: **{authenticated_email}**")
            st.write("O backup automático está **ativo** (a cada 5 novos clientes).")
            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Forçar Backup para o Drive Agora", type="primary", use_container_width=True):
                    backup_manager.trigger_manual_backup()
            with c2:
                if st.button("Desconectar / Trocar Conta", use_container_width=True):
                    google_drive_service.disconnect_drive_account()
        else:
            # UI para o processo de configuração e conexão
            st.warning("Nenhuma conta Google Drive conectada.")
            st.markdown("---")

            st.subheader("Passo 1: Fazer upload do `credentials.json`")
            uploaded_creds = st.file_uploader(
                "Selecione o arquivo de credenciais (`credentials.json`) baixado do Google Cloud.",
                type=['json']
            )
            if uploaded_creds is not None:
                with open(google_drive_service.CREDENTIALS_FILE, "wb") as f:
                    f.write(uploaded_creds.getbuffer())
                st.success(f"Arquivo `{uploaded_creds.name}` salvo! Agora você pode se conectar no Passo 2.")
                if os.path.exists(google_drive_service.TOKEN_FILE):
                    os.remove(google_drive_service.TOKEN_FILE)
                st.rerun()

            st.markdown("---")
            st.subheader("Passo 2: Conectar ao Google Drive")
            
            # Habilita o botão apenas se o Passo 1 foi concluído
            connect_button_disabled = not creds_exist
            
            if connect_button_disabled:
                st.info("Complete o Passo 1 para habilitar a conexão.")
            
            if st.button("Conectar ao Google Drive", type="primary", use_container_width=True, disabled=connect_button_disabled):
                # Guarda no estado que o usuário iniciou a autenticação
                st.session_state.authentication_started = True

            # Se o usuário iniciou a autenticação, mostra a UI para colar o código
            if st.session_state.get("authentication_started"):
                google_drive_service.initiate_authentication()

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerenciar a conexão com o Google Drive: {e}")
        st.info("Verifique se o arquivo 'credentials.json' está correto e tente novamente.")

# --- Seção 3: Instruções de Configuração ---
with st.expander("Como configurar o arquivo `credentials.json`?", expanded=False):
    st.markdown("""
    Para usar o backup em nuvem, você precisa de um arquivo de credenciais do Google. Siga os passos:

    1.  **Acesse o Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com/)
    2.  **Crie um Novo Projeto:** No topo da página, clique em "Selecionar um projeto" > "NOVO PROJETO". Dê um nome (ex: `App de Backup`) e clique em "CRIAR".
    3.  **Ative a API do Google Drive:** Na barra de busca, procure por **"Google Drive API"** e clique em **"ATIVAR"**.
    4.  **Configure a Tela de Consentimento:**
        *   No menu lateral, vá para "APIs e Serviços" > "Tela de consentimento OAuth".
        *   Escolha **"Externo"** e clique em "CRIAR".
        *   Preencha o "Nome do app" (ex: `App de Backup`) e seu "E-mail de suporte do usuário".
        *   Role até o fim e clique em "SALVAR E CONTINUAR" nas seções seguintes, não precisa adicionar mais nada.
    5.  **Adicione seu E-mail como Testador:**
        *   Ainda na "Tela de consentimento OAuth", vá para a aba **"Usuários de teste"**.
        *   Clique em **"+ ADICIONAR USUÁRIOS"**, digite seu próprio e-mail do Google e clique em "SALVAR".
    6.  **Crie as Credenciais:**
        *   No menu lateral, vá para **"Credenciais"**.
        *   Clique em **"+ CRIAR CREDENCIAIS"** > **"ID do cliente OAuth"**.
        *   Em "Tipo de aplicativo", selecione **"App para computador"**.
        *   Clique em **"CRIAR"**.
    7.  **Baixe o Arquivo:**
        *   Uma janela aparecerá. Clique em **"FAZER O DOWNLOAD DO JSON"**.
        *   **Renomeie** o arquivo baixado para `credentials.json`.
        *   Use o botão de upload no **Passo 1** acima para enviar este arquivo.
    """)