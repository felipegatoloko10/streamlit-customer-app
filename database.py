import sqlite3
import pandas as pd

# Nota: As funções st (streamlit) foram removidas deste arquivo para uma melhor separação de responsabilidades.
# As páginas da interface do usuário serão responsáveis por exibir mensagens.

# --- Constantes de Colunas ---
DB_COLUMNS = [
    'nome_completo', 'cpf', 'whatsapp', 'email', 'data_nascimento', 
    'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
    'data_cadastro' 
]
ALL_COLUMNS_WITH_ID = ['id'] + DB_COLUMNS

# --- Funções de Conexão e Criação ---
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect('customers.db')
    try:
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
                data_cadastro DATE DEFAULT CURRENT_DATE
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        # Em vez de st.error, podemos logar o erro ou simplesmente levantá-lo
        print(f"Erro ao inicializar o banco de dados: {e}")
        conn.close()
        raise
    return conn

# --- Funções de CRUD (Create, Read, Update, Delete) ---
def insert_customer(data):
    """
    Insere um novo cliente.
    Retorna (True, None) em sucesso, (False, "mensagem de erro") em falha.
    """
    if 'data_cadastro' in data:
        del data['data_cadastro'] 
    if not any(data.values()):
        return False, "O formulário está vazio."
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO customers ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"O CPF '{data.get('cpf')}' já existe no banco de dados."
    except sqlite3.Error as e:
        return False, f"Ocorreu um erro ao salvar: {e}"
    finally:
        if conn:
            conn.close()

def fetch_data(conn, search_query=None, state_filter=None):
    """Busca dados de clientes, opcionalmente com filtros."""
    try:
        base_query = f"SELECT {', '.join(ALL_COLUMNS_WITH_ID)} FROM customers"
        params = []
        conditions = []
        if search_query:
            conditions.append("(nome_completo LIKE ? OR cpf LIKE ?)")
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        if state_filter and state_filter != "Todos":
            conditions.append("estado = ?")
            params.append(state_filter)
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        df = pd.read_sql_query(base_query, conn, params=params)
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.date
        df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce').dt.date
        return df
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame(columns=ALL_COLUMNS_WITH_ID)

def commit_changes(edited_df, original_df, conn):
    """
    Comita alterações (updates, deletes) do data_editor.
    Retorna um dicionário com o resultado e uma mensagem de erro em caso de falha.
    """
    updates, deletes = [], []
    
    if 'Deletar' in edited_df.columns:
        delete_mask = edited_df['Deletar'] == True
        deletes = edited_df.loc[delete_mask, 'id'].tolist()
        edited_df = edited_df[~delete_mask]

    original_df.set_index('id', inplace=True)
    edited_df.set_index('id', inplace=True)

    for idx, row in edited_df.iterrows():
        if idx in original_df.index:
            original_row = original_df.loc[idx]
            if not row.astype(str).equals(original_row.astype(str)):
                row['data_nascimento'] = row['data_nascimento'].strftime('%Y-%m-%d') if pd.notna(row['data_nascimento']) else None
                row_for_db = row.copy()
                row_for_db['data_cadastro'] = original_row['data_cadastro'].strftime('%Y-%m-%d') if pd.notna(original_row['data_cadastro']) else None
                update_data = tuple(row_for_db[col] for col in DB_COLUMNS) + (idx,)
                updates.append(update_data)

    try:
        cursor = conn.cursor()
        if updates:
            update_columns = [col for col in DB_COLUMNS if col != 'data_cadastro']
            update_query = f"UPDATE customers SET {', '.join([f'{col}=?' for col in update_columns])} WHERE id=?"
            final_updates = [u[:-2] + (u[-1],) for u in updates]
            cursor.executemany(update_query, final_updates)
        if deletes:
            cursor.executemany("DELETE FROM customers WHERE id=?", [(d,) for d in deletes])
        conn.commit()
        return {"updated": len(updates), "deleted": len(deletes)}, None
    except sqlite3.Error as e:
        conn.rollback()
        return None, f"Ocorreu um erro no banco de dados: {e}"

# --- Funções Auxiliares ---
def df_to_csv(df):
    """Converte um DataFrame para CSV para download."""
    return df.to_csv(index=False).encode('utf-8')