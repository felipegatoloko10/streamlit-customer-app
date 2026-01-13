import sqlite3
import pandas as pd
import streamlit as st
import logging

# ... (código anterior mantido: logging, exceções, constantes)
# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass

class DuplicateCPFError(DatabaseError):
    """Exceção para CPF duplicado."""
    pass

# --- Constantes de Colunas ---
DB_COLUMNS = [
    'nome_completo', 'cpf', 'whatsapp', 'email', 'data_nascimento', 
    'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
    'data_cadastro' 
]
ALL_COLUMNS_WITH_ID = ['id'] + DB_COLUMNS


@st.cache_resource
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados, usando o cache do Streamlit."""
    try:
        conn = sqlite3.connect('customers.db', check_same_thread=False)
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                nome_completo TEXT,
                cpf TEXT UNIQUE,
                whatsapp TEXT,
                email TEXT,
                data_nascimento DATE,
                cep TEXT,
                endereco TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                data_cadastro DATE DEFAULT (date('now'))
            )
        ''')
        conn.commit()
        logging.info("Conexão com o banco de dados estabelecida e tabela garantida.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Erro ao inicializar o banco de dados: {e}")
        raise DatabaseError(f"Não foi possível conectar ou criar o banco de dados: {e}") from e

def _build_where_clause(search_query: str = None, state_filter: str = None):
    """Constrói a cláusula WHERE e os parâmetros para a consulta SQL."""
    params = []
    conditions = []
    if search_query:
        conditions.append("(nome_completo LIKE ? OR cpf LIKE ?)")
        params.extend([f'%{search_query}%', f'%{search_query}%'])
    if state_filter and state_filter != "Todos":
        conditions.append("estado = ?")
        params.append(state_filter)
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def count_total_records(search_query: str = None, state_filter: str = None) -> int:
    """Conta o número total de registros que correspondem aos filtros."""
    conn = get_db_connection()
    where_clause, params = _build_where_clause(search_query, state_filter)
    query = f"SELECT COUNT(id) FROM customers{where_clause}"
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        logging.error(f"Erro ao contar registros: {e}")
        raise DatabaseError(f"Não foi possível contar os registros: {e}") from e

def fetch_data(search_query: str = None, state_filter: str = None, page: int = 1, page_size: int = 10):
    """Busca dados de clientes com paginação."""
    conn = get_db_connection()
    
    where_clause, params = _build_where_clause(search_query, state_filter)
    offset = (page - 1) * page_size
    
    query = f"SELECT {', '.join(ALL_COLUMNS_WITH_ID)} FROM customers{where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    
    try:
        df = pd.read_sql_query(query, conn, params=params + [page_size, offset])
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.date
        df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce').dt.date
        return df
    except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
        logging.error(f"Erro ao buscar dados com paginação: {e}")
        return pd.DataFrame(columns=ALL_COLUMNS_WITH_ID)

# ... (resto do código mantido: insert_customer, commit_changes, etc.)
def insert_customer(data: dict):
    """
    Insere um novo cliente.
    Lança DuplicateCPFError em caso de CPF duplicado e DatabaseError para outras falhas.
    """
    if 'data_cadastro' in data:
        del data['data_cadastro'] 
    if not any(data.values()):
        raise ValueError("O formulário não pode estar vazio.")
        
    conn = get_db_connection()
    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO customers ({columns}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.execute(sql, list(data.values()))
        conn.commit()
        logging.info(f"Cliente '{data.get('nome_completo')}' inserido com sucesso.")
        
    except sqlite3.IntegrityError as e:
        logging.warning(f"Tentativa de inserir CPF duplicado: {data.get('cpf')}")
        raise DuplicateCPFError(f"O CPF '{data.get('cpf')}' já existe no banco de dados.") from e
    except sqlite3.Error as e:
        logging.error(f"Erro ao inserir cliente: {e}")
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao salvar: {e}") from e

def _get_deletes(edited_df: pd.DataFrame) -> list:
    """Extrai IDs dos registros marcados para deleção."""
    if 'Deletar' not in edited_df.columns:
        return []
    delete_mask = edited_df['Deletar'] == True
    return edited_df.loc[delete_mask, 'id'].tolist()

def _get_updates(edited_df: pd.DataFrame, original_df: pd.DataFrame) -> list:
    """Extrai dados dos registros que foram atualizados."""
    updates = []
    # Alinhar os dataframes pelo índice
    original_df.set_index('id', inplace=True)
    edited_df.set_index('id', inplace=True)
    
    # Iterar sobre o DF editado para encontrar mudanças
    for idx, row in edited_df.iterrows():
        if idx in original_df.index:
            original_row = original_df.loc[idx]
            # Comparar como strings para evitar problemas de tipo
            if not row.astype(str).equals(original_row.astype(str)):
                row['data_nascimento'] = row['data_nascimento'].strftime('%Y-%m-%d') if pd.notna(row['data_nascimento']) else None
                # O campo data_cadastro não deve ser atualizável
                update_data = tuple(row[col] for col in DB_COLUMNS if col != 'data_cadastro') + (idx,)
                updates.append(update_data)
    return updates

def commit_changes(edited_df: pd.DataFrame, original_df: pd.DataFrame):
    """
    Comita alterações (updates, deletes) do data_editor.
    Lança DatabaseError em caso de falha.
    """
    deletes = _get_deletes(edited_df)
    # Remove as linhas marcadas para deleção do df editado para não processá-las como update
    if 'Deletar' in edited_df.columns:
        edited_df = edited_df[edited_df['Deletar'] != True]
        
    updates = _get_updates(edited_df, original_df)
    
    if not updates and not deletes:
        logging.info("Nenhuma alteração para comitar.")
        return {"updated": 0, "deleted": 0}

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if updates:
            update_columns = [col for col in DB_COLUMNS if col != 'data_cadastro']
            update_query = f"UPDATE customers SET {', '.join([f'{col}=?' for col in update_columns])} WHERE id=?"
            cursor.executemany(update_query, updates)
            logging.info(f"{len(updates)} registro(s) atualizado(s).")
        if deletes:
            cursor.executemany("DELETE FROM customers WHERE id=?", [(d,) for d in deletes])
            logging.info(f"{len(deletes)} registro(s) deletado(s).")
            
        conn.commit()
        return {"updated": len(updates), "deleted": len(deletes)}
        
    except sqlite3.Error as e:
        logging.error(f"Erro ao comitar alterações: {e}")
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro no banco de dados ao salvar as alterações: {e}") from e

# --- Funções Auxiliares ---
def df_to_csv(df: pd.DataFrame) -> bytes:
    """Converte um DataFrame para CSV para download."""
    return df.to_csv(index=False).encode('utf-8')