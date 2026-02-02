import sqlite3
import pandas as pd
import streamlit as st
import logging
import validators
import services
import backup_manager

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
        if not row.get('cpf'):
            raise validators.ValidationError("O campo 'CPF' é obrigatório.")
        validators.is_valid_cpf(row['cpf'])
    elif doc_type == 'CNPJ':
        if not row.get('cnpj'):
            raise validators.ValidationError("O campo 'CNPJ' é obrigatório.")
        validators.is_valid_cnpj(row['cnpj'])
    
    if row.get('telefone1'):
        validators.is_valid_whatsapp(row['telefone1'])
    if row.get('telefone2'):
        validators.is_valid_whatsapp(row['telefone2'])
    if row.get('email'):
        validators.is_valid_email(row['email'])

def insert_customer(data: dict):
    """Insere um novo cliente após validação e sanitização."""
    
    clean_data = {}
    for col in DB_COLUMNS:
        if col in data and data[col] not in [None, '']:
            value = data[col]
            if col == 'cpf':
                clean_data[col] = validators.unformat_cpf(value)
            elif col == 'cnpj':
                clean_data[col] = validators.unformat_cnpj(value)
            elif col in ['telefone1', 'telefone2']:
                clean_data[col] = validators.unformat_whatsapp(value)
            else:
                clean_data[col] = value

    _validate_row(pd.Series(clean_data))
    
    conn = get_db_connection()
    try:
        columns = ', '.join(clean_data.keys())
        placeholders = ', '.join(['?'] * len(clean_data))
        sql = f"INSERT INTO customers ({columns}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.execute(sql, list(clean_data.values()))
        new_customer_id = cursor.lastrowid
        conn.commit()
        logging.info(f"Cliente '{clean_data.get('nome_completo')}' inserido com sucesso com ID: {new_customer_id}.")

        try:
            services.send_new_customer_email(data, new_customer_id)
        except Exception as e:
            logging.error(f"Falha ao enviar e-mail de notificação para o cliente ID {new_customer_id}: {e}")
        
        try:
            backup_manager.increment_and_check_backup()
        except Exception as e:
            logging.error(f"Erro ao tentar verificar/realizar backup automático: {e}")

    except sqlite3.IntegrityError as e:
        logging.warning(f"Tentativa de inserir CPF/CNPJ duplicado para '{clean_data.get('nome_completo')}'.")
        raise DuplicateEntryError("O CPF ou CNPJ informado já existe no banco de dados.") from e
    except sqlite3.Error as e:
        logging.error(f"Erro ao inserir cliente '{clean_data.get('nome_completo')}': {e}")
        conn.rollback()
        raise DatabaseError(f"Ocorreu um erro ao salvar o novo cliente: {e}") from e

# ... (o resto do arquivo permanece o mesmo)
def delete_customer(customer_id: int):
    # ...
def update_customer(customer_id: int, data: dict):
    # ...
# etc.
