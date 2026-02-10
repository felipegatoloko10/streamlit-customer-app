import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import patch
import database
from models import Cliente, Contato, Endereco
import pandas as pd
import datetime

# Setup in-memory database for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(autouse=True)
def mock_get_session(session):
    with patch("database.get_session", return_value=session):
        # We also need to patch database_config.engine if it's used directly in read functions
        with patch("database.database_config.engine", session.bind):
            yield

def test_insert_customer(session):
    customer_data = {
        'nome_completo': 'Test User', 
        'tipo_documento': 'CPF', 
        'cpf': '123.456.789-00',
        'email': 'test@example.com',
        'telefone1': '(11) 99999-9999'
    }
    
    # Mock validators to avoid external API calls or complex regex logic if needed
    # But database.py validators usage is minimal/internal, so we might rely on them providing we pass valid format.
    # The provided CPF is valid format but might fail check_digit if logic is strict.
    # Let's mock validators.unformat_cpf/cnpj and is_valid to be safe or pass valid data.
    # Assuming validators work for "valid-looking" dummy data or we mock them.
    
    with patch('validators.is_valid_cpf', return_value=True), \
         patch('validators.unformat_cpf', side_effect=lambda x: x.replace('.', '').replace('-', '')), \
         patch('validators.unformat_whatsapp', side_effect=lambda x: x):
         
        database.insert_customer(customer_data)
    
    cliente = session.exec(select(Cliente)).first()
    assert cliente is not None
    assert cliente.nome_completo == 'Test User'
    assert cliente.cpf == '12345678900'
    
    contato = session.exec(select(Contato)).first()
    assert contato is not None
    assert contato.email_contato == 'test@example.com'

def test_insert_customer_duplicate_cpf(session):
    customer_data = {
        'nome_completo': 'Test User 1', 
        'tipo_documento': 'CPF', 
        'cpf': '123.456.789-00'
    }
    
    with patch('validators.is_valid_cpf', return_value=True), \
         patch('validators.unformat_cpf', side_effect=lambda x: x.replace('.', '').replace('-', '')):
        
        database.insert_customer(customer_data)
        
        with pytest.raises(database.DuplicateEntryError):
            database.insert_customer(customer_data)

def test_update_customer(session):
    # Setup initial data
    cliente = Cliente(nome_completo="Old Name", tipo_documento="CPF", cpf="11111111111")
    session.add(cliente)
    session.commit()
    
    update_data = {'nome_completo': 'New Name'}
    
    database.update_customer(cliente.id, update_data)
    
    updated_cliente = session.get(Cliente, cliente.id)
    assert updated_cliente.nome_completo == 'New Name'

def test_delete_customer(session):
    cliente = Cliente(nome_completo="To Delete", tipo_documento="CPF", cpf="22222222222")
    session.add(cliente)
    session.commit()
    
    database.delete_customer(cliente.id)
    
    deleted_cliente = session.get(Cliente, cliente.id)
    assert deleted_cliente is None

def test_fetch_data(session):
    # Create sample data
    c1 = Cliente(nome_completo="User A", tipo_documento="CPF", cpf="111")
    c2 = Cliente(nome_completo="User B", tipo_documento="CNPJ", cnpj="222")
    session.add(c1)
    session.add(c2)
    session.commit()
    
    # We create address to test joins
    e1 = Endereco(cliente_id=c1.id, tipo_endereco="Principal", estado="SP", cidade="Sao Paulo")
    session.add(e1)
    session.commit()
    
    with patch('database.database_config.engine', session.bind):
        df = database.fetch_data()
    
    # Depending on default ordering (DESC id), User B might be first
    assert len(df) == 2
    assert "User A" in df['nome_completo'].values
    assert "User B" in df['nome_completo'].values

def test_get_customer_by_id(session):
    c1 = Cliente(nome_completo="Target User", tipo_documento="CPF", cpf="999")
    session.add(c1)
    session.commit()
    
    data = database.get_customer_by_id(c1.id)
    assert data is not None
    assert data['nome_completo'] == "Target User"

def test_count_total_records(session):
    session.add(Cliente(nome_completo="1", tipo_documento="CPF"))
    session.add(Cliente(nome_completo="2", tipo_documento="CPF"))
    session.commit()
    
    count = database.count_total_records()
    assert count == 2