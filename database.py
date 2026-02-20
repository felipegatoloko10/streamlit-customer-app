import pandas as pd
import streamlit as st
import logging
import validators
import integration_services as services
import backup_manager
import datetime
import json
import sqlite3
from sqlmodel import select, Session, text
import database_config
from models import Cliente, Contato, Endereco, AuditLog, ChatHistory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass

class DuplicateEntryError(DatabaseError):
    """Exceção para entradas duplicadas (CPF/CNPJ)."""
    pass

# --- Constantes de Colunas ---
CLIENTES_COLUMNS = [
    'nome_completo', 'tipo_documento', 'cpf', 'cnpj',
    'data_nascimento', 'observacao', 'data_cadastro'
]

CONTATOS_COLUMNS = [
    'cliente_id', 'nome_contato', 'telefone', 'email_contato', 'cargo_contato', 'tipo_contato'
]

ENDERECOS_COLUMNS = [
    'cliente_id', 'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'tipo_endereco'
]

def log_action(cursor, entidade, entidade_id, acao, antes=None, depois=None):
    """Registra uma ação na tabela de auditoria."""
    import json
    sql = "INSERT INTO audit_logs (entidade, entidade_id, acao, dados_anteriores, dados_novos) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (
        entidade, 
        entidade_id, 
        acao, 
        json.dumps(antes, default=str) if antes else None, 
        json.dumps(depois, default=str) if depois else None
    ))

def _sanitize_data(data: dict) -> dict:
    """Padroniza textos (Title Case) e remove espaços extras dos dados do cliente."""
    clean = data.copy()
    
    # Campos que devem ser Title Case (Ex: "João Silva", "Rua das Flores")
    text_fields = ['nome_completo', 'contato1', 'contato2', 'cargo', 'logradouro', 'endereco', 'bairro', 'cidade']
    for field in text_fields:
        if clean.get(field):
            # Limpa espaços e coloca em Title Case
            clean[field] = " ".join(clean[field].split()).title()
            
    # Estado (UF) sempre em Maiúsculo (Ex: "SP")
    if clean.get('estado'):
        clean['estado'] = clean['estado'].strip().upper()[:2]
        
    # CEP limpo (apenas números)
    if clean.get('cep'):
        clean['cep'] = "".join(filter(str.isdigit, clean['cep']))
        
    return clean

def _validate_cliente_data(cliente_data: dict):
    """Valida os dados de um cliente antes de inserir/atualizar."""
    if not cliente_data.get('nome_completo') or not cliente_data.get('tipo_documento'):
        raise validators.ValidationError("Os campos 'Nome Completo' e 'Tipo de Documento' são obrigatórios para o cliente.")

    doc_type = cliente_data.get('tipo_documento')
    if doc_type == 'CPF':
        if not cliente_data.get('cpf'):
            raise validators.ValidationError("O campo 'CPF' é obrigatório para o cliente.")
        validators.is_valid_cpf(cliente_data['cpf'])
    elif doc_type == 'CNPJ':
        if not cliente_data.get('cnpj'):
            raise validators.ValidationError("O campo 'CNPJ' é obrigatório para o cliente.")
        validators.is_valid_cnpj(cliente_data['cnpj'])



def get_session():
    """Retorna uma nova sessão do banco de dados."""
    return Session(database_config.engine)

def log_audit(session: Session, entidade: str, entidade_id: int, acao: str, antes: dict = None, depois: dict = None, usuario: str = "Sistema"):
    """Registra uma ação na tabela de auditoria."""
    log = AuditLog(
        entidade=entidade,
        entidade_id=entidade_id,
        acao=acao,
        dados_anteriores=json.dumps(antes, default=str) if antes else None,
        dados_novos=json.dumps(depois, default=str) if depois else None,
        usuario=usuario
    )
    session.add(log)

def insert_customer(data: dict):
    """Insere um novo cliente e seus contatos/endereços usando SQLModel."""
    # Higieniza os dados
    data = _sanitize_data(data)
    
    # Validações básicas (mantendo a lógica original)
    _validate_cliente_data(data)

    with get_session() as session:
        try:
            # 1. Cliente
            cliente = Cliente(
                nome_completo=data.get('nome_completo'),
                tipo_documento=data.get('tipo_documento'),
                cpf=validators.unformat_cpf(data.get('cpf')) if data.get('cpf') else None,
                cnpj=validators.unformat_cnpj(data.get('cnpj')) if data.get('cnpj') else None,
                data_nascimento=data.get('data_nascimento'),
                observacao=data.get('observacao')
            )
            session.add(cliente)
            session.flush() # Para obter o ID gerado

            # 2. Contatos
            if data.get('telefone1') or data.get('contato1') or data.get('email') or data.get('cargo'):
                contato1 = Contato(
                    cliente_id=cliente.id,
                    nome_contato=data.get('contato1'),
                    telefone=validators.unformat_whatsapp(data.get('telefone1')) if data.get('telefone1') else None,
                    email_contato=data.get('email'),
                    cargo_contato=data.get('cargo'),
                    tipo_contato='Principal'
                )
                session.add(contato1)
            
            if data.get('telefone2') or data.get('contato2'):
                contato2 = Contato(
                    cliente_id=cliente.id,
                    nome_contato=data.get('contato2'),
                    telefone=validators.unformat_whatsapp(data.get('telefone2')) if data.get('telefone2') else None,
                    tipo_contato='Secundário'
                )
                session.add(contato2)

            # 3. Endereço
            if any(data.get(field) for field in ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado']):
                endereco = Endereco(
                    cliente_id=cliente.id,
                    cep=data.get('cep'),
                    logradouro=data.get('endereco'),
                    numero=data.get('numero'),
                    complemento=data.get('complemento'),
                    bairro=data.get('bairro'),
                    cidade=data.get('cidade'),
                    estado=data.get('estado'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    tipo_endereco='Principal'
                )
                session.add(endereco)

            # Auditoria
            log_audit(session, 'cliente', cliente.id, 'INSERT', depois=cliente.model_dump())
            
            session.commit()
            logging.info(f"Cliente '{cliente.nome_completo}' inserido com sucesso com ID: {cliente.id}.")

            # Tarefas assíncronas (mantidas do original)
            try:
                services.send_new_customer_email(data, cliente.id)
            except Exception as e:
                logging.error(f"Falha ao enviar e-mail de notificação: {e}")
            
            try:
                backup_manager.increment_and_check_backup()
            except Exception as e:
                logging.error(f"Erro ao tentar backup automático: {e}")

        except Exception as e:
            session.rollback()
            # Mapeamento de erros para manter compatibilidade
            if "UNIQUE constraint failed" in str(e):
                 raise DuplicateEntryError("O CPF ou CNPJ informado já existe.") from e
            raise DatabaseError(f"Erro ao salvar cliente: {e}") from e

def update_customer(customer_id: int, data: dict):
    """Atualiza um cliente existente e seus contatos/endereços após validação e sanitização."""
    # Higieniza os dados
    data = _sanitize_data(data)
    
    with get_session() as session:
        try:
            # Busca o cliente existente
            cliente = session.get(Cliente, customer_id)
            if not cliente:
                raise DatabaseError(f"Cliente com ID {customer_id} não encontrado.")

            # Dados anteriores para auditoria
            antes = cliente.model_dump()
            
            # 1. Atualizar Cliente
            if data.get('nome_completo'):
                cliente.nome_completo = data.get('nome_completo')
            if data.get('tipo_documento'):
                cliente.tipo_documento = data.get('tipo_documento')
            if data.get('data_nascimento'):
                cliente.data_nascimento = data.get('data_nascimento')
            if data.get('observacao'):
                cliente.observacao = data.get('observacao')
            if data.get('cpf'):
                cliente.cpf = validators.unformat_cpf(data.get('cpf'))
            if data.get('cnpj'):
                cliente.cnpj = validators.unformat_cnpj(data.get('cnpj'))
            
            session.add(cliente)

            # 2. Atualizar Contatos
            # Simplificação: Busca o contato principal existente ou cria um novo
            stmt_contato1 = select(Contato).where(Contato.cliente_id == customer_id, Contato.tipo_contato == 'Principal')
            contato1 = session.exec(stmt_contato1).first()

            if data.get('contato1') or data.get('telefone1') or data.get('email') or data.get('cargo'):
                if not contato1:
                    contato1 = Contato(cliente_id=cliente.id, tipo_contato='Principal')
                
                if data.get('contato1'): contato1.nome_contato = data.get('contato1')
                if data.get('telefone1'): contato1.telefone = validators.unformat_whatsapp(data.get('telefone1'))
                if data.get('email'): contato1.email_contato = data.get('email')
                if data.get('cargo'): contato1.cargo_contato = data.get('cargo')
                session.add(contato1)

            # Contato Secundário
            stmt_contato2 = select(Contato).where(Contato.cliente_id == customer_id, Contato.tipo_contato == 'Secundário')
            contato2 = session.exec(stmt_contato2).first()

            if data.get('contato2') or data.get('telefone2'):
                if not contato2:
                    contato2 = Contato(cliente_id=cliente.id, tipo_contato='Secundário')
                
                if data.get('contato2'): contato2.nome_contato = data.get('contato2')
                if data.get('telefone2'): contato2.telefone = validators.unformat_whatsapp(data.get('telefone2'))
                session.add(contato2)

            # 3. Atualizar Endereço
            stmt_endereco = select(Endereco).where(Endereco.cliente_id == customer_id, Endereco.tipo_endereco == 'Principal')
            endereco = session.exec(stmt_endereco).first()
            
            endereco_fields = ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'latitude', 'longitude']
            if any(data.get(f) for f in endereco_fields):
                if not endereco:
                    endereco = Endereco(cliente_id=cliente.id, tipo_endereco='Principal')
                
                if data.get('cep'): endereco.cep = data.get('cep')
                if data.get('endereco'): endereco.logradouro = data.get('endereco')
                if data.get('numero'): endereco.numero = data.get('numero')
                if data.get('complemento'): endereco.complemento = data.get('complemento')
                if data.get('bairro'): endereco.bairro = data.get('bairro')
                if data.get('cidade'): endereco.cidade = data.get('cidade')
                if data.get('estado'): endereco.estado = data.get('estado')
                if data.get('latitude'): endereco.latitude = data.get('latitude')
                if data.get('longitude'): endereco.longitude = data.get('longitude')
                session.add(endereco)

            # Auditoria
            log_audit(session, 'cliente', customer_id, 'UPDATE', antes=antes, depois=cliente.model_dump())
            
            session.commit()
            logging.info(f"Cliente com ID {customer_id} atualizado com sucesso.")

        except Exception as e:
            session.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise DuplicateEntryError("O CPF ou CNPJ informado já existe.") from e
            raise DatabaseError(f"Erro ao atualizar cliente: {e}") from e

def delete_customer(customer_id: int):
    """Exclui um cliente e seus dados relacionados."""
    with get_session() as session:
        try:
            cliente = session.get(Cliente, customer_id)
            if not cliente:
                raise DatabaseError(f"Cliente com ID {customer_id} não encontrado.")
            
            # Auditoria antes de excluir
            log_audit(session, 'cliente', customer_id, 'DELETE', antes=cliente.model_dump())
            
            session.delete(cliente)
            session.commit()
            logging.info(f"Cliente com ID {customer_id} excluído com sucesso.")
            
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Erro ao excluir cliente: {e}") from e

def get_customer_by_id(customer_id: int) -> dict:
    """Busca um único cliente pelo seu ID e retorna como um dicionário."""
    
    select_columns = [
        "cl.id", "cl.nome_completo", "cl.tipo_documento", "cl.cpf", "cl.cnpj",
        "cl.data_nascimento", "cl.observacao", "cl.data_cadastro",
        "co1.nome_contato AS contato1", "co1.telefone AS telefone1", "co1.email_contato AS email", "co1.cargo_contato AS cargo",
        "co2.nome_contato AS contato2", "co2.telefone AS telefone2", # Secondary contact
        "en.cep", "en.logradouro AS endereco", "en.numero", "en.complemento", "en.bairro", "en.cidade", "en.estado",
        "en.latitude", "en.longitude"
    ]
    
    query = f"""
        SELECT {', '.join(select_columns)}
        FROM clientes cl
        LEFT JOIN contatos co1 ON cl.id = co1.cliente_id AND co1.tipo_contato = 'Principal'
        LEFT JOIN contatos co2 ON cl.id = co2.cliente_id AND co2.tipo_contato = 'Secundário'
        LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        WHERE cl.id = %s
    """
    
    try:
        df = pd.read_sql_query(query, database_config.engine, params=(customer_id,))
        
        if not df.empty:
            customer_dict = df.iloc[0].to_dict()
            
            # Format dates (Pandas often returns Timestamp, convert to date)
            if customer_dict.get('data_nascimento'):
                try:
                    val = customer_dict['data_nascimento']
                    if isinstance(val, str):
                         customer_dict['data_nascimento'] = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                    elif hasattr(val, 'date'):
                         customer_dict['data_nascimento'] = val.date()
                except (ValueError, TypeError):
                    customer_dict['data_nascimento'] = None

            if customer_dict.get('data_cadastro'):
                try:
                    val = customer_dict['data_cadastro']
                    if isinstance(val, str):
                        customer_dict['data_cadastro'] = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                    elif hasattr(val, 'date'):
                         customer_dict['data_cadastro'] = val.date()
                except (ValueError, TypeError):
                    customer_dict['data_cadastro'] = None

            # Format CPF/CNPJ (unformat when saving, format when retrieving for display)
            if customer_dict.get('cpf'):
                customer_dict['cpf'] = validators.format_cpf(customer_dict.get('cpf'))
            if customer_dict.get('cnpj'):
                customer_dict['cnpj'] = validators.format_cnpj(customer_dict.get('cnpj'))
            
            # Format phone numbers
            if customer_dict.get('telefone1'):
                customer_dict['telefone1'] = validators.format_whatsapp(customer_dict.get('telefone1'))
            if customer_dict.get('telefone2'):
                customer_dict['telefone2'] = validators.format_whatsapp(customer_dict.get('telefone2'))

            return customer_dict
        else:
            return None

    except Exception as e:
        raise DatabaseError(f"Erro ao buscar cliente por ID: {e}") from e

def _build_where_clause(search_query: str = None, state_filter: str = None, start_date=None, end_date=None,
                        main_table_alias='cl', address_table_alias='en'):
    params = []
    conditions = []
    if search_query:
        # Postgres ILIKE is better for case-insensitive search
        conditions.append(f"({main_table_alias}.nome_completo ILIKE %s OR {main_table_alias}.cpf ILIKE %s OR {main_table_alias}.cnpj ILIKE %s)")
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if state_filter and state_filter != "Todos":
        conditions.append(f"{address_table_alias}.estado = %s")
        params.append(state_filter)
    if start_date and end_date:
        conditions.append(f"{main_table_alias}.data_cadastro BETWEEN %s AND %s")
        params.extend([start_date, end_date])
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def count_total_records(search_query: str = None, state_filter: str = None) -> int:
    
    # Pass aliases to _build_where_clause
    where_clause, params = _build_where_clause(search_query, state_filter, main_table_alias='cl', address_table_alias='en')
    
    query = "SELECT COUNT(DISTINCT cl.id) FROM clientes cl"
    if state_filter and state_filter != "Todos":
        query += " LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'"
    
    query += where_clause
    
    try:
        # Use pandas read_sql_query for simple scalar fetch too, or direct execution
        df = pd.read_sql_query(query, database_config.engine, params=params)
        return int(df.iloc[0, 0])
    except Exception as e:
        raise DatabaseError(f"Não foi possível contar os registros: {e}") from e

def fetch_data(search_query: str = None, state_filter: str = None, page: int = 1, page_size: int = 10):
    
    select_columns = [
        "cl.id", "cl.nome_completo", "cl.tipo_documento", "cl.cpf", "cl.cnpj",
        "cl.data_nascimento", "cl.observacao", "cl.data_cadastro",
        "co.nome_contato AS contato1", "co.telefone AS telefone1", "co.email_contato AS email", "co.cargo_contato AS cargo",
        "en.cep", "en.logradouro AS endereco", "en.numero", "en.complemento", "en.bairro", "en.cidade", "en.estado"
    ]
    
    # Use standard where clause builder
    where_clause, params = _build_where_clause(search_query, state_filter, main_table_alias='cl', address_table_alias='en')

    offset = (page - 1) * page_size
    
    # Se o filtro de estado estiver ativo, usamos JOIN (INNER) para filtrar. 
    # Caso contrário, usamos LEFT JOIN para não "esconder" clientes sem endereço principal.
    join_type = "JOIN" if (state_filter and state_filter != "Todos") else "LEFT JOIN"

    query = f"""
        SELECT {', '.join(select_columns)}
        FROM clientes cl
        LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
        {join_type} enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        {where_clause}
        ORDER BY cl.id DESC
        LIMIT %s OFFSET %s
    """
    
    try:
        # Pass page_size and offset to params
        full_params = params + [page_size, offset]
        df = pd.read_sql_query(query, database_config.engine, params=full_params)
        
        # Apply formatting as per original function
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.date
        df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce').dt.date
        
        if 'cpf' in df.columns:
            df['cpf'] = df['cpf'].apply(validators.format_cpf)
        if 'cnpj' in df.columns:
            df['cnpj'] = df['cnpj'].apply(validators.format_cnpj)
        
        # Adjust for new contact field names
        if 'telefone1' in df.columns: # co.telefone AS telefone1
            df['link_wpp_1'] = df['telefone1'].apply(validators.get_whatsapp_url)
            df['telefone1'] = df['telefone1'].apply(validators.format_whatsapp)
        # Note: 'telefone2' and 'link_wpp_2' are not directly supported in this simplified join.
        # This will be a known limitation for this refactoring stage and needs dedicated handling if full original data is required.

        return df
    except Exception as e:
         raise DatabaseError(f"Erro ao buscar dados: {e}") from e

def get_new_customers_timeseries(start_date, end_date, period='M'):
    """
    Busca dados para o gráfico de série temporal de novos clientes.
    Agrupa por Dia ('D'), Semana ('W'), ou Mês ('M').
    """
    
    if period == 'D':
        date_format = 'YYYY-MM-DD'
    elif period == 'W':
        # ISO Week
        date_format = 'YYYY-IW'
    else: # Mês
        date_format = 'YYYY-MM'
        
    query = f"""
        SELECT 
            TO_CHAR(data_cadastro, '{date_format}') as time_period,
            COUNT(id) as count
        FROM clientes
        WHERE data_cadastro BETWEEN %s AND %s
        GROUP BY time_period
        ORDER BY time_period;
    """
    try:
        df = pd.read_sql_query(query, database_config.engine, params=[start_date, end_date])
        return df
    except Exception as e:
        raise DatabaseError(f"Erro ao buscar série temporal de clientes: {e}") from e

def get_customers_by_state_for_map(start_date, end_date):
    """
    Busca a contagem de clientes por estado para o mapa coroplético.
    """
    query = """
        SELECT en.estado, COUNT(cl.id) as count 
        FROM clientes cl
        JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        WHERE en.estado IS NOT NULL AND en.estado != '' AND cl.data_cadastro BETWEEN %s AND %s
        GROUP BY en.estado;
    """
    try:
        df = pd.read_sql_query(query, database_config.engine, params=[start_date, end_date])
        return df
    except Exception as e:
        raise DatabaseError(f"Erro ao buscar contagem de clientes por estado: {e}") from e

def get_top_cities_by_state(start_date, end_date, state=None):
    """
    Busca o top 10 de cidades, opcionalmente filtrando por um estado.
    """
    # Pass state_filter directly to _build_where_clause
    where_clause, params = _build_where_clause(start_date=start_date, end_date=end_date, state_filter=state,
                                               main_table_alias='cl', address_table_alias='en')

    query = f"""
        SELECT en.cidade, COUNT(cl.id) as count
        FROM clientes cl
        JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        {where_clause}
        GROUP BY en.cidade
        ORDER BY count DESC
        LIMIT 10;
    """
    try:
        df = pd.read_sql_query(query, database_config.engine, params=params)
        return df
    except Exception as e:
        raise DatabaseError(f"Erro ao buscar top cidades: {e}") from e

def get_data_health_summary():
    """
    Calcula a porcentagem de completude para campos chave.
    """
    query = """
        SELECT
            COUNT(DISTINCT cl.id) as total_customers,
            COUNT(CASE WHEN co.email_contato IS NOT NULL AND co.email_contato != '' THEN 1 END) as with_email,
            COUNT(CASE WHEN co.telefone IS NOT NULL AND co.telefone != '' THEN 1 END) as with_phone,
            COUNT(CASE WHEN en.cep IS NOT NULL AND en.cep != '' THEN 1 END) as with_cep
        FROM clientes cl
        LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
        LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal';
    """
    try:
        df = pd.read_sql_query(query, database_config.engine)
        if df.empty or df['total_customers'][0] == 0:
            return {'email_completeness': 0, 'phone_completeness': 0, 'cep_completeness': 0}
        
        summary = {
            'email_completeness': (df['with_email'][0] / df['total_customers'][0]) * 100,
            'phone_completeness': (df['with_phone'][0] / df['total_customers'][0]) * 100,
            'cep_completeness': (df['with_cep'][0] / df['total_customers'][0]) * 100
        }
        return summary
    except Exception as e:
        raise DatabaseError(f"Erro ao calcular saúde dos dados: {e}") from e

def get_incomplete_customers():
    """
    Busca clientes com informações chave faltando.
    """
    query = """
        SELECT cl.id, cl.nome_completo, 
               CASE WHEN co.email_contato IS NULL OR co.email_contato = '' THEN 1 ELSE 0 END as missing_email,
               CASE WHEN co.telefone IS NULL OR co.telefone = '' THEN 1 ELSE 0 END as missing_phone,
               CASE WHEN en.cep IS NULL OR en.cep = '' THEN 1 ELSE 0 END as missing_cep
        FROM clientes cl
        LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
        LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        WHERE missing_email = 1 OR missing_phone = 1 OR missing_cep = 1
        ORDER BY cl.id DESC;
    """
    try:
        df = pd.read_sql_query(query, database_config.engine)
        return df
    except Exception as e:
        raise DatabaseError(f"Erro ao buscar clientes incompletos: {e}") from e

def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def get_customer_locations() -> pd.DataFrame:
    """
    Busca as localizações (latitude e longitude) de todos os clientes.
    Retorna um DataFrame com 'id', 'latitude' e 'longitude'.
    """
    query = """
        SELECT cl.id, en.latitude, en.longitude, cl.nome_completo, en.estado, en.cidade
        FROM clientes cl
        JOIN enderecos en ON cl.id = en.cliente_id
        WHERE en.latitude IS NOT NULL AND en.longitude IS NOT NULL;
    """
    try:
        df = pd.read_sql_query(query, database_config.engine)
        return df
    except Exception as e:
         raise DatabaseError(f"Erro ao buscar localizações de clientes: {e}") from e

def get_all_states() -> list:
    """Retorna uma lista de todos os estados (UF) únicos presentes na base de dados."""
    query = "SELECT DISTINCT estado FROM enderecos WHERE estado IS NOT NULL AND estado != '' ORDER BY estado"
    try:
        df = pd.read_sql_query(query, database_config.engine)
        return df['estado'].tolist()
    except Exception as e:
        logging.error(f"Erro ao buscar estados: {e}")
        return []

# --- Chat Bot Persistence ---



def save_chat_message(phone_number, role, content, external_id=None):
    """Salva uma mensagem no histórico do chat (Postgres) via SQL direto."""
    try:
        from sqlalchemy import text as sa_text
        with database_config.engine.connect() as conn:
            conn.execute(
                sa_text("""
                    INSERT INTO chat_history (phone_number, role, content, timestamp, is_read, external_id)
                    VALUES (:phone, :role, :content, NOW(), 0, :eid)
                """),
                {"phone": phone_number, "role": role, "content": content, "eid": external_id}
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao salvar mensagem de chat: {e}")

def check_message_exists(external_id):
    """Verifica se uma mensagem com este ID externo já foi processada."""
    if not external_id:
        return False
    try:
        from sqlalchemy import text as sa_text
        with database_config.engine.connect() as conn:
            result = conn.execute(
                sa_text("SELECT id FROM chat_history WHERE external_id = :eid LIMIT 1"),
                {"eid": external_id}
            ).fetchone()
            return result is not None
    except Exception as e:
        logging.error(f"Erro ao verificar existência de mensagem: {e}")
        return False

def get_chat_history(phone_number, limit=20):
    """Recupera o histórico recente de conversas com um número (Postgres)."""
    try:
        with get_session() as session:
            # SQLModel select
            statement = select(ChatHistory).where(ChatHistory.phone_number == phone_number).order_by(ChatHistory.timestamp.desc()).limit(limit)
            results = session.exec(statement).all()
            
            # Retorna na ordem cronológica (mais antigo primeiro) para o LLM entender
            history = []
            for r in reversed(results):
                history.append({
                    "role": r.role,
                    "parts": [r.content]
                })
            return history
    except Exception as e:
        logging.error(f"Erro ao recuperar histórico de chat: {e}")
        return []

def get_recent_chats_summary(limit=50):
    """Retorna um resumo das últimas mensagens trocadas para o Dashboard (Postgres)."""
    try:
        # Using pandas with the engine directly for summary query
        query = '''
            SELECT phone_number, role, content, timestamp 
            FROM chat_history 
            ORDER BY timestamp DESC
            LIMIT %s
        '''
        df = pd.read_sql_query(query, database_config.engine, params=(limit,))
        return df
    except Exception as e:
        logging.error(f"Erro ao buscar resumo de chats: {e}")
        return pd.DataFrame()
