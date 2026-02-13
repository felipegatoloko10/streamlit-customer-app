import os
import json
import streamlit as st
import google_drive_service
import datetime
from services.customer_service import CustomerService

BACKUP_COUNTER_FILE = "backup_counter.json"
BACKUP_CONFIG_FILE = "backup_config.json"
# DB_FILE não é mais usado para backup direto
DRIVE_BACKUP_FILE_NAME = "customers_export.json"

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
    try:
        with open(BACKUP_COUNTER_FILE, 'w') as f:
            json.dump({"count": count}, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar contador: {e}")

def load_backup_threshold():
    """Carrega o limite de clientes para o backup automático."""
    if os.path.exists(BACKUP_CONFIG_FILE):
        try:
            with open(BACKUP_CONFIG_FILE, 'r') as f:
                return json.load(f).get("threshold", 5)
        except (IOError, json.JSONDecodeError):
            return 5
    return 5

def save_backup_config(threshold):
    """Salva a configuração de frequência do backup automático."""
    try:
        with open(BACKUP_CONFIG_FILE, 'w') as f:
            json.dump({"threshold": threshold}, f)
    except Exception as e:
        st.error(f"Erro ao salvar config de backup: {e}")

def _generate_json_export():
    """Gera um arquivo JSON com todos os dados dos clientes."""
    service = CustomerService()
    # Usando paginação grande para pegar tudo (limit 10000) ou criar método .all() no repo.
    # Vamos usar list_customers com limite alto.
    # Idealmente, criar um método export_all no repo.
    # Por enquanto, vamos iterar ou aumentar o limite.
    # Vamos assumir que 10000 é suficiente por enquanto ou paginar.
    all_customers = service.get_customer_grid_data(page_size=10000) 
    # Note: get_customer_grid_data retorna dicts formatados para UI.
    # Para backup puro, seria melhor o model_dump raw.
    # Vamos usar o que temos para simplicidade de restauração futura (embora raw fosse melhor).
    
    # Melhor abordagem: exportar usando pandas do repository para garantir dados crus?
    # Ou criar um método getAll no service.
    # Vamos deixar simples: exportar o grid data por enquanto.
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"customers_backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_customers, f, ensure_ascii=False, indent=4, default=str)
        
    return filename

def _perform_gdrive_backup():
    """Gera JSON e faz upload para o Drive."""
    try:
        json_file = _generate_json_export()
        
        # Nome no Drive (sobrescreve o anterior ou cria novo versionado?)
        # Vamos manter um nome fixo para "último backup" ou adicionar data?
        # A função original usava 'customers_backup.db'.
        # Vamos usar 'customers_full_backup.json' para manter único e atualizar versões no Drive se configurado assim.
        
        google_drive_service.upload_file_to_drive(json_file, DRIVE_BACKUP_FILE_NAME)
        st.toast("Backup (Exportação JSON) para Google Drive concluído!", icon="✅")
        
        # Limpa arquivo local
        if os.path.exists(json_file):
            os.remove(json_file)
            
        return True
    except Exception as e:
        st.error(f"Erro no backup para o Drive: {e}")
        return False

def increment_and_check_backup():
    """Verifica contagem e dispara backup se necessário."""
    import google_drive_service
    import logging

    if not os.path.exists(google_drive_service.TOKEN_FILE):
        return 0

    try:
        service = CustomerService()
        current_count = service.count_customers()
    except Exception as e:
        logging.error(f"Erro ao contar para backup: {e}")
        return 0
    
    threshold = load_backup_threshold()

    if current_count > 0 and current_count % threshold == 0:
        logging.info("Iniciando backup automático...")
        try:
            _perform_gdrive_backup()
        except Exception as e:
            logging.error(f"Falha no backup auto: {e}")
        
    return current_count

import pandas as pd
import io

# ... imports existing ...

def _generate_csv_export():
    """Gera um arquivo CSV com todos os dados dos clientes."""
    service = CustomerService()
    all_customers = service.get_customer_grid_data(page_size=10000)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"customers_backup_{timestamp}.csv"
    
    df = pd.DataFrame(all_customers)
    df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
    
    return filename

def generate_local_export(format='json'):
    """Gera o arquivo de exportação localmente e retorna o caminho."""
    if format.lower() == 'csv':
        return _generate_csv_export()
    return _generate_json_export()

def restore_data(file_path: str, format: str):
    """Restaura dados a partir de um arquivo JSON ou CSV."""
    service = CustomerService()
    success_count = 0
    error_count = 0
    errors = []

    try:
        data = []
        if format.lower() == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif format.lower() == 'csv':
            # Detecção de separador simples ou fixo em ';'
            try:
                df = pd.read_csv(file_path, sep=';')
            except:
                df = pd.read_csv(file_path, sep=',')
            
            # Substituir NaN por None ou string vazia para evitar problemas na validação
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient='records')
        
        for item in data:
            try:
                # Remove campos que não devem ser passados para criação (como ID, link_wpp)
                # O create_customer ignora chaves extras? Não, ele usa .get().
                # Mas é bom limpar para garantir.
                # O create_customer espera 'endereco' para logradouro.
                # O get_customer_grid_data retorna 'endereco' com o logradouro, então deve casar.
                
                # Tratamento de ID: removemos para criar novos registros
                if 'id' in item:
                    del item['id']
                
                service.create_customer(item)
                success_count += 1
            except Exception as e:
                # Se for duplicado, apenas conta como erro/ignorado
                if "já existe" in str(e) or "DuplicateEntryError" in str(e):
                    # Opcional: tentar update? Por hora, apenas skip.
                    pass
                error_count += 1
                errors.append(f"Erro no item {item.get('nome_completo', 'Desconhecido')}: {str(e)}")

        return {
            "success": True,
            "imported": success_count,
            "errors": error_count,
            "details": errors
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro fatal ao ler arquivo: {str(e)}"
        }

def trigger_manual_backup():
    """Manual trigger."""
    with st.spinner("Gerando exportação e enviando para o Drive..."):
        _perform_gdrive_backup()

