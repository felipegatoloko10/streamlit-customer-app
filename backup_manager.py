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

def save_backup_config(threshold):
    """Salva a configuração de frequência do backup automático."""
    with open(BACKUP_CONFIG_FILE, 'w') as f:
        json.dump({"threshold": threshold}, f)

def _perform_gdrive_backup():
    """Função interna para realizar o backup para o Google Drive."""
    if not os.path.exists(DB_FILE):
        st.error(f"Erro ao criar backup: arquivo do banco de dados ('{DB_FILE}') não encontrado.")
        return False
        
    temp_db_path = f"temp_{DRIVE_BACKUP_FILE_NAME}"
    try:
        shutil.copy(DB_FILE, temp_db_path)
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
    Verifica a quantidade real de clientes no banco e decide se é hora de fazer backup.
    """
    import database
    import google_drive_service
    import logging

    # 1. Verifica se o Google Drive está autenticado primeiro de forma silenciosa
    if not os.path.exists(google_drive_service.TOKEN_FILE):
        logging.info("Backup automático ignorado: Google Drive não autenticado.")
        return 0

    try:
        # Conta quantos clientes reais existem no banco de dados
        current_count = database.count_total_records()
    except Exception as e:
        logging.error(f"Erro ao contar registros para backup: {e}")
        return 0
    
    threshold = load_backup_threshold()

    # Só faz o backup se atingir o limite exato (múltiplo)
    if current_count > 0 and current_count % threshold == 0:
        logging.info(f"Iniciando backup automático (Limite {threshold} atingido).")
        # Rodamos o backup de forma que não trave a interface principal se possível
        try:
            _perform_gdrive_backup()
        except Exception as e:
            logging.error(f"Falha no backup automático: {e}")
        
    return current_count

def trigger_manual_backup():
    """Dispara um backup manual para o Google Drive."""
    with st.spinner("Iniciando backup manual para o Google Drive..."):
        _perform_gdrive_backup()
