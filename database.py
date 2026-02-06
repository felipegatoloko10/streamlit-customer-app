import sqlite3
import pandas as pd
import streamlit as st
import logging
import validators
import services
import backup_manager
import datetime

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


@st.cache_resource
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados, e garante que o esquema da tabela está atualizado."""
    conn = sqlite3.connect('customers.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns and 'tipo_documento' not in columns:
        logging.warning("Tabela antiga 'customers' detectada. Por segurança, os dados não foram apagados. Migre-os para a nova estrutura 'clientes' manualmente.")


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            tipo_documento TEXT NOT NULL,
            cpf TEXT UNIQUE,
            cnpj TEXT UNIQUE,
            data_nascimento DATE,
            data_cadastro DATE DEFAULT (date('now')),
            observacao TEXT,
            CHECK (
                (tipo_documento = 'CPF' AND cpf IS NOT NULL) OR
                (tipo_documento = 'CNPJ' AND cnpj IS NOT NULL)
            )
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            nome_contato TEXT,
            telefone TEXT,
            email_contato TEXT,
            cargo_contato TEXT,
            tipo_contato TEXT, -- e.g., 'Principal', 'Secundário', 'Financeiro'
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enderecos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            cep TEXT,
            logradouro TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            latitude REAL,
            longitude REAL,
            tipo_endereco TEXT, -- e.g., 'Principal', 'Entrega', 'Cobrança'
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            entidade TEXT, -- 'cliente', 'contato', 'endereco'
            entidade_id INTEGER,
            acao TEXT, -- 'INSERT', 'UPDATE', 'DELETE'
            dados_anteriores TEXT, -- JSON
            dados_novos TEXT, -- JSON
            usuario TEXT DEFAULT 'Sistema'
        )
    ''')
    conn.commit()
    logging.info("Conexão com o banco de dados estabelecida e esquema garantido.")
    return conn

def log_action(cursor, entidade, entidade_id, acao, antes=None, depois=None):
    """Registra uma ação na tabela de auditoria."""
    import json
    sql = "INSERT INTO audit_logs (entidade, entidade_id, acao, dados_anteriores, dados_novos) VALUES (?, ?, ?, ?, ?)"
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

def insert_customer(data: dict):
    """Insere um novo cliente e seus contatos/endereços após validação e sanitização."""
    # Higieniza os dados antes de qualquer operação
    data = _sanitize_data(data)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # 1. Preparar e inserir dados na tabela clientes
        cliente_data = {
            'nome_completo': data.get('nome_completo'),
            'tipo_documento': data.get('tipo_documento'),
            'cpf': validators.unformat_cpf(data.get('cpf')) if data.get('cpf') else None,
            'cnpj': validators.unformat_cnpj(data.get('cnpj')) if data.get('cnpj') else None,
            'data_nascimento': data.get('data_nascimento'),
            'observacao': data.get('observacao'),
            # data_cadastro is handled by DEFAULT (date('now'))
        }
        # Filter out None values to use DEFAULT where applicable
        cliente_data_filtered = {k: v for k, v in cliente_data.items() if v is not None}
        
        # Validate primary client data
        _validate_cliente_data(cliente_data)

        clientes_cols = ', '.join(cliente_data_filtered.keys())
        clientes_placeholders = ', '.join(['?'] * len(cliente_data_filtered))
        sql_clientes = f"INSERT INTO clientes ({clientes_cols}) VALUES ({clientes_placeholders})"
        cursor.execute(sql_clientes, list(cliente_data_filtered.values()))
        cliente_id = cursor.lastrowid
        
        # Registrar Log de Auditoria
        log_action(cursor, 'cliente', cliente_id, 'INSERT', depois=cliente_data_filtered)
        
        logging.info(f"Cliente '{cliente_data.get('nome_completo')}' inserido com sucesso com ID: {cliente_id}.")

        # 2. Preparar e inserir dados na tabela contatos (até 2 contatos, e-mail e cargo)
        contacts_to_insert = []
        if data.get('telefone1') or data.get('contato1') or data.get('email') or data.get('cargo'):
            contacts_to_insert.append({
                'cliente_id': cliente_id,
                'nome_contato': data.get('contato1'),
                'telefone': validators.unformat_whatsapp(data.get('telefone1')) if data.get('telefone1') else None,
                'email_contato': data.get('email'),
                'cargo_contato': data.get('cargo'),
                'tipo_contato': 'Principal'
            })
        if data.get('telefone2') or data.get('contato2'):
            contacts_to_insert.append({
                'cliente_id': cliente_id,
                'nome_contato': data.get('contato2'),
                'telefone': validators.unformat_whatsapp(data.get('telefone2')) if data.get('telefone2') else None,
                'email_contato': None, # Assuming email/cargo from original 'customers' belong to contact1
                'cargo_contato': None,
                'tipo_contato': 'Secundário'
            })

        for contact in contacts_to_insert:
            contact_data_filtered = {k: v for k, v in contact.items() if v is not None}
            if contact_data_filtered: # Only insert if there's actual data
                contatos_cols = ', '.join(contact_data_filtered.keys())
                contatos_placeholders = ', '.join(['?'] * len(contact_data_filtered))
                sql_contatos = f"INSERT INTO contatos ({contatos_cols}) VALUES ({contatos_placeholders})"
                cursor.execute(sql_contatos, list(contact_data_filtered.values()))
                logging.info(f"Contato para cliente {cliente_id} inserido.")

        # 3. Preparar e inserir dados na tabela enderecos
        if any(data.get(field) for field in ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado']):
            endereco_data = {
                'cliente_id': cliente_id,
                'cep': data.get('cep'),
                'logradouro': data.get('endereco'),
                'numero': data.get('numero'),
                'complemento': data.get('complemento'),
                'bairro': data.get('bairro'),
                'cidade': data.get('cidade'),
                'estado': data.get('estado'),
                'latitude': data.get('latitude'), # Added
                'longitude': data.get('longitude'), # Added
                'tipo_endereco': 'Principal' # Defaulting for now
            }
            endereco_data_filtered = {k: v for k, v in endereco_data.items() if v is not None}
            if endereco_data_filtered:
                enderecos_cols = ', '.join(endereco_data_filtered.keys())
                enderecos_placeholders = ', '.join(['?'] * len(endereco_data_filtered))
                sql_enderecos = f"INSERT INTO enderecos ({enderecos_cols}) VALUES ({enderecos_placeholders})"
                cursor.execute(sql_enderecos, list(endereco_data_filtered.values()))
                logging.info(f"Endereço para cliente {cliente_id} inserido.")

        conn.commit()

        # Try to send email and backup, but don't roll back if they fail
        try:
            services.send_new_customer_email(data, cliente_id)
        except Exception as e:
            logging.error(f"Falha ao enviar e-mail de notificação: {e}")
        
        try:
            backup_manager.increment_and_check_backup()
        except Exception as e:
            logging.error(f"Erro ao tentar backup automático: {e}")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise DuplicateEntryError("O CPF ou CNPJ informado já existe.") from e
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao salvar o novo cliente: {e}") from e
    except validators.ValidationError as e:
        conn.rollback()
        raise DatabaseError(f"Erro de validação ao salvar o cliente: {e}") from e

def update_customer(customer_id: int, data: dict):
    """Atualiza um cliente existente e seus contatos/endereços após validação e sanitização."""
    # Higieniza os dados recebidos para atualização
    data = _sanitize_data(data)
    
    conn = get_db_connection()
    try:
        # Obter dados atuais para o log de auditoria
        antes = get_customer_by_id(customer_id)
        
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # 1. Atualizar dados na tabela clientes
        cliente_update_payload = {}
        for col in ['nome_completo', 'tipo_documento', 'data_nascimento', 'observacao']:
            if data.get(col) is not None:
                cliente_update_payload[col] = data[col]
        
        # Handle CPF/CNPJ update specifically
        if data.get('cpf') is not None:
            cliente_update_payload['cpf'] = validators.unformat_cpf(data['cpf'])
        if data.get('cnpj') is not None:
            cliente_update_payload['cnpj'] = validators.unformat_cnpj(data['cnpj'])

        if cliente_update_payload:
            clientes_columns_to_update = ', '.join([f'{key} = ?' for key in cliente_update_payload.keys()])
            sql_clientes_update = f"UPDATE clientes SET {clientes_columns_to_update} WHERE id = ?"
            cursor.execute(sql_clientes_update, list(cliente_update_payload.values()) + [customer_id])
            logging.info(f"Cliente com ID {customer_id} atualizado na tabela clientes.")

        # Registrar Log de Auditoria
        log_action(cursor, 'cliente', customer_id, 'UPDATE', antes=antes, depois=data)

        # 2. Atualizar/Inserir dados na tabela contatos (complexidade simplificada para esta fase)
        # For simplicity in this refactoring step, we will assume a primary contact based on data.
        # A more robust solution for multiple contacts would involve dedicated UI and explicit contact IDs.
        
        # Contact 1 (assuming it's the 'Principal')
        contact1_payload = {}
        if data.get('contato1') is not None:
            contact1_payload['nome_contato'] = data['contato1']
        if data.get('telefone1') is not None:
            contact1_payload['telefone'] = validators.unformat_whatsapp(data['telefone1'])
        if data.get('email') is not None: # Original email field
            contact1_payload['email_contato'] = data['email']
        if data.get('cargo') is not None: # Original cargo field
            contact1_payload['cargo_contato'] = data['cargo']

        if contact1_payload:
            # Try to update an existing 'Principal' contact
            cursor.execute("SELECT id FROM contatos WHERE cliente_id = ? AND tipo_contato = 'Principal'", (customer_id,))
            existing_contact1_id = cursor.fetchone()
            
            if existing_contact1_id:
                contact1_columns_to_update = ', '.join([f'{key} = ?' for key in contact1_payload.keys()])
                sql_update_contact1 = f"UPDATE contatos SET {contact1_columns_to_update} WHERE id = ?"
                cursor.execute(sql_update_contact1, list(contact1_payload.values()) + [existing_contact1_id[0]])
                logging.info(f"Contato Principal para cliente {customer_id} atualizado.")
            else:
                # Insert new 'Principal' contact
                contact1_payload['cliente_id'] = customer_id
                contact1_payload['tipo_contato'] = 'Principal'
                contatos_cols = ', '.join(contact1_payload.keys())
                contatos_placeholders = ', '.join(['?'] * len(contact1_payload))
                sql_insert_contact1 = f"INSERT INTO contatos ({contatos_cols}) VALUES ({contatos_placeholders})"
                cursor.execute(sql_insert_contact1, list(contact1_payload.values()))
                logging.info(f"Novo Contato Principal para cliente {customer_id} inserido.")

        # Contact 2 (assuming it's the 'Secundário')
        contact2_payload = {}
        if data.get('contato2') is not None:
            contact2_payload['nome_contato'] = data['contato2']
        if data.get('telefone2') is not None:
            contact2_payload['telefone'] = validators.unformat_whatsapp(data['telefone2'])

        if contact2_payload:
            cursor.execute("SELECT id FROM contatos WHERE cliente_id = ? AND tipo_contato = 'Secundário'", (customer_id,))
            existing_contact2_id = cursor.fetchone()

            if existing_contact2_id:
                contact2_columns_to_update = ', '.join([f'{key} = ?' for key in contact2_payload.keys()])
                sql_update_contact2 = f"UPDATE contatos SET {contact2_columns_to_update} WHERE id = ?"
                cursor.execute(sql_update_contact2, list(contact2_payload.values()) + [existing_contact2_id[0]])
                logging.info(f"Contato Secundário para cliente {customer_id} atualizado.")
            else:
                contact2_payload['cliente_id'] = customer_id
                contact2_payload['tipo_contato'] = 'Secundário'
                contatos_cols = ', '.join(contact2_payload.keys())
                contatos_placeholders = ', '.join(['?'] * len(contact2_payload))
                sql_insert_contact2 = f"INSERT INTO contatos ({contatos_cols}) VALUES ({contatos_placeholders})"
                cursor.execute(sql_insert_contact2, list(contact2_payload.values()))
                logging.info(f"Novo Contato Secundário para cliente {customer_id} inserido.")


        # 3. Atualizar/Inserir dados na tabela enderecos (simplificado)
        # Similar to contacts, assume a primary address based on data.
        endereco_payload = {}
        if data.get('cep') is not None:
            endereco_payload['cep'] = data['cep']
        if data.get('endereco') is not None:
            endereco_payload['logradouro'] = data['endereco']
        if data.get('numero') is not None:
            endereco_payload['numero'] = data['numero']
        if data.get('complemento') is not None:
            endereco_payload['complemento'] = data['complemento']
        if data.get('bairro') is not None:
            endereco_payload['bairro'] = data['bairro']
        if data.get('cidade') is not None:
            endereco_payload['cidade'] = data['cidade']
        if data.get('estado') is not None:
            endereco_payload['estado'] = data['estado']
        if data.get('latitude') is not None: # Added
            endereco_payload['latitude'] = data['latitude'] # Added
        if data.get('longitude') is not None: # Added
            endereco_payload['longitude'] = data['longitude'] # Added

        if endereco_payload:
            cursor.execute("SELECT id FROM enderecos WHERE cliente_id = ? AND tipo_endereco = 'Principal'", (customer_id,))
            existing_address_id = cursor.fetchone()

            if existing_address_id:
                endereco_payload['tipo_endereco'] = 'Principal' # Ensure type is set if updating
                enderecos_columns_to_update = ', '.join([f'{key} = ?' for key in endereco_payload.keys()])
                sql_update_address = f"UPDATE enderecos SET {enderecos_columns_to_update} WHERE id = ?"
                cursor.execute(sql_update_address, list(endereco_payload.values()) + [existing_address_id[0]])
                logging.info(f"Endereço Principal para cliente {customer_id} atualizado.")
            else:
                endereco_payload['cliente_id'] = customer_id
                endereco_payload['tipo_endereco'] = 'Principal'
                enderecos_cols = ', '.join(endereco_payload.keys())
                enderecos_placeholders = ', '.join(['?'] * len(endereco_payload))
                sql_insert_address = f"INSERT INTO enderecos ({enderecos_cols}) VALUES ({enderecos_placeholders})"
                cursor.execute(sql_insert_address, list(endereco_payload.values()))
                logging.info(f"Novo Endereço Principal para cliente {customer_id} inserido.")

        conn.commit()

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise DuplicateEntryError("O CPF ou CNPJ informado já existe ou outro erro de integridade.") from e
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Erro de banco de dados ao atualizar o cliente: {e}") from e
    except validators.ValidationError as e:
        conn.rollback()
        raise DatabaseError(f"Erro de validação ao atualizar o cliente: {e}") from e

def delete_customer(customer_id: int):
    """Exclui um cliente e seus contatos/endereços associados, aproveitando ON DELETE CASCADE."""
    conn = get_db_connection()
    try:
        # Obter dados antes para o log
        antes = get_customer_by_id(customer_id)
        
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        # Registrar Log de Auditoria antes de deletar
        log_action(cursor, 'cliente', customer_id, 'DELETE', antes=antes)
        
        cursor.execute("DELETE FROM clientes WHERE id = ?", (customer_id,))
        if cursor.rowcount == 0:
            raise DatabaseError(f"Cliente com ID {customer_id} não encontrado para exclusão.")
        conn.commit()
        logging.info(f"Cliente com ID {customer_id} e dados relacionados excluídos com sucesso.")
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao excluir o cliente: {e}") from e

def get_customer_by_id(customer_id: int) -> dict:
    """Busca um único cliente pelo seu ID e retorna como um dicionário."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row # Return rows as dict-like objects
    
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
        WHERE cl.id = ?
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (customer_id,))
        customer_row = cursor.fetchone()
        
        if customer_row:
            customer_dict = dict(customer_row)
            
            # Format dates
            if customer_dict.get('data_nascimento'):
                try:
                    customer_dict['data_nascimento'] = datetime.datetime.strptime(customer_dict['data_nascimento'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    customer_dict['data_nascimento'] = None
            if customer_dict.get('data_cadastro'):
                try:
                    customer_dict['data_cadastro'] = datetime.datetime.strptime(customer_dict['data_cadastro'], '%Y-%m-%d').date()
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

    except sqlite3.Error as e:
        raise DatabaseError(f"Erro ao buscar cliente por ID: {e}") from e

def _build_where_clause(search_query: str = None, state_filter: str = None, start_date=None, end_date=None,
                        main_table_alias='cl', address_table_alias='en'):
    params = []
    conditions = []
    if search_query:
        conditions.append(f"({main_table_alias}.nome_completo LIKE ? OR {main_table_alias}.cpf LIKE ? OR {main_table_alias}.cnpj LIKE ?)")
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if state_filter and state_filter != "Todos":
        conditions.append(f"{address_table_alias}.estado = ?")
        params.append(state_filter)
    if start_date and end_date:
        conditions.append(f"{main_table_alias}.data_cadastro BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def count_total_records(search_query: str = None, state_filter: str = None) -> int:
    conn = get_db_connection()
    
    # Pass aliases to _build_where_clause
    where_clause, params = _build_where_clause(search_query, state_filter, main_table_alias='cl', address_table_alias='en')
    
    query = "SELECT COUNT(DISTINCT cl.id) FROM clientes cl"
    if state_filter and state_filter != "Todos":
        query += " LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'"
    
    query += where_clause
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        raise DatabaseError(f"Não foi possível contar os registros: {e}") from e

def fetch_data(search_query: str = None, state_filter: str = None, page: int = 1, page_size: int = 10):
    conn = get_db_connection()
    
    select_columns = [
        "cl.id", "cl.nome_completo", "cl.tipo_documento", "cl.cpf", "cl.cnpj",
        "cl.data_nascimento", "cl.observacao", "cl.data_cadastro",
        "co.nome_contato AS contato1", "co.telefone AS telefone1", "co.email_contato AS email", "co.cargo_contato AS cargo",
        "en.cep", "en.logradouro AS endereco", "en.numero", "en.complemento", "en.bairro", "en.cidade", "en.estado"
    ]
    
    where_clause_parts = []
    params = []

    # Original _build_where_clause now needs to be adapted for 'clientes' table
    if search_query:
        where_clause_parts.append("(cl.nome_completo LIKE ? OR cl.cpf LIKE ? OR cl.cnpj LIKE ?)")
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if state_filter and state_filter != "Todos":
        where_clause_parts.append("en.estado = ?") # Filter by address state
        params.append(state_filter)
    
    # We will adjust filtering by date for cl.data_cadastro in the main query if needed in a later ticket
    # For now, keeping the query structure aligned with the original fetch_data which uses data_cadastro from customers
    # This will be refined as other reporting functions are refactored.

    where_sql = " WHERE " + " AND ".join(where_clause_parts) if where_clause_parts else ""

    offset = (page - 1) * page_size
    
    # Se o filtro de estado estiver ativo, usamos JOIN (INNER) para filtrar. 
    # Caso contrário, usamos LEFT JOIN para não "esconder" clientes sem endereço principal.
    join_type = "JOIN" if (state_filter and state_filter != "Todos") else "LEFT JOIN"

    query = f"""
        SELECT {', '.join(select_columns)}
        FROM clientes cl
        LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
        {join_type} enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        {where_sql}
        ORDER BY cl.id DESC
        LIMIT ? OFFSET ?
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=params + [page_size, offset])
        
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
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar dados: {e}") from e

def get_new_customers_timeseries(start_date, end_date, period='M'):
    """
    Busca dados para o gráfico de série temporal de novos clientes.
    Agrupa por Dia ('D'), Semana ('W'), ou Mês ('M').
    """
    conn = get_db_connection()
    
    if period == 'D':
        date_format = '%Y-%m-%d'
    elif period == 'W':
        # ISO Week
        date_format = '%Y-%W'
    else: # Mês
        date_format = '%Y-%m'
        
    query = f"""
        SELECT 
            strftime('{date_format}', data_cadastro) as time_period,
            COUNT(id) as count
        FROM clientes
        WHERE data_cadastro BETWEEN ? AND ?
        GROUP BY time_period
        ORDER BY time_period;
    """
    try:
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar série temporal de clientes: {e}") from e

def get_customers_by_state_for_map(start_date, end_date):
    """
    Busca a contagem de clientes por estado para o mapa coroplético.
    """
    conn = get_db_connection()
    query = """
        SELECT en.estado, COUNT(cl.id) as count 
        FROM clientes cl
        JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
        WHERE en.estado IS NOT NULL AND en.estado != '' AND cl.data_cadastro BETWEEN ? AND ?
        GROUP BY en.estado;
    """
    try:
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar contagem de clientes por estado: {e}") from e

def get_top_cities_by_state(start_date, end_date, state=None):
    """
    Busca o top 10 de cidades, opcionalmente filtrando por um estado.
    """
    conn = get_db_connection()
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
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar top cidades: {e}") from e

def get_data_health_summary():
    """
    Calcula a porcentagem de completude para campos chave.
    """
    conn = get_db_connection()
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
        df = pd.read_sql_query(query, conn)
        if df.empty or df['total_customers'][0] == 0:
            return {'email_completeness': 0, 'phone_completeness': 0, 'cep_completeness': 0}
        
        summary = {
            'email_completeness': (df['with_email'][0] / df['total_customers'][0]) * 100,
            'phone_completeness': (df['with_phone'][0] / df['total_customers'][0]) * 100,
            'cep_completeness': (df['with_cep'][0] / df['total_customers'][0]) * 100
        }
        return summary
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao calcular saúde dos dados: {e}") from e

def get_incomplete_customers():
    """
    Busca clientes com informações chave faltando.
    """
    conn = get_db_connection()
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
        df = pd.read_sql_query(query, conn)
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar clientes incompletos: {e}") from e

def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def get_customer_locations() -> pd.DataFrame:
    """
    Busca as localizações (latitude e longitude) de todos os clientes.
    Retorna um DataFrame com 'id', 'latitude' e 'longitude'.
    """
    conn = get_db_connection()
    query = """
        SELECT cl.id, en.latitude, en.longitude, cl.nome_completo, en.estado, en.cidade
        FROM clientes cl
        JOIN enderecos en ON cl.id = en.cliente_id
        WHERE en.latitude IS NOT NULL AND en.longitude IS NOT NULL;
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar localizações de clientes: {e}") from e
