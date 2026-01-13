import pytest
import sqlite3
import pandas as pd
from unittest.mock import patch
import database

@pytest.fixture
def db_connection():
    """Fixture para criar um banco de dados em memória para os testes."""
    conn = sqlite3.connect(":memory:")
    conn.execute('''
        CREATE TABLE customers (
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
    yield conn
    conn.close()

@patch('database.get_db_connection')
def test_insert_customer(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    customer_data = {'nome_completo': 'Test User', 'cpf': '123.456.789-00'}
    database.insert_customer(customer_data)
    df = pd.read_sql_query("SELECT * FROM customers", db_connection)
    assert len(df) == 1
    assert df.iloc[0]['nome_completo'] == 'Test User'

@patch('database.get_db_connection')
def test_insert_customer_duplicate_cpf(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    customer_data = {'nome_completo': 'Test User', 'cpf': '123.456.789-00'}
    database.insert_customer(customer_data)
    with pytest.raises(database.DuplicateCPFError):
        database.insert_customer(customer_data)

@patch('database.get_db_connection')
def test_fetch_data(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (nome_completo, cpf) VALUES ('Test User 1', '111.111.111-11')")
    db_connection.execute("INSERT INTO customers (nome_completo, cpf) VALUES ('Test User 2', '222.222.222-22')")
    db_connection.commit()
    
    df = database.fetch_data()
    assert len(df) == 2

@patch('database.get_db_connection')
def test_commit_changes_update(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (id, nome_completo, cpf) VALUES (1, 'Original Name', '111.111.111-11')")
    db_connection.commit()

    original_df = database.fetch_data()
    edited_df = original_df.copy()
    edited_df.loc[0, 'nome_completo'] = 'Updated Name'
    
    database.commit_changes(edited_df, original_df)
    
    df = pd.read_sql_query("SELECT * FROM customers WHERE id=1", db_connection)
    assert df.iloc[0]['nome_completo'] == 'Updated Name'

@patch('database.get_db_connection')
def test_commit_changes_delete(mock_get_db_connection, db_connection):
    mock_get_db_connection.return_value = db_connection
    db_connection.execute("INSERT INTO customers (id, nome_completo, cpf) VALUES (1, 'User to Delete', '111.111.111-11')")
    db_connection.commit()

    original_df = database.fetch_data()
    edited_df = original_df.copy()
    edited_df['Deletar'] = True
    
    database.commit_changes(edited_df, original_df)
    
    df = pd.read_sql_query("SELECT * FROM customers", db_connection)
    assert len(df) == 0
