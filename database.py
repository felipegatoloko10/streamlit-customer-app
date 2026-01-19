import sqlite3
import pandas as pd
import streamlit as st
import logging
import validators
import services

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass

class DuplicateEntryError(DatabaseError):
    """Exceção para entradas duplicadas (CPF/CNPJ)."""
    pass

# --- Constantes de Colunas ---
DB_COLUMNS = [
    'nome_completo', 'tipo_documento', 'cpf', 'cnpj', 
    'contato1', 'telefone1', 'contato2', 'telefone2', 'cargo',
    'email', 'data_nascimento', 
    'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
    'observacao', 'data_cadastro' 
]
ALL_COLUMNS_WITH_ID = ['id'] + DB_COLUMNS


@st.cache_resource
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados, e garante que o esquema da tabela está atualizado."""
    conn = sqlite3.connect('customers.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Verifica se a tabela já tem o novo esquema
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'tipo_documento' not in columns:
        cursor.execute("DROP TABLE IF EXISTS customers")
        logging.info("Tabela 'customers' antiga encontrada e descartada.")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            nome_completo TEXT NOT NULL,
            tipo_documento TEXT NOT NULL,
            cpf TEXT UNIQUE,
            cnpj TEXT UNIQUE,
            contato1 TEXT,
            telefone1 TEXT,
            contato2 TEXT,
            telefone2 TEXT,
            cargo TEXT,
            email TEXT,
            data_nascimento DATE,
            cep TEXT,
            endereco TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            observacao TEXT,
            data_cadastro DATE DEFAULT (date('now')),
            CHECK (
                (tipo_documento = 'CPF' AND cpf IS NOT NULL) OR 
                (tipo_documento = 'CNPJ' AND cnpj IS NOT NULL)
            )
        )
    ''')
    conn.commit()
    logging.info("Conexão com o banco de dados estabelecida e tabela garantida.")
    return conn

def _validate_row(row: pd.Series):
    """Valida os dados de uma linha antes de inserir/atualizar."""
    doc_type = row.get('tipo_documento')
    if not row.get('nome_completo') or not doc_type:
        raise validators.ValidationError("Os campos 'Nome Completo' e 'Tipo de Documento' são obrigatórios.")

    if doc_type == 'CPF':
        if not row.get('cpf') or len(row.get('cpf')) == 0:
            raise validators.ValidationError("O campo 'CPF' é obrigatório.")
        validators.is_valid_cpf(row['cpf'])
    elif doc_type == 'CNPJ':
        if not row.get('cnpj') or len(row.get('cnpj')) == 0:
            raise validators.ValidationError("O campo 'CNPJ' é obrigatório.")
        validators.is_valid_cnpj(row['cnpj'])
    
    if row.get('telefone1') and len(row.get('telefone1')) > 0:
        validators.is_valid_whatsapp(row['telefone1'])
    if row.get('telefone2') and len(row.get('telefone2')) > 0:
        validators.is_valid_whatsapp(row['telefone2'])
    if row.get('email') and len(row.get('email')) > 0:
        validators.is_valid_email(row['email'])

def insert_customer(data: dict):
    """Insere um novo cliente após validação."""
    data_to_insert = {k: v for k, v in data.items() if v is not None and v != ''}
    
    _validate_row(pd.Series(data_to_insert))
    
    conn = get_db_connection()
    try:
        columns = ', '.join(data_to_insert.keys())
        placeholders = ', '.join(['?'] * len(data_to_insert))
        sql = f"INSERT INTO customers ({columns}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.execute(sql, list(data_to_insert.values()))
        new_customer_id = cursor.lastrowid  # Pega o ID do cliente recém-criado
        conn.commit()
        logging.info(f"Cliente '{data.get('nome_completo')}' inserido com sucesso com ID: {new_customer_id}.")

        # Tenta enviar o e-mail de notificação (sem quebrar a aplicação se falhar)
        try:
            services.send_new_customer_email(data, new_customer_id)
        except Exception as e:
            logging.error(f"Falha ao enviar e-mail de notificação para o cliente ID {new_customer_id}: {e}")
            # O st.warning será mostrado na tela pelo próprio service
        
    except sqlite3.IntegrityError as e:
        logging.warning(f"Tentativa de inserir CPF/CNPJ duplicado.")
        raise DuplicateEntryError(f"O CPF ou CNPJ informado já existe no banco de dados.") from e
    except sqlite3.Error as e:
        logging.error(f"Erro ao inserir cliente: {e}")
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao salvar: {e}") from e

def delete_customer(customer_id: int):
    """Deleta um cliente do banco de dados pelo ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        logging.info(f"Cliente com ID {customer_id} excluído com sucesso.")
        if cursor.rowcount == 0:
            raise DatabaseError(f"Cliente com ID {customer_id} não encontrado para exclusão.")
    except sqlite3.Error as e:
        logging.error(f"Erro ao excluir cliente com ID {customer_id}: {e}")
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao excluir o cliente: {e}") from e

def update_customer(customer_id: int, data: dict):
    """Atualiza os dados de um cliente existente após validação."""
    data_to_update = {k: v for k, v in data.items() if v is not None}

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Busca os dados originais para validação completa
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        original_customer_row = cursor.fetchone()
        if not original_customer_row:
            raise DatabaseError(f"Cliente com ID {customer_id} não encontrado para atualização.")
        
        original_customer_dict = dict(original_customer_row)
        
        # Cria uma visão mesclada dos dados para validação
        merged_data_for_validation = original_customer_dict.copy()
        merged_data_for_validation.update(data_to_update)

        # Remove a formatação dos campos relevantes antes da validação
        doc_type = merged_data_for_validation.get('tipo_documento')
        if doc_type == 'CPF' and 'cpf' in merged_data_for_validation:
            merged_data_for_validation['cpf'] = validators.unformat_cpf(merged_data_for_validation['cpf'])
        elif doc_type == 'CNPJ' and 'cnpj' in merged_data_for_validation:
            merged_data_for_validation['cnpj'] = validators.unformat_cnpj(merged_data_for_validation['cnpj'])

        if 'telefone1' in merged_data_for_validation:
            merged_data_for_validation['telefone1'] = validators.unformat_whatsapp(merged_data_for_validation['telefone1'])
        if 'telefone2' in merged_data_for_validation:
            merged_data_for_validation['telefone2'] = validators.unformat_whatsapp(merged_data_for_validation['telefone2'])

        # Realiza a validação com os dados mesclados e não formatados
        _validate_row(pd.Series(merged_data_for_validation))

        # Prepara os dados para o update (apenas o que foi alterado)
        update_payload = {}
        for key, value in data_to_update.items():
            # Remove a formatação para salvar no banco
            if key == 'cpf':
                update_payload[key] = validators.unformat_cpf(value)
            elif key == 'cnpj':
                update_payload[key] = validators.unformat_cnpj(value)
            elif key in ['telefone1', 'telefone2']:
                update_payload[key] = validators.unformat_whatsapp(value)
            else:
                update_payload[key] = value

        if not update_payload:
            logging.info(f"Nenhum dado para atualizar para o cliente ID {customer_id}.")
            return

        # Constrói e executa a query de atualização
        columns_to_update = ', '.join([f'{key} = ?' for key in update_payload.keys()])
        sql = f"UPDATE customers SET {columns_to_update} WHERE id = ?"
        
        values = list(update_payload.values()) + [customer_id]
        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"Cliente com ID {customer_id} atualizado com sucesso.")

    except (validators.ValidationError, sqlite3.IntegrityError) as e:
        conn.rollback()
        logging.error(f"Erro de validação ou integridade ao atualizar cliente ID {customer_id}: {e}")
        # A mensagem de erro específica de validação já é clara o suficiente
        raise DuplicateEntryError(str(e)) from e
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Erro de banco de dados ao atualizar cliente ID {customer_id}: {e}")
        raise DatabaseError(f"Ocorreu um erro de banco de dados ao salvar as alterações: {e}") from e


def _build_where_clause(search_query: str = None, state_filter: str = None, start_date=None, end_date=None):
    params = []
    conditions = []
    if search_query:
        conditions.append("(nome_completo LIKE ? OR cpf LIKE ? OR cnpj LIKE ?)")
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if state_filter and state_filter != "Todos":
        conditions.append("estado = ?")
        params.append(state_filter)
    
    if start_date and end_date:
        conditions.append("data_cadastro BETWEEN ? AND ?")
        params.extend([start_date, end_date])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def count_total_records(search_query: str = None, state_filter: str = None) -> int:
    conn = get_db_connection()
    # Note: count_total_records in the data grid does not use date filters, so we don't pass them here.
    where_clause, params = _build_where_clause(search_query, state_filter)
    query = f"SELECT COUNT(id) FROM customers{where_clause}"
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        raise DatabaseError(f"Não foi possível contar os registros: {e}") from e

def fetch_data(search_query: str = None, state_filter: str = None, page: int = 1, page_size: int = 10000):
    conn = get_db_connection()
    # Note: fetch_data for the main grid does not use date filters.
    where_clause, params = _build_where_clause(search_query, state_filter)
    offset = (page - 1) * page_size
    query = f"SELECT {', '.join(ALL_COLUMNS_WITH_ID)} FROM customers{where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    
    try:
        df = pd.read_sql_query(query, conn, params=params + [page_size, offset])
        # Converte para data, tratando erros
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.date
        df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce').dt.date
        
        # Formata colunas para exibição
        if 'cpf' in df.columns:
            df['cpf'] = df['cpf'].apply(validators.format_cpf)
        if 'cnpj' in df.columns:
            df['cnpj'] = df['cnpj'].apply(validators.format_cnpj)
        
        # Formata os números de telefone para exibição, mas mantém os dados originais para edição
        if 'telefone1' in df.columns:
            df['link_wpp_1'] = df['telefone1'].apply(validators.get_whatsapp_url)
            df['telefone1'] = df['telefone1'].apply(validators.format_whatsapp)
        if 'telefone2' in df.columns:
            df['link_wpp_2'] = df['telefone2'].apply(validators.get_whatsapp_url)
            df['telefone2'] = df['telefone2'].apply(validators.format_whatsapp)
            
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar dados: {e}") from e


def get_customer_by_id(customer_id: int) -> dict:
    """Busca um único cliente pelo seu ID e retorna como um dicionário."""
    conn = get_db_connection()
    # Garante que a conexão retorna um objeto que se comporta como dict
    conn.row_factory = sqlite3.Row
    
    query = f"SELECT {', '.join(ALL_COLUMNS_WITH_ID)} FROM customers WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (customer_id,))
        customer_row = cursor.fetchone()
        
        if customer_row:
            # Converte a linha do banco de dados (Row) em um dicionário
            customer_dict = dict(customer_row)
            
            # Formata as datas e outros campos, similar a `fetch_data`
            if customer_dict.get('data_nascimento'):
                try:
                    customer_dict['data_nascimento'] = pd.to_datetime(customer_dict['data_nascimento'], errors='coerce').date()
                except (ValueError, TypeError):
                    customer_dict['data_nascimento'] = None # Ou um valor padrão
            if customer_dict.get('data_cadastro'):
                try:
                    customer_dict['data_cadastro'] = pd.to_datetime(customer_dict['data_cadastro'], errors='coerce').date()
                except (ValueError, TypeError):
                    customer_dict['data_cadastro'] = None

            # Usa .get() para segurança, caso a coluna não exista no resultado
            if customer_dict.get('cpf'):
                customer_dict['cpf'] = validators.format_cpf(customer_dict.get('cpf'))
            if customer_dict.get('cnpj'):
                customer_dict['cnpj'] = validators.format_cnpj(customer_dict.get('cnpj'))
            if customer_dict.get('telefone1'):
                customer_dict['telefone1'] = validators.format_whatsapp(customer_dict.get('telefone1'))
            if customer_dict.get('telefone2'):
                customer_dict['telefone2'] = validators.format_whatsapp(customer_dict.get('telefone2'))

            return customer_dict
        else:
            return None # Retorna None se o cliente não for encontrado

    except sqlite3.Error as e:
        raise DatabaseError(f"Erro ao buscar cliente por ID: {e}") from e



def fetch_dashboard_data(start_date=None, end_date=None) -> pd.DataFrame:
    """Busca apenas as colunas necessárias para os gráficos e tabelas do dashboard."""
    conn = get_db_connection()
    columns_to_fetch = "nome_completo, email, cidade, data_cadastro, tipo_documento, estado"
    
    where_clause, params = _build_where_clause(start_date=start_date, end_date=end_date)
    
    query = f"SELECT {columns_to_fetch} FROM customers{where_clause} ORDER BY data_cadastro DESC"
    try:
        df = pd.read_sql_query(query, conn, params=params)
        # Converte o tipo de dado após a busca
        df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce').dt.date
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        raise DatabaseError(f"Erro ao buscar dados para o dashboard: {e}") from e


def _get_updates(edited_df: pd.DataFrame, original_df: pd.DataFrame) -> list:
    updates = []
    original_df_indexed = original_df.set_index('id')
    
    for _, edited_row in edited_df.iterrows():
        idx = edited_row['id']
        if idx in original_df_indexed.index:
            original_row = original_df_indexed.loc[idx]
            
            row_changed = False
            editable_cols = [col for col in DB_COLUMNS if col not in ['id', 'data_cadastro']]
            
            for col in editable_cols: 
                edited_value = edited_row.get(col)
                original_value = original_row.get(col)

                # Convert pandas NaT/NaN to None for consistent comparison
                if pd.isna(edited_value): edited_value = None
                if pd.isna(original_value): original_value = None
                
                # Special handling for dates
                if col in ['data_nascimento']:
                    edited_date = pd.to_datetime(edited_value).date() if edited_value else None
                    original_date = pd.to_datetime(original_value).date() if original_value else None
                    if edited_date != original_date:
                        row_changed = True
                        break
                    continue

                # Handle case where one is None and the other is an empty string
                if (edited_value is None and original_value == '') or \
                   (edited_value == '' and original_value is None):
                    continue

                # Direct comparison for other types
                if edited_value != original_value:
                    row_changed = True
                    break
            
            if row_changed:
                _validate_row(edited_row)
                
                update_values = []
                update_columns = [col for col in DB_COLUMNS if col != 'data_cadastro']
                for col in update_columns:
                    value = edited_row.get(col)
                    if col == 'data_nascimento' and pd.notna(value):
                        update_values.append(pd.to_datetime(value).strftime('%Y-%m-%d'))
                    elif value == '':
                        update_values.append(None)
                    else:
                        update_values.append(value)
                
                update_data = tuple(update_values) + (idx,)
                updates.append(update_data)
    return updates



def commit_changes(edited_df: pd.DataFrame, original_df: pd.DataFrame):
    # Lógica de exclusão removida
    
    try:
        updates = _get_updates(edited_df, original_df)
    except validators.ValidationError as e:
        raise DatabaseError(f"Erro de validação ao salvar: {e}") from e

    if not updates: 
        return {"updated": 0, "deleted": 0}

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if updates:
            update_columns = [col for col in DB_COLUMNS if col != 'data_cadastro']
            update_query = f"UPDATE customers SET {', '.join([f'{col}=?' for col in update_columns])} WHERE id=?"
            cursor.executemany(update_query, updates)
        # Lógica de exclusão removida
            
        conn.commit()
        return {"updated": len(updates), "deleted": 0}
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro no banco de dados: {e}") from e

def get_total_customers_count() -> int:
    conn = get_db_connection()
    query = "SELECT COUNT(id) FROM customers"
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        raise DatabaseError(f"Não foi possível contar o total de clientes: {e}") from e

def get_new_customers_in_period_count(start_date, end_date) -> int:
    """Conta novos clientes dentro de um período de datas específico."""
    conn = get_db_connection()
    where_clause, params = _build_where_clause(start_date=start_date, end_date=end_date)
    query = f"SELECT COUNT(id) FROM customers{where_clause}"
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        raise DatabaseError(f"Não foi possível contar novos clientes do período: {e}") from e

def get_customer_counts_by_state(start_date=None, end_date=None) -> pd.Series:
    conn = get_db_connection()
    
    # Adiciona a condição de agrupamento ao WHERE
    base_query = "SELECT estado, COUNT(id) as count FROM customers"
    group_by_clause = " GROUP BY estado ORDER BY count DESC"
    
    # Constrói a cláusula WHERE
    where_clause, params = _build_where_clause(start_date=start_date, end_date=end_date)

    # Adiciona condição de estado não nulo
    if where_clause:
        query = f"{base_query}{where_clause} AND estado IS NOT NULL AND estado != ''{group_by_clause}"
    else:
        query = f"{base_query} WHERE estado IS NOT NULL AND estado != ''{group_by_clause}"

    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df.set_index('estado')['count']
    except sqlite3.Error as e:
        raise DatabaseError(f"Não foi possível obter a contagem de clientes por estado: {e}") from e

def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')
