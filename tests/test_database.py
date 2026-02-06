import pytest
import sqlite3
import pandas as pd
from unittest.mock import patch
import database
import validators

@pytest.fixture
def db_connection():
    """Fixture para criar um banco de dados em memória para os testes."""
    conn = sqlite3.connect(":memory:")
    # Usando o esquema de tabela mais recente do database.py
    conn.execute('''
        CREATE TABLE customers (
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
    yield conn
    conn.close()

@patch('database.get_db_connection')
@patch('validators.is_valid_cpf', return_value=True) # Mock para evitar validação real do CPF
def test_insert_customer(mock_is_valid_cpf, mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    customer_data = {'nome_completo': 'Test User', 'tipo_documento': 'CPF', 'cpf': '123.456.789-00'}
    database.insert_customer(customer_data)
    
    df = pd.read_sql_query("SELECT * FROM customers", db_connection)
    assert len(df) == 1
    assert df.iloc[0]['nome_completo'] == 'Test User'
    assert df.iloc[0]['tipo_documento'] == 'CPF'

@patch('database.get_db_connection')
@patch('validators.is_valid_cpf', return_value=True)
def test_insert_customer_duplicate_cpf(mock_is_valid_cpf, mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    customer_data = {'nome_completo': 'Test User', 'tipo_documento': 'CPF', 'cpf': '123.456.789-00'}
    database.insert_customer(customer_data)
    
    with pytest.raises(database.DuplicateEntryError):
        database.insert_customer(customer_data)

@patch('database.get_db_connection')
def test_fetch_data(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (nome_completo, tipo_documento, cpf) VALUES ('Test User 1', 'CPF', '111.111.111-11')")
    db_connection.execute("INSERT INTO customers (nome_completo, tipo_documento, cnpj) VALUES ('Test User 2', 'CNPJ', '11.111.111/0001-11')")
    db_connection.commit()
    
    df = database.fetch_data()
    assert len(df) == 2

@patch('database.get_db_connection')
@patch('validators.is_valid_cpf', return_value=True)
def test_commit_changes_update(mock_is_valid_cpf, mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (id, nome_completo, tipo_documento, cpf) VALUES (1, 'Original Name', 'CPF', '111.111.111-11')")
    db_connection.commit()

    # Criando um DataFrame consistente com as colunas esperadas por fetch_data
    original_df = pd.DataFrame({
        'id': [1],
        'nome_completo': ['Original Name'],
        'tipo_documento': ['CPF'],
        'cpf': ['111.111.111-11'],
        'cnpj': [None], 'contato1': [None], 'telefone1': [None], 'contato2': [None], 
        'telefone2': [None], 'cargo': [None], 'email': [None], 'data_nascimento': [None],
        'cep': [None], 'endereco': [None], 'numero': [None], 'complemento': [None], 
        'bairro': [None], 'cidade': [None], 'estado': [None], 'observacao': [None], 
        'data_cadastro': [pd.to_datetime('today').date()]
    })

    edited_df = original_df.copy()
    edited_df.loc[0, 'nome_completo'] = 'Updated Name'
    
    # Mock para a função _get_updates não depender de fetch_data
    database.commit_changes(edited_df, original_df)
    
    df = pd.read_sql_query("SELECT * FROM customers WHERE id=1", db_connection)
    assert df.iloc[0]['nome_completo'] == 'Updated Name'


@patch('database.get_db_connection')
def test_commit_changes_delete(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (id, nome_completo, tipo_documento, cpf) VALUES (1, 'User to Delete', 'CPF', '111.111.111-11')")
    db_connection.commit()

    original_df = pd.DataFrame({'id': [1], 'nome_completo': ['User to Delete']})
    
    # Adicionando a coluna 'Deletar' para simular a ação na UI
    edited_df = original_df.copy()
    edited_df['Deletar'] = True
    
    database.commit_changes(edited_df, original_df)
    
    df = pd.read_sql_query("SELECT * FROM customers", db_connection)
    assert len(df) == 0