import os
import json
import streamlit as st
import google_drive_service
import datetime
import pandas as pd
import io

# from services.customer_service import CustomerService  <-- REMOVIDO PARA EVITAR CIRCULAR IMPORT

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
    from services.customer_service import CustomerService
    service = CustomerService()
    
    # Usando paginação grande para pegar tudo
    all_customers = service.get_customer_grid_data(page_size=10000) 
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"customers_backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_customers, f, ensure_ascii=False, indent=4, default=str)
        
    return filename

def _perform_gdrive_backup():
    """Gera JSON e faz upload para o Drive."""
    try:
        json_file = _generate_json_export()
        
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
    import logging
    from services.customer_service import CustomerService

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

def _generate_csv_export():
    """Gera um arquivo CSV com todos os dados dos clientes."""
    from services.customer_service import CustomerService
    service = CustomerService()
    all_customers = service.get_customer_grid_data(page_size=10000)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"customers_backup_{timestamp}.csv"
    
    df = pd.DataFrame(all_customers)
    # Força ponto e vírgula para abrir fácil no Excel pt-BR, e utf-8-sig para acentos
    df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
    
    return filename

def generate_local_export(format='json'):
    """Gera o arquivo de exportação localmente e retorna o caminho."""
    if format.lower() == 'csv':
        return _generate_csv_export()
    # Default json
    return _generate_json_export()

def restore_data(file_path: str, format: str):
    """Restaura dados a partir de um arquivo JSON ou CSV."""
    from services.customer_service import CustomerService
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
            # Tenta ler com separador ; primeiro (padrão do nosso export)
            try:
                df = pd.read_csv(file_path, sep=';')
                # Se só tiver 1 coluna, pode ser que o separador seja vírgula
                if df.shape[1] == 1:
                     df_comma = pd.read_csv(file_path, sep=',')
                     if df_comma.shape[1] > 1:
                         df = df_comma
            except:
                df = pd.read_csv(file_path, sep=',')
            
            # Substituir NaN por None ou string vazia para evitar problemas na validação
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient='records')
        
        for item in data:
            try:
                # Tratamento de ID: removemos para criar novos registros no Postgres
                if 'id' in item:
                    del item['id']
                
                # Adaptação de campos se necessário (ex: renomear colunas do CSV se vierem diferentes)
                # Assumindo que o CSV tem os mesmos nomes de colunas que as chaves do dict do service
                
                service.create_customer(item)
                success_count += 1
            except Exception as e:
                # Se for duplicado, apenas conta como erro/ignorado
                # Verifica erro de duplicidade do Postgres/Supabase
                if "duplicate key value violates unique constraint" in str(e) or "already exists" in str(e):
                    pass
                else:
                     errors.append(f"Erro no item {item.get('nome_completo', 'Desconhecido')}: {str(e)}")
                error_count += 1

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
    """Dispara backup manual para o Google Drive."""
    with st.spinner("Gerando exportação e enviando para o Drive..."):
        _perform_gdrive_backup()
