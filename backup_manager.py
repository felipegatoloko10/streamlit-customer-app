import os
import json
import streamlit as st
import google_drive_service
import shutil
import time

BACKUP_COUNTER_FILE = "backup_counter.json"
BACKUP_CONFIG_FILE = "backup_config.json"
DB_FILE = "customers.db"
DRIVE_BACKUP_FILE_NAME = "customers_backup.db"

def load_counter():
    """Carrega o contador de clientes para backup automático."""
    if os.path.exists(BACKUP_COUNTER_FILE):
        try:
            with open(BACKUP_COUNTER_FILE, 'r') as f:
                return json.load(f).get("count", 0)
        except (IOError, json.JSONDecodeError):
            return 0
    return 0

def save_counter(count):
    """Salva o contador de clientes para backup automático."""
    with open(BACKUP_COUNTER_FILE, 'w') as f:
        json.dump({"count": count}, f, indent=4)

def load_backup_threshold():
    """Carrega o limite de clientes para o backup automático."""
    if os.path.exists(BACKUP_CONFIG_FILE):
        try:
            with open(BACKUP_CONFIG_FILE, 'r') as f:
                return json.load(f).get("threshold", 5) # Padrão 5 se a chave não existir
        except (IOError, json.JSONDecodeError):
            return 5
    return 5 # Padrão 5 se o arquivo não existir

def _perform_gdrive_backup():
    """Função interna para realizar o backup para o Google Drive."""
    temp_db_path = f"temp_{DRIVE_BACKUP_FILE_NAME}"
    try:
        shutil.copy(DB_FILE, temp_db_path)
    except FileNotFoundError:
        st.error(f"Erro ao criar backup: arquivo do banco de dados ('{DB_FILE}') não encontrado.")
        return False

    try:
        google_drive_service.upload_file_to_drive(temp_db_path, DRIVE_BACKUP_FILE_NAME)
        st.toast("Backup para o Google Drive concluído com sucesso!", icon="✅")
        return True
    except google_drive_service.GoogleDriveServiceError as e:
        st.error(f"Erro no backup para o Google Drive: {e}")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o backup: {e}")
        return False
    finally:
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
    
    threshold = load_backup_threshold()

    if current_count >= threshold:
        st.toast(f"Gatilho de backup automático atingido ({threshold} clientes). Iniciando backup...", icon="☁️")
        time.sleep(2) # Pausa para o toast ser visível
        if _perform_gdrive_backup():
            save_counter(0)
        else:
            st.warning("Backup automático falhou. O contador não foi resetado e tentará novamente no próximo cliente.")
    return current_count

def trigger_manual_backup():
    """Dispara um backup manual para o Google Drive."""
    st.info("Iniciando backup manual para o Google Drive...")
    _perform_gdrive_backup()
    st.rerun()
