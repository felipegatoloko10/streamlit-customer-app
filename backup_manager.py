import os
import json
import streamlit as st
import google_drive_service
import shutil
import time

BACKUP_COUNTER_FILE = "backup_counter.json"
NEW_CUSTOMER_THRESHOLD = 5
DB_FILE = "customers.db" # Referência ao arquivo do banco de dados principal
DRIVE_BACKUP_FILE_NAME = "customers_backup.db" # Nome fixo para o arquivo no Google Drive

def load_counter():
    """Carrega o contador de clientes para backup automático."""
    if os.path.exists(BACKUP_COUNTER_FILE):
        with open(BACKUP_COUNTER_FILE, 'r') as f:
            return json.load(f).get("count", 0)
    return 0

def save_counter(count):
    """Salva o contador de clientes para backup automático."""
    with open(BACKUP_COUNTER_FILE, 'w') as f:
        json.dump({"count": count}, f, indent=4)

def _perform_gdrive_backup():
    """Função interna para realizar o backup para o Google Drive."""
    # 1. Cria uma cópia temporária do DB para upload
    temp_db_path = f"temp_{DRIVE_BACKUP_FILE_NAME}"
    try:
        shutil.copy(DB_FILE, temp_db_path)
    except FileNotFoundError:
        st.error(f"Erro ao criar backup: arquivo '{DB_FILE}' não encontrado.")
        return False # Indica falha

    try:
        # 2. Envia para o Google Drive (sobrescreve se existir)
        google_drive_service.upload_file_to_drive(temp_db_path, DRIVE_BACKUP_FILE_NAME)
        st.success("Backup do banco de dados enviado para o Google Drive com sucesso!")
        return True # Indica sucesso
    except google_drive_service.GoogleDriveServiceError as e:
        st.error(f"Erro no backup para o Google Drive: {e}")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o backup: {e}")
        return False
    finally:
        # 3. Limpa o arquivo temporário
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def increment_and_check_backup():
    """
    Incrementa o contador de clientes e verifica se é hora de fazer um backup.
    Se for, faz o backup e envia para o Google Drive.
    """
    current_count = load_counter()
    current_count += 1
    save_counter(current_count)

    if current_count >= NEW_CUSTOMER_THRESHOLD:
        st.info(f"Contador de clientes atingiu {NEW_CUSTOMER_THRESHOLD}. Iniciando backup automático para o Google Drive...")
        if _perform_gdrive_backup():
            save_counter(0) # Reseta o contador apenas se o backup foi bem-sucedido
        else:
            st.warning("Backup automático falhou, o contador não foi resetado. Tente novamente.")
    return current_count

def trigger_manual_backup():
    """Dispara um backup manual para o Google Drive."""
    st.info("Iniciando backup manual para o Google Drive...")
    _perform_gdrive_backup()
    st.rerun() # Atualiza a UI após o backup manual