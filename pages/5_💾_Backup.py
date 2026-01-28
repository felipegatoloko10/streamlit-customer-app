import streamlit as st
import os
import shutil
import datetime
from streamlit_modal import Modal
import sqlite3

st.set_page_config(
    page_title="Backup e Restauração",
    page_icon="💾"
)

def is_valid_db_file(file_path: str) -> bool:
    """Verifica se um arquivo é um banco de dados SQLite3 válido."""
    try:
        # Conecta em modo somente leitura para segurança
        conn = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        # Executa uma verificação de integridade
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        # O resultado esperado para um banco de dados íntegro é 'ok'
        return result and result[0] == 'ok'
    except sqlite3.Error:
        # Se ocorrer qualquer erro de SQLite, o arquivo é inválido
        return False


st.title("💾 Backup e Restauração de Dados")

st.info("Esta seção permite que você salve (backup) e recupere (restaure) o banco de dados de clientes.")

DB_FILE = 'customers.db'

# --- Seção de Backup ---
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

# --- Seção de Restauração ---
st.header("2. Restaurar a partir de um Backup")
st.write(f"Selecione um arquivo de backup (.db) para restaurar a base de dados. **Atenção: esta ação substituirá todos os dados atuais!**")

# Variáveis de estado para gerenciar o arquivo e sua validade
if 'temp_uploaded_filepath' not in st.session_state:
    st.session_state.temp_uploaded_filepath = None
if 'is_uploaded_file_valid' not in st.session_state:
    st.session_state.is_uploaded_file_valid = False
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None

uploaded_file = st.file_uploader("Escolha um arquivo de backup (.db)", type=['db'], key="backup_uploader")

# Detectar se um novo arquivo foi carregado ou se o uploader foi limpo
if uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_filename:
    # Um novo arquivo foi carregado - limpar arquivo anterior se houver
    if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
        os.remove(st.session_state.temp_uploaded_filepath)

    st.session_state.uploaded_filename = uploaded_file.name
    # Usar um path seguro no diretório do script
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
        os.remove(temp_path) # Remover arquivo inválido
        st.session_state.temp_uploaded_filepath = None
        st.session_state.uploaded_filename = None # Resetar para permitir novo upload
elif uploaded_file is None and st.session_state.uploaded_filename is not None:
    # O uploader foi limpo pelo usuário (ou por uma ação interna)
    if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
        os.remove(st.session_state.temp_uploaded_filepath)
    st.session_state.temp_uploaded_filepath = None
    st.session_state.is_uploaded_file_valid = False
    st.session_state.uploaded_filename = None

# Agora, o restante da UI depende do estado atual
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
                        # 1. Backup de segurança
                        if os.path.exists(DB_FILE):
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            pre_restore_backup_filename = f"pre-restore-backup_{timestamp}.db"
                            shutil.copy(DB_FILE, pre_restore_backup_filename)
                            st.info(f"Backup de segurança criado: `{pre_restore_backup_filename}`")

                        # 2. Mover o arquivo temporário validado para o local do DB_FILE
                        shutil.move(st.session_state.temp_uploaded_filepath, DB_FILE)
                        st.session_state.temp_uploaded_filepath = None # Limpar o path do temporário

                        st.success("Banco de dados restaurado com sucesso! O aplicativo será reiniciado.")
                        
                        # 3. Limpar caches
                        st.cache_resource.clear()
                        st.cache_data.clear()
                        
                        restore_modal.close()
                        st.rerun()

                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado durante a restauração: {e}")
                        restore_modal.close()

            with col2:
                if st.button("Cancelar"):
                    # Se cancelar, limpar o arquivo temporário e resetar o estado
                    if st.session_state.temp_uploaded_filepath and os.path.exists(st.session_state.temp_uploaded_filepath):
                        os.remove(st.session_state.temp_uploaded_filepath)
                    st.session_state.temp_uploaded_filepath = None
                    st.session_state.is_uploaded_file_valid = False
                    st.session_state.uploaded_filename = None
                    restore_modal.close()