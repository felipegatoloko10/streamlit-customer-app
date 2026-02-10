import pytest
from sqlmodel import Session, create_engine, SQLModel
from models import Cliente, Contato, Endereco
from repositories.customer_repository import CustomerRepository
from datetime import date

# Cria um banco de dados em memória para testes
@pytest.fixture
def db_session():
    """Fixture que cria uma sessão de banco de dados isolada para testes."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def customer_repository(db_session):
    """Fixture que cria uma instância do CustomerRepository."""
    return CustomerRepository(db_session)

@pytest.fixture
def sample_cliente():
    """Fixture que cria um cliente de exemplo."""
    return Cliente(
        nome_completo="João da Silva",
        tipo_documento="CPF",
        cpf="12345678900",
        data_nascimento=date(1990, 1, 1),
        data_cadastro=date.today()
    )

@pytest.fixture
def sample_contato():
    """Fixture que cria um contato de exemplo."""
    return Contato(
        nome_contato="João da Silva",
        telefone="11999999999",
        email_contato="joao@example.com",
        tipo_contato="Principal"
    )

@pytest.fixture
def sample_endereco():
    """Fixture que cria um endereço de exemplo."""
    return Endereco(
        cep="01234567",
        logradouro="Rua Exemplo",
        numero="123",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        tipo_endereco="Principal",
        latitude=-23.550520,
        longitude=-46.633308
    )


class TestCustomerRepository:
    """Testes para CustomerRepository."""

    def test_create_customer(self, customer_repository, sample_cliente, sample_contato, sample_endereco):
        """Testa a criação de um cliente com contatos e endereços."""
        created_cliente = customer_repository.create_customer(
            sample_cliente,
            [sample_contato],
            [sample_endereco]
        )
        
        assert created_cliente.id is not None
        assert created_cliente.nome_completo == "João da Silva"
        assert len(created_cliente.contatos) == 1
        assert len(created_cliente.enderecos) == 1
        assert created_cliente.contatos[0].telefone == "11999999999"
        assert created_cliente.enderecos[0].cidade == "São Paulo"

    def test_get_customer_by_id(self, customer_repository, sample_cliente, sample_contato, sample_endereco):
        """Testa a busca de um cliente por ID."""
        created = customer_repository.create_customer(sample_cliente, [sample_contato], [sample_endereco])
        
        fetched = customer_repository.get(created.id)
        
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.nome_completo == "João da Silva"
        # Eager loading deve carregar as relationships
        assert len(fetched.contatos) == 1
        assert len(fetched.enderecos) == 1

    def test_list_customers(self, customer_repository, sample_cliente):
        """Testa a listagem paginada de clientes."""
        # Cria alguns clientes
        for i in range(5):
            cliente = Cliente(
                nome_completo=f"Cliente {i}",
                tipo_documento="CPF",
                cpf=f"1234567890{i}",
                data_cadastro=date.today()
            )
            customer_repository.create_customer(cliente, [], [])
        
        # Busca com paginação
        results = customer_repository.list_customers(offset=0, limit=3)
        
        assert len(results) == 3

    def test_count_customers(self, customer_repository, sample_cliente):
        """Testa a contagem de clientes."""
        # Cria alguns clientes
        for i in range(5):
            cliente = Cliente(
                nome_completo=f"Cliente {i}",
                tipo_documento="CPF",
                cpf=f"1234567890{i}",
                data_cadastro=date.today()
            )
            customer_repository.create_customer(cliente, [], [])
        
        count = customer_repository.count_customers()
        
        assert count == 5

    def test_search_customers(self, customer_repository):
        """Testa a busca de clientes por nome ou CPF."""
        cliente1 = Cliente(
            nome_completo="Maria Santos",
            tipo_documento="CPF",
            cpf="11111111111",
            data_cadastro=date.today()
        )
        cliente2 = Cliente(
            nome_completo="José Oliveira",
            tipo_documento="CPF",
            cpf="22222222222",
            data_cadastro=date.today()
        )
        
        customer_repository.create_customer(cliente1, [], [])
        customer_repository.create_customer(cliente2, [], [])
        
        # Busca por nome
        results = customer_repository.list_customers(search_query="Maria")
        assert len(results) == 1
        assert results[0].nome_completo == "Maria Santos"

    def test_update_customer(self, customer_repository, sample_cliente, sample_contato, sample_endereco):
        """Testa a atualização de um cliente."""
        created = customer_repository.create_customer(sample_cliente, [sample_contato], [sample_endereco])
        
        update_data = {
            "nome_completo": "João Silva Atualizado",
            "observacao": "Cliente VIP"
        }
        
        updated = customer_repository.update_customer(created.id, update_data)
        
        assert updated is not None
        assert updated.nome_completo == "João Silva Atualizado"
        assert updated.observacao == "Cliente VIP"

    def test_delete_customer(self, customer_repository, sample_cliente, sample_contato, sample_endereco):
        """Testa a exclusão de um cliente."""
        created = customer_repository.create_customer(sample_cliente, [sample_contato], [sample_endereco])
        customer_id = created.id
        
        result = customer_repository.delete_customer(customer_id)
        
        assert result is True
        
        # Verifica que o cliente foi removido
        deleted = customer_repository.get(customer_id)
        assert deleted is None

    def test_get_unique_states(self, customer_repository):
        """Testa a obtenção de estados únicos."""
        endereco_sp = Endereco(cep="01234567", estado="SP", tipo_endereco="Principal")
        endereco_rj = Endereco(cep="12345678", estado="RJ", tipo_endereco="Principal")
        
        cliente1 = Cliente(nome_completo="Cliente SP", tipo_documento="CPF", cpf="11111111111", data_cadastro=date.today())
        cliente2 = Cliente(nome_completo="Cliente RJ", tipo_documento="CPF", cpf="22222222222", data_cadastro=date.today())
        
        customer_repository.create_customer(cliente1, [], [endereco_sp])
        customer_repository.create_customer(cliente2, [], [endereco_rj])
        
        states = customer_repository.get_unique_states()
        
        assert len(states) == 2
        assert "SP" in states
        assert "RJ" in states
