import streamlit as st
import os
import shutil
import datetime
from streamlit_modal import Modal
import sqlite3
import google_drive_service
import backup_manager

st.set_page_config(
    page_title="Backup e Restauração",
    page_icon="💾"
)

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

st.title("💾 Backup e Restauração de Dados")
st.info("Esta seção permite que você salve (backup) e recupere (restaure) o banco de dados de clientes.")

DB_FILE = 'customers.db'

# --- Seção 1. Criar e Baixar um Backup ---
st.header("1. Criar e Baixar um Backup")
st.write(f"Clique no botão abaixo para baixar uma cópia de segurança do seu banco de dados atual (`{DB_FILE}`).")

try:
    with open(DB_FILE, "rb") as fp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{DB_FILE}_{timestamp}.db"
        
        st.download_button(
            label="Clique para Baixar o Backup",
            data=fp,
            file_name=backup_filename,
            mime="application/octet-stream",
            width='stretch'
        )
except FileNotFoundError:
    st.error(f"O arquivo do banco de dados (`{DB_FILE}`) não foi encontrado. Cadastre pelo menos um cliente para criar o banco de dados e poder fazer o backup.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao preparar o backup para download: {e}")

st.markdown("---")

# --- Seção 2. Restaurar a partir de um Backup ---
st.header("2. Restaurar a partir de um Backup")
st.write(f"Selecione um arquivo de backup (.db) para restaurar a base de dados. **Atenção: esta ação substituirá todos os dados atuais!**")

if 'temp_uploaded_filepath' not in st.session_state:
    st.session_state.temp_uploaded_filepath = None
if 'is_uploaded_file_valid' not in st.session_state:
    st.session_state.is_uploaded_file_valid = False
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None

uploaded_file = st.file_uploader("Escolha um arquivo de backup (.db)", type=['db'], key="backup_uploader")

if uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_filename:
    if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
        os.remove(st.session_state.temp_uploaded_filepath)

    st.session_state.uploaded_filename = uploaded_file.name
    temp_path = os.path.join(os.path.dirname(__file__), f"temp_uploaded_{uploaded_file.name}")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.session_state.temp_uploaded_filepath = temp_path
    
    if is_valid_db_file(temp_path):
        st.session_state.is_uploaded_file_valid = True
        st.success(f"Arquivo '{uploaded_file.name}' validado com sucesso! Pronto para restauração.")
    else:
        st.session_state.is_uploaded_file_valid = False
        st.error(f"O arquivo '{uploaded_file.name}' não parece ser um banco de dados SQLite válido ou está corrompido. Por favor, tente outro arquivo.")
        os.remove(temp_path)
        st.session_state.temp_uploaded_filepath = None
        st.session_state.uploaded_filename = None
elif uploaded_file is None and st.session_state.uploaded_filename is not None:
    if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
        os.remove(st.session_state.temp_uploaded_filepath)
    st.session_state.temp_uploaded_filepath = None
    st.session_state.is_uploaded_file_valid = False
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

st.markdown("---")

# --- Seção 3. Backup em Nuvem (Google Drive) ---
st.header("3. Backup em Nuvem (Google Drive)")
st.write("Configure e gerencie o backup automático do banco de dados para o seu Google Drive.")

authenticated_email = google_drive_service.get_authenticated_user_email()

if authenticated_email:
    st.success(f"Conectado ao Google Drive como: **{authenticated_email}**")
    if st.button("Desconectar / Trocar Conta Google Drive"):
        google_drive_service.disconnect_drive_account()
    st.markdown("---")
    st.write("O backup automático será feito a cada 5 novos clientes cadastrados. Você também pode forçar um backup agora:")
    if st.button("Forçar Backup Agora para o Google Drive", type="primary"):
        backup_manager.trigger_manual_backup()
else:
    st.warning("Nenhuma conta Google Drive conectada. O backup automático será iniciado e pedirá sua autenticação na próxima vez que o backup automático for acionado.")
    st.info("Para conectar, clique no botão 'Forçar Backup Agora para o Google Drive'.")
    if st.button("Forçar Backup Agora para o Google Drive", type="primary", key="connect_gdrive_button_bottom"):
        backup_manager.trigger_manual_backup()
