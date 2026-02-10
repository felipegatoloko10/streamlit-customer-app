import streamlit as st
import os
import shutil
import datetime
import json
import sqlite3
import google_drive_service
import backup_manager

import integration_services as services

# --- Configurações da Página e Constantes ---
st.set_page_config(page_title="Backup e Restauração", layout="centered")

# Exibe o status da nuvem na sidebar
services.show_cloud_status()

st.title("💾 Backup e Restauração de Dados")

# Exibe mensagem de sucesso se veio de uma autenticação
if st.session_state.get("auth_success"):
    st.success("✅ Conexão com Google Drive estabelecida com sucesso!")
    del st.session_state.auth_success

st.info("Gerencie cópias de segurança locais e em nuvem do seu banco de dados.")

DB_FILE = 'customers.db'

# --- Funções Auxiliares ---
def is_valid_db_file(file_path: str) -> bool:
    """Verifica se um arquivo é um banco de dados SQLite3 válido."""
    if not os.path.exists(file_path):
        return False
    try:
        conn = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 'ok'
    except sqlite3.Error:
        return False

def save_backup_config(threshold):
    """Salva a configuração de frequência do backup automático."""
    config_data = {"threshold": threshold}
    try:
        with open(backup_manager.BACKUP_CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
    except IOError as e:
        st.error(f"Erro ao salvar configurações de backup: {e}")

# --- Seção 1: Backup e Restauração Local ---
with st.expander("1. Backup e Restauração Local (Manual)", expanded=False):
    st.subheader("Criar e Baixar um Backup Local")
    if os.path.exists(DB_FILE):
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
    else:
        st.warning(f"O arquivo do banco de dados (`{DB_FILE}`) ainda não existe. Cadastre um cliente para criá-lo.")
    
    st.markdown("---")
    
    st.subheader("Restaurar a partir de um Backup Local")
    uploaded_file = st.file_uploader("Selecione um arquivo .db do seu computador:", type=['db'], key="backup_uploader")

    if uploaded_file:
        # Lógica de restauração a ser implementada (simples para este exemplo)
        st.info("Funcionalidade de restauração em desenvolvimento.")


# --- Seção 2: Backup em Nuvem (Google Drive) ---
st.markdown("---")
st.header("Backup em Nuvem (Google Drive)")

try:
    authenticated_email = google_drive_service.get_authenticated_user_email()

    if authenticated_email:
        st.success(f"**Status:** Conectado ao Google Drive como `{authenticated_email}`")
        st.markdown("---")
        
        st.subheader("Opções de Backup na Nuvem")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fazer Backup para o Drive Agora", type="primary", use_container_width=True):
                backup_manager.trigger_manual_backup()
        with col2:
            if st.button("Desconectar / Trocar Conta", use_container_width=True):
                google_drive_service.disconnect_drive_account()
                st.rerun()
        
        st.markdown("---")
        st.subheader("Backup Automático")
        current_threshold = backup_manager.load_backup_threshold()
        new_threshold = st.slider(
            f"Fazer backup a cada X novos clientes:",
            min_value=1, max_value=10, value=current_threshold
        )
        if new_threshold != current_threshold:
            save_backup_config(new_threshold)
            st.toast(f"Frequência de backup atualizada para cada {new_threshold} clientes.")

    else: # UI para quando o usuário NÃO ESTÁ CONECTADO
        st.warning("**Status:** Nenhuma conta Google Drive conectada.")
        st.markdown("---")
        
        with st.expander("Como configurar o backup no Google Drive?", expanded=True):
            st.subheader("Passo 1: Faça o upload do seu `credentials.json`")
            st.info("Para usar o backup em nuvem, você precisa de um arquivo de credenciais do Google.")
            
            uploaded_creds = st.file_uploader("Selecione o arquivo de credenciais", type=['json'], key="gdrive_creds_uploader")
            
            if uploaded_creds:
                # Verifica se o arquivo já existe e se o conteúdo é o mesmo para evitar loop
                creds_content = uploaded_creds.getbuffer()
                should_save = True
                if os.path.exists(google_drive_service.CREDENTIALS_FILE):
                    with open(google_drive_service.CREDENTIALS_FILE, "rb") as f:
                        if f.read() == creds_content:
                            should_save = False
                
                if should_save:
                    with open(google_drive_service.CREDENTIALS_FILE, "wb") as f:
                        f.write(creds_content)
                    st.success(f"Arquivo `{uploaded_creds.name}` salvo! Prossiga para o Passo 2.")
                    # Limpa o token antigo para forçar nova autenticação se as credenciais mudaram
                    if os.path.exists(google_drive_service.TOKEN_FILE):
                        os.remove(google_drive_service.TOKEN_FILE)
                    st.rerun()

            st.markdown("---")
            
            st.subheader("Passo 2: Conecte sua Conta Google")
            creds_exist = os.path.exists(google_drive_service.CREDENTIALS_FILE)
            
            if not creds_exist:
                st.caption("O botão de conexão será habilitado após o upload do `credentials.json` no Passo 1.")
            
            # Novo fluxo de autenticação manual para nuvem
            if creds_exist:
                auth_url = google_drive_service.get_auth_url()
                st.markdown(f"1. [Clique aqui para autorizar o acesso ao Google Drive]({auth_url})")
                st.write("2. Faça login, copie o **código** que o Google fornecer e cole abaixo:")
                
                auth_code = st.text_input("Cole o código de autorização aqui:", key="gdrive_auth_code")
                
                if st.button("Confirmar Conexão", type="primary", use_container_width=True):
                    if auth_code:
                        with st.spinner("Validando conexão..."):
                            success = google_drive_service.finalize_manual_auth(auth_code)
                        if success:
                            st.success("Conexão estabelecida!")
                            st.rerun()
                    else:
                        st.warning("Por favor, insira o código de autorização.")
            
            st.markdown("---")
            with st.expander("Instruções detalhadas para gerar o `credentials.json`"):
                st.markdown("""
                1.  **Acesse o Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com/)
                2.  **Crie um Novo Projeto:** No topo da página, clique em "Selecionar um projeto" > "NOVO PROJETO". Dê um nome (ex: `App Backup`) e clique em "CRIAR".
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
                    *   Uma janela aparecerá. Clique no botão **"FAZER O DOWNLOAD DO JSON"**.
                    *   **Renomeie** o arquivo baixado para `credentials.json`.
                    *   Use o botão de upload no **Passo 1** acima para enviar este arquivo.
                """)

except Exception as e:
    st.error(f"Ocorreu um erro fatal na página de Backup: {e}")
    st.exception(e)