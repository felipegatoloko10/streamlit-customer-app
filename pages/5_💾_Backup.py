import streamlit as st
import os
import shutil
import datetime
from streamlit_modal import Modal
import sqlite3
import google_drive_service
import backup_manager

# --- Configurações da Página e Constantes ---
st.set_page_config(page_title="Backup e Restauração", layout="wide")
st.title("💾 Backup e Restauração de Dados")
st.info("Gerencie cópias de segurança locais e em nuvem do seu banco de dados.")

DB_FILE = 'customers.db'

def is_valid_db_file(file_path: str) -> bool:
    """Verifica se um arquivo é um banco de dados SQLite3 válido."""
    try:
        conn = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 'ok'
    except sqlite3.Error:
        return False

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
        st.warning(f"O arquivo do banco de dados (`{DB_FILE}`) ainda não existe.")
    
    st.markdown("---")
    
    st.subheader("Restaurar a partir de um Backup Local")
    st.write(f"Selecione um arquivo de backup (.db) do seu computador. **Atenção: esta ação substituirá todos os dados atuais!**")

    # A lógica de restauração local existente permanece aqui
    if 'temp_uploaded_filepath' not in st.session_state:
        st.session_state.temp_uploaded_filepath = None
    if 'is_uploaded_file_valid' not in st.session_state:
        st.session_state.is_uploaded_file_valid = False
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None

    uploaded_file = st.file_uploader("Escolha um arquivo de backup (.db)", type=['db'], key="backup_uploader")

    if uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_filename:
        # ... (código de validação do arquivo de restauração)
        st.session_state.uploaded_filename = uploaded_file.name
        temp_path = os.path.join(os.path.dirname(__file__), f"temp_uploaded_{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.temp_uploaded_filepath = temp_path
        if is_valid_db_file(temp_path):
            st.session_state.is_uploaded_file_valid = True
            st.success(f"Arquivo '{uploaded_file.name}' validado! Pronto para restauração.")
        else:
            st.session_state.is_uploaded_file_valid = False
            st.error(f"O arquivo '{uploaded_file.name}' não é um banco de dados válido.")
            os.remove(temp_path)
            st.session_state.temp_uploaded_filepath = None
            st.session_state.uploaded_filename = None
    
    if st.session_state.is_uploaded_file_valid and st.session_state.temp_uploaded_filepath:
        st.warning(f"""
        **Você está prestes a substituir o banco de dados atual pelos dados do arquivo '{st.session_state.uploaded_filename}'.**
        
        Todos os clientes cadastrados desde a criação deste backup serão perdidos. 
        
        Esta ação criará um backup de segurança do estado atual antes de restaurar, mas prossiga com cautela.
        """)

        restore_modal = Modal(
            "Confirmar Restauração",
            key="restore_modal",
            padding=20,
            max_width=500
        )

        if st.button("Iniciar Processo de Restauração", type="primary"):
            restore_modal.open()

        if restore_modal.is_open():
            with restore_modal.container():
                st.write("### Confirmação Final")
                st.write(f"Tem certeza de que deseja substituir o banco de dados atual pelo arquivo **{st.session_state.uploaded_filename}**?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sim, Restaurar Agora", type="primary"):
                        try:
                            if os.path.exists(DB_FILE):
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                pre_restore_backup_filename = f"pre-restore-backup_{timestamp}.db"
                                shutil.copy(DB_FILE, pre_restore_backup_filename)
                                st.info(f"Backup de segurança criado: `{pre_restore_backup_filename}`")

                            shutil.move(st.session_state.temp_uploaded_filepath, DB_FILE)
                            st.session_state.temp_uploaded_filepath = None

                            st.success("Banco de dados restaurado com sucesso! O aplicativo será reiniciado.")
                            st.cache_resource.clear()
                            st.cache_data.clear()
                            
                            restore_modal.close()
                            st.rerun()

                        except Exception as e:
                            st.error(f"Ocorreu um erro inesperado durante a restauração: {e}")
                            restore_modal.close()

                with col2:
                    if st.button("Cancelar"):
                        if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
                            os.remove(st.session_state.temp_uploaded_filepath)
                        st.session_state.temp_uploaded_filepath = None
                        st.session_state.is_uploaded_file_valid = False
                        st.session_state.uploaded_filename = None
                        restore_modal.close()

# --- Seção 2: Backup em Nuvem (Google Drive) ---
with st.expander("2. Backup em Nuvem (Google Drive)", expanded=True):
    st.subheader("Status e Ações")

    try:
        authenticated_email = google_drive_service.get_authenticated_user_email()

        if authenticated_email:
            st.success(f"Conectado ao Google Drive como: **{authenticated_email}**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Forçar Backup para o Drive Agora", type="primary", use_container_width=True):
                    backup_manager.trigger_manual_backup()
            with c2:
                if st.button("Desconectar / Trocar Conta", use_container_width=True):
                    google_drive_service.disconnect_drive_account()
        else:
            st.warning("Nenhuma conta Google Drive conectada.")
            if st.button("Conectar ao Google Drive", type="primary", use_container_width=True):
                # A função abaixo irá mostrar os passos de autenticação na tela
                google_drive_service.initiate_authentication()
    
    except google_drive_service.GoogleDriveServiceError as e:
        st.error(f"Erro de Serviço: {e}")
        st.info("Verifique se o arquivo 'credentials.json' está correto e tente novamente.")

# --- Seção 3: Configuração e Ajuda ---
with st.expander("3. Como Configurar o Backup no Google Drive?"):
    st.info("Para usar o backup em nuvem, você precisa de um arquivo de credenciais do Google.")

    uploaded_creds = st.file_uploader("1. Faça o upload do seu arquivo `credentials.json` aqui:", type=['json'])
    if uploaded_creds is not None:
        try:
            with open(google_drive_service.CREDENTIALS_FILE, "wb") as f:
                f.write(uploaded_creds.getbuffer())
            st.success(f"Arquivo `{uploaded_creds.name}` salvo como `{google_drive_service.CREDENTIALS_FILE}`! Agora você pode se conectar.")
            # Desconecta a conta antiga para forçar o uso das novas credenciais
            if os.path.exists(google_drive_service.TOKEN_FILE):
                google_drive_service.disconnect_drive_account()
            else:
                st.rerun()

        except Exception as e:
            st.error(f"Não foi possível salvar o arquivo de credenciais: {e}")

    st.markdown("---")
    st.subheader("2. Siga os passos abaixo para gerar o arquivo:")
    st.markdown("""
    1.  **Acesse o Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com/)
    2.  **Crie um Novo Projeto:** Se não tiver um, clique em "Selecionar um projeto" e "NOVO PROJETO". Dê um nome (ex: "App Backup") e clique em "CRIAR".
    3.  **Ative a API do Google Drive:** No menu de busca, procure por **"Google Drive API"** e clique em **"ATIVAR"**.
    4.  **Configure a Tela de Consentimento:**
        *   No menu à esquerda, vá para "Tela de consentimento OAuth".
        *   Escolha o tipo de usuário **"Externo"** e clique em "CRIAR".
        *   Preencha o "Nome do app" (ex: "App Backup") e seu "E-mail de suporte do usuário".
        *   Role até o fim e clique em "SALVAR E CONTINUAR" nas seções seguintes, não precisa adicionar mais nada.
    5.  **Crie as Credenciais:**
        *   No menu à esquerda, vá para **"Credenciais"**.
        *   Clique em **"+ CRIAR CREDENCIAIS"** e escolha **"ID do cliente OAuth"**.
        *   No campo "Tipo de aplicativo", selecione **"App para computador"**.
        *   Clique em **"CRIAR"**.
    6.  **Baixe e Faça o Upload:**
        *   Uma janela aparecerá. Clique no botão **"FAZER O DOWNLOAD DO JSON"**.
        *   O arquivo baixado terá um nome longo. **Renomeie-o para `credentials.json`**.
        *   Use o botão de upload acima para enviar este arquivo.
    """)